import { useState } from 'react'
import { $api } from '@/lib/api/$api'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { cn } from '@/lib/utils'
import { Star, AlertTriangle } from 'lucide-react'

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
      <Card>
        <CardHeader>
          <CardTitle className="font-display text-xl">Confirm Your Review</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-muted-foreground">
            You are about to submit a review for <strong className="text-foreground">{hostName}</strong>
          </p>

          <div className="rounded-lg bg-muted p-4">
            <div className="mb-2 flex items-center gap-2">
              <span className="text-sm font-medium text-muted-foreground">Rating:</span>
              <span className="flex items-center gap-0.5 text-amber-400">
                {[1, 2, 3, 4, 5].map((i) => (
                  <Star
                    key={i}
                    className={cn(
                      "h-4 w-4",
                      i <= rating ? "fill-current" : "fill-none opacity-30"
                    )}
                  />
                ))}
              </span>
              <span className="text-sm text-muted-foreground">({ratingLabels[rating]})</span>
            </div>
            {comment.trim() && (
              <div className="flex gap-2">
                <span className="text-sm font-medium text-muted-foreground">Comment:</span>
                <span className="flex-1 text-sm italic text-muted-foreground">
                  "{comment.trim()}"
                </span>
              </div>
            )}
          </div>

          <div className="flex items-start gap-2 rounded-lg bg-amber-50 p-3 text-sm text-amber-700 dark:bg-amber-900/20 dark:text-amber-400">
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
            <p>This action cannot be undone. Are you sure you want to submit?</p>
          </div>

          <div className="flex justify-end gap-3">
            <Button
              variant="outline"
              onClick={handleCancelConfirmation}
              disabled={createReviewMutation.isPending}
            >
              Go Back
            </Button>
            <Button
              onClick={handleConfirmSubmit}
              disabled={createReviewMutation.isPending}
              className="bg-green-600 hover:bg-green-700"
            >
              {createReviewMutation.isPending
                ? 'Submitting...'
                : 'Confirm & Submit'}
            </Button>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="font-display text-xl">Leave a Review</CardTitle>
        <CardDescription>
          How was your experience with <strong className="text-foreground">{hostName}</strong>?
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Star Rating Selector */}
        <div className="space-y-2">
          <Label>Rating *</Label>
          <div
            className="flex gap-1"
            onMouseLeave={handleStarLeave}
          >
            {[1, 2, 3, 4, 5].map((value) => (
              <button
                key={value}
                type="button"
                onClick={() => handleStarClick(value)}
                onMouseEnter={() => handleStarHover(value)}
                className="p-1 transition-transform hover:scale-110"
                aria-label={`Rate ${value} star${value > 1 ? 's' : ''}`}
              >
                <Star
                  className={cn(
                    "h-8 w-8 transition-colors",
                    value <= displayRating
                      ? "fill-amber-400 text-amber-400"
                      : "fill-none text-muted-foreground/30"
                  )}
                />
              </button>
            ))}
          </div>
          {displayRating > 0 && (
            <span className="text-sm font-medium text-muted-foreground">
              {ratingLabels[displayRating]}
            </span>
          )}
        </div>

        {/* Written Review Textarea */}
        <div className="space-y-2">
          <Label htmlFor="review-comment">Written Review (Optional)</Label>
          <textarea
            id="review-comment"
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            placeholder="Share your experience with this host..."
            className="min-h-28 w-full resize-y rounded-lg border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
            maxLength={2000}
            rows={5}
          />
          <div className="text-right text-xs text-muted-foreground">
            {comment.length} / 2000 characters
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="rounded-lg border border-destructive bg-destructive/10 px-3 py-2 text-sm text-destructive">
            {error}
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex justify-end gap-3">
          {onCancel && (
            <Button
              type="button"
              variant="outline"
              onClick={onCancel}
            >
              Cancel
            </Button>
          )}
          <Button
            type="button"
            onClick={handleSubmitClick}
            disabled={!isValid}
          >
            Submit Review
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}

export default ReviewForm
