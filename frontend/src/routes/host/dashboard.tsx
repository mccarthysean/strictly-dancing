import { createFileRoute, Link } from '@tanstack/react-router'
import { useMemo } from 'react'
import { $api } from '@/lib/api/$api'
import { useAuth } from '@/contexts/AuthContext'
import type { components } from '@/types/api.gen'

export const Route = createFileRoute('/host/dashboard')({
  component: HostDashboardPage,
})

type BookingStatus = components['schemas']['BookingStatus']
type BookingWithDetailsResponse = components['schemas']['BookingWithDetailsResponse']
type ReviewWithUserResponse = components['schemas']['ReviewWithUserResponse']

const STATUS_BADGES: Record<BookingStatus, { label: string; color: string; bgColor: string }> = {
  pending: { label: 'Pending', color: '#92400e', bgColor: '#fef3c7' },
  confirmed: { label: 'Confirmed', color: '#065f46', bgColor: '#d1fae5' },
  in_progress: { label: 'In Progress', color: '#1e40af', bgColor: '#dbeafe' },
  completed: { label: 'Completed', color: '#374151', bgColor: '#f3f4f6' },
  cancelled: { label: 'Cancelled', color: '#991b1b', bgColor: '#fee2e2' },
  disputed: { label: 'Disputed', color: '#92400e', bgColor: '#fef3c7' },
}

