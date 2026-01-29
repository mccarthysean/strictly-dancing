import { createFileRoute, Link, useNavigate } from '@tanstack/react-router'
import { useState } from 'react'
import { $api } from '@/lib/api/$api'
import { useAuth } from '@/contexts/AuthContext'
import type { components } from '@/types/api.gen'

export const Route = createFileRoute('/bookings/$bookingId')({
  component: BookingDetailPage,
})

type BookingStatus = components['schemas']['BookingStatus']

const STATUS_BADGES: Record<BookingStatus, { label: string; color: string; bgColor: string }> = {
  pending: { label: 'Pending Confirmation', color: '#92400e', bgColor: '#fef3c7' },
  confirmed: { label: 'Confirmed', color: '#065f46', bgColor: '#d1fae5' },
  in_progress: { label: 'In Progress', color: '#1e40af', bgColor: '#dbeafe' },
  completed: { label: 'Completed', color: '#374151', bgColor: '#f3f4f6' },
  cancelled: { label: 'Cancelled', color: '#991b1b', bgColor: '#fee2e2' },
  disputed: { label: 'Disputed', color: '#92400e', bgColor: '#fef3c7' },
}

function BookingDetailPage() {
  const { bookingId } = Route.useParams()
  const { isAuthenticated, isLoading: authLoading, user } = useAuth()
  const navigate = useNavigate()
  const [cancelReason, setCancelReason] = useState('')
  const [showCancelModal, setShowCancelModal] = useState(false)
  const [actionError, setActionError] = useState<string | null>(null)
  const [actionSuccess, setActionSuccess] = useState<string | null>(null)

  // Fetch booking details
  const { data: booking, isLoading, error, refetch } = $api.useQuery(
    'get',
    '/api/v1/bookings/{booking_id}',
    {
      params: {
        path: { booking_id: bookingId },
      },
    },
    {
      enabled: isAuthenticated,
    }
  )

  // Mutations for booking actions
  const confirmMutation = $api.useMutation('post', '/api/v1/bookings/{booking_id}/confirm')
  const cancelMutation = $api.useMutation('post', '/api/v1/bookings/{booking_id}/cancel')
  const startMutation = $api.useMutation('post', '/api/v1/bookings/{booking_id}/start')
  const completeMutation = $api.useMutation('post', '/api/v1/bookings/{booking_id}/complete')

  // Start conversation mutation
  const startConversationMutation = $api.useMutation('post', '/api/v1/conversations')

  const isHost = user?.id === booking?.host_id
  const isClient = user?.id === booking?.client_id
  const otherParty = isHost ? booking?.client : booking?.host

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    })
  }

  const formatTime = (dateStr: string) => {
    return new Date(dateStr).toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
    })
  }

  const formatPrice = (cents: number) => `$${(cents / 100).toFixed(2)}`

  const clearMessages = () => {
    setActionError(null)
    setActionSuccess(null)
  }

  const handleConfirm = async () => {
    clearMessages()
    try {
      await confirmMutation.mutateAsync({
        params: { path: { booking_id: bookingId } },
      })
      setActionSuccess('Booking confirmed successfully!')
      refetch()
    } catch {
      setActionError('Failed to confirm booking. Please try again.')
    }
  }

  const handleDecline = async () => {
    clearMessages()
    try {
      await cancelMutation.mutateAsync({
        params: { path: { booking_id: bookingId } },
        body: { reason: 'Declined by host' },
      })
      setActionSuccess('Booking declined.')
      refetch()
    } catch {
      setActionError('Failed to decline booking. Please try again.')
    }
  }

  const handleCancel = async () => {
    clearMessages()
    try {
      await cancelMutation.mutateAsync({
        params: { path: { booking_id: bookingId } },
        body: { reason: cancelReason || null },
      })
      setActionSuccess('Booking cancelled.')
      setShowCancelModal(false)
      setCancelReason('')
      refetch()
    } catch {
      setActionError('Failed to cancel booking. Please try again.')
    }
  }

  const handleStart = async () => {
    clearMessages()
    try {
      await startMutation.mutateAsync({
        params: { path: { booking_id: bookingId } },
      })
      setActionSuccess('Session started!')
      refetch()
    } catch {
      setActionError('Failed to start session. You can only start within 30 minutes of scheduled time.')
    }
  }

  const handleComplete = async () => {
    clearMessages()
    try {
      await completeMutation.mutateAsync({
        params: { path: { booking_id: bookingId } },
      })
      setActionSuccess('Session completed! Payment has been processed.')
      refetch()
    } catch {
      setActionError('Failed to complete session. Please try again.')
    }
  }

  const handleMessage = async () => {
    if (!otherParty) return
    clearMessages()
    try {
      const conversation = await startConversationMutation.mutateAsync({
        body: { participant_id: otherParty.id },
      })
      navigate({ to: '/messages/$conversationId', params: { conversationId: conversation.id } })
    } catch {
      setActionError('Failed to start conversation. Please try again.')
    }
  }

  const handleAddToCalendar = () => {
    if (!booking) return

    const startDate = new Date(booking.scheduled_start)
    const endDate = new Date(booking.scheduled_end)

    // Format for Google Calendar
    const formatDateForCalendar = (date: Date) => {
      return date.toISOString().replace(/-|:|\.\d+/g, '').slice(0, 15) + 'Z'
    }

    const title = encodeURIComponent(
      `Dance Session with ${otherParty?.first_name ?? 'Host'} ${otherParty?.last_name ?? ''}`
    )
    const details = encodeURIComponent(
      `Dance style: ${booking.dance_style?.name ?? 'TBD'}\nDuration: ${booking.duration_minutes} minutes\n\nBooked through Strictly Dancing`
    )
    const location = encodeURIComponent(booking.location_name ?? '')

    const googleCalendarUrl = `https://calendar.google.com/calendar/render?action=TEMPLATE&text=${title}&dates=${formatDateForCalendar(startDate)}/${formatDateForCalendar(endDate)}&details=${details}&location=${location}`

    window.open(googleCalendarUrl, '_blank')
  }

  // Check if session can be started (within 30 minutes of scheduled time)
  const canStartSession = () => {
    if (!booking || booking.status !== 'confirmed') return false
    const now = new Date()
    const scheduledStart = new Date(booking.scheduled_start)
    const timeDiff = scheduledStart.getTime() - now.getTime()
    const minutesUntilStart = timeDiff / (1000 * 60)
    // Can start 30 minutes before or any time after scheduled start
    return minutesUntilStart <= 30
  }

  // Auth loading state
  if (authLoading) {
    return (
      <div style={styles.loadingContainer}>
        <div style={styles.spinner} />
        <p style={styles.loadingText}>Loading...</p>
      </div>
    )
  }

  // Not authenticated
  if (!isAuthenticated) {
    return (
      <div style={styles.container}>
        <div style={styles.authRequired}>
          <h2 style={styles.authTitle}>Login Required</h2>
          <p style={styles.authText}>Please log in to view booking details.</p>
          <Link to="/login" style={styles.primaryButton}>
            Log In
          </Link>
        </div>
      </div>
    )
  }

  // Loading booking
  if (isLoading) {
    return (
      <div style={styles.loadingContainer}>
        <div style={styles.spinner} />
        <p style={styles.loadingText}>Loading booking details...</p>
      </div>
    )
  }

  // Error state
  if (error || !booking) {
    return (
      <div style={styles.container}>
        <div style={styles.errorContainer}>
          <h2 style={styles.errorTitle}>Booking Not Found</h2>
          <p style={styles.errorText}>
            This booking doesn't exist or you don't have permission to view it.
          </p>
          <Link to="/bookings" style={styles.backLink}>
            Back to Bookings
          </Link>
        </div>
      </div>
    )
  }

  const statusBadge = STATUS_BADGES[booking.status]

  return (
    <div style={styles.container}>
      {/* Header */}
      <div style={styles.header}>
        <Link to="/bookings" style={styles.backLink}>
          &larr; Back to Bookings
        </Link>
        <div
          style={{
            ...styles.statusBadge,
            color: statusBadge.color,
            backgroundColor: statusBadge.bgColor,
          }}
        >
          {statusBadge.label}
        </div>
      </div>

      {/* Success/Error Messages */}
      {actionSuccess && (
        <div style={styles.successBanner}>
          {actionSuccess}
          <button type="button" onClick={clearMessages} style={styles.dismissButton}>
            &times;
          </button>
        </div>
      )}
      {actionError && (
        <div style={styles.errorBanner}>
          {actionError}
          <button type="button" onClick={clearMessages} style={styles.dismissButton}>
            &times;
          </button>
        </div>
      )}

      {/* Main Content */}
      <div style={styles.mainContent}>
        {/* Other Party Info */}
        <div style={styles.card}>
          <div style={styles.cardHeader}>
            <div style={styles.avatar}>
              {otherParty
                ? `${otherParty.first_name.charAt(0)}${otherParty.last_name.charAt(0)}`
                : '?'}
            </div>
            <div>
              <p style={styles.partyLabel}>{isHost ? 'Client' : 'Host'}</p>
              <h2 style={styles.partyName}>
                {otherParty ? `${otherParty.first_name} ${otherParty.last_name}` : 'Unknown'}
              </h2>
            </div>
          </div>
          {!isHost && otherParty && (
            <Link
              from="/bookings/$bookingId"
              to="/hosts/$hostId"
              params={{ hostId: booking.host_profile_id }}
              style={styles.viewProfileLink}
            >
              View Profile
            </Link>
          )}
        </div>

        {/* Session Details */}
        <div style={styles.card}>
          <h3 style={styles.cardTitle}>Session Details</h3>

          <div style={styles.detailRow}>
            <span style={styles.detailLabel}>Date</span>
            <span style={styles.detailValue}>{formatDate(booking.scheduled_start)}</span>
          </div>

          <div style={styles.detailRow}>
            <span style={styles.detailLabel}>Time</span>
            <span style={styles.detailValue}>
              {formatTime(booking.scheduled_start)} - {formatTime(booking.scheduled_end)}
            </span>
          </div>

          <div style={styles.detailRow}>
            <span style={styles.detailLabel}>Duration</span>
            <span style={styles.detailValue}>{booking.duration_minutes} minutes</span>
          </div>

          {booking.dance_style && (
            <div style={styles.detailRow}>
              <span style={styles.detailLabel}>Dance Style</span>
              <span style={styles.danceStyleBadge}>{booking.dance_style.name}</span>
            </div>
          )}
        </div>

        {/* Location */}
        <div style={styles.card}>
          <h3 style={styles.cardTitle}>Location</h3>
          {booking.location_name ? (
            <>
              <p style={styles.locationText}>{booking.location_name}</p>
              {booking.location_notes && (
                <p style={styles.locationNotes}>{booking.location_notes}</p>
              )}
              {/* Map placeholder */}
              {booking.latitude && booking.longitude && (
                <div style={styles.mapContainer}>
                  <div style={styles.mapPlaceholder}>
                    <span style={styles.mapIcon}>Map</span>
                    <p style={styles.mapText}>
                      {booking.latitude.toFixed(4)}, {booking.longitude.toFixed(4)}
                    </p>
                    <a
                      href={`https://www.google.com/maps?q=${booking.latitude},${booking.longitude}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      style={styles.mapLink}
                    >
                      Open in Google Maps
                    </a>
                  </div>
                </div>
              )}
            </>
          ) : (
            <p style={styles.locationText}>Location to be determined</p>
          )}
        </div>

        {/* Pricing */}
        <div style={styles.card}>
          <h3 style={styles.cardTitle}>Pricing</h3>

          <div style={styles.detailRow}>
            <span style={styles.detailLabel}>Hourly Rate</span>
            <span style={styles.detailValue}>{formatPrice(booking.hourly_rate_cents)}/hr</span>
          </div>

          <div style={styles.detailRow}>
            <span style={styles.detailLabel}>Session Total</span>
            <span style={styles.detailValue}>{formatPrice(booking.amount_cents)}</span>
          </div>

          {isHost && (
            <>
              <div style={styles.detailRow}>
                <span style={styles.detailLabel}>Platform Fee</span>
                <span style={styles.detailValue}>-{formatPrice(booking.platform_fee_cents)}</span>
              </div>
              <div style={{ ...styles.detailRow, ...styles.totalRow }}>
                <span style={styles.detailLabel}>Your Earnings</span>
                <span style={styles.totalValue}>{formatPrice(booking.host_payout_cents)}</span>
              </div>
            </>
          )}
        </div>

        {/* Notes */}
        {(booking.client_notes ?? booking.host_notes) && (
          <div style={styles.card}>
            <h3 style={styles.cardTitle}>Notes</h3>
            {booking.client_notes && (
              <div style={styles.noteSection}>
                <p style={styles.noteLabel}>From Client:</p>
                <p style={styles.noteText}>{booking.client_notes}</p>
              </div>
            )}
            {booking.host_notes && (
              <div style={styles.noteSection}>
                <p style={styles.noteLabel}>From Host:</p>
                <p style={styles.noteText}>{booking.host_notes}</p>
              </div>
            )}
          </div>
        )}

        {/* Cancellation Info */}
        {booking.status === 'cancelled' && (
          <div style={styles.card}>
            <h3 style={styles.cardTitle}>Cancellation Details</h3>
            {booking.cancellation_reason && (
              <p style={styles.cancellationReason}>{booking.cancellation_reason}</p>
            )}
            <p style={styles.cancellationInfo}>
              Cancelled on {booking.cancelled_at ? formatDate(booking.cancelled_at) : 'N/A'}
            </p>
          </div>
        )}
      </div>

      {/* Action Buttons */}
      <div style={styles.actionsContainer}>
        {/* Quick Actions */}
        <div style={styles.quickActions}>
          <button
            type="button"
            onClick={handleMessage}
            style={styles.secondaryButton}
            disabled={startConversationMutation.isPending}
          >
            {startConversationMutation.isPending ? 'Opening...' : 'Message'}
          </button>
          {booking.status !== 'cancelled' && booking.status !== 'completed' && (
            <button type="button" onClick={handleAddToCalendar} style={styles.secondaryButton}>
              Add to Calendar
            </button>
          )}
        </div>

        {/* Role-based Actions */}
        {isHost && booking.status === 'pending' && (
          <div style={styles.hostActions}>
            <button
              type="button"
              onClick={handleConfirm}
              style={styles.primaryButton}
              disabled={confirmMutation.isPending}
            >
              {confirmMutation.isPending ? 'Confirming...' : 'Confirm Booking'}
            </button>
            <button
              type="button"
              onClick={handleDecline}
              style={styles.dangerButton}
              disabled={cancelMutation.isPending}
            >
              {cancelMutation.isPending ? 'Declining...' : 'Decline'}
            </button>
          </div>
        )}

        {booking.status === 'confirmed' && (
          <div style={styles.sessionActions}>
            {canStartSession() ? (
              <button
                type="button"
                onClick={handleStart}
                style={styles.primaryButton}
                disabled={startMutation.isPending}
              >
                {startMutation.isPending ? 'Starting...' : 'Start Session'}
              </button>
            ) : (
              <p style={styles.sessionNote}>
                You can start the session 30 minutes before the scheduled time.
              </p>
            )}
            <button
              type="button"
              onClick={() => setShowCancelModal(true)}
              style={styles.outlineButton}
            >
              Cancel Booking
            </button>
          </div>
        )}

        {isHost && booking.status === 'in_progress' && (
          <div style={styles.sessionActions}>
            <button
              type="button"
              onClick={handleComplete}
              style={styles.primaryButton}
              disabled={completeMutation.isPending}
            >
              {completeMutation.isPending ? 'Completing...' : 'Complete Session'}
            </button>
          </div>
        )}

        {isClient && booking.status === 'completed' && (
          <div style={styles.reviewAction}>
            <Link
              to="/bookings/$bookingId"
              params={{ bookingId }}
              style={styles.primaryButton}
              onClick={(e) => {
                e.preventDefault()
                // For now, show a placeholder - review form will be integrated later
                alert('Review feature coming soon!')
              }}
            >
              Leave a Review
            </Link>
          </div>
        )}
      </div>

      {/* Cancel Modal */}
      {showCancelModal && (
        <div style={styles.modalOverlay}>
          <div style={styles.modal}>
            <h3 style={styles.modalTitle}>Cancel Booking</h3>
            <p style={styles.modalText}>
              Are you sure you want to cancel this booking? This action cannot be undone.
            </p>
            <textarea
              value={cancelReason}
              onChange={(e) => setCancelReason(e.target.value)}
              placeholder="Reason for cancellation (optional)"
              style={styles.textarea}
            />
            <div style={styles.modalActions}>
              <button
                type="button"
                onClick={() => {
                  setShowCancelModal(false)
                  setCancelReason('')
                }}
                style={styles.outlineButton}
              >
                Keep Booking
              </button>
              <button
                type="button"
                onClick={handleCancel}
                style={styles.dangerButton}
                disabled={cancelMutation.isPending}
              >
                {cancelMutation.isPending ? 'Cancelling...' : 'Yes, Cancel'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    maxWidth: '800px',
    margin: '0 auto',
    padding: '1rem',
    paddingBottom: '8rem',
  },
  loadingContainer: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: '50vh',
  },
  spinner: {
    width: '40px',
    height: '40px',
    border: '4px solid #e5e7eb',
    borderTop: '4px solid #e11d48',
    borderRadius: '50%',
    animation: 'spin 1s linear infinite',
  },
  loadingText: {
    marginTop: '1rem',
    color: '#6b7280',
  },
  authRequired: {
    backgroundColor: 'white',
    borderRadius: '12px',
    boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
    padding: '2rem',
    maxWidth: '400px',
    margin: '2rem auto',
    textAlign: 'center',
  },
  authTitle: {
    fontSize: '1.25rem',
    fontWeight: 600,
    color: '#1f2937',
    marginTop: 0,
    marginBottom: '0.5rem',
  },
  authText: {
    color: '#6b7280',
    marginBottom: '1.5rem',
  },
  errorContainer: {
    backgroundColor: 'white',
    borderRadius: '12px',
    boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
    padding: '2rem',
    textAlign: 'center',
  },
  errorTitle: {
    fontSize: '1.25rem',
    fontWeight: 600,
    color: '#1f2937',
    marginTop: 0,
    marginBottom: '0.5rem',
  },
  errorText: {
    color: '#6b7280',
    marginBottom: '1.5rem',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '1.5rem',
  },
  backLink: {
    color: '#6b7280',
    textDecoration: 'none',
    fontSize: '0.9375rem',
    display: 'flex',
    alignItems: 'center',
    gap: '0.25rem',
  },
  statusBadge: {
    padding: '0.5rem 1rem',
    borderRadius: '9999px',
    fontSize: '0.875rem',
    fontWeight: 600,
  },
  successBanner: {
    backgroundColor: '#d1fae5',
    color: '#065f46',
    padding: '1rem',
    borderRadius: '8px',
    marginBottom: '1rem',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  errorBanner: {
    backgroundColor: '#fee2e2',
    color: '#991b1b',
    padding: '1rem',
    borderRadius: '8px',
    marginBottom: '1rem',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  dismissButton: {
    background: 'none',
    border: 'none',
    fontSize: '1.25rem',
    cursor: 'pointer',
    padding: '0 0.5rem',
    color: 'inherit',
  },
  mainContent: {
    display: 'flex',
    flexDirection: 'column',
    gap: '1rem',
  },
  card: {
    backgroundColor: 'white',
    borderRadius: '12px',
    boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
    padding: '1.25rem',
  },
  cardHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: '1rem',
  },
  avatar: {
    width: '60px',
    height: '60px',
    borderRadius: '50%',
    backgroundColor: '#e11d48',
    color: 'white',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontWeight: 'bold',
    fontSize: '1.25rem',
    flexShrink: 0,
  },
  partyLabel: {
    fontSize: '0.75rem',
    color: '#9ca3af',
    margin: 0,
    marginBottom: '0.125rem',
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
  },
  partyName: {
    fontSize: '1.25rem',
    fontWeight: 600,
    color: '#1f2937',
    margin: 0,
  },
  viewProfileLink: {
    display: 'inline-block',
    marginTop: '1rem',
    color: '#e11d48',
    textDecoration: 'none',
    fontSize: '0.9375rem',
    fontWeight: 500,
  },
  cardTitle: {
    fontSize: '1rem',
    fontWeight: 600,
    color: '#1f2937',
    margin: 0,
    marginBottom: '1rem',
  },
  detailRow: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '0.75rem 0',
    borderBottom: '1px solid #f3f4f6',
  },
  detailLabel: {
    color: '#6b7280',
    fontSize: '0.9375rem',
  },
  detailValue: {
    color: '#1f2937',
    fontSize: '0.9375rem',
    fontWeight: 500,
  },
  danceStyleBadge: {
    display: 'inline-block',
    padding: '0.25rem 0.75rem',
    backgroundColor: '#f3e8ff',
    color: '#7c3aed',
    borderRadius: '9999px',
    fontSize: '0.875rem',
    fontWeight: 500,
  },
  totalRow: {
    borderBottom: 'none',
    paddingTop: '1rem',
    marginTop: '0.5rem',
    borderTop: '2px solid #e5e7eb',
  },
  totalValue: {
    color: '#059669',
    fontSize: '1.125rem',
    fontWeight: 700,
  },
  locationText: {
    color: '#1f2937',
    margin: 0,
    marginBottom: '0.5rem',
  },
  locationNotes: {
    color: '#6b7280',
    fontSize: '0.875rem',
    margin: 0,
    marginBottom: '1rem',
    fontStyle: 'italic',
  },
  mapContainer: {
    marginTop: '1rem',
  },
  mapPlaceholder: {
    backgroundColor: '#f3f4f6',
    borderRadius: '8px',
    padding: '2rem',
    textAlign: 'center',
  },
  mapIcon: {
    fontSize: '2rem',
    display: 'block',
    marginBottom: '0.5rem',
  },
  mapText: {
    color: '#6b7280',
    fontSize: '0.875rem',
    margin: 0,
    marginBottom: '0.5rem',
  },
  mapLink: {
    color: '#e11d48',
    textDecoration: 'none',
    fontSize: '0.875rem',
    fontWeight: 500,
  },
  noteSection: {
    marginBottom: '1rem',
  },
  noteLabel: {
    fontSize: '0.75rem',
    color: '#9ca3af',
    margin: 0,
    marginBottom: '0.25rem',
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
  },
  noteText: {
    color: '#4b5563',
    margin: 0,
    whiteSpace: 'pre-wrap',
  },
  cancellationReason: {
    color: '#1f2937',
    margin: 0,
    marginBottom: '0.5rem',
  },
  cancellationInfo: {
    color: '#6b7280',
    fontSize: '0.875rem',
    margin: 0,
  },
  actionsContainer: {
    position: 'fixed',
    bottom: 0,
    left: 0,
    right: 0,
    backgroundColor: 'white',
    borderTop: '1px solid #e5e7eb',
    padding: '1rem',
    display: 'flex',
    flexDirection: 'column',
    gap: '0.75rem',
  },
  quickActions: {
    display: 'flex',
    gap: '0.75rem',
    justifyContent: 'center',
  },
  hostActions: {
    display: 'flex',
    gap: '0.75rem',
    justifyContent: 'center',
  },
  sessionActions: {
    display: 'flex',
    flexDirection: 'column',
    gap: '0.5rem',
    alignItems: 'center',
  },
  reviewAction: {
    display: 'flex',
    justifyContent: 'center',
  },
  sessionNote: {
    color: '#6b7280',
    fontSize: '0.875rem',
    margin: 0,
    textAlign: 'center',
  },
  primaryButton: {
    padding: '0.875rem 1.5rem',
    backgroundColor: '#e11d48',
    color: 'white',
    border: 'none',
    borderRadius: '8px',
    fontSize: '0.9375rem',
    fontWeight: 600,
    cursor: 'pointer',
    textDecoration: 'none',
    textAlign: 'center',
  },
  secondaryButton: {
    padding: '0.75rem 1.25rem',
    backgroundColor: '#f3f4f6',
    color: '#374151',
    border: 'none',
    borderRadius: '8px',
    fontSize: '0.9375rem',
    fontWeight: 500,
    cursor: 'pointer',
  },
  outlineButton: {
    padding: '0.75rem 1.25rem',
    backgroundColor: 'transparent',
    color: '#374151',
    border: '1px solid #d1d5db',
    borderRadius: '8px',
    fontSize: '0.9375rem',
    fontWeight: 500,
    cursor: 'pointer',
  },
  dangerButton: {
    padding: '0.75rem 1.25rem',
    backgroundColor: '#dc2626',
    color: 'white',
    border: 'none',
    borderRadius: '8px',
    fontSize: '0.9375rem',
    fontWeight: 600,
    cursor: 'pointer',
  },
  modalOverlay: {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '1rem',
    zIndex: 1000,
  },
  modal: {
    backgroundColor: 'white',
    borderRadius: '12px',
    padding: '1.5rem',
    maxWidth: '400px',
    width: '100%',
  },
  modalTitle: {
    fontSize: '1.125rem',
    fontWeight: 600,
    color: '#1f2937',
    margin: 0,
    marginBottom: '0.5rem',
  },
  modalText: {
    color: '#6b7280',
    margin: 0,
    marginBottom: '1rem',
  },
  textarea: {
    width: '100%',
    minHeight: '80px',
    padding: '0.75rem',
    border: '1px solid #d1d5db',
    borderRadius: '8px',
    fontSize: '0.9375rem',
    resize: 'vertical',
    marginBottom: '1rem',
    boxSizing: 'border-box',
  },
  modalActions: {
    display: 'flex',
    gap: '0.75rem',
    justifyContent: 'flex-end',
  },
}
