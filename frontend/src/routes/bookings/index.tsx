import { createFileRoute, Link, useNavigate } from '@tanstack/react-router'
import { useState, useMemo } from 'react'
import { $api } from '@/lib/api/$api'
import { useAuth } from '@/contexts/AuthContext'
import type { components } from '@/types/api.gen'

export const Route = createFileRoute('/bookings/')({
  component: BookingsListPage,
})

type BookingStatus = components['schemas']['BookingStatus']
type BookingWithDetailsResponse = components['schemas']['BookingWithDetailsResponse']

type TabKey = 'upcoming' | 'past' | 'cancelled'

interface Tab {
  key: TabKey
  label: string
  statuses: BookingStatus[]
}

const TABS: Tab[] = [
  { key: 'upcoming', label: 'Upcoming', statuses: ['pending', 'confirmed', 'in_progress'] },
  { key: 'past', label: 'Past', statuses: ['completed'] },
  { key: 'cancelled', label: 'Cancelled', statuses: ['cancelled', 'disputed'] },
]

const STATUS_BADGES: Record<BookingStatus, { label: string; color: string; bgColor: string }> = {
  pending: { label: 'Pending', color: '#92400e', bgColor: '#fef3c7' },
  confirmed: { label: 'Confirmed', color: '#065f46', bgColor: '#d1fae5' },
  in_progress: { label: 'In Progress', color: '#1e40af', bgColor: '#dbeafe' },
  completed: { label: 'Completed', color: '#374151', bgColor: '#f3f4f6' },
  cancelled: { label: 'Cancelled', color: '#991b1b', bgColor: '#fee2e2' },
  disputed: { label: 'Disputed', color: '#92400e', bgColor: '#fef3c7' },
}

