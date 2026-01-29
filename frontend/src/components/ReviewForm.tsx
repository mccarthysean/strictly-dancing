import { useState } from 'react'
import { $api } from '@/lib/api/$api'

interface ReviewFormProps {
  bookingId: string
  hostName: string
  onSuccess?: () => void
  onCancel?: () => void
}

export function ReviewForm({
  bookingId,
  hostName,
  onSuccess,
  onCancel,
}: ReviewFormProps) {
  const [rating, setRating] = useState(0)
  const [hoveredRating, setHoveredRating] = useState(0)
  const [comment, setComment] = useState('')
  const [showConfirmation, setShowConfirmation] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const createReviewMutation = $api.useMutation(
    'post',
    '/api/v1/bookings/{booking_id}/review'
  )

  const isValid = rating >= 1 && rating <= 5

  const handleStarClick = (value: number) => {
    setRating(value)
    setError(null)
  }

  const handleStarHover = (value: number) => {
    setHoveredRating(value)
  }

  const handleStarLeave = () => {
    setHoveredRating(0)
  }

  const handleSubmitClick = () => {
    if (!isValid) {
      setError('Please select a rating')
      return
    }
    setShowConfirmation(true)
  }

  const handleConfirmSubmit = async () => {
    try {
      await createReviewMutation.mutateAsync({
        params: { path: { booking_id: bookingId } },
        body: {
          rating,
          comment: comment.trim() || null,
        },
      })
      onSuccess?.()
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to submit review'
      setError(errorMessage)
      setShowConfirmation(false)
    }
  }

  const handleCancelConfirmation = () => {
    setShowConfirmation(false)
  }

  const displayRating = hoveredRating || rating
  const ratingLabels = ['', 'Poor', 'Fair', 'Good', 'Great', 'Excellent']

  if (showConfirmation) {
    return (
      <div style={styles.container}>
        <div style={styles.confirmationCard}>
          <h3 style={styles.confirmationTitle}>Confirm Your Review</h3>

          <div style={styles.confirmationContent}>
            <p style={styles.confirmationText}>
              You are about to submit a review for{' '}
              <strong>{hostName}</strong>
            </p>

            <div style={styles.confirmationSummary}>
              <div style={styles.summaryRow}>
                <span style={styles.summaryLabel}>Rating:</span>
                <span style={styles.summaryValue}>
                  {'★'.repeat(rating)}
                  {'☆'.repeat(5 - rating)} ({ratingLabels[rating]})
                </span>
              </div>
              {comment.trim() && (
                <div style={styles.summaryRow}>
                  <span style={styles.summaryLabel}>Comment:</span>
                  <span style={styles.summaryValueText}>
                    "{comment.trim()}"
                  </span>
                </div>
              )}
            </div>

            <p style={styles.confirmationWarning}>
              This action cannot be undone. Are you sure you want to submit?
            </p>
          </div>

          <div style={styles.confirmationButtons}>
            <button
              onClick={handleCancelConfirmation}
              style={styles.cancelButton}
              disabled={createReviewMutation.isPending}
            >
              Go Back
            </button>
            <button
              onClick={handleConfirmSubmit}
              style={styles.confirmButton}
              disabled={createReviewMutation.isPending}
            >
              {createReviewMutation.isPending
                ? 'Submitting...'
                : 'Confirm & Submit'}
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div style={styles.container}>
      <div style={styles.formCard}>
        <h2 style={styles.title}>Leave a Review</h2>
        <p style={styles.subtitle}>
          How was your experience with <strong>{hostName}</strong>?
        </p>

        {/* Star Rating Selector */}
        <div style={styles.ratingSection}>
          <label style={styles.label}>Rating *</label>
          <div
            style={styles.starsContainer}
            onMouseLeave={handleStarLeave}
          >
            {[1, 2, 3, 4, 5].map((value) => (
              <button
                key={value}
                type="button"
                onClick={() => handleStarClick(value)}
                onMouseEnter={() => handleStarHover(value)}
                style={{
                  ...styles.starButton,
                  color: value <= displayRating ? '#facc15' : '#d1d5db',
                }}
                aria-label={`Rate ${value} star${value > 1 ? 's' : ''}`}
              >
                {value <= displayRating ? '★' : '☆'}
              </button>
            ))}
          </div>
          {displayRating > 0 && (
            <span style={styles.ratingLabel}>
              {ratingLabels[displayRating]}
            </span>
          )}
        </div>

        {/* Written Review Textarea */}
        <div style={styles.commentSection}>
          <label htmlFor="review-comment" style={styles.label}>
            Written Review (Optional)
          </label>
          <textarea
            id="review-comment"
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            placeholder="Share your experience with this host..."
            style={styles.textarea}
            maxLength={2000}
            rows={5}
          />
          <div style={styles.charCount}>
            {comment.length} / 2000 characters
          </div>
        </div>

        {/* Error Message */}
        {error && <div style={styles.errorMessage}>{error}</div>}

        {/* Action Buttons */}
        <div style={styles.buttonContainer}>
          {onCancel && (
            <button
              type="button"
              onClick={onCancel}
              style={styles.cancelButton}
            >
              Cancel
            </button>
          )}
          <button
            type="button"
            onClick={handleSubmitClick}
            style={{
              ...styles.submitButton,
              opacity: isValid ? 1 : 0.5,
              cursor: isValid ? 'pointer' : 'not-allowed',
            }}
            disabled={!isValid}
          >
            Submit Review
          </button>
        </div>
      </div>
    </div>
  )
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    width: '100%',
  },
  formCard: {
    backgroundColor: 'white',
    borderRadius: '12px',
    boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
    padding: '1.5rem',
  },
  title: {
    fontSize: '1.25rem',
    fontWeight: 'bold',
    color: '#1f2937',
    marginBottom: '0.5rem',
    margin: 0,
  },
  subtitle: {
    color: '#6b7280',
    marginBottom: '1.5rem',
    marginTop: '0.5rem',
  },
  ratingSection: {
    marginBottom: '1.5rem',
  },
  label: {
    display: 'block',
    fontSize: '0.875rem',
    fontWeight: '500',
    color: '#374151',
    marginBottom: '0.5rem',
  },
  starsContainer: {
    display: 'flex',
    gap: '0.25rem',
    marginBottom: '0.5rem',
  },
  starButton: {
    background: 'none',
    border: 'none',
    fontSize: '2.5rem',
    cursor: 'pointer',
    padding: '0.25rem',
    lineHeight: 1,
    transition: 'transform 0.1s ease',
  },
  ratingLabel: {
    fontSize: '0.875rem',
    color: '#6b7280',
    fontWeight: '500',
  },
  commentSection: {
    marginBottom: '1.5rem',
  },
  textarea: {
    width: '100%',
    padding: '0.75rem',
    borderRadius: '8px',
    border: '1px solid #d1d5db',
    fontSize: '1rem',
    resize: 'vertical',
    fontFamily: 'inherit',
    boxSizing: 'border-box',
  },
  charCount: {
    fontSize: '0.75rem',
    color: '#9ca3af',
    textAlign: 'right',
    marginTop: '0.25rem',
  },
  errorMessage: {
    backgroundColor: '#fef2f2',
    color: '#b91c1c',
    padding: '0.75rem',
    borderRadius: '8px',
    marginBottom: '1rem',
    fontSize: '0.875rem',
  },
  buttonContainer: {
    display: 'flex',
    gap: '0.75rem',
    justifyContent: 'flex-end',
  },
  cancelButton: {
    padding: '0.75rem 1.5rem',
    borderRadius: '8px',
    border: '1px solid #d1d5db',
    backgroundColor: 'white',
    color: '#374151',
    fontSize: '1rem',
    fontWeight: '500',
    cursor: 'pointer',
  },
  submitButton: {
    padding: '0.75rem 1.5rem',
    borderRadius: '8px',
    border: 'none',
    backgroundColor: '#7c3aed',
    color: 'white',
    fontSize: '1rem',
    fontWeight: '500',
    cursor: 'pointer',
  },
  // Confirmation styles
  confirmationCard: {
    backgroundColor: 'white',
    borderRadius: '12px',
    boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
    padding: '1.5rem',
  },
  confirmationTitle: {
    fontSize: '1.25rem',
    fontWeight: 'bold',
    color: '#1f2937',
    margin: 0,
    marginBottom: '1rem',
  },
  confirmationContent: {
    marginBottom: '1.5rem',
  },
  confirmationText: {
    color: '#374151',
    marginBottom: '1rem',
    marginTop: 0,
  },
  confirmationSummary: {
    backgroundColor: '#f9fafb',
    borderRadius: '8px',
    padding: '1rem',
    marginBottom: '1rem',
  },
  summaryRow: {
    display: 'flex',
    marginBottom: '0.5rem',
  },
  summaryLabel: {
    fontWeight: '500',
    color: '#374151',
    width: '80px',
    flexShrink: 0,
  },
  summaryValue: {
    color: '#facc15',
    letterSpacing: '0.1em',
  },
  summaryValueText: {
    color: '#6b7280',
    fontStyle: 'italic',
    flex: 1,
    wordBreak: 'break-word',
  },
  confirmationWarning: {
    color: '#92400e',
    backgroundColor: '#fffbeb',
    padding: '0.75rem',
    borderRadius: '8px',
    fontSize: '0.875rem',
    margin: 0,
  },
  confirmationButtons: {
    display: 'flex',
    gap: '0.75rem',
    justifyContent: 'flex-end',
  },
  confirmButton: {
    padding: '0.75rem 1.5rem',
    borderRadius: '8px',
    border: 'none',
    backgroundColor: '#16a34a',
    color: 'white',
    fontSize: '1rem',
    fontWeight: '500',
    cursor: 'pointer',
  },
}

export default ReviewForm