function HostDashboardPage() {
  const { isAuthenticated, isLoading: authLoading, user } = useAuth()

  // Fetch host profile
  const { data: hostProfile, isLoading: profileLoading, error: profileError } = $api.useQuery(
    'get',
    '/api/v1/users/me/host-profile',
    {},
    {
      enabled: isAuthenticated,
    }
  )

  // Fetch upcoming bookings (pending, confirmed, in_progress)
  const { data: bookingsResponse, isLoading: bookingsLoading, error: bookingsError } = $api.useQuery(
    'get',
    '/api/v1/bookings',
    {
      params: {
        query: {
          status: ['pending', 'confirmed', 'in_progress'],
          limit: 5,
        },
      },
    },
    {
      enabled: isAuthenticated,
    }
  )

  // Filter bookings where user is host and scheduled_start is in the future
  const upcomingBookings = useMemo(() => {
    if (!bookingsResponse?.items || !user) return []
    const now = new Date()
    return bookingsResponse.items
      .filter((booking: BookingWithDetailsResponse) => {
        // Only show bookings where user is the host
        const isHost = booking.host_id === user.id
        const startDate = new Date(booking.scheduled_start)
        return isHost && startDate >= now
      })
      .slice(0, 5)
  }, [bookingsResponse, user])

  // Fetch recent reviews - need hostProfile id
  const { data: reviewsResponse, isLoading: reviewsLoading, error: reviewsError } = $api.useQuery(
    'get',
    '/api/v1/hosts/{host_id}/reviews',
    {
      params: {
        path: { host_id: hostProfile?.id ?? '' },
        query: { limit: 3 },
      },
    },
    {
      enabled: isAuthenticated && !!hostProfile?.id,
    }
  )

  // Fetch completed bookings for earnings calculation
  const { data: completedBookingsResponse } = $api.useQuery(
    'get',
    '/api/v1/bookings',
    {
      params: {
        query: {
          status: ['completed'],
          limit: 100,
        },
      },
    },
    {
      enabled: isAuthenticated,
    }
  )

  // Calculate earnings from completed bookings where user is host
  const earningsSummary = useMemo(() => {
    if (!completedBookingsResponse?.items || !user) {
      return { totalEarnings: 0, totalSessions: 0, thisMonthEarnings: 0 }
    }

    const now = new Date()
    const startOfMonth = new Date(now.getFullYear(), now.getMonth(), 1)

    let totalEarnings = 0
    let totalSessions = 0
    let thisMonthEarnings = 0

    completedBookingsResponse.items.forEach((booking: BookingWithDetailsResponse) => {
      if (booking.host_id === user.id && booking.status === 'completed') {
        const payout = booking.host_payout_cents ?? 0
        totalEarnings += payout
        totalSessions += 1

        const completedAt = booking.actual_end ? new Date(booking.actual_end) : new Date(booking.scheduled_end)
        if (completedAt >= startOfMonth) {
          thisMonthEarnings += payout
        }
      }
    })

    return { totalEarnings, totalSessions, thisMonthEarnings }
  }, [completedBookingsResponse, user])

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

  const formatRelativeDate = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24))

    if (diffDays === 0) return 'Today'
    if (diffDays === 1) return 'Yesterday'
    if (diffDays < 7) return `${diffDays} days ago`
    if (diffDays < 30) {
      const weeks = Math.floor(diffDays / 7)
      return `${weeks} week${weeks > 1 ? 's' : ''} ago`
    }
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  }

  const renderStars = (rating: number) => {
    return (
      <div style={styles.stars}>
        {[1, 2, 3, 4, 5].map((star) => (
          <span
            key={star}
            style={{
              ...styles.star,
              color: star <= rating ? '#fbbf24' : '#e5e7eb',
            }}
          >
            &#9733;
          </span>
        ))}
      </div>
    )
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
          <p style={styles.authText}>Please log in to view your host dashboard.</p>
          <Link to="/login" style={styles.loginButton}>
            Log In
          </Link>
        </div>
      </div>
    )
  }

  // Check if user is a host
  const isHost = user?.user_type === 'host' || user?.user_type === 'both'

  if (!isHost) {
    return (
      <div style={styles.container}>
        <div style={styles.authRequired}>
          <h2 style={styles.authTitle}>Not a Host</h2>
          <p style={styles.authText}>You need to become a host to access this dashboard.</p>
          <Link to="/" style={styles.becomeHostButton}>
            Become a Host
          </Link>
        </div>
      </div>
    )
  }

  // Loading profile
  if (profileLoading) {
    return (
      <div style={styles.loadingContainer}>
        <div style={styles.spinner} />
        <p style={styles.loadingText}>Loading dashboard...</p>
      </div>
    )
  }

  // Profile error
  if (profileError || !hostProfile) {
    return (
      <div style={styles.container}>
        <div style={styles.errorContainer}>
          <p style={styles.errorText}>Failed to load host profile. Please try again.</p>
        </div>
      </div>
    )
  }

  return (
    <div style={styles.container}>
      {/* Header */}
      <div style={styles.header}>
        <h1 style={styles.title}>Host Dashboard</h1>
        <p style={styles.subtitle}>
          Welcome back, {user?.first_name}!
        </p>
      </div>

      {/* Stats Cards */}
      <div style={styles.statsGrid}>
        {/* Rating */}
        <div style={styles.statCard}>
          <div style={styles.statIcon}>&#9733;</div>
          <div style={styles.statContent}>
            <p style={styles.statLabel}>Rating</p>
            <p style={styles.statValue}>
              {hostProfile.rating_average ? hostProfile.rating_average.toFixed(1) : 'N/A'}
            </p>
            <p style={styles.statSubtext}>
              {hostProfile.total_reviews ?? 0} review{(hostProfile.total_reviews ?? 0) !== 1 ? 's' : ''}
            </p>
          </div>
        </div>

        {/* Total Sessions */}
        <div style={styles.statCard}>
          <div style={styles.statIcon}>&#128197;</div>
          <div style={styles.statContent}>
            <p style={styles.statLabel}>Sessions</p>
            <p style={styles.statValue}>{earningsSummary.totalSessions}</p>
            <p style={styles.statSubtext}>completed</p>
          </div>
        </div>

        {/* This Month Earnings */}
        <div style={styles.statCard}>
          <div style={styles.statIcon}>&#128176;</div>
          <div style={styles.statContent}>
            <p style={styles.statLabel}>This Month</p>
            <p style={styles.statValue}>{formatPrice(earningsSummary.thisMonthEarnings)}</p>
            <p style={styles.statSubtext}>earnings</p>
          </div>
        </div>

        {/* Total Earnings */}
        <div style={styles.statCard}>
          <div style={styles.statIcon}>&#128178;</div>
          <div style={styles.statContent}>
            <p style={styles.statLabel}>Total Earnings</p>
            <p style={styles.statValue}>{formatPrice(earningsSummary.totalEarnings)}</p>
            <p style={styles.statSubtext}>all time</p>
          </div>
        </div>
      </div>

      {/* Main Content Grid */}
      <div style={styles.contentGrid}>
        {/* Upcoming Bookings Section */}
        <div style={styles.section}>
          <div style={styles.sectionHeader}>
            <h2 style={styles.sectionTitle}>Upcoming Bookings</h2>
            <Link to="/bookings" style={styles.viewAllLink}>
              View all
            </Link>
          </div>

          {bookingsLoading ? (
            <div style={styles.sectionLoading}>
              <div style={styles.smallSpinner} />
              <span>Loading...</span>
            </div>
          ) : bookingsError ? (
            <p style={styles.sectionError}>Failed to load bookings</p>
          ) : upcomingBookings.length === 0 ? (
            <div style={styles.emptySection}>
              <p style={styles.emptyText}>No upcoming bookings</p>
              <p style={styles.emptySubtext}>
                New booking requests will appear here
              </p>
            </div>
          ) : (
            <div style={styles.bookingsList}>
              {upcomingBookings.map((booking: BookingWithDetailsResponse) => {
                const statusBadge = STATUS_BADGES[booking.status]
                return (
                  <Link
                    key={booking.id}
                    to="/bookings/$bookingId"
                    params={{ bookingId: booking.id }}
                    style={styles.bookingCard}
                  >
                    <div style={styles.bookingInfo}>
                      <div style={styles.bookingAvatar}>
                        {booking.client
                          ? `${booking.client.first_name.charAt(0)}${booking.client.last_name.charAt(0)}`
                          : '?'}
                      </div>
                      <div style={styles.bookingDetails}>
                        <p style={styles.bookingName}>
                          {booking.client
                            ? `${booking.client.first_name} ${booking.client.last_name}`
                            : 'Unknown'}
                        </p>
                        <p style={styles.bookingDateTime}>
                          {formatDate(booking.scheduled_start)} at {formatTime(booking.scheduled_start)}
                        </p>
                        {booking.dance_style && (
                          <span style={styles.danceStyleTag}>{booking.dance_style.name}</span>
                        )}
                      </div>
                    </div>
                    <div style={styles.bookingMeta}>
                      <span
                        style={{
                          ...styles.statusBadge,
                          color: statusBadge.color,
                          backgroundColor: statusBadge.bgColor,
                        }}
                      >
                        {statusBadge.label}
                      </span>
                      <span style={styles.bookingAmount}>{formatPrice(booking.amount_cents)}</span>
                    </div>
                  </Link>
                )
              })}
            </div>
          )}
        </div>

        {/* Recent Reviews Section */}
        <div style={styles.section}>
          <div style={styles.sectionHeader}>
            <h2 style={styles.sectionTitle}>Recent Reviews</h2>
            {hostProfile && (
              <Link
                to="/hosts/$hostId"
                params={{ hostId: hostProfile.id }}
                style={styles.viewAllLink}
              >
                View all
              </Link>
            )}
          </div>

          {reviewsLoading ? (
            <div style={styles.sectionLoading}>
              <div style={styles.smallSpinner} />
              <span>Loading...</span>
            </div>
          ) : reviewsError ? (
            <p style={styles.sectionError}>Failed to load reviews</p>
          ) : !reviewsResponse?.items || reviewsResponse.items.length === 0 ? (
            <div style={styles.emptySection}>
              <p style={styles.emptyText}>No reviews yet</p>
              <p style={styles.emptySubtext}>
                Reviews from clients will appear here after sessions
              </p>
            </div>
          ) : (
            <div style={styles.reviewsList}>
              {reviewsResponse.items.map((review: ReviewWithUserResponse) => (
                <div key={review.id} style={styles.reviewCard}>
                  <div style={styles.reviewHeader}>
                    <div style={styles.reviewerInfo}>
                      <div style={styles.reviewerAvatar}>
                        {review.reviewer
                          ? `${review.reviewer.first_name.charAt(0)}${review.reviewer.last_name.charAt(0)}`
                          : '?'}
                      </div>
                      <div>
                        <p style={styles.reviewerName}>
                          {review.reviewer
                            ? `${review.reviewer.first_name} ${review.reviewer.last_name}`
                            : 'Anonymous'}
                        </p>
                        <p style={styles.reviewDate}>{formatRelativeDate(review.created_at)}</p>
                      </div>
                    </div>
                    {renderStars(review.rating)}
                  </div>
                  {review.comment && (
                    <p style={styles.reviewComment}>{review.comment}</p>
                  )}
                  {review.host_response && (
                    <div style={styles.hostResponse}>
                      <span style={styles.hostResponseIcon}>↩</span>
                      <span style={styles.hostResponseLabel}>Your response</span>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Quick Actions */}
      <div style={styles.quickActionsSection}>
        <h2 style={styles.sectionTitle}>Quick Actions</h2>
        <div style={styles.quickActionsGrid}>
          <Link to="/bookings" style={styles.quickActionCard}>
            <span style={styles.quickActionIcon}>&#128197;</span>
            <span style={styles.quickActionLabel}>My Bookings</span>
          </Link>
          <Link to="/messages" style={styles.quickActionCard}>
            <span style={styles.quickActionIcon}>&#128172;</span>
            <span style={styles.quickActionLabel}>Messages</span>
          </Link>
          <Link to="/hosts/$hostId" params={{ hostId: hostProfile.id }} style={styles.quickActionCard}>
            <span style={styles.quickActionIcon}>&#128100;</span>
            <span style={styles.quickActionLabel}>View Profile</span>
          </Link>
        </div>
      </div>
    </div>
  )
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    maxWidth: '1200px',
    margin: '0 auto',
    padding: '1rem',
  },
  loadingContainer: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: '60vh',
  },
  spinner: {
    width: '40px',
    height: '40px',
    border: '4px solid #e5e7eb',
    borderTop: '4px solid #e11d48',
    borderRadius: '50%',
    animation: 'spin 1s linear infinite',
  },
  smallSpinner: {
    width: '20px',
    height: '20px',
    border: '2px solid #e5e7eb',
    borderTop: '2px solid #e11d48',
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
    backgroundColor: '#fef2f2',
    borderRadius: '12px',
    marginTop: '2rem',
  },
  errorText: {
    color: '#dc2626',
    margin: 0,
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
  becomeHostButton: {
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
  header: {
    marginBottom: '1.5rem',
  },
  title: {
    fontSize: 'clamp(1.5rem, 4vw, 2rem)',
    fontWeight: 'bold',
    color: '#1f2937',
    margin: 0,
    marginBottom: '0.25rem',
  },
  subtitle: {
    color: '#6b7280',
    margin: 0,
    fontSize: '1rem',
  },
  statsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
    gap: '1rem',
    marginBottom: '2rem',
  },
  statCard: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.75rem',
    backgroundColor: 'white',
    borderRadius: '12px',
    boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
    padding: '1rem',
  },
  statIcon: {
    fontSize: '1.5rem',
    opacity: 0.8,
  },
  statContent: {
    flex: 1,
  },
  statLabel: {
    fontSize: '0.75rem',
    color: '#6b7280',
    margin: 0,
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
  },
  statValue: {
    fontSize: '1.25rem',
    fontWeight: 700,
    color: '#1f2937',
    margin: 0,
  },
  statSubtext: {
    fontSize: '0.75rem',
    color: '#9ca3af',
    margin: 0,
  },
  contentGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
    gap: '1.5rem',
    marginBottom: '2rem',
  },
  section: {
    backgroundColor: 'white',
    borderRadius: '12px',
    boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
    padding: '1.25rem',
  },
  sectionHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '1rem',
  },
  sectionTitle: {
    fontSize: '1.125rem',
    fontWeight: 600,
    color: '#1f2937',
    margin: 0,
  },
  viewAllLink: {
    fontSize: '0.875rem',
    color: '#e11d48',
    textDecoration: 'none',
    fontWeight: 500,
  },
  sectionLoading: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '0.5rem',
    padding: '2rem',
    color: '#6b7280',
  },
  sectionError: {
    color: '#dc2626',
    textAlign: 'center',
    padding: '1rem',
  },
  emptySection: {
    textAlign: 'center',
    padding: '2rem 1rem',
  },
  emptyText: {
    color: '#6b7280',
    margin: 0,
    marginBottom: '0.25rem',
    fontWeight: 500,
  },
  emptySubtext: {
    color: '#9ca3af',
    margin: 0,
    fontSize: '0.875rem',
  },
  bookingsList: {
    display: 'flex',
    flexDirection: 'column',
    gap: '0.75rem',
  },
  bookingCard: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '0.875rem',
    backgroundColor: '#fafafa',
    borderRadius: '8px',
    border: '1px solid #e5e7eb',
    textDecoration: 'none',
    color: 'inherit',
    transition: 'background-color 0.2s, border-color 0.2s',
  },
  bookingInfo: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.75rem',
    flex: 1,
    minWidth: 0,
  },
  bookingAvatar: {
    width: '40px',
    height: '40px',
    borderRadius: '50%',
    backgroundColor: '#e11d48',
    color: 'white',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '0.875rem',
    fontWeight: 600,
    flexShrink: 0,
  },
  bookingDetails: {
    minWidth: 0,
  },
  bookingName: {
    fontWeight: 600,
    color: '#1f2937',
    margin: 0,
    fontSize: '0.9375rem',
    whiteSpace: 'nowrap',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
  },
  bookingDateTime: {
    color: '#6b7280',
    margin: 0,
    fontSize: '0.8125rem',
  },
  danceStyleTag: {
    display: 'inline-block',
    padding: '0.125rem 0.375rem',
    backgroundColor: '#f3e8ff',
    color: '#7c3aed',
    borderRadius: '4px',
    fontSize: '0.6875rem',
    fontWeight: 500,
    marginTop: '0.25rem',
  },
  bookingMeta: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'flex-end',
    gap: '0.25rem',
    marginLeft: '0.5rem',
  },
  statusBadge: {
    padding: '0.25rem 0.5rem',
    borderRadius: '4px',
    fontSize: '0.6875rem',
    fontWeight: 600,
    whiteSpace: 'nowrap',
  },
  bookingAmount: {
    fontWeight: 600,
    color: '#1f2937',
    fontSize: '0.875rem',
  },
  reviewsList: {
    display: 'flex',
    flexDirection: 'column',
    gap: '0.75rem',
  },
  reviewCard: {
    padding: '0.875rem',
    backgroundColor: '#fafafa',
    borderRadius: '8px',
    border: '1px solid #e5e7eb',
  },
  reviewHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    flexWrap: 'wrap',
    gap: '0.5rem',
    marginBottom: '0.5rem',
  },
  reviewerInfo: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
  },
  reviewerAvatar: {
    width: '32px',
    height: '32px',
    borderRadius: '50%',
    backgroundColor: '#e11d48',
    color: 'white',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '0.75rem',
    fontWeight: 600,
    flexShrink: 0,
  },
  reviewerName: {
    fontWeight: 600,
    color: '#1f2937',
    margin: 0,
    fontSize: '0.875rem',
  },
  reviewDate: {
    color: '#9ca3af',
    margin: 0,
    fontSize: '0.75rem',
  },
  stars: {
    display: 'flex',
    gap: '1px',
  },
  star: {
    fontSize: '0.875rem',
  },
  reviewComment: {
    color: '#4b5563',
    margin: 0,
    fontSize: '0.875rem',
    lineHeight: 1.5,
    display: '-webkit-box',
    WebkitLineClamp: 2,
    WebkitBoxOrient: 'vertical',
    overflow: 'hidden',
  },
  hostResponse: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.375rem',
    marginTop: '0.5rem',
    padding: '0.375rem 0.5rem',
    backgroundColor: '#f3f4f6',
    borderRadius: '4px',
  },
  hostResponseIcon: {
    color: '#e11d48',
    fontSize: '0.75rem',
  },
  hostResponseLabel: {
    color: '#6b7280',
    fontSize: '0.75rem',
  },
  quickActionsSection: {
    marginTop: '1rem',
  },
  quickActionsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))',
    gap: '1rem',
    marginTop: '1rem',
  },
  quickActionCard: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: '0.5rem',
    padding: '1.25rem 1rem',
    backgroundColor: 'white',
    borderRadius: '12px',
    boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
    textDecoration: 'none',
    color: '#1f2937',
    transition: 'box-shadow 0.2s, transform 0.2s',
  },
  quickActionIcon: {
    fontSize: '1.5rem',
  },
  quickActionLabel: {
    fontSize: '0.875rem',
    fontWeight: 500,
    textAlign: 'center',
  },
}
