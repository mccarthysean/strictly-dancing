/**
 * Active Session Screen
 *
 * Shows the active session view with:
 * - Map showing both users' locations
 * - Session timer showing elapsed time
 * - Complete Session button (for host)
 * - Emergency contact button
 */

import { createFileRoute, Link, useNavigate } from '@tanstack/react-router'
import { useState, useEffect, useCallback } from 'react'
import { $api } from '@/lib/api/$api'
import { useAuth } from '@/contexts/AuthContext'
import { useLocationTracking } from '@/hooks/useLocationTracking'
import { LocationMap } from '@/components/LocationMap'

export const Route = createFileRoute('/bookings/$bookingId/active')({
  component: ActiveSessionPage,
})

function ActiveSessionPage() {
  const { bookingId } = Route.useParams()
  const { isAuthenticated, isLoading: authLoading, user } = useAuth()
  const navigate = useNavigate()

  const [elapsedTime, setElapsedTime] = useState<number>(0)
  const [actionError, setActionError] = useState<string | null>(null)
  const [actionSuccess, setActionSuccess] = useState<string | null>(null)
  const [showCompleteConfirm, setShowCompleteConfirm] = useState(false)

  // Fetch booking details
  const { data: booking, isLoading, error } = $api.useQuery(
    'get',
    '/api/v1/bookings/{booking_id}',
    {
      params: {
        path: { booking_id: bookingId },
      },
    },
    {
      enabled: isAuthenticated,
      refetchInterval: 30000, // Refresh every 30 seconds to check status
    }
  )

  // Location tracking hook
  const {
    myLocation,
    partnerLocation,
    isConnected,
    isTracking,
    permission,
    error: locationError,
    sessionEnded,
    stopTracking,
    requestPermission,
  } = useLocationTracking({
    bookingId,
    autoStart: booking?.status === 'in_progress',
  })

  // Complete session mutation
  const completeMutation = $api.useMutation('post', '/api/v1/bookings/{booking_id}/complete')

  // Start conversation mutation
  const startConversationMutation = $api.useMutation('post', '/api/v1/conversations')

  const isHost = user?.id === booking?.host_id
  const otherParty = isHost ? booking?.client : booking?.host
  const otherPartyLabel = otherParty
    ? `${otherParty.first_name} ${otherParty.last_name}`
    : 'Partner'

  // Calculate elapsed time
  useEffect(() => {
    if (!booking?.actual_start) return

    const startTime = new Date(booking.actual_start).getTime()

    const updateElapsed = () => {
      const now = Date.now()
      setElapsedTime(Math.floor((now - startTime) / 1000))
    }

    updateElapsed()
    const interval = setInterval(updateElapsed, 1000)

    return () => clearInterval(interval)
  }, [booking?.actual_start])

  // Handle session ended from WebSocket
  useEffect(() => {
    if (sessionEnded) {
      setActionSuccess('Session has ended. Redirecting...')
      setTimeout(() => {
        navigate({ to: '/bookings/$bookingId', params: { bookingId } })
      }, 2000)
    }
  }, [sessionEnded, navigate, bookingId])

  // Redirect if booking is not in progress
  useEffect(() => {
    if (booking && booking.status !== 'in_progress') {
      navigate({ to: '/bookings/$bookingId', params: { bookingId } })
    }
  }, [booking, navigate, bookingId])

  const formatElapsedTime = useCallback((seconds: number) => {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    const secs = seconds % 60

    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
    }
    return `${minutes}:${secs.toString().padStart(2, '0')}`
  }, [])

  const handleCompleteSession = async () => {
    setActionError(null)
    try {
      await completeMutation.mutateAsync({
        params: { path: { booking_id: bookingId } },
      })
      setActionSuccess('Session completed successfully!')
      stopTracking()
      setTimeout(() => {
        navigate({ to: '/bookings/$bookingId', params: { bookingId } })
      }, 2000)
    } catch {
      setActionError('Failed to complete session. Please try again.')
    }
    setShowCompleteConfirm(false)
  }

  const handleMessagePartner = async () => {
    if (!otherParty) return

    try {
      const result = await startConversationMutation.mutateAsync({
        body: {
          participant_id: otherParty.id,
        },
      })
      navigate({ to: '/messages/$conversationId', params: { conversationId: result.id } })
    } catch {
      setActionError('Failed to start conversation')
    }
  }

  const handleEmergencyCall = () => {
    // Open emergency call dialog or call emergency services
    if (window.confirm('Do you want to call emergency services (911)?')) {
      window.location.href = 'tel:911'
    }
  }

  // Loading and auth states
  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin w-8 h-8 border-4 border-purple-500 border-t-transparent rounded-full" />
      </div>
    )
  }

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4">
        <div className="text-center">
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Login Required</h2>
          <p className="text-gray-600 mb-4">Please log in to view this session.</p>
          <Link
            to="/login"
            className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
          >
            Login
          </Link>
        </div>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin w-8 h-8 border-4 border-purple-500 border-t-transparent rounded-full mx-auto mb-4" />
          <p className="text-gray-600">Loading session...</p>
        </div>
      </div>
    )
  }

  if (error || !booking) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4">
        <div className="text-center">
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Session Not Found</h2>
          <p className="text-gray-600 mb-4">Unable to load session details.</p>
          <Link to="/bookings" className="text-purple-600 hover:text-purple-700">
            Back to Bookings
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 pb-32">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-2xl mx-auto px-4 py-3">
          <div className="flex items-center justify-between">
            <Link
              to="/bookings/$bookingId"
              params={{ bookingId }}
              className="text-gray-500 hover:text-gray-700"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
            </Link>
            <h1 className="text-lg font-semibold text-gray-900">Active Session</h1>
            <div className="w-6" /> {/* Spacer for centering */}
          </div>
        </div>
      </div>

      {/* Alert Messages */}
      {actionError && (
        <div className="max-w-2xl mx-auto px-4 mt-4">
          <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-red-700">
            {actionError}
          </div>
        </div>
      )}
      {actionSuccess && (
        <div className="max-w-2xl mx-auto px-4 mt-4">
          <div className="bg-green-50 border border-green-200 rounded-lg p-3 text-green-700">
            {actionSuccess}
          </div>
        </div>
      )}

      <div className="max-w-2xl mx-auto px-4 py-4 space-y-4">
        {/* Session Timer */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
          <div className="text-center">
            <div className="inline-flex items-center gap-2 px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm font-medium mb-2">
              <span className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
              Session In Progress
            </div>
            <div className="text-4xl font-mono font-bold text-gray-900 my-2">
              {formatElapsedTime(elapsedTime)}
            </div>
            <p className="text-sm text-gray-500">
              {booking.dance_style?.name ?? 'Dance Session'} with {otherPartyLabel}
            </p>
          </div>
        </div>

        {/* Location Tracking Status */}
        {permission !== 'granted' && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-4">
            <div className="flex items-start gap-3">
              <svg
                className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                />
              </svg>
              <div className="flex-1">
                <h3 className="font-medium text-yellow-800">Location Sharing Disabled</h3>
                <p className="text-sm text-yellow-700 mt-1">
                  {permission === 'denied'
                    ? 'Location permission was denied. Please enable location in your browser settings.'
                    : permission === 'unavailable'
                      ? 'Location services are not available on this device.'
                      : 'Enable location sharing for safety during your session.'}
                </p>
                {permission === 'prompt' && (
                  <button
                    type="button"
                    onClick={requestPermission}
                    className="mt-2 text-sm font-medium text-yellow-800 hover:text-yellow-900"
                  >
                    Enable Location Sharing
                  </button>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Location Error */}
        {locationError && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-4">
            <p className="text-sm text-red-700">{locationError}</p>
          </div>
        )}

        {/* Location Map */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          <div className="p-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h2 className="font-semibold text-gray-900">Location</h2>
              <div className="flex items-center gap-2 text-xs">
                {isConnected ? (
                  <span className="flex items-center gap-1 text-green-600">
                    <span className="w-2 h-2 bg-green-500 rounded-full" />
                    Connected
                  </span>
                ) : isTracking ? (
                  <span className="flex items-center gap-1 text-yellow-600">
                    <span className="w-2 h-2 bg-yellow-500 rounded-full animate-pulse" />
                    Connecting...
                  </span>
                ) : (
                  <span className="flex items-center gap-1 text-gray-400">
                    <span className="w-2 h-2 bg-gray-400 rounded-full" />
                    Disconnected
                  </span>
                )}
              </div>
            </div>
          </div>
          <LocationMap
            myLocation={myLocation}
            partnerLocation={partnerLocation}
            myLabel="You"
            partnerLabel={otherParty?.first_name ?? 'Partner'}
            showControls={true}
          />
        </div>

        {/* Session Info */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
          <h2 className="font-semibold text-gray-900 mb-3">Session Details</h2>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-500">Scheduled Duration</span>
              <span className="font-medium text-gray-900">{booking.duration_minutes} minutes</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Started At</span>
              <span className="font-medium text-gray-900">
                {booking.actual_start
                  ? new Date(booking.actual_start).toLocaleTimeString('en-US', {
                      hour: 'numeric',
                      minute: '2-digit',
                    })
                  : 'Not started'}
              </span>
            </div>
            {booking.location_name && (
              <div className="flex justify-between">
                <span className="text-gray-500">Location</span>
                <span className="font-medium text-gray-900">{booking.location_name}</span>
              </div>
            )}
          </div>
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-2 gap-3">
          <button
            type="button"
            onClick={handleMessagePartner}
            className="flex items-center justify-center gap-2 py-3 px-4 bg-white border border-gray-200 rounded-xl text-gray-700 hover:bg-gray-50 transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
              />
            </svg>
            Message
          </button>

          <button
            type="button"
            onClick={handleEmergencyCall}
            className="flex items-center justify-center gap-2 py-3 px-4 bg-red-50 border border-red-200 rounded-xl text-red-700 hover:bg-red-100 transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z"
              />
            </svg>
            Emergency
          </button>
        </div>
      </div>

      {/* Fixed Bottom Action Bar */}
      {isHost && (
        <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 p-4 safe-area-pb">
          <div className="max-w-2xl mx-auto">
            <button
              type="button"
              onClick={() => setShowCompleteConfirm(true)}
              disabled={completeMutation.isPending}
              className="w-full py-3 px-4 bg-green-600 text-white font-semibold rounded-xl hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {completeMutation.isPending ? 'Completing...' : 'Complete Session'}
            </button>
          </div>
        </div>
      )}

      {/* Complete Confirmation Modal */}
      {showCompleteConfirm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl shadow-xl max-w-sm w-full p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Complete Session?</h3>
            <p className="text-gray-600 mb-4">
              This will end the session and process the payment. The client will be charged and you
              will receive your payout.
            </p>
            <div className="bg-gray-50 rounded-lg p-3 mb-4 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-500">Session Duration</span>
                <span className="font-medium">{formatElapsedTime(elapsedTime)}</span>
              </div>
              <div className="flex justify-between mt-1">
                <span className="text-gray-500">Your Payout</span>
                <span className="font-medium text-green-600">
                  ${((booking.host_payout_cents ?? 0) / 100).toFixed(2)}
                </span>
              </div>
            </div>
            <div className="flex gap-3">
              <button
                type="button"
                onClick={() => setShowCompleteConfirm(false)}
                className="flex-1 py-2.5 px-4 border border-gray-300 text-gray-700 rounded-xl hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleCompleteSession}
                disabled={completeMutation.isPending}
                className="flex-1 py-2.5 px-4 bg-green-600 text-white rounded-xl hover:bg-green-700 disabled:opacity-50 transition-colors"
              >
                {completeMutation.isPending ? 'Processing...' : 'Complete'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
