import { createFileRoute, Link } from '@tanstack/react-router'
import { $api } from '@/lib/api/$api'
import type { components } from '@/types/api.gen'
import { ReviewsList } from '@/components/ReviewsList'

export const Route = createFileRoute('/hosts/$hostId')({
  component: HostProfilePage,
})

type HostDanceStyleResponse = components['schemas']['HostDanceStyleResponse']

function HostProfilePage() {
  const { hostId } = Route.useParams()

  const { data: host, isLoading, error } = $api.useQuery(
    'get',
    '/api/v1/hosts/{host_id}',
    { params: { path: { host_id: hostId } } }
  )

  if (isLoading) {
    return (
      <div style={styles.loadingContainer}>
        <div style={styles.spinner} />
        <p style={styles.loadingText}>Loading host profile...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div style={styles.errorContainer}>
        <h2 style={styles.errorTitle}>Host Not Found</h2>
        <p style={styles.errorText}>
          The host profile you're looking for doesn't exist or has been removed.
        </p>
        <Link to="/hosts" style={styles.backLink}>
          Back to Host Discovery
        </Link>
      </div>
    )
  }

  if (!host) {
    return null
  }

  const formatPrice = (cents: number) => {
    return `$${(cents / 100).toFixed(0)}`
  }

  const formatRating = (rating: number | null | undefined) => {
    return rating ? rating.toFixed(1) : 'No ratings'
  }

  const getSkillLevelLabel = (level: number) => {
    const labels: Record<number, string> = {
      1: 'Beginner',
      2: 'Intermediate',
      3: 'Advanced',
      4: 'Expert',
      5: 'Master',
    }
    return labels[level] ?? 'Unknown'
  }

  const getVerificationBadge = (status: string) => {
    if (status === 'verified') {
      return (
        <span style={styles.verifiedBadge}>
          <svg
            style={styles.verifiedIcon}
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 20 20"
            fill="currentColor"
          >
            <path
              fillRule="evenodd"
              d="M16.403 12.652a3 3 0 000-5.304 3 3 0 00-3.75-3.751 3 3 0 00-5.305 0 3 3 0 00-3.751 3.75 3 3 0 000 5.305 3 3 0 003.75 3.751 3 3 0 005.305 0 3 3 0 003.751-3.75zm-2.546-4.46a.75.75 0 00-1.214-.883l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z"
              clipRule="evenodd"
            />
          </svg>
          Verified Host
        </span>
      )
    }
    if (status === 'pending') {
      return (
        <span style={styles.pendingBadge}>
          <svg
            style={styles.pendingIcon}
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 20 20"
            fill="currentColor"
          >
            <path
              fillRule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zm.75-13a.75.75 0 00-1.5 0v5c0 .414.336.75.75.75h4a.75.75 0 000-1.5h-3.25V5z"
              clipRule="evenodd"
            />
          </svg>
          Verification Pending
        </span>
      )
    }
    return null
  }

  return (
    <div style={styles.container}>
      {/* Header Section */}
      <div style={styles.header}>
        <Link to="/hosts" from="/hosts/$hostId" style={styles.backButton}>
          &larr; Back to hosts
        </Link>
      </div>

      {/* Profile Card */}
      <div style={styles.profileCard}>
        {/* Photo and Basic Info */}
        <div style={styles.topSection}>
          <div style={styles.photoContainer}>
            <div style={styles.photoPlaceholder}>
              {host.first_name.charAt(0)}{host.last_name.charAt(0)}
            </div>
          </div>
          <div style={styles.basicInfo}>
            <div style={styles.nameRow}>
              <h1 style={styles.name}>
                {host.first_name} {host.last_name}
              </h1>
              {getVerificationBadge(host.verification_status)}
            </div>
            {host.headline && (
              <p style={styles.headline}>{host.headline}</p>
            )}
            <div style={styles.statsRow}>
              <div style={styles.stat}>
                <span style={styles.statValue}>
                  {host.rating_average ? (
                    <>
                      <span style={styles.starIcon}>&#9733;</span>
                      {formatRating(host.rating_average)}
                    </>
                  ) : (
                    'New Host'
                  )}
                </span>
                <span style={styles.statLabel}>
                  {host.total_reviews > 0 ? `(${host.total_reviews} reviews)` : ''}
                </span>
              </div>
              <div style={styles.stat}>
                <span style={styles.statValue}>{host.total_sessions}</span>
                <span style={styles.statLabel}>sessions</span>
              </div>
              <div style={styles.stat}>
                <span style={styles.statValue}>{formatPrice(host.hourly_rate_cents)}</span>
                <span style={styles.statLabel}>/ hour</span>
              </div>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div style={styles.actionButtons}>
          <a
            href={`/hosts/${hostId}/book`}
            style={styles.bookButton}
          >
            Book Now
          </a>
          <a
            href={`/messages?newConversation=${hostId}`}
            style={styles.messageButton}
          >
            Message
          </a>
        </div>
      </div>

      {/* Bio Section */}
      {host.bio && (
        <div style={styles.section}>
          <h2 style={styles.sectionTitle}>About</h2>
          <p style={styles.bio}>{host.bio}</p>
        </div>
      )}

      {/* Dance Styles Section */}
      {host.dance_styles && host.dance_styles.length > 0 && (
        <div style={styles.section}>
          <h2 style={styles.sectionTitle}>Dance Styles</h2>
          <div style={styles.danceStylesGrid}>
            {host.dance_styles.map((style: HostDanceStyleResponse) => (
              <div key={style.dance_style_id} style={styles.danceStyleCard}>
                <div style={styles.danceStyleHeader}>
                  <span style={styles.danceStyleName}>
                    {style.dance_style.name}
                  </span>
                  <span style={styles.danceStyleCategory}>
                    {style.dance_style.category}
                  </span>
                </div>
                <div style={styles.skillLevel}>
                  <span style={styles.skillLabel}>Skill Level:</span>
                  <span style={styles.skillValue}>
                    {getSkillLevelLabel(style.skill_level)}
                  </span>
                  <div style={styles.skillDots}>
                    {[1, 2, 3, 4, 5].map((level) => (
                      <span
                        key={level}
                        style={{
                          ...styles.skillDot,
                          backgroundColor: level <= style.skill_level ? '#e11d48' : '#e5e7eb',
                        }}
                      />
                    ))}
                  </div>
                </div>
                {style.dance_style.description && (
                  <p style={styles.danceStyleDescription}>
                    {style.dance_style.description}
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Reviews Section */}
      <div style={styles.section}>
        <h2 style={styles.sectionTitle}>Reviews</h2>
        <ReviewsList hostId={hostId} totalReviews={host.total_reviews} />
      </div>
    </div>
  )
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    maxWidth: '800px',
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
  loadingText: {
    marginTop: '1rem',
    color: '#6b7280',
  },
  errorContainer: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: '60vh',
    padding: '2rem',
    textAlign: 'center',
  },
  errorTitle: {
    fontSize: '1.5rem',
    fontWeight: 'bold',
    color: '#1f2937',
    marginBottom: '0.5rem',
  },
  errorText: {
    color: '#6b7280',
    marginBottom: '1.5rem',
  },
  backLink: {
    color: '#e11d48',
    textDecoration: 'none',
    fontWeight: 500,
  },
  header: {
    marginBottom: '1rem',
  },
  backButton: {
    color: '#6b7280',
    textDecoration: 'none',
    fontSize: '0.875rem',
  },
  profileCard: {
    backgroundColor: 'white',
    borderRadius: '12px',
    boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
    padding: '1.5rem',
    marginBottom: '1.5rem',
  },
  topSection: {
    display: 'flex',
    gap: '1.5rem',
    flexWrap: 'wrap',
  },
  photoContainer: {
    flexShrink: 0,
  },
  photoPlaceholder: {
    width: '120px',
    height: '120px',
    borderRadius: '50%',
    backgroundColor: '#e11d48',
    color: 'white',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '2.5rem',
    fontWeight: 'bold',
  },
  basicInfo: {
    flex: 1,
    minWidth: '200px',
  },
  nameRow: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.75rem',
    flexWrap: 'wrap',
  },
  name: {
    fontSize: 'clamp(1.5rem, 4vw, 2rem)',
    fontWeight: 'bold',
    color: '#1f2937',
    margin: 0,
  },
  verifiedBadge: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '0.25rem',
    padding: '0.25rem 0.75rem',
    backgroundColor: '#dcfce7',
    color: '#166534',
    borderRadius: '9999px',
    fontSize: '0.75rem',
    fontWeight: 500,
  },
  verifiedIcon: {
    width: '16px',
    height: '16px',
  },
  pendingBadge: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '0.25rem',
    padding: '0.25rem 0.75rem',
    backgroundColor: '#fef3c7',
    color: '#92400e',
    borderRadius: '9999px',
    fontSize: '0.75rem',
    fontWeight: 500,
  },
  pendingIcon: {
    width: '14px',
    height: '14px',
  },
  headline: {
    color: '#6b7280',
    fontSize: '1rem',
    margin: '0.5rem 0',
  },
  statsRow: {
    display: 'flex',
    gap: '1.5rem',
    marginTop: '1rem',
    flexWrap: 'wrap',
  },
  stat: {
    display: 'flex',
    alignItems: 'baseline',
    gap: '0.25rem',
  },
  statValue: {
    fontSize: '1.125rem',
    fontWeight: 600,
    color: '#1f2937',
  },
  statLabel: {
    fontSize: '0.875rem',
    color: '#6b7280',
  },
  starIcon: {
    color: '#fbbf24',
    marginRight: '0.25rem',
  },
  actionButtons: {
    display: 'flex',
    gap: '1rem',
    marginTop: '1.5rem',
    flexWrap: 'wrap',
  },
  bookButton: {
    flex: 1,
    minWidth: '140px',
    padding: '0.875rem 1.5rem',
    backgroundColor: '#e11d48',
    color: 'white',
    border: 'none',
    borderRadius: '8px',
    fontSize: '1rem',
    fontWeight: 600,
    textAlign: 'center',
    textDecoration: 'none',
    cursor: 'pointer',
  },
  messageButton: {
    flex: 1,
    minWidth: '140px',
    padding: '0.875rem 1.5rem',
    backgroundColor: 'white',
    color: '#1f2937',
    border: '2px solid #e5e7eb',
    borderRadius: '8px',
    fontSize: '1rem',
    fontWeight: 600,
    textAlign: 'center',
    textDecoration: 'none',
    cursor: 'pointer',
  },
  section: {
    backgroundColor: 'white',
    borderRadius: '12px',
    boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
    padding: '1.5rem',
    marginBottom: '1.5rem',
  },
  sectionTitle: {
    fontSize: '1.25rem',
    fontWeight: 600,
    color: '#1f2937',
    marginTop: 0,
    marginBottom: '1rem',
  },
  bio: {
    color: '#4b5563',
    lineHeight: 1.6,
    margin: 0,
    whiteSpace: 'pre-wrap',
  },
  danceStylesGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
    gap: '1rem',
  },
  danceStyleCard: {
    padding: '1rem',
    border: '1px solid #e5e7eb',
    borderRadius: '8px',
    backgroundColor: '#fafafa',
  },
  danceStyleHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '0.5rem',
  },
  danceStyleName: {
    fontSize: '1rem',
    fontWeight: 600,
    color: '#1f2937',
  },
  danceStyleCategory: {
    fontSize: '0.75rem',
    color: '#6b7280',
    textTransform: 'capitalize',
    padding: '0.125rem 0.5rem',
    backgroundColor: '#e5e7eb',
    borderRadius: '4px',
  },
  skillLevel: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
    flexWrap: 'wrap',
  },
  skillLabel: {
    fontSize: '0.875rem',
    color: '#6b7280',
  },
  skillValue: {
    fontSize: '0.875rem',
    fontWeight: 500,
    color: '#1f2937',
  },
  skillDots: {
    display: 'flex',
    gap: '0.25rem',
  },
  skillDot: {
    width: '8px',
    height: '8px',
    borderRadius: '50%',
  },
  danceStyleDescription: {
    fontSize: '0.875rem',
    color: '#6b7280',
    marginTop: '0.5rem',
    marginBottom: 0,
  },
}