function BookingsListPage() {
  const { isAuthenticated, isLoading: authLoading, user } = useAuth()
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState<TabKey>('upcoming')

  // Get the statuses for the active tab
  const activeTabConfig = TABS.find((tab) => tab.key === activeTab)
  const statuses = activeTabConfig?.statuses ?? []

  // Fetch bookings
  const { data: bookingsResponse, isLoading, error } = $api.useQuery(
    'get',
    '/api/v1/bookings',
    {
      params: {
        query: {
          status: statuses,
          limit: 50,
        },
      },
    },
    {
      enabled: isAuthenticated,
    }
  )

  // Filter bookings based on tab (additional client-side filter for date-based logic)
  const filteredBookings = useMemo(() => {
    if (!bookingsResponse?.items) return []

    const now = new Date()
    return bookingsResponse.items.filter((booking: BookingWithDetailsResponse) => {
      const scheduledEnd = new Date(booking.scheduled_end)

      if (activeTab === 'upcoming') {
        // Upcoming: future or ongoing, not cancelled/completed
        return scheduledEnd >= now || booking.status === 'in_progress'
      }
      if (activeTab === 'past') {
        // Past: completed sessions
        return booking.status === 'completed'
      }
      // Cancelled: cancelled or disputed
      return booking.status === 'cancelled' || booking.status === 'disputed'
    })
  }, [bookingsResponse, activeTab])

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      weekday: 'short',
      month: 'short',
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

  const handleBookingClick = (bookingId: string) => {
    // Navigate to booking detail page (to be implemented in T067)
    navigate({ to: '/bookings/$bookingId', params: { bookingId } })
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
          <p style={styles.authText}>Please log in to view your bookings.</p>
          <Link to="/login" style={styles.loginButton}>
            Log In
          </Link>
          <p style={styles.registerText}>
            Don't have an account?{' '}
            <Link to="/register" style={styles.registerLink}>
              Register
            </Link>
          </p>
        </div>
      </div>
    )
  }

  return (
    <div style={styles.container}>
      <h1 style={styles.title}>My Bookings</h1>

      {/* Tabs */}
      <div style={styles.tabsContainer}>
        {TABS.map((tab) => (
          <button
            key={tab.key}
            type="button"
            onClick={() => setActiveTab(tab.key)}
            style={{
              ...styles.tab,
              ...(activeTab === tab.key ? styles.tabActive : {}),
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Content */}
      {isLoading ? (
        <div style={styles.loadingContainer}>
          <div style={styles.spinner} />
          <p style={styles.loadingText}>Loading bookings...</p>
        </div>
      ) : error ? (
        <div style={styles.errorContainer}>
          <p style={styles.errorText}>Failed to load bookings. Please try again.</p>
        </div>
      ) : filteredBookings.length === 0 ? (
        <div style={styles.emptyState}>
          <div style={styles.emptyIcon}>
            {activeTab === 'upcoming' ? '📅' : activeTab === 'past' ? '✓' : '✕'}
          </div>
          <h3 style={styles.emptyTitle}>
            {activeTab === 'upcoming'
              ? 'No upcoming bookings'
              : activeTab === 'past'
                ? 'No past bookings'
                : 'No cancelled bookings'}
          </h3>
          <p style={styles.emptyText}>
            {activeTab === 'upcoming'
              ? 'Book a session with a dance host to get started!'
              : activeTab === 'past'
                ? 'Your completed sessions will appear here.'
                : 'Cancelled or disputed bookings will appear here.'}
          </p>
          {activeTab === 'upcoming' && (
            <Link to="/hosts" style={styles.findHostButton}>
              Find a Host
            </Link>
          )}
        </div>
      ) : (
        <div style={styles.bookingsList}>
          {filteredBookings.map((booking: BookingWithDetailsResponse) => {
            const statusBadge = STATUS_BADGES[booking.status]
            const isHost = user?.id === booking.host_id
            const otherParty = isHost ? booking.client : booking.host

            return (
              <div
                key={booking.id}
                style={styles.bookingCard}
                onClick={() => handleBookingClick(booking.id)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    handleBookingClick(booking.id)
                  }
                }}
                role="button"
                tabIndex={0}
              >
                {/* Status badge */}
                <div
                  style={{
                    ...styles.statusBadge,
                    color: statusBadge.color,
                    backgroundColor: statusBadge.bgColor,
                  }}
                >
                  {statusBadge.label}
                </div>

                {/* Main content */}
                <div style={styles.cardContent}>
                  {/* Avatar and name */}
                  <div style={styles.cardHeader}>
                    <div style={styles.avatar}>
                      {otherParty
                        ? `${otherParty.first_name.charAt(0)}${otherParty.last_name.charAt(0)}`
                        : '?'}
                    </div>
                    <div>
                      <p style={styles.partyLabel}>
                        {isHost ? 'Session with client' : 'Session with host'}
                      </p>
                      <p style={styles.partyName}>
                        {otherParty
                          ? `${otherParty.first_name} ${otherParty.last_name}`
                          : 'Unknown'}
                      </p>
                    </div>
                  </div>

                  {/* Date and time */}
                  <div style={styles.dateTimeRow}>
                    <div style={styles.dateTime}>
                      <span style={styles.dateTimeIcon}>📅</span>
                      <span>{formatDate(booking.scheduled_start)}</span>
                    </div>
                    <div style={styles.dateTime}>
                      <span style={styles.dateTimeIcon}>🕐</span>
                      <span>
                        {formatTime(booking.scheduled_start)} - {formatTime(booking.scheduled_end)}
                      </span>
                    </div>
                  </div>

                  {/* Dance style and price */}
                  <div style={styles.detailsRow}>
                    {booking.dance_style && (
                      <span style={styles.danceStyle}>{booking.dance_style.name}</span>
                    )}
                    <span style={styles.price}>{formatPrice(booking.amount_cents)}</span>
                  </div>

                  {/* Location */}
                  {booking.location_name && (
                    <p style={styles.location}>
                      <span style={styles.locationIcon}>📍</span>
                      {booking.location_name}
                    </p>
                  )}
                </div>

                {/* Arrow indicator */}
                <div style={styles.arrowIndicator}>&rarr;</div>
              </div>
            )
          })}
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
  },
  title: {
    fontSize: 'clamp(1.5rem, 4vw, 2rem)',
    fontWeight: 'bold',
    color: '#1f2937',
    marginBottom: '1.5rem',
  },
  loadingContainer: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: '40vh',
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
  errorContainer: {
    padding: '2rem',
    textAlign: 'center',
  },
  errorText: {
    color: '#dc2626',
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
  loginButton: {
    display: 'block',
    width: '100%',
    padding: '0.875rem',
    backgroundColor: '#e11d48',
    color: 'white',
    border: 'none',
    borderRadius: '8px',
    fontSize: '1rem',
    fontWeight: 600,
    textDecoration: 'none',
    textAlign: 'center',
  },
  registerText: {
    marginTop: '1rem',
    fontSize: '0.875rem',
    color: '#6b7280',
  },
  registerLink: {
    color: '#e11d48',
    textDecoration: 'none',
    fontWeight: 500,
  },
  tabsContainer: {
    display: 'flex',
    gap: '0.5rem',
    marginBottom: '1.5rem',
    borderBottom: '2px solid #e5e7eb',
    paddingBottom: '0',
  },
  tab: {
    padding: '0.75rem 1.5rem',
    border: 'none',
    borderBottom: '3px solid transparent',
    backgroundColor: 'transparent',
    cursor: 'pointer',
    fontSize: '0.9375rem',
    fontWeight: 500,
    color: '#6b7280',
    marginBottom: '-2px',
    transition: 'all 0.2s',
  },
  tabActive: {
    color: '#e11d48',
    borderBottomColor: '#e11d48',
  },
  emptyState: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '3rem',
    textAlign: 'center',
    backgroundColor: 'white',
    borderRadius: '12px',
    boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
  },
  emptyIcon: {
    fontSize: '3rem',
    marginBottom: '1rem',
  },
  emptyTitle: {
    fontSize: '1.25rem',
    fontWeight: 600,
    color: '#1f2937',
    marginTop: 0,
    marginBottom: '0.5rem',
  },
  emptyText: {
    color: '#6b7280',
    marginBottom: '1.5rem',
  },
  findHostButton: {
    display: 'inline-block',
    padding: '0.75rem 1.5rem',
    backgroundColor: '#e11d48',
    color: 'white',
    border: 'none',
    borderRadius: '8px',
    fontSize: '0.9375rem',
    fontWeight: 600,
    textDecoration: 'none',
    cursor: 'pointer',
  },
  bookingsList: {
    display: 'flex',
    flexDirection: 'column',
    gap: '1rem',
  },
  bookingCard: {
    display: 'flex',
    alignItems: 'center',
    backgroundColor: 'white',
    borderRadius: '12px',
    boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
    padding: '1rem 1.25rem',
    cursor: 'pointer',
    transition: 'box-shadow 0.2s, transform 0.2s',
    position: 'relative',
  },
  statusBadge: {
    position: 'absolute',
    top: '1rem',
    right: '3rem',
    padding: '0.25rem 0.5rem',
    borderRadius: '4px',
    fontSize: '0.75rem',
    fontWeight: 600,
  },
  cardContent: {
    flex: 1,
    minWidth: 0,
  },
  cardHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.75rem',
    marginBottom: '0.75rem',
  },
  avatar: {
    width: '45px',
    height: '45px',
    borderRadius: '50%',
    backgroundColor: '#e11d48',
    color: 'white',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontWeight: 'bold',
    fontSize: '1rem',
    flexShrink: 0,
  },
  partyLabel: {
    fontSize: '0.75rem',
    color: '#9ca3af',
    margin: 0,
    marginBottom: '0.125rem',
  },
  partyName: {
    fontSize: '1rem',
    fontWeight: 600,
    color: '#1f2937',
    margin: 0,
  },
  dateTimeRow: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '1rem',
    marginBottom: '0.5rem',
  },
  dateTime: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.375rem',
    fontSize: '0.875rem',
    color: '#4b5563',
  },
  dateTimeIcon: {
    fontSize: '0.875rem',
  },
  detailsRow: {
    display: 'flex',
    alignItems: 'center',
    gap: '1rem',
    marginBottom: '0.25rem',
  },
  danceStyle: {
    display: 'inline-block',
    padding: '0.25rem 0.5rem',
    backgroundColor: '#f3e8ff',
    color: '#7c3aed',
    borderRadius: '4px',
    fontSize: '0.75rem',
    fontWeight: 500,
  },
  price: {
    fontSize: '1rem',
    fontWeight: 600,
    color: '#1f2937',
  },
  location: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.375rem',
    fontSize: '0.8125rem',
    color: '#6b7280',
    margin: 0,
    marginTop: '0.25rem',
  },
  locationIcon: {
    fontSize: '0.875rem',
  },
  arrowIndicator: {
    fontSize: '1.25rem',
    color: '#9ca3af',
    marginLeft: '1rem',
  },
}
