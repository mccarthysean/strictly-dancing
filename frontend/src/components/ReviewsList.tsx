import { useState } from 'react'
import { $api } from '@/lib/api/$api'
import type { components } from '@/types/api.gen'

type ReviewWithUserResponse = components['schemas']['ReviewWithUserResponse']

interface ReviewsListProps {
  hostId: string
  totalReviews: number
}

export function ReviewsList({ hostId, totalReviews }: ReviewsListProps) {
  const [cursor, setCursor] = useState<string | null>(null)
  const [allReviews, setAllReviews] = useState<ReviewWithUserResponse[]>([])
  const [hasLoadedOnce, setHasLoadedOnce] = useState(false)

  const { data, isLoading, error } = $api.useQuery(
    'get',
    '/api/v1/hosts/{host_id}/reviews',
    {
      params: {
        path: { host_id: hostId },
        query: { limit: 10, ...(cursor ? { cursor } : {}) },
      },
    }
  )

  // Update reviews when new data arrives
  if (data && !hasLoadedOnce) {
    setAllReviews(data.items ?? [])
    setHasLoadedOnce(true)
  }

  const handleLoadMore = () => {
    if (data?.next_cursor) {
      // Append new reviews to existing ones
      setAllReviews(prev => [...prev, ...(data.items ?? [])])
      setCursor(data.next_cursor)
    }
  }

  // Combine initial load with subsequent loads
  const reviews = cursor ? allReviews : (data?.items ?? [])
  const hasMore = data?.has_more ?? false

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24))

    if (diffDays === 0) {
      return 'Today'
    } else if (diffDays === 1) {
      return 'Yesterday'
    } else if (diffDays < 7) {
      return `${diffDays} days ago`
    } else if (diffDays < 30) {
      const weeks = Math.floor(diffDays / 7)
      return `${weeks} week${weeks > 1 ? 's' : ''} ago`
    } else if (diffDays < 365) {
      const months = Math.floor(diffDays / 30)
      return `${months} month${months > 1 ? 's' : ''} ago`
    }
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    })
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

  if (isLoading && !hasLoadedOnce) {
    return (
      <div style={styles.loadingContainer}>
        <div style={styles.spinner} />
        <p style={styles.loadingText}>Loading reviews...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div style={styles.errorContainer}>
        <p style={styles.errorText}>Failed to load reviews. Please try again.</p>
      </div>
    )
  }

  if (totalReviews === 0) {
    return (
      <div style={styles.emptyContainer}>
        <p style={styles.emptyText}>No reviews yet. Be the first to book a session!</p>
      </div>
    )
  }

  return (
    <div style={styles.container}>
      <div style={styles.reviewsHeader}>
        <span style={styles.reviewCount}>{totalReviews} review{totalReviews !== 1 ? 's' : ''}</span>
      </div>

      <div style={styles.reviewsList}>
        {reviews.map((review) => (
          <div key={review.id} style={styles.reviewCard}>
            {/* Review Header */}
            <div style={styles.reviewHeader}>
              <div style={styles.reviewerInfo}>
                <div style={styles.reviewerAvatar}>
                  {review.reviewer ? (
                    `${review.reviewer.first_name.charAt(0)}${review.reviewer.last_name.charAt(0)}`
                  ) : (
                    '?'
                  )}
                </div>
                <div style={styles.reviewerDetails}>
                  <span style={styles.reviewerName}>
                    {review.reviewer
                      ? `${review.reviewer.first_name} ${review.reviewer.last_name}`
                      : 'Anonymous'}
                  </span>
                  <span style={styles.reviewDate}>{formatDate(review.created_at)}</span>
                </div>
              </div>
              {renderStars(review.rating)}
            </div>

            {/* Review Comment */}
            {review.comment && (
              <div style={styles.reviewComment}>
                <p style={styles.commentText}>{review.comment}</p>
              </div>
            )}

            {/* Host Response Section */}
            {review.host_response && (
              <div style={styles.hostResponseSection}>
                <div style={styles.hostResponseHeader}>
                  <span style={styles.hostResponseIcon}>↩</span>
                  <span style={styles.hostResponseLabel}>Response from Host</span>
                  {review.host_responded_at && (
                    <span style={styles.hostResponseDate}>
                      {formatDate(review.host_responded_at)}
                    </span>
                  )}
                </div>
                <p style={styles.hostResponseText}>{review.host_response}</p>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Load More Button */}
      {hasMore && (
        <div style={styles.loadMoreContainer}>
          <button
            onClick={handleLoadMore}
            disabled={isLoading}
            style={{
              ...styles.loadMoreButton,
              ...(isLoading ? styles.loadMoreButtonDisabled : {}),
            }}
          >
            {isLoading ? 'Loading...' : 'Load More Reviews'}
          </button>
        </div>
      )}
    </div>
  )
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    gap: '1rem',
  },
  loadingContainer: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    padding: '2rem',
  },
  spinner: {
    width: '32px',
    height: '32px',
    border: '3px solid #e5e7eb',
    borderTop: '3px solid #e11d48',
    borderRadius: '50%',
    animation: 'spin 1s linear infinite',
  },
  loadingText: {
    marginTop: '0.75rem',
    color: '#6b7280',
    fontSize: '0.875rem',
  },
  errorContainer: {
    padding: '1.5rem',
    backgroundColor: '#fef2f2',
    borderRadius: '8px',
    textAlign: 'center',
  },
  errorText: {
    color: '#dc2626',
    margin: 0,
  },
  emptyContainer: {
    padding: '1.5rem',
    textAlign: 'center',
  },
  emptyText: {
    color: '#9ca3af',
    fontStyle: 'italic',
    margin: 0,
  },
  reviewsHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
  },
  reviewCount: {
    fontSize: '0.875rem',
    color: '#6b7280',
  },
  reviewsList: {
    display: 'flex',
    flexDirection: 'column',
    gap: '1rem',
  },
  reviewCard: {
    padding: '1rem',
    backgroundColor: '#fafafa',
    borderRadius: '8px',
    border: '1px solid #e5e7eb',
  },
  reviewHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    flexWrap: 'wrap',
    gap: '0.75rem',
    marginBottom: '0.75rem',
  },
  reviewerInfo: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.75rem',
  },
  reviewerAvatar: {
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
  reviewerDetails: {
    display: 'flex',
    flexDirection: 'column',
  },
  reviewerName: {
    fontWeight: 600,
    color: '#1f2937',
    fontSize: '0.9375rem',
  },
  reviewDate: {
    fontSize: '0.75rem',
    color: '#9ca3af',
  },
  stars: {
    display: 'flex',
    gap: '2px',
  },
  star: {
    fontSize: '1.125rem',
  },
  reviewComment: {
    marginTop: '0.5rem',
  },
  commentText: {
    color: '#4b5563',
    lineHeight: 1.6,
    margin: 0,
    whiteSpace: 'pre-wrap',
  },
  hostResponseSection: {
    marginTop: '1rem',
    padding: '1rem',
    backgroundColor: '#f3f4f6',
    borderRadius: '6px',
    borderLeft: '3px solid #e11d48',
  },
  hostResponseHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
    marginBottom: '0.5rem',
    flexWrap: 'wrap',
  },
  hostResponseIcon: {
    color: '#e11d48',
    fontSize: '1rem',
  },
  hostResponseLabel: {
    fontWeight: 600,
    color: '#1f2937',
    fontSize: '0.875rem',
  },
  hostResponseDate: {
    fontSize: '0.75rem',
    color: '#9ca3af',
    marginLeft: 'auto',
  },
  hostResponseText: {
    color: '#4b5563',
    lineHeight: 1.6,
    margin: 0,
    fontSize: '0.9375rem',
    whiteSpace: 'pre-wrap',
  },
  loadMoreContainer: {
    display: 'flex',
    justifyContent: 'center',
    marginTop: '0.5rem',
  },
  loadMoreButton: {
    padding: '0.75rem 1.5rem',
    backgroundColor: 'white',
    color: '#1f2937',
    border: '1px solid #e5e7eb',
    borderRadius: '8px',
    fontSize: '0.875rem',
    fontWeight: 500,
    cursor: 'pointer',
    transition: 'background-color 0.2s',
  },
  loadMoreButtonDisabled: {
    opacity: 0.6,
    cursor: 'not-allowed',
  },
}

export default ReviewsList
