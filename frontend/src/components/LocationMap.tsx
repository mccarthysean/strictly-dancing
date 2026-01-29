/**
 * LocationMap component for displaying user and partner locations on a map.
 *
 * Uses a simple visual representation since we don't want to add a full map library.
 * Shows:
 * - Both user locations as markers
 * - Distance between users
 * - Last update timestamps
 */

import { useMemo } from 'react'

interface LocationData {
  latitude: number
  longitude: number
  accuracy?: number
  altitude?: number
  heading?: number
  speed?: number
  timestamp: string
}

interface LocationMapProps {
  /** Current user's location */
  myLocation: LocationData | null
  /** Partner's location */
  partnerLocation: LocationData | null
  /** Current user's name or label */
  myLabel?: string
  /** Partner's name or label */
  partnerLabel?: string
  /** Whether to show the map controls */
  showControls?: boolean
  /** Additional CSS class */
  className?: string
}

/**
 * Calculate distance between two coordinates using Haversine formula
 */
function calculateDistance(
  lat1: number,
  lon1: number,
  lat2: number,
  lon2: number
): number {
  const R = 6371 // Earth's radius in kilometers
  const dLat = ((lat2 - lat1) * Math.PI) / 180
  const dLon = ((lon2 - lon1) * Math.PI) / 180
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos((lat1 * Math.PI) / 180) *
      Math.cos((lat2 * Math.PI) / 180) *
      Math.sin(dLon / 2) *
      Math.sin(dLon / 2)
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
  return R * c
}

/**
 * Format distance for display
 */
function formatDistance(km: number): string {
  if (km < 0.1) {
    return `${Math.round(km * 1000)} m`
  }
  if (km < 1) {
    return `${Math.round(km * 1000)} m`
  }
  return `${km.toFixed(1)} km`
}

/**
 * Format time ago from timestamp
 */
function formatTimeAgo(timestamp: string): string {
  const now = new Date()
  const then = new Date(timestamp)
  const seconds = Math.floor((now.getTime() - then.getTime()) / 1000)

  if (seconds < 10) return 'just now'
  if (seconds < 60) return `${seconds}s ago`
  if (seconds < 120) return '1 min ago'
  if (seconds < 3600) return `${Math.floor(seconds / 60)} min ago`
  return then.toLocaleTimeString()
}

/**
 * Open location in Google Maps
 */
function openInGoogleMaps(lat: number, lng: number) {
  const url = `https://www.google.com/maps?q=${lat},${lng}`
  window.open(url, '_blank')
}

