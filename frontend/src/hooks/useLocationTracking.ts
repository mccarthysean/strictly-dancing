/**
 * Location tracking hook for real-time location sharing during active sessions.
 *
 * Handles:
 * - Geolocation API permission handling
 * - WebSocket connection for location updates
 * - Automatic location updates every 30 seconds
 * - Receiving partner's location updates
 */

import { useCallback, useEffect, useRef, useState } from 'react'
import { getAccessToken } from '@/lib/api/$api'

// API base URL from environment variable
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8001'
const WS_BASE_URL = API_BASE_URL.replace(/^http/, 'ws')

// Location update interval (30 seconds)
const LOCATION_UPDATE_INTERVAL_MS = 30_000

// WebSocket message types
type LocationMessageType =
  | 'location_update'
  | 'location_received'
  | 'connected'
  | 'disconnected'
  | 'error'
  | 'session_ended'

interface LocationData {
  latitude: number
  longitude: number
  accuracy?: number
  altitude?: number
  heading?: number
  speed?: number
  timestamp: string
}

interface WebSocketMessage {
  type: LocationMessageType
  booking_id: string
  data?: {
    user_id?: string
    user_role?: string
    location?: LocationData
    message?: string
  }
  timestamp: string
  sender_id?: string
}

// Geolocation permission state
type GeolocationPermission = 'prompt' | 'granted' | 'denied' | 'unavailable'

interface LocationTrackingState {
  /** Current user's location */
  myLocation: LocationData | null
  /** Partner's location */
  partnerLocation: LocationData | null
  /** Whether WebSocket is connected */
  isConnected: boolean
  /** Whether location tracking is active */
  isTracking: boolean
  /** Geolocation permission state */
  permission: GeolocationPermission
  /** Error message if any */
  error: string | null
  /** Whether session has ended */
  sessionEnded: boolean
}

interface UseLocationTrackingOptions {
  /** Booking ID for the active session */
  bookingId: string
  /** Whether to automatically start tracking */
  autoStart?: boolean
  /** Location update interval in milliseconds (default: 30000) */
  updateInterval?: number
}

interface UseLocationTrackingReturn extends LocationTrackingState {
  /** Start location tracking */
  startTracking: () => Promise<void>
  /** Stop location tracking */
  stopTracking: () => void
  /** Request geolocation permission */
  requestPermission: () => Promise<GeolocationPermission>
  /** Send a manual location update */
  sendLocationUpdate: (location: GeolocationPosition) => void
}

