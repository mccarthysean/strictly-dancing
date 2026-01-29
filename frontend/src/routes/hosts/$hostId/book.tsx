import { createFileRoute, Link, useRouter } from '@tanstack/react-router'
import { useState, useMemo } from 'react'
import { $api } from '@/lib/api/$api'
import { useAuth } from '@/contexts/AuthContext'
import type { components } from '@/types/api.gen'

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
      <div style={styles.loadingContainer}>
        <div style={styles.spinner} />
        <p style={styles.loadingText}>Loading booking details...</p>
      </div>
    )
  }

  // Error state
  if (hostError || !host) {
    return (
      <div style={styles.errorContainer}>
        <h2 style={styles.errorTitle}>Host Not Found</h2>
        <p style={styles.errorText}>
          The host you're trying to book doesn't exist or is unavailable.
        </p>
        <Link to="/hosts" style={styles.backLink}>
          Back to Host Discovery
        </Link>
      </div>
    )
  }

  // Auth required state
  if (!isAuthenticated) {
    return (
      <div style={styles.container}>
        <div style={styles.header}>
          <Link to="/hosts/$hostId" params={{ hostId }} style={styles.backButton}>
            &larr; Back to profile
          </Link>
        </div>
        <div style={styles.authRequired}>
          <h2 style={styles.authTitle}>Login Required</h2>
          <p style={styles.authText}>
            Please log in to book a session with {host.first_name}.
          </p>
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
      {/* Header */}
      <div style={styles.header}>
        <Link to="/hosts/$hostId" params={{ hostId }} from="/hosts/$hostId/book" style={styles.backButton}>
          &larr; Back to profile
        </Link>
      </div>

      <h1 style={styles.title}>
        Book a session with {host.first_name} {host.last_name}
      </h1>

      {/* Main content */}
      <div style={styles.content}>
        {/* Left side: Calendar and time selection */}
        <div style={styles.selectionPanel}>
          {/* Duration picker */}
          <div style={styles.section}>
            <h2 style={styles.sectionTitle}>Select Duration</h2>
            <div style={styles.durationGrid}>
              {DURATION_OPTIONS.map((option) => (
                <button
                  key={option.value}
                  type="button"
                  onClick={() => {
                    setDurationMinutes(option.value)
                    setSelectedTime(null) // Reset time when duration changes
                  }}
                  style={{
                    ...styles.durationButton,
                    ...(durationMinutes === option.value ? styles.durationButtonActive : {}),
                  }}
                >
                  {option.label}
                </button>
              ))}
            </div>
          </div>

          {/* Calendar */}
          <div style={styles.section}>
            <h2 style={styles.sectionTitle}>Select Date</h2>
            {availabilityLoading ? (
              <div style={styles.loadingCalendar}>Loading availability...</div>
            ) : (
              <div style={styles.calendar}>
                <div style={styles.calendarHeader}>
                  <span style={styles.calendarMonth}>
                    {today.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}
                  </span>
                </div>
                <div style={styles.calendarGrid}>
                  {calendarDays.map((day) => (
                    <button
                      key={day.date}
                      type="button"
                      onClick={() => day.isAvailable && handleDateSelect(day.date)}
                      disabled={!day.isAvailable}
                      style={{
                        ...styles.calendarDay,
                        ...(day.isAvailable ? styles.calendarDayAvailable : styles.calendarDayUnavailable),
                        ...(selectedDate === day.date ? styles.calendarDaySelected : {}),
                      }}
                    >
                      {day.dayNum}
                    </button>
                  ))}
                </div>
                <div style={styles.calendarLegend}>
                  <span style={styles.legendItem}>
                    <span style={styles.legendDotAvailable} /> Available
                  </span>
                  <span style={styles.legendItem}>
                    <span style={styles.legendDotUnavailable} /> Unavailable
                  </span>
                </div>
              </div>
            )}
          </div>

          {/* Time slot selection */}
          {selectedDate && (
            <div style={styles.section}>
              <h2 style={styles.sectionTitle}>
                Select Time
                <span style={styles.selectedDateDisplay}>
                  {' '}
                  for{' '}
                  {new Date(selectedDate + 'T00:00:00').toLocaleDateString('en-US', {
                    weekday: 'short',
                    month: 'short',
                    day: 'numeric',
                  })}
                </span>
              </h2>
              {validTimeSlots.length === 0 ? (
                <p style={styles.noSlots}>
                  No available time slots for {durationMinutes} minutes on this date.
                  Try a shorter duration or different date.
                </p>
              ) : (
                <div style={styles.timeSlotGrid}>
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
                      <button
                        key={`${index}-${time}`}
                        type="button"
                        onClick={() => setSelectedTime(time)}
                        style={{
                          ...styles.timeSlotButton,
                          ...(selectedTime === time ? styles.timeSlotButtonActive : {}),
                        }}
                      >
                        {formatTime(time)}
                      </button>
                    ))
                  })}
                </div>
              )}
            </div>
          )}

          {/* Client notes */}
          {selectedTime && (
            <div style={styles.section}>
              <h2 style={styles.sectionTitle}>Notes (Optional)</h2>
              <textarea
                value={clientNotes}
                onChange={(e) => setClientNotes(e.target.value)}
                placeholder="Add any notes for your host..."
                style={styles.notesTextarea}
                maxLength={1000}
              />
            </div>
          )}
        </div>

        {/* Right side: Price breakdown */}
        <div style={styles.summaryPanel}>
          <div style={styles.hostSummary}>
            <div style={styles.hostAvatar}>
              {host.first_name.charAt(0)}
              {host.last_name.charAt(0)}
            </div>
            <div>
              <p style={styles.hostName}>
                {host.first_name} {host.last_name}
              </p>
              <p style={styles.hostRate}>{formatPrice(host.hourly_rate_cents)} / hour</p>
            </div>
          </div>

          {priceBreakdown && (
            <div style={styles.priceBreakdown}>
              <h3 style={styles.priceTitle}>Price Breakdown</h3>
              <div style={styles.priceRow}>
                <span>
                  {formatPrice(priceBreakdown.hourlyRate)}/hr x{' '}
                  {durationMinutes >= 60
                    ? `${durationMinutes / 60} hr${durationMinutes > 60 ? 's' : ''}`
                    : `${durationMinutes} min`}
                </span>
                <span>{formatPrice(priceBreakdown.subtotal)}</span>
              </div>
              <div style={styles.priceRow}>
                <span>Service fee (15%)</span>
                <span>{formatPrice(priceBreakdown.platformFee)}</span>
              </div>
              <div style={styles.priceDivider} />
              <div style={styles.priceRowTotal}>
                <span>Total</span>
                <span>{formatPrice(priceBreakdown.total)}</span>
              </div>
            </div>
          )}

          {/* Booking summary */}
          {selectedDate && selectedTime && (
            <div style={styles.bookingSummary}>
              <h3 style={styles.summaryTitle}>Your Booking</h3>
              <p style={styles.summaryDetail}>
                <strong>Date:</strong>{' '}
                {new Date(selectedDate + 'T00:00:00').toLocaleDateString('en-US', {
                  weekday: 'long',
                  month: 'long',
                  day: 'numeric',
                })}
              </p>
              <p style={styles.summaryDetail}>
                <strong>Time:</strong> {formatTime(selectedTime)}
              </p>
              <p style={styles.summaryDetail}>
                <strong>Duration:</strong>{' '}
                {durationMinutes >= 60
                  ? `${durationMinutes / 60} hour${durationMinutes > 60 ? 's' : ''}`
                  : `${durationMinutes} minutes`}
              </p>
            </div>
          )}

          {bookingError && (
            <div style={styles.errorBox}>
              {bookingError}
            </div>
          )}

          <button
            type="button"
            onClick={handleBookNow}
            disabled={!selectedDate || !selectedTime || createBooking.isPending}
            style={{
              ...styles.bookButton,
              ...((!selectedDate || !selectedTime || createBooking.isPending)
                ? styles.bookButtonDisabled
                : {}),
            }}
          >
            {createBooking.isPending ? 'Processing...' : 'Confirm Booking'}
          </button>

          <p style={styles.disclaimer}>
            You won't be charged until the host confirms your booking.
          </p>
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
  title: {
    fontSize: 'clamp(1.25rem, 3vw, 1.75rem)',
    fontWeight: 'bold',
    color: '#1f2937',
    marginBottom: '1.5rem',
  },
  content: {
    display: 'flex',
    gap: '2rem',
    flexWrap: 'wrap',
  },
  selectionPanel: {
    flex: '2',
    minWidth: '300px',
  },
  summaryPanel: {
    flex: '1',
    minWidth: '280px',
    backgroundColor: 'white',
    borderRadius: '12px',
    boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
    padding: '1.5rem',
    alignSelf: 'flex-start',
    position: 'sticky',
    top: '1rem',
  },
  section: {
    backgroundColor: 'white',
    borderRadius: '12px',
    boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
    padding: '1.5rem',
    marginBottom: '1.5rem',
  },
  sectionTitle: {
    fontSize: '1.125rem',
    fontWeight: 600,
    color: '#1f2937',
    marginTop: 0,
    marginBottom: '1rem',
  },
  selectedDateDisplay: {
    fontWeight: 'normal',
    color: '#6b7280',
  },
  durationGrid: {
    display: 'flex',
    gap: '0.5rem',
    flexWrap: 'wrap',
  },
  durationButton: {
    padding: '0.75rem 1rem',
    border: '2px solid #e5e7eb',
    borderRadius: '8px',
    backgroundColor: 'white',
    cursor: 'pointer',
    fontSize: '0.875rem',
    fontWeight: 500,
    transition: 'all 0.2s',
  },
  durationButtonActive: {
    borderColor: '#e11d48',
    backgroundColor: '#fdf2f4',
    color: '#e11d48',
  },
  loadingCalendar: {
    padding: '2rem',
    textAlign: 'center',
    color: '#6b7280',
  },
  calendar: {
    padding: '0.5rem',
  },
  calendarHeader: {
    marginBottom: '1rem',
    textAlign: 'center',
  },
  calendarMonth: {
    fontWeight: 600,
    color: '#1f2937',
  },
  calendarGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(7, 1fr)',
    gap: '0.5rem',
  },
  calendarDay: {
    aspectRatio: '1',
    border: 'none',
    borderRadius: '8px',
    fontSize: '0.875rem',
    fontWeight: 500,
    cursor: 'pointer',
    transition: 'all 0.2s',
  },
  calendarDayAvailable: {
    backgroundColor: '#dcfce7',
    color: '#166534',
  },
  calendarDayUnavailable: {
    backgroundColor: '#f3f4f6',
    color: '#9ca3af',
    cursor: 'not-allowed',
  },
  calendarDaySelected: {
    backgroundColor: '#e11d48',
    color: 'white',
  },
  calendarLegend: {
    display: 'flex',
    gap: '1rem',
    justifyContent: 'center',
    marginTop: '1rem',
    fontSize: '0.75rem',
    color: '#6b7280',
  },
  legendItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.25rem',
  },
  legendDotAvailable: {
    width: '8px',
    height: '8px',
    borderRadius: '50%',
    backgroundColor: '#dcfce7',
    border: '1px solid #166534',
  },
  legendDotUnavailable: {
    width: '8px',
    height: '8px',
    borderRadius: '50%',
    backgroundColor: '#f3f4f6',
    border: '1px solid #9ca3af',
  },
  noSlots: {
    color: '#6b7280',
    fontStyle: 'italic',
    textAlign: 'center',
    padding: '1rem',
  },
  timeSlotGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(90px, 1fr))',
    gap: '0.5rem',
  },
  timeSlotButton: {
    padding: '0.75rem',
    border: '2px solid #e5e7eb',
    borderRadius: '8px',
    backgroundColor: 'white',
    cursor: 'pointer',
    fontSize: '0.875rem',
    fontWeight: 500,
    transition: 'all 0.2s',
  },
  timeSlotButtonActive: {
    borderColor: '#e11d48',
    backgroundColor: '#fdf2f4',
    color: '#e11d48',
  },
  notesTextarea: {
    width: '100%',
    minHeight: '80px',
    padding: '0.75rem',
    border: '2px solid #e5e7eb',
    borderRadius: '8px',
    fontSize: '0.875rem',
    resize: 'vertical',
    boxSizing: 'border-box',
  },
  hostSummary: {
    display: 'flex',
    alignItems: 'center',
    gap: '1rem',
    paddingBottom: '1rem',
    borderBottom: '1px solid #e5e7eb',
    marginBottom: '1rem',
  },
  hostAvatar: {
    width: '50px',
    height: '50px',
    borderRadius: '50%',
    backgroundColor: '#e11d48',
    color: 'white',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontWeight: 'bold',
    fontSize: '1.125rem',
  },
  hostName: {
    fontWeight: 600,
    color: '#1f2937',
    margin: 0,
  },
  hostRate: {
    color: '#6b7280',
    fontSize: '0.875rem',
    margin: 0,
  },
  priceBreakdown: {
    marginBottom: '1.5rem',
  },
  priceTitle: {
    fontSize: '1rem',
    fontWeight: 600,
    color: '#1f2937',
    marginTop: 0,
    marginBottom: '0.75rem',
  },
  priceRow: {
    display: 'flex',
    justifyContent: 'space-between',
    fontSize: '0.875rem',
    color: '#6b7280',
    marginBottom: '0.5rem',
  },
  priceDivider: {
    height: '1px',
    backgroundColor: '#e5e7eb',
    margin: '0.75rem 0',
  },
  priceRowTotal: {
    display: 'flex',
    justifyContent: 'space-between',
    fontSize: '1rem',
    fontWeight: 600,
    color: '#1f2937',
  },
  bookingSummary: {
    backgroundColor: '#f9fafb',
    borderRadius: '8px',
    padding: '1rem',
    marginBottom: '1rem',
  },
  summaryTitle: {
    fontSize: '0.875rem',
    fontWeight: 600,
    color: '#1f2937',
    marginTop: 0,
    marginBottom: '0.5rem',
  },
  summaryDetail: {
    fontSize: '0.875rem',
    color: '#4b5563',
    margin: '0.25rem 0',
  },
  errorBox: {
    backgroundColor: '#fef2f2',
    border: '1px solid #fecaca',
    borderRadius: '8px',
    padding: '0.75rem',
    color: '#dc2626',
    fontSize: '0.875rem',
    marginBottom: '1rem',
  },
  bookButton: {
    width: '100%',
    padding: '1rem',
    backgroundColor: '#e11d48',
    color: 'white',
    border: 'none',
    borderRadius: '8px',
    fontSize: '1rem',
    fontWeight: 600,
    cursor: 'pointer',
    transition: 'background-color 0.2s',
  },
  bookButtonDisabled: {
    backgroundColor: '#d1d5db',
    cursor: 'not-allowed',
  },
  disclaimer: {
    fontSize: '0.75rem',
    color: '#9ca3af',
    textAlign: 'center',
    marginTop: '0.75rem',
    marginBottom: 0,
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
}