export function LocationMap({
  myLocation,
  partnerLocation,
  myLabel = 'You',
  partnerLabel = 'Partner',
  showControls = true,
  className = '',
}: LocationMapProps) {
  // Calculate distance between users
  const distance = useMemo(() => {
    if (!myLocation || !partnerLocation) return null
    return calculateDistance(
      myLocation.latitude,
      myLocation.longitude,
      partnerLocation.latitude,
      partnerLocation.longitude
    )
  }, [myLocation, partnerLocation])

  // Calculate relative positions for the visual map (normalized to 0-100)
  const positions = useMemo(() => {
    if (!myLocation && !partnerLocation) {
      return { my: null, partner: null }
    }

    if (myLocation && !partnerLocation) {
      return { my: { x: 50, y: 50 }, partner: null }
    }

    if (!myLocation && partnerLocation) {
      return { my: null, partner: { x: 50, y: 50 } }
    }

    if (myLocation && partnerLocation) {
      // Calculate relative positions
      const latDiff = partnerLocation.latitude - myLocation.latitude
      const lngDiff = partnerLocation.longitude - myLocation.longitude

      // Scale to fit in view (max difference shown is ~5km)
      const maxDiff = 0.05 // ~5km at equator
      const scaledLatDiff = Math.max(-1, Math.min(1, latDiff / maxDiff))
      const scaledLngDiff = Math.max(-1, Math.min(1, lngDiff / maxDiff))

      // Convert to percentage (center at 50%)
      const myX = 50 - scaledLngDiff * 30
      const myY = 50 + scaledLatDiff * 30
      const partnerX = 50 + scaledLngDiff * 30
      const partnerY = 50 - scaledLatDiff * 30

      return {
        my: { x: myX, y: myY },
        partner: { x: partnerX, y: partnerY },
      }
    }

    return { my: null, partner: null }
  }, [myLocation, partnerLocation])

  return (
    <div className={`bg-gray-100 rounded-lg overflow-hidden ${className}`}>
      {/* Map visualization */}
      <div
        className="relative bg-gradient-to-br from-blue-50 to-green-50 border-b border-gray-200"
        style={{ height: '200px' }}
      >
        {/* Grid lines */}
        <div className="absolute inset-0 grid grid-cols-4 grid-rows-4">
          {Array.from({ length: 16 }).map((_, i) => (
            <div key={i} className="border border-gray-200/30" />
          ))}
        </div>

        {/* Connection line between users */}
        {positions.my && positions.partner && (
          <svg
            className="absolute inset-0 w-full h-full pointer-events-none"
            style={{ zIndex: 1 }}
          >
            <line
              x1={`${positions.my.x}%`}
              y1={`${positions.my.y}%`}
              x2={`${positions.partner.x}%`}
              y2={`${positions.partner.y}%`}
              stroke="#3B82F6"
              strokeWidth="2"
              strokeDasharray="4 4"
            />
          </svg>
        )}

        {/* My location marker */}
        {positions.my && (
          <div
            className="absolute transform -translate-x-1/2 -translate-y-1/2"
            style={{
              left: `${positions.my.x}%`,
              top: `${positions.my.y}%`,
              zIndex: 10,
            }}
          >
            <div className="relative">
              {/* Accuracy circle */}
              {myLocation?.accuracy && (
                <div
                  className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 rounded-full bg-blue-500/20 border border-blue-500/30"
                  style={{
                    width: Math.min(100, Math.max(20, myLocation.accuracy / 2)),
                    height: Math.min(100, Math.max(20, myLocation.accuracy / 2)),
                  }}
                />
              )}
              {/* Marker */}
              <div className="relative">
                <div className="w-4 h-4 rounded-full bg-blue-500 border-2 border-white shadow-lg" />
                <div className="absolute -bottom-6 left-1/2 -translate-x-1/2 whitespace-nowrap text-xs font-medium text-blue-700 bg-white px-1 rounded shadow-sm">
                  {myLabel}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Partner location marker */}
        {positions.partner && (
          <div
            className="absolute transform -translate-x-1/2 -translate-y-1/2"
            style={{
              left: `${positions.partner.x}%`,
              top: `${positions.partner.y}%`,
              zIndex: 10,
            }}
          >
            <div className="relative">
              {/* Accuracy circle */}
              {partnerLocation?.accuracy && (
                <div
                  className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 rounded-full bg-purple-500/20 border border-purple-500/30"
                  style={{
                    width: Math.min(100, Math.max(20, partnerLocation.accuracy / 2)),
                    height: Math.min(100, Math.max(20, partnerLocation.accuracy / 2)),
                  }}
                />
              )}
              {/* Marker */}
              <div className="relative">
                <div className="w-4 h-4 rounded-full bg-purple-500 border-2 border-white shadow-lg" />
                <div className="absolute -bottom-6 left-1/2 -translate-x-1/2 whitespace-nowrap text-xs font-medium text-purple-700 bg-white px-1 rounded shadow-sm">
                  {partnerLabel}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* No location message */}
        {!myLocation && !partnerLocation && (
          <div className="absolute inset-0 flex items-center justify-center text-gray-400">
            <div className="text-center">
              <svg
                className="w-12 h-12 mx-auto mb-2 opacity-50"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
                />
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
                />
              </svg>
              <p className="text-sm">Waiting for location data...</p>
            </div>
          </div>
        )}
      </div>

      {/* Location info panel */}
      <div className="p-3 space-y-2">
        {/* Distance */}
        {distance !== null && (
          <div className="flex items-center justify-center gap-2 text-sm">
            <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"
              />
            </svg>
            <span className="font-medium text-gray-700">{formatDistance(distance)} apart</span>
          </div>
        )}

        {/* Location details */}
        <div className="grid grid-cols-2 gap-2 text-xs">
          {/* My location */}
          <div className="bg-white rounded p-2">
            <div className="flex items-center gap-1 mb-1">
              <div className="w-2 h-2 rounded-full bg-blue-500" />
              <span className="font-medium text-gray-700">{myLabel}</span>
            </div>
            {myLocation ? (
              <div className="space-y-0.5 text-gray-500">
                <p>
                  {myLocation.latitude.toFixed(5)}, {myLocation.longitude.toFixed(5)}
                </p>
                {myLocation.accuracy && <p>±{Math.round(myLocation.accuracy)}m accuracy</p>}
                <p className="text-gray-400">{formatTimeAgo(myLocation.timestamp)}</p>
              </div>
            ) : (
              <p className="text-gray-400">No location</p>
            )}
          </div>

          {/* Partner location */}
          <div className="bg-white rounded p-2">
            <div className="flex items-center gap-1 mb-1">
              <div className="w-2 h-2 rounded-full bg-purple-500" />
              <span className="font-medium text-gray-700">{partnerLabel}</span>
            </div>
            {partnerLocation ? (
              <div className="space-y-0.5 text-gray-500">
                <p>
                  {partnerLocation.latitude.toFixed(5)}, {partnerLocation.longitude.toFixed(5)}
                </p>
                {partnerLocation.accuracy && <p>±{Math.round(partnerLocation.accuracy)}m accuracy</p>}
                <p className="text-gray-400">{formatTimeAgo(partnerLocation.timestamp)}</p>
              </div>
            ) : (
              <p className="text-gray-400">Waiting...</p>
            )}
          </div>
        </div>

        {/* Controls */}
        {showControls && (
          <div className="flex gap-2 pt-1">
            {myLocation && (
              <button
                type="button"
                onClick={() => openInGoogleMaps(myLocation.latitude, myLocation.longitude)}
                className="flex-1 px-3 py-1.5 text-xs font-medium text-blue-600 bg-blue-50 rounded hover:bg-blue-100 transition-colors"
              >
                View My Location
              </button>
            )}
            {partnerLocation && (
              <button
                type="button"
                onClick={() => openInGoogleMaps(partnerLocation.latitude, partnerLocation.longitude)}
                className="flex-1 px-3 py-1.5 text-xs font-medium text-purple-600 bg-purple-50 rounded hover:bg-purple-100 transition-colors"
              >
                View Partner Location
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