export function useLocationTracking({
  bookingId,
  autoStart = false,
  updateInterval = LOCATION_UPDATE_INTERVAL_MS,
}: UseLocationTrackingOptions): UseLocationTrackingReturn {
  const [state, setState] = useState<LocationTrackingState>({
    myLocation: null,
    partnerLocation: null,
    isConnected: false,
    isTracking: false,
    permission: 'prompt',
    error: null,
    sessionEnded: false,
  })

  const wsRef = useRef<WebSocket | null>(null)
  const watchIdRef = useRef<number | null>(null)
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const lastPositionRef = useRef<GeolocationPosition | null>(null)

  // Check geolocation permission
  const checkPermission = useCallback(async (): Promise<GeolocationPermission> => {
    if (!navigator.geolocation) {
      return 'unavailable'
    }

    if (navigator.permissions) {
      try {
        const result = await navigator.permissions.query({ name: 'geolocation' })
        return result.state as GeolocationPermission
      } catch {
        // Permissions API may not support geolocation query
        return 'prompt'
      }
    }

    return 'prompt'
  }, [])

  // Request geolocation permission
  const requestPermission = useCallback(async (): Promise<GeolocationPermission> => {
    if (!navigator.geolocation) {
      setState((prev) => ({ ...prev, permission: 'unavailable', error: 'Geolocation not supported' }))
      return 'unavailable'
    }

    return new Promise((resolve) => {
      navigator.geolocation.getCurrentPosition(
        () => {
          setState((prev) => ({ ...prev, permission: 'granted', error: null }))
          resolve('granted')
        },
        (error) => {
          let permission: GeolocationPermission = 'denied'
          let errorMessage = 'Location permission denied'

          if (error.code === error.POSITION_UNAVAILABLE) {
            permission = 'unavailable'
            errorMessage = 'Location unavailable'
          } else if (error.code === error.TIMEOUT) {
            errorMessage = 'Location request timed out'
          }

          setState((prev) => ({ ...prev, permission, error: errorMessage }))
          resolve(permission)
        },
        { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
      )
    })
  }, [])

  // Convert GeolocationPosition to LocationData
  const positionToLocationData = useCallback((position: GeolocationPosition): LocationData => {
    const data: LocationData = {
      latitude: position.coords.latitude,
      longitude: position.coords.longitude,
      timestamp: new Date(position.timestamp).toISOString(),
    }

    // Only add optional fields if they have actual values
    if (position.coords.accuracy !== null) {
      data.accuracy = position.coords.accuracy
    }
    if (position.coords.altitude !== null) {
      data.altitude = position.coords.altitude
    }
    if (position.coords.heading !== null) {
      data.heading = position.coords.heading
    }
    if (position.coords.speed !== null) {
      data.speed = position.coords.speed
    }

    return data
  }, [])

  // Send location update via WebSocket
  const sendLocationUpdate = useCallback(
    (position: GeolocationPosition) => {
      if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
        return
      }

      const locationData = positionToLocationData(position)

      wsRef.current.send(
        JSON.stringify({
          type: 'location_update',
          latitude: locationData.latitude,
          longitude: locationData.longitude,
          accuracy: locationData.accuracy,
          altitude: locationData.altitude,
          heading: locationData.heading,
          speed: locationData.speed,
        })
      )

      setState((prev) => ({ ...prev, myLocation: locationData }))
      lastPositionRef.current = position
    },
    [positionToLocationData]
  )

  // Handle incoming WebSocket messages
  const handleWebSocketMessage = useCallback((event: MessageEvent) => {
    try {
      const message: WebSocketMessage = JSON.parse(event.data)

      switch (message.type) {
        case 'connected':
          setState((prev) => ({ ...prev, isConnected: true, error: null }))
          break

        case 'location_received':
          if (message.data?.location) {
            setState((prev) => ({ ...prev, partnerLocation: message.data?.location ?? null }))
          }
          break

        case 'disconnected':
          // Partner disconnected - keep their last known location
          break

        case 'session_ended':
          setState((prev) => ({
            ...prev,
            sessionEnded: true,
            isTracking: false,
          }))
          break

        case 'error':
          setState((prev) => ({ ...prev, error: message.data?.message ?? 'Unknown error' }))
          break
      }
    } catch {
      // Ignore parse errors
    }
  }, [])

  // Connect to WebSocket
  const connectWebSocket = useCallback(() => {
    const token = getAccessToken()
    if (!token) {
      setState((prev) => ({ ...prev, error: 'Not authenticated' }))
      return
    }

    const wsUrl = `${WS_BASE_URL}/ws/location/${bookingId}?token=${encodeURIComponent(token)}`

    const ws = new WebSocket(wsUrl)
    wsRef.current = ws

    ws.onopen = () => {
      setState((prev) => ({ ...prev, isConnected: true, error: null }))
    }

    ws.onmessage = handleWebSocketMessage

    ws.onerror = () => {
      setState((prev) => ({ ...prev, error: 'WebSocket connection error' }))
    }

    ws.onclose = (event) => {
      setState((prev) => ({
        ...prev,
        isConnected: false,
        isTracking: false,
        error: event.code === 4003 ? 'Session not in progress' : null,
      }))
    }
  }, [bookingId, handleWebSocketMessage])

  // Start location tracking
  const startTracking = useCallback(async () => {
    // Check/request permission first
    let permission = await checkPermission()
    if (permission === 'prompt') {
      permission = await requestPermission()
    }

    if (permission !== 'granted') {
      return
    }

    setState((prev) => ({ ...prev, isTracking: true, error: null }))

    // Connect WebSocket
    connectWebSocket()

    // Start watching location
    watchIdRef.current = navigator.geolocation.watchPosition(
      (position) => {
        lastPositionRef.current = position
        sendLocationUpdate(position)
      },
      (error) => {
        let errorMessage = 'Location error'
        if (error.code === error.PERMISSION_DENIED) {
          errorMessage = 'Location permission denied'
          setState((prev) => ({ ...prev, permission: 'denied' }))
        } else if (error.code === error.POSITION_UNAVAILABLE) {
          errorMessage = 'Location unavailable'
        } else if (error.code === error.TIMEOUT) {
          errorMessage = 'Location request timed out'
        }
        setState((prev) => ({ ...prev, error: errorMessage }))
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 5000 }
    )

    // Also set up interval to send updates periodically (in case watchPosition doesn't fire often enough)
    intervalRef.current = setInterval(() => {
      if (lastPositionRef.current && wsRef.current?.readyState === WebSocket.OPEN) {
        sendLocationUpdate(lastPositionRef.current)
      }
    }, updateInterval)
  }, [checkPermission, requestPermission, connectWebSocket, sendLocationUpdate, updateInterval])

  // Stop location tracking
  const stopTracking = useCallback(() => {
    // Stop watching position
    if (watchIdRef.current !== null) {
      navigator.geolocation.clearWatch(watchIdRef.current)
      watchIdRef.current = null
    }

    // Clear interval
    if (intervalRef.current !== null) {
      clearInterval(intervalRef.current)
      intervalRef.current = null
    }

    // Close WebSocket
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }

    setState((prev) => ({
      ...prev,
      isTracking: false,
      isConnected: false,
    }))
  }, [])

  // Check initial permission state
  useEffect(() => {
    checkPermission().then((permission) => {
      setState((prev) => ({ ...prev, permission }))
    })
  }, [checkPermission])

  // Auto-start if enabled
  useEffect(() => {
    if (autoStart) {
      startTracking()
    }

    return () => {
      stopTracking()
    }
    // Only run on mount/unmount
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [autoStart])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopTracking()
    }
    // Only run on unmount
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return {
    ...state,
    startTracking,
    stopTracking,
    requestPermission,
    sendLocationUpdate,
  }
}
