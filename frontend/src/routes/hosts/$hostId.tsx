import { createFileRoute, Link } from '@tanstack/react-router'
import { $api } from '@/lib/api/$api'
import type { components } from '@/types/api.gen'
import { ReviewsList } from '@/components/ReviewsList'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { cn } from '@/lib/utils'
import { ArrowLeft, BadgeCheck, Clock, Star, MessageSquare, Loader2 } from 'lucide-react'

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
      <div className="flex min-h-[60vh] flex-col items-center justify-center">
        <Loader2 className="h-10 w-10 animate-spin text-primary" />
        <p className="mt-4 text-muted-foreground">Loading host profile...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex min-h-[60vh] flex-col items-center justify-center p-8 text-center">
        <h2 className="mb-2 font-display text-2xl font-bold text-foreground">Host Not Found</h2>
        <p className="mb-6 text-muted-foreground">
          The host profile you're looking for doesn't exist or has been removed.
        </p>
        <Button asChild variant="default">
          <Link to="/hosts" className="no-underline">
            Back to Host Discovery
          </Link>
        </Button>
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

  return (
    <div className="mx-auto max-w-4xl p-4">
      {/* Header */}
      <div className="mb-4">
        <Link
          to="/hosts"
          from="/hosts/$hostId"
          className="inline-flex items-center gap-1 text-sm text-muted-foreground no-underline hover:text-foreground"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to hosts
        </Link>
      </div>

      {/* Profile Card */}
      <Card className="mb-6">
        <CardContent className="p-6">
          {/* Photo and Basic Info */}
          <div className="flex flex-wrap gap-6">
            <Avatar className="h-28 w-28 text-4xl">
              <AvatarFallback className="bg-rose-600 text-white dark:bg-rose-gold-400 dark:text-foreground">
                {host.first_name.charAt(0)}{host.last_name.charAt(0)}
              </AvatarFallback>
            </Avatar>

            <div className="flex-1 space-y-3">
              <div className="flex flex-wrap items-center gap-3">
                <h1 className="font-display text-[clamp(1.5rem,4vw,2rem)] font-bold text-foreground">
                  {host.first_name} {host.last_name}
                </h1>
                {host.verification_status === 'verified' && (
                  <Badge className="bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400">
                    <BadgeCheck className="mr-1 h-3 w-3" />
                    Verified Host
                  </Badge>
                )}
                {host.verification_status === 'pending' && (
                  <Badge variant="secondary" className="bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400">
                    <Clock className="mr-1 h-3 w-3" />
                    Verification Pending
                  </Badge>
                )}
              </div>

              {host.headline && (
                <p className="text-muted-foreground">{host.headline}</p>
              )}

              <div className="flex flex-wrap items-baseline gap-6">
                <div className="flex items-baseline gap-1">
                  <span className="flex items-center gap-1 text-lg font-semibold text-foreground">
                    {host.rating_average ? (
                      <>
                        <Star className="h-5 w-5 fill-amber-400 text-amber-400" />
                        {formatRating(host.rating_average)}
                      </>
                    ) : (
                      'New Host'
                    )}
                  </span>
                  {host.total_reviews > 0 && (
                    <span className="text-sm text-muted-foreground">
                      ({host.total_reviews} reviews)
                    </span>
                  )}
                </div>
                <div className="flex items-baseline gap-1">
                  <span className="text-lg font-semibold text-foreground">{host.total_sessions}</span>
                  <span className="text-sm text-muted-foreground">sessions</span>
                </div>
                <div className="flex items-baseline gap-1">
                  <span className="text-lg font-semibold text-foreground">{formatPrice(host.hourly_rate_cents)}</span>
                  <span className="text-sm text-muted-foreground">/ hour</span>
                </div>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="mt-6 flex flex-wrap gap-4">
            <Button asChild className="flex-1 min-w-[140px]">
              <a href={`/hosts/${hostId}/book`} className="no-underline">
                Book Now
              </a>
            </Button>
            <Button asChild variant="outline" className="flex-1 min-w-[140px]">
              <a href={`/messages?newConversation=${hostId}`} className="no-underline">
                <MessageSquare className="mr-2 h-4 w-4" />
                Message
              </a>
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Bio Section */}
      {host.bio && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="font-display text-xl">About</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="whitespace-pre-wrap leading-relaxed text-muted-foreground">
              {host.bio}
            </p>
          </CardContent>
        </Card>
      )}

      {/* Dance Styles Section */}
      {host.dance_styles && host.dance_styles.length > 0 && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="font-display text-xl">Dance Styles</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              {host.dance_styles.map((style: HostDanceStyleResponse) => (
                <div
                  key={style.dance_style_id}
                  className="rounded-lg border border-border bg-muted/30 p-4"
                >
                  <div className="mb-2 flex items-center justify-between">
                    <span className="font-semibold text-foreground">
                      {style.dance_style.name}
                    </span>
                    <Badge variant="secondary" className="text-xs capitalize">
                      {style.dance_style.category}
                    </Badge>
                  </div>
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-sm text-muted-foreground">Skill Level:</span>
                    <span className="text-sm font-medium text-foreground">
                      {getSkillLevelLabel(style.skill_level)}
                    </span>
                    <div className="flex gap-1">
                      {[1, 2, 3, 4, 5].map((level) => (
                        <span
                          key={level}
                          className={cn(
                            "h-2 w-2 rounded-full",
                            level <= style.skill_level
                              ? "bg-rose-600 dark:bg-rose-gold-400"
                              : "bg-muted-foreground/20"
                          )}
                        />
                      ))}
                    </div>
                  </div>
                  {style.dance_style.description && (
                    <p className="mt-2 text-sm text-muted-foreground">
                      {style.dance_style.description}
                    </p>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Reviews Section */}
      <Card>
        <CardHeader>
          <CardTitle className="font-display text-xl">Reviews</CardTitle>
        </CardHeader>
        <CardContent>
          <ReviewsList hostId={hostId} totalReviews={host.total_reviews} />
        </CardContent>
      </Card>
    </div>
  )
}
