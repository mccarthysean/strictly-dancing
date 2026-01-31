import { createFileRoute, Link, useNavigate } from '@tanstack/react-router'
import { useState, useMemo } from 'react'
import { $api } from '@/lib/api/$api'
import { useAuth } from '@/contexts/AuthContext'
import type { components } from '@/types/api.gen'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { cn } from '@/lib/utils'
import { Calendar, Clock, MapPin, ChevronRight, Loader2 } from 'lucide-react'

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

const STATUS_BADGES: Record<BookingStatus, { label: string; variant: 'default' | 'secondary' | 'destructive' | 'outline' }> = {
  pending: { label: 'Pending', variant: 'secondary' },
  confirmed: { label: 'Confirmed', variant: 'default' },
  in_progress: { label: 'In Progress', variant: 'default' },
  completed: { label: 'Completed', variant: 'outline' },
  cancelled: { label: 'Cancelled', variant: 'destructive' },
  disputed: { label: 'Disputed', variant: 'destructive' },
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
      <div className="flex min-h-[40vh] flex-col items-center justify-center">
        <Loader2 className="h-10 w-10 animate-spin text-primary" />
        <p className="mt-4 text-muted-foreground">Loading...</p>
      </div>
    )
  }

  // Not authenticated
  if (!isAuthenticated) {
    return (
      <div className="mx-auto max-w-4xl p-4">
        <Card className="mx-auto max-w-md">
          <CardContent className="p-8 text-center">
            <h2 className="mb-2 font-display text-xl font-semibold text-foreground">Login Required</h2>
            <p className="mb-6 text-muted-foreground">Please log in to view your bookings.</p>
            <Button asChild className="w-full">
              <Link to="/login" className="no-underline">
                Log In
              </Link>
            </Button>
            <p className="mt-4 text-sm text-muted-foreground">
              Don't have an account?{' '}
              <Link to="/register" className="font-medium text-primary no-underline hover:underline">
                Register
              </Link>
            </p>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-4xl p-4">
      <h1 className="mb-6 font-display text-[clamp(1.5rem,4vw,2rem)] font-bold text-foreground">
        My Bookings
      </h1>

      {/* Tabs */}
      <div className="mb-6 flex gap-2 border-b border-border">
        {TABS.map((tab) => (
          <button
            key={tab.key}
            type="button"
            onClick={() => setActiveTab(tab.key)}
            className={cn(
              "-mb-px border-b-2 px-4 py-3 text-sm font-medium transition-colors",
              activeTab === tab.key
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground hover:text-foreground"
            )}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Content */}
      {isLoading ? (
        <div className="flex min-h-[40vh] flex-col items-center justify-center">
          <Loader2 className="h-10 w-10 animate-spin text-primary" />
          <p className="mt-4 text-muted-foreground">Loading bookings...</p>
        </div>
      ) : error ? (
        <Card className="border-destructive bg-destructive/10">
          <CardContent className="p-4 text-center text-destructive">
            <p>Failed to load bookings. Please try again.</p>
          </CardContent>
        </Card>
      ) : filteredBookings.length === 0 ? (
        <Card className="bg-muted/50">
          <CardContent className="flex flex-col items-center justify-center p-12 text-center">
            <div className="mb-4 text-5xl">
              {activeTab === 'upcoming' ? '📅' : activeTab === 'past' ? '✓' : '✕'}
            </div>
            <h3 className="mb-2 font-display text-xl font-semibold text-foreground">
              {activeTab === 'upcoming'
                ? 'No upcoming bookings'
                : activeTab === 'past'
                  ? 'No past bookings'
                  : 'No cancelled bookings'}
            </h3>
            <p className="mb-6 text-muted-foreground">
              {activeTab === 'upcoming'
                ? 'Book a session with a dance host to get started!'
                : activeTab === 'past'
                  ? 'Your completed sessions will appear here.'
                  : 'Cancelled or disputed bookings will appear here.'}
            </p>
            {activeTab === 'upcoming' && (
              <Button asChild>
                <Link to="/hosts" className="no-underline">
                  Find a Host
                </Link>
              </Button>
            )}
          </CardContent>
        </Card>
      ) : (
        <div className="flex flex-col gap-4">
          {filteredBookings.map((booking: BookingWithDetailsResponse) => {
            const statusBadge = STATUS_BADGES[booking.status]
            const isHost = user?.id === booking.host_id
            const otherParty = isHost ? booking.client : booking.host

            return (
              <Card
                key={booking.id}
                className="cursor-pointer transition-all hover:-translate-y-0.5 hover:shadow-md"
                onClick={() => handleBookingClick(booking.id)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    handleBookingClick(booking.id)
                  }
                }}
                role="button"
                tabIndex={0}
              >
                <CardContent className="relative flex items-center p-4">
                  {/* Status badge */}
                  <Badge
                    variant={statusBadge.variant}
                    className="absolute right-12 top-4"
                  >
                    {statusBadge.label}
                  </Badge>

                  {/* Main content */}
                  <div className="flex-1 pr-8">
                    {/* Avatar and name */}
                    <div className="mb-3 flex items-center gap-3">
                      <Avatar>
                        <AvatarFallback className="bg-rose-600 text-white dark:bg-rose-gold-400 dark:text-foreground">
                          {otherParty
                            ? `${otherParty.first_name.charAt(0)}${otherParty.last_name.charAt(0)}`
                            : '?'}
                        </AvatarFallback>
                      </Avatar>
                      <div>
                        <p className="text-xs text-muted-foreground">
                          {isHost ? 'Session with client' : 'Session with host'}
                        </p>
                        <p className="font-semibold text-foreground">
                          {otherParty
                            ? `${otherParty.first_name} ${otherParty.last_name}`
                            : 'Unknown'}
                        </p>
                      </div>
                    </div>

                    {/* Date and time */}
                    <div className="mb-2 flex flex-wrap gap-4 text-sm text-muted-foreground">
                      <div className="flex items-center gap-1.5">
                        <Calendar className="h-4 w-4" />
                        <span>{formatDate(booking.scheduled_start)}</span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <Clock className="h-4 w-4" />
                        <span>
                          {formatTime(booking.scheduled_start)} - {formatTime(booking.scheduled_end)}
                        </span>
                      </div>
                    </div>

                    {/* Dance style and price */}
                    <div className="mb-1 flex items-center gap-4">
                      {booking.dance_style && (
                        <Badge variant="secondary" className="bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400">
                          {booking.dance_style.name}
                        </Badge>
                      )}
                      <span className="font-semibold text-foreground">{formatPrice(booking.amount_cents)}</span>
                    </div>

                    {/* Location */}
                    {booking.location_name && (
                      <p className="flex items-center gap-1.5 text-xs text-muted-foreground">
                        <MapPin className="h-3 w-3" />
                        {booking.location_name}
                      </p>
                    )}
                  </div>

                  {/* Arrow indicator */}
                  <ChevronRight className="h-5 w-5 text-muted-foreground/50" />
                </CardContent>
              </Card>
            )
          })}
        </div>
      )}
    </div>
  )
}
