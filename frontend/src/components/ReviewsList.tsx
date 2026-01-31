import { useState } from 'react'
import { $api } from '@/lib/api/$api'
import type { components } from '@/types/api.gen'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { cn } from '@/lib/utils'
import { Star, Loader2, CornerDownRight } from 'lucide-react'

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
      <div className="flex gap-0.5">
        {[1, 2, 3, 4, 5].map((star) => (
          <Star
            key={star}
            className={cn(
              "h-4 w-4",
              star <= rating
                ? "fill-amber-400 text-amber-400"
                : "fill-none text-muted-foreground/30"
            )}
          />
        ))}
      </div>
    )
  }

  if (isLoading && !hasLoadedOnce) {
    return (
      <div className="flex flex-col items-center py-8">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
        <p className="mt-3 text-sm text-muted-foreground">Loading reviews...</p>
      </div>
    )
  }

  if (error) {
    return (
      <Card className="border-destructive bg-destructive/10">
        <CardContent className="p-6 text-center text-destructive">
          <p>Failed to load reviews. Please try again.</p>
        </CardContent>
      </Card>
    )
  }

  if (totalReviews === 0) {
    return (
      <div className="py-6 text-center">
        <p className="italic text-muted-foreground">No reviews yet. Be the first to book a session!</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="text-sm text-muted-foreground">
        {totalReviews} review{totalReviews !== 1 ? 's' : ''}
      </div>

      <div className="space-y-4">
        {reviews.map((review) => (
          <Card key={review.id} className="bg-muted/30">
            <CardContent className="p-4">
              {/* Review Header */}
              <div className="mb-3 flex flex-wrap items-start justify-between gap-3">
                <div className="flex items-center gap-3">
                  <Avatar className="h-10 w-10">
                    <AvatarFallback className="bg-rose-600 text-sm text-white dark:bg-rose-gold-400 dark:text-foreground">
                      {review.reviewer ? (
                        `${review.reviewer.first_name.charAt(0)}${review.reviewer.last_name.charAt(0)}`
                      ) : (
                        '?'
                      )}
                    </AvatarFallback>
                  </Avatar>
                  <div>
                    <span className="font-semibold text-foreground">
                      {review.reviewer
                        ? `${review.reviewer.first_name} ${review.reviewer.last_name}`
                        : 'Anonymous'}
                    </span>
                    <div className="text-xs text-muted-foreground">{formatDate(review.created_at)}</div>
                  </div>
                </div>
                {renderStars(review.rating)}
              </div>

              {/* Review Comment */}
              {review.comment && (
                <p className="whitespace-pre-wrap leading-relaxed text-muted-foreground">
                  {review.comment}
                </p>
              )}

              {/* Host Response Section */}
              {review.host_response && (
                <div className="mt-4 rounded-md border-l-4 border-rose-600 bg-muted p-4 dark:border-rose-gold-400">
                  <div className="mb-2 flex flex-wrap items-center gap-2">
                    <CornerDownRight className="h-4 w-4 text-rose-600 dark:text-rose-gold-400" />
                    <span className="text-sm font-semibold text-foreground">Response from Host</span>
                    {review.host_responded_at && (
                      <span className="ml-auto text-xs text-muted-foreground">
                        {formatDate(review.host_responded_at)}
                      </span>
                    )}
                  </div>
                  <p className="whitespace-pre-wrap text-sm leading-relaxed text-muted-foreground">
                    {review.host_response}
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Load More Button */}
      {hasMore && (
        <div className="flex justify-center pt-2">
          <Button
            onClick={handleLoadMore}
            disabled={isLoading}
            variant="outline"
          >
            {isLoading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Loading...
              </>
            ) : (
              'Load More Reviews'
            )}
          </Button>
        </div>
      )}
    </div>
  )
}

export default ReviewsList
