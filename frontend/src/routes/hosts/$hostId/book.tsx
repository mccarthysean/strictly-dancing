import { createFileRoute, Link, useRouter } from '@tanstack/react-router'
import { useState, useMemo } from 'react'
import { $api } from '@/lib/api/$api'
import { useAuth } from '@/contexts/AuthContext'
import type { components } from '@/types/api.gen'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Separator } from '@/components/ui/separator'
import { cn } from '@/lib/utils'
import { ArrowLeft, Loader2 } from 'lucide-react'

export const Route = createFileRoute('/hosts/$hostId/book')({
  component: BookingFlowPage,
})

type AvailabilityForDateResponse = components['schemas']['AvailabilityForDateResponse']
type AvailabilitySlot = components['schemas']['AvailabilitySlot']

const DURATION_OPTIONS = [
  { value: 30, label: '30 min' },
  { value: 60, label: '1 hour' },
  { value: 90, label: '1.5 hours' },
  { value: 120, label: '2 hours' },
  { value: 180, label: '3 hours' },
  { value: 240, label: '4 hours' },
]

function BookingFlowPage() {
  const { hostId } = Route.useParams()
  const router = useRouter()
  const { isAuthenticated } = useAuth()

  // State
  const [selectedDate, setSelectedDate] = useState<string | null>(null)
  const [selectedTime, setSelectedTime] = useState<string | null>(null)
  const [durationMinutes, setDurationMinutes] = useState(60)
  const [clientNotes, setClientNotes] = useState('')
  const [bookingError, setBookingError] = useState<string | null>(null)

  // Calculate date range for availability (today + 30 days)
  const today = new Date()
  const startDateStr = today.toISOString().split('T')[0] ?? ''
  const endDateStr = new Date(today.getTime() + 30 * 24 * 60 * 60 * 1000)
    .toISOString()
    .split('T')[0] ?? ''

  // Fetch host profile
  const { data: host, isLoading: hostLoading, error: hostError } = $api.useQuery(
    'get',
    '/api/v1/hosts/{host_id}',
    { params: { path: { host_id: hostId } } }
  )

  // Fetch availability
  const { data: availability, isLoading: availabilityLoading } = $api.useQuery(
    'get',
    '/api/v1/hosts/{host_id}/availability',
    {
      params: {
        path: { host_id: hostId },
        query: {
          start_date: startDateStr,
          end_date: endDateStr,
        },
      },
    }
  )

  // Create booking mutation
  const createBooking = $api.useMutation('post', '/api/v1/bookings')

  // Get dates that have availability
  const availableDates = useMemo(() => {
    if (!availability?.availability) return new Set<string>()
    return new Set(
      availability.availability
        .filter((day: AvailabilityForDateResponse) =>
          day.slots && day.slots.length > 0
        )
        .map((day: AvailabilityForDateResponse) => day.availability_date)
    )
  }, [availability])

  // Get available time slots for selected date
  const availableSlots = useMemo(() => {
    if (!selectedDate || !availability?.availability) return []
    const dayAvailability = availability.availability.find(
      (day: AvailabilityForDateResponse) => day.availability_date === selectedDate
    )
    return dayAvailability?.slots ?? []
  }, [selectedDate, availability])

  // Filter time slots that can fit the selected duration
  const validTimeSlots = useMemo(() => {
    return availableSlots.filter((slot: AvailabilitySlot) => {
      if (!slot.start_time || !slot.end_time) return false
      const startMinutes = timeToMinutes(slot.start_time)
      const endMinutes = timeToMinutes(slot.end_time)
      return endMinutes - startMinutes >= durationMinutes
    })
  }, [availableSlots, durationMinutes])

  // Generate calendar days
  const calendarDays = useMemo(() => {
    const days: { date: string; dayNum: number; isAvailable: boolean; isPast: boolean }[] = []
    const currentDate = new Date(today)
    for (let i = 0; i < 30; i++) {
      const dateStr = currentDate.toISOString().split('T')[0]
      days.push({
        date: dateStr ?? '',
        dayNum: currentDate.getDate(),
        isAvailable: availableDates.has(dateStr ?? ''),
        isPast: false,
      })
      currentDate.setDate(currentDate.getDate() + 1)
    }
    return days
  }, [availableDates])

  // Calculate price breakdown
  const priceBreakdown = useMemo(() => {
    if (!host) return null
    const hourlyRate = host.hourly_rate_cents
    const totalMinutes = durationMinutes
    const subtotal = Math.round((hourlyRate * totalMinutes) / 60)
    const platformFee = Math.round(subtotal * 0.15) // 15% platform fee
    const total = subtotal + platformFee
    return { hourlyRate, subtotal, platformFee, total }
  }, [host, durationMinutes])

  const formatPrice = (cents: number) => `$${(cents / 100).toFixed(2)}`

  const formatTime = (timeStr: string) => {
    const [hours, minutes] = timeStr.split(':').map(Number)
    if (hours === undefined || minutes === undefined) return timeStr
    const period = hours >= 12 ? 'PM' : 'AM'
    const displayHours = hours % 12 || 12
    return `${displayHours}:${minutes.toString().padStart(2, '0')} ${period}`
  }

  const timeToMinutes = (timeStr: string) => {
    const [hours, minutes] = timeStr.split(':').map(Number)
    return (hours ?? 0) * 60 + (minutes ?? 0)
  }

  const handleDateSelect = (date: string) => {
    setSelectedDate(date)
    setSelectedTime(null) // Reset time when date changes
  }

  const handleBookNow = async () => {
    if (!selectedDate || !selectedTime || !isAuthenticated) return
    setBookingError(null)

    try {
      // Parse selected time and create datetime
      const scheduledStart = `${selectedDate}T${selectedTime}:00`

      await createBooking.mutateAsync({
        body: {
          host_id: hostId,
          scheduled_start: scheduledStart,
          duration_minutes: durationMinutes,
          client_notes: clientNotes || null,
        },
      })

      // Redirect to home page on success (bookings list to be implemented)
      router.navigate({ to: '/' })
    } catch (err) {
      const error = err as { body?: { detail?: string } }
      setBookingError(error.body?.detail ?? 'Failed to create booking. Please try again.')
    }
  }

  // Loading state
  if (hostLoading) {
    return (
      <div className="flex min-h-[60vh] flex-col items-center justify-center">
        <Loader2 className="h-10 w-10 animate-spin text-primary" />
        <p className="mt-4 text-muted-foreground">Loading booking details...</p>
      </div>
    )
  }

  // Error state
  if (hostError || !host) {
    return (
      <div className="flex min-h-[60vh] flex-col items-center justify-center p-8 text-center">
        <h2 className="mb-2 font-display text-2xl font-bold text-foreground">Host Not Found</h2>
        <p className="mb-6 text-muted-foreground">
          The host you're trying to book doesn't exist or is unavailable.
        </p>
        <Button asChild>
          <Link to="/hosts" className="no-underline">
            Back to Host Discovery
          </Link>
        </Button>
      </div>
    )
  }

  // Auth required state
  if (!isAuthenticated) {
    return (
      <div className="mx-auto max-w-7xl p-4">
        <div className="mb-4">
          <Link
            to="/hosts/$hostId"
            params={{ hostId }}
            className="inline-flex items-center gap-1 text-sm text-muted-foreground no-underline hover:text-foreground"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to profile
          </Link>
        </div>
        <Card className="mx-auto max-w-md">
          <CardContent className="p-8 text-center">
            <h2 className="mb-2 font-display text-xl font-semibold text-foreground">Login Required</h2>
            <p className="mb-6 text-muted-foreground">
              Please log in to book a session with {host.first_name}.
            </p>
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
    <div className="mx-auto max-w-7xl p-4">
      {/* Header */}
      <div className="mb-4">
        <Link
          to="/hosts/$hostId"
          params={{ hostId }}
          from="/hosts/$hostId/book"
          className="inline-flex items-center gap-1 text-sm text-muted-foreground no-underline hover:text-foreground"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to profile
        </Link>
      </div>

      <h1 className="mb-6 font-display text-[clamp(1.25rem,3vw,1.75rem)] font-bold text-foreground">
        Book a session with {host.first_name} {host.last_name}
      </h1>

      {/* Main content */}
      <div className="flex flex-col gap-8 lg:flex-row">
        {/* Left side: Calendar and time selection */}
        <div className="flex-[2] space-y-6">
          {/* Duration picker */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Select Duration</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {DURATION_OPTIONS.map((option) => (
                  <Button
                    key={option.value}
                    type="button"
                    variant={durationMinutes === option.value ? 'default' : 'outline'}
                    onClick={() => {
                      setDurationMinutes(option.value)
                      setSelectedTime(null) // Reset time when duration changes
                    }}
                  >
                    {option.label}
                  </Button>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Calendar */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Select Date</CardTitle>
            </CardHeader>
            <CardContent>
              {availabilityLoading ? (
                <div className="flex items-center justify-center py-8 text-muted-foreground">
                  <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                  Loading availability...
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="text-center font-medium text-foreground">
                    {today.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}
                  </div>
                  <div className="grid grid-cols-7 gap-2">
                    {calendarDays.map((day) => (
                      <button
                        key={day.date}
                        type="button"
                        onClick={() => day.isAvailable && handleDateSelect(day.date)}
                        disabled={!day.isAvailable}
                        className={cn(
                          "aspect-square rounded-lg text-sm font-medium transition-colors",
                          day.isAvailable
                            ? "bg-green-100 text-green-700 hover:bg-green-200 dark:bg-green-900/30 dark:text-green-400 dark:hover:bg-green-900/50"
                            : "cursor-not-allowed bg-muted text-muted-foreground/50",
                          selectedDate === day.date &&
                            "bg-primary text-primary-foreground hover:bg-primary/90 dark:bg-primary dark:text-primary-foreground"
                        )}
                      >
                        {day.dayNum}
                      </button>
                    ))}
                  </div>
                  <div className="flex items-center justify-center gap-4 text-xs text-muted-foreground">
                    <span className="flex items-center gap-1">
                      <span className="h-2 w-2 rounded-full bg-green-200 ring-1 ring-green-600" />
                      Available
                    </span>
                    <span className="flex items-center gap-1">
                      <span className="h-2 w-2 rounded-full bg-muted ring-1 ring-muted-foreground/50" />
                      Unavailable
                    </span>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Time slot selection */}
          {selectedDate && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">
                  Select Time
                  <span className="ml-2 font-normal text-muted-foreground">
                    for{' '}
                    {new Date(selectedDate + 'T00:00:00').toLocaleDateString('en-US', {
                      weekday: 'short',
                      month: 'short',
                      day: 'numeric',
                    })}
                  </span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                {validTimeSlots.length === 0 ? (
                  <p className="py-4 text-center italic text-muted-foreground">
                    No available time slots for {durationMinutes} minutes on this date.
                    Try a shorter duration or different date.
                  </p>
                ) : (
                  <div className="grid grid-cols-3 gap-2 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6">
                    {validTimeSlots.map((slot: AvailabilitySlot, index: number) => {
                      // Generate start times within the slot
                      const startMinutes = timeToMinutes(slot.start_time ?? '00:00')
                      const endMinutes = timeToMinutes(slot.end_time ?? '00:00')
                      const times: string[] = []
                      for (let t = startMinutes; t + durationMinutes <= endMinutes; t += 30) {
                        const hours = Math.floor(t / 60)
                        const mins = t % 60
                        times.push(`${hours.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}`)
                      }
                      return times.map((time) => (
                        <Button
                          key={`${index}-${time}`}
                          type="button"
                          variant={selectedTime === time ? 'default' : 'outline'}
                          size="sm"
                          onClick={() => setSelectedTime(time)}
                        >
                          {formatTime(time)}
                        </Button>
                      ))
                    })}
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Client notes */}
          {selectedTime && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Notes (Optional)</CardTitle>
              </CardHeader>
              <CardContent>
                <textarea
                  value={clientNotes}
                  onChange={(e) => setClientNotes(e.target.value)}
                  placeholder="Add any notes for your host..."
                  className="min-h-20 w-full resize-y rounded-lg border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                  maxLength={1000}
                />
              </CardContent>
            </Card>
          )}
        </div>

        {/* Right side: Price breakdown */}
        <div className="flex-1">
          <Card className="sticky top-20">
            <CardContent className="p-6">
              <div className="mb-4 flex items-center gap-4 border-b border-border pb-4">
                <Avatar className="h-12 w-12">
                  <AvatarFallback className="bg-rose-600 text-white dark:bg-rose-gold-400 dark:text-foreground">
                    {host.first_name.charAt(0)}{host.last_name.charAt(0)}
                  </AvatarFallback>
                </Avatar>
                <div>
                  <p className="font-semibold text-foreground">
                    {host.first_name} {host.last_name}
                  </p>
                  <p className="text-sm text-muted-foreground">{formatPrice(host.hourly_rate_cents)} / hour</p>
                </div>
              </div>

              {priceBreakdown && (
                <div className="mb-6 space-y-3">
                  <h3 className="font-semibold text-foreground">Price Breakdown</h3>
                  <div className="flex justify-between text-sm text-muted-foreground">
                    <span>
                      {formatPrice(priceBreakdown.hourlyRate)}/hr x{' '}
                      {durationMinutes >= 60
                        ? `${durationMinutes / 60} hr${durationMinutes > 60 ? 's' : ''}`
                        : `${durationMinutes} min`}
                    </span>
                    <span>{formatPrice(priceBreakdown.subtotal)}</span>
                  </div>
                  <div className="flex justify-between text-sm text-muted-foreground">
                    <span>Service fee (15%)</span>
                    <span>{formatPrice(priceBreakdown.platformFee)}</span>
                  </div>
                  <Separator />
                  <div className="flex justify-between font-semibold text-foreground">
                    <span>Total</span>
                    <span>{formatPrice(priceBreakdown.total)}</span>
                  </div>
                </div>
              )}

              {/* Booking summary */}
              {selectedDate && selectedTime && (
                <div className="mb-4 rounded-lg bg-muted p-4">
                  <h3 className="mb-2 text-sm font-semibold text-foreground">Your Booking</h3>
                  <p className="text-sm text-muted-foreground">
                    <strong>Date:</strong>{' '}
                    {new Date(selectedDate + 'T00:00:00').toLocaleDateString('en-US', {
                      weekday: 'long',
                      month: 'long',
                      day: 'numeric',
                    })}
                  </p>
                  <p className="text-sm text-muted-foreground">
                    <strong>Time:</strong> {formatTime(selectedTime)}
                  </p>
                  <p className="text-sm text-muted-foreground">
                    <strong>Duration:</strong>{' '}
                    {durationMinutes >= 60
                      ? `${durationMinutes / 60} hour${durationMinutes > 60 ? 's' : ''}`
                      : `${durationMinutes} minutes`}
                  </p>
                </div>
              )}

              {bookingError && (
                <div className="mb-4 rounded-lg border border-destructive bg-destructive/10 px-3 py-2 text-sm text-destructive">
                  {bookingError}
                </div>
              )}

              <Button
                onClick={handleBookNow}
                disabled={!selectedDate || !selectedTime || createBooking.isPending}
                className="w-full"
              >
                {createBooking.isPending ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Processing...
                  </>
                ) : (
                  'Confirm Booking'
                )}
              </Button>

              <p className="mt-3 text-center text-xs text-muted-foreground">
                You won't be charged until the host confirms your booking.
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
