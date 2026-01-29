import { createFileRoute, Link } from '@tanstack/react-router'
import { useState, useCallback, useEffect } from 'react'
import { $api } from '@/lib/api/$api'
import { useAuth } from '@/contexts/AuthContext'
import type { components } from '@/types/api.gen'

export const Route = createFileRoute('/host/availability')({
  component: HostAvailabilityPage,
})

type DayOfWeek = components['schemas']['DayOfWeek']
type RecurringAvailabilityResponse = components['schemas']['RecurringAvailabilityResponse']
type AvailabilityOverrideResponse = components['schemas']['AvailabilityOverrideResponse']
type AvailabilityOverrideType = components['schemas']['AvailabilityOverrideType']

// Days of week mapping
const DAYS_OF_WEEK: { value: DayOfWeek; label: string; short: string }[] = [
  { value: 0, label: 'Monday', short: 'Mon' },
  { value: 1, label: 'Tuesday', short: 'Tue' },
  { value: 2, label: 'Wednesday', short: 'Wed' },
  { value: 3, label: 'Thursday', short: 'Thu' },
  { value: 4, label: 'Friday', short: 'Fri' },
  { value: 5, label: 'Saturday', short: 'Sat' },
  { value: 6, label: 'Sunday', short: 'Sun' },
]

// Time slot options (30-minute intervals)
const TIME_SLOTS: string[] = []
for (let hour = 0; hour < 24; hour++) {
  for (let min = 0; min < 60; min += 30) {
    const h = hour.toString().padStart(2, '0')
    const m = min.toString().padStart(2, '0')
    TIME_SLOTS.push(`${h}:${m}`)
  }
}

// Format time for display
function formatTime(time: string): string {
  const parts = time.split(':')
  const hours = parts[0] ?? '00'
  const minutes = parts[1] ?? '00'
  const h = parseInt(hours)
  const ampm = h >= 12 ? 'PM' : 'AM'
  const displayHour = h === 0 ? 12 : h > 12 ? h - 12 : h
  return `${displayHour}:${minutes} ${ampm}`
}

// Format date for display
function formatDate(dateStr: string): string {
  const date = new Date(dateStr + 'T00:00:00')
  return date.toLocaleDateString('en-US', {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })
}

// Time slot type for weekly schedule
interface WeeklySlot {
  dayOfWeek: DayOfWeek
  startTime: string
  endTime: string
  id?: string | undefined
  isActive?: boolean | undefined
}

function HostAvailabilityPage() {
  const { isAuthenticated, isLoading: authLoading, user } = useAuth()

  // Weekly schedule state
  const [weeklySlots, setWeeklySlots] = useState<WeeklySlot[]>([])
  const [isEditingWeekly, setIsEditingWeekly] = useState(false)

  // Override state
  const [overrides, setOverrides] = useState<AvailabilityOverrideResponse[]>([])
  const [showAddOverride, setShowAddOverride] = useState(false)
  const [newOverrideDate, setNewOverrideDate] = useState('')
  const [newOverrideType, setNewOverrideType] = useState<AvailabilityOverrideType>('blocked')
  const [newOverrideStartTime, setNewOverrideStartTime] = useState('09:00')
  const [newOverrideEndTime, setNewOverrideEndTime] = useState('17:00')
  const [newOverrideAllDay, setNewOverrideAllDay] = useState(false)
  const [newOverrideReason, setNewOverrideReason] = useState('')

  // UI state
  const [isSaving, setIsSaving] = useState(false)
  const [saveError, setSaveError] = useState<string | null>(null)
  const [saveSuccess, setSaveSuccess] = useState(false)
  const [activeTab, setActiveTab] = useState<'weekly' | 'overrides' | 'blocked'>('weekly')

  // Fetch availability
  const { data: availabilityData, isLoading: availabilityLoading, error: availabilityError, refetch } = $api.useQuery(
    'get',
    '/api/v1/users/me/host-profile/availability',
    {},
    {
      enabled: isAuthenticated,
    }
  )

  // Initialize state from fetched data
  useEffect(() => {
    if (availabilityData) {
      // Map recurring availability to weekly slots
      const slots: WeeklySlot[] = (availabilityData.recurring ?? []).map((rec: RecurringAvailabilityResponse) => ({
        dayOfWeek: rec.day_of_week,
        startTime: rec.start_time,
        endTime: rec.end_time,
        id: rec.id,
        isActive: rec.is_active,
      }))
      setWeeklySlots(slots)

      // Set overrides
      setOverrides(availabilityData.overrides ?? [])
    }
  }, [availabilityData])

  // Save weekly schedule mutation
  const saveWeeklyMutation = $api.useMutation('put', '/api/v1/users/me/host-profile/availability')

  // Add override mutation
  const addOverrideMutation = $api.useMutation('post', '/api/v1/users/me/host-profile/availability/overrides')

  // Delete override mutation
  const deleteOverrideMutation = $api.useMutation('delete', '/api/v1/users/me/host-profile/availability/overrides/{override_id}')

  // Add a time slot to a day
  const handleAddSlot = useCallback((dayOfWeek: DayOfWeek) => {
    setWeeklySlots((prev) => [
      ...prev,
      { dayOfWeek, startTime: '09:00', endTime: '17:00' },
    ])
    setIsEditingWeekly(true)
  }, [])

  // Remove a time slot
  const handleRemoveSlot = useCallback((index: number) => {
    setWeeklySlots((prev) => prev.filter((_, i) => i !== index))
    setIsEditingWeekly(true)
  }, [])

  // Update a time slot
  const handleUpdateSlot = useCallback((index: number, field: 'startTime' | 'endTime', value: string) => {
    setWeeklySlots((prev) => {
      const updated = [...prev]
      const existing = updated[index]
      if (existing) {
        updated[index] = {
          dayOfWeek: existing.dayOfWeek,
          startTime: field === 'startTime' ? value : existing.startTime,
          endTime: field === 'endTime' ? value : existing.endTime,
          id: existing.id,
          isActive: existing.isActive,
        }
      }
      return updated
    })
    setIsEditingWeekly(true)
  }, [])

  // Save weekly schedule
  const handleSaveWeekly = async () => {
    setIsSaving(true)
    setSaveError(null)
    setSaveSuccess(false)

    try {
      // Build the recurring array from weekly slots
      const recurring = weeklySlots.map((slot) => ({
        day_of_week: slot.dayOfWeek,
        start_time: slot.startTime,
        end_time: slot.endTime,
      }))

      await saveWeeklyMutation.mutateAsync({
        body: { recurring },
      })

      setIsEditingWeekly(false)
      setSaveSuccess(true)
      await refetch()

      // Auto-hide success message
      setTimeout(() => setSaveSuccess(false), 3000)
    } catch (error) {
      if (error instanceof Error) {
        setSaveError(error.message)
      } else {
        setSaveError('Failed to save availability. Please try again.')
      }
    } finally {
      setIsSaving(false)
    }
  }

  // Cancel weekly changes
  const handleCancelWeekly = useCallback(() => {
    // Reset to original data
    if (availabilityData) {
      const slots: WeeklySlot[] = (availabilityData.recurring ?? []).map((rec: RecurringAvailabilityResponse) => ({
        dayOfWeek: rec.day_of_week,
        startTime: rec.start_time,
        endTime: rec.end_time,
        id: rec.id,
        isActive: rec.is_active,
      }))
      setWeeklySlots(slots)
    }
    setIsEditingWeekly(false)
    setSaveError(null)
  }, [availabilityData])

  // Add an override
  const handleAddOverride = async () => {
    if (!newOverrideDate) {
      setSaveError('Please select a date')
      return
    }

    setIsSaving(true)
    setSaveError(null)

    try {
      await addOverrideMutation.mutateAsync({
        body: {
          override_date: newOverrideDate,
          override_type: newOverrideType,
          start_time: newOverrideAllDay ? null : newOverrideStartTime,
          end_time: newOverrideAllDay ? null : newOverrideEndTime,
          all_day: newOverrideAllDay,
          reason: newOverrideReason || null,
        },
      })

      // Reset form
      setShowAddOverride(false)
      setNewOverrideDate('')
      setNewOverrideType('blocked')
      setNewOverrideStartTime('09:00')
      setNewOverrideEndTime('17:00')
      setNewOverrideAllDay(false)
      setNewOverrideReason('')

      setSaveSuccess(true)
      await refetch()

      // Auto-hide success message
      setTimeout(() => setSaveSuccess(false), 3000)
    } catch (error) {
      if (error instanceof Error) {
        setSaveError(error.message)
      } else {
        setSaveError('Failed to add override. Please try again.')
      }
    } finally {
      setIsSaving(false)
    }
  }

  // Delete an override
  const handleDeleteOverride = async (overrideId: string) => {
    setIsSaving(true)
    setSaveError(null)

    try {
      await deleteOverrideMutation.mutateAsync({
        params: { path: { override_id: overrideId } },
      })

      setSaveSuccess(true)
      await refetch()

      // Auto-hide success message
      setTimeout(() => setSaveSuccess(false), 3000)
    } catch (error) {
      if (error instanceof Error) {
        setSaveError(error.message)
      } else {
        setSaveError('Failed to delete override. Please try again.')
      }
    } finally {
      setIsSaving(false)
    }
  }

  // Get slots for a specific day
  const getSlotsForDay = (dayOfWeek: DayOfWeek) => {
    return weeklySlots
      .map((slot, index) => ({ ...slot, originalIndex: index }))
      .filter((slot) => slot.dayOfWeek === dayOfWeek)
  }

  // Filter overrides by type
  const availableOverrides = overrides.filter((o) => o.override_type === 'available')
  const blockedOverrides = overrides.filter((o) => o.override_type === 'blocked')

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
          <p style={styles.authText}>Please log in to manage your availability.</p>
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
          <p style={styles.authText}>You need to become a host to manage availability.</p>
          <Link to="/" style={styles.becomeHostButton}>
            Become a Host
          </Link>
        </div>
      </div>
    )
  }

  // Loading availability
  if (availabilityLoading) {
    return (
      <div style={styles.loadingContainer}>
        <div style={styles.spinner} />
        <p style={styles.loadingText}>Loading availability...</p>
      </div>
    )
  }

  // Error loading
  if (availabilityError) {
    return (
      <div style={styles.container}>
        <div style={styles.errorContainer}>
          <p style={styles.errorText}>Failed to load availability. Please try again.</p>
          <button onClick={() => refetch()} style={styles.retryButton}>
            Retry
          </button>
        </div>
      </div>
    )
  }

  return (
    <div style={styles.container}>
      {/* Header */}
      <div style={styles.header}>
        <Link to="/host/dashboard" style={styles.backLink}>
          &larr; Back to Dashboard
        </Link>
        <h1 style={styles.title}>Manage Availability</h1>
        <p style={styles.subtitle}>
          Set your weekly schedule and manage one-time exceptions
        </p>
      </div>

      {/* Success Message */}
      {saveSuccess && (
        <div style={styles.successBanner}>
          Changes saved successfully!
        </div>
      )}

      {/* Error Message */}
      {saveError && (
        <div style={styles.errorBanner}>
          {saveError}
          <button onClick={() => setSaveError(null)} style={styles.dismissButton}>
            &times;
          </button>
        </div>
      )}

      {/* Tabs */}
      <div style={styles.tabs}>
        <button
          onClick={() => setActiveTab('weekly')}
          style={{
            ...styles.tab,
            ...(activeTab === 'weekly' ? styles.activeTab : {}),
          }}
        >
          Weekly Schedule
        </button>
        <button
          onClick={() => setActiveTab('overrides')}
          style={{
            ...styles.tab,
            ...(activeTab === 'overrides' ? styles.activeTab : {}),
          }}
        >
          One-Time Slots
          {availableOverrides.length > 0 && (
            <span style={styles.tabBadge}>{availableOverrides.length}</span>
          )}
        </button>
        <button
          onClick={() => setActiveTab('blocked')}
          style={{
            ...styles.tab,
            ...(activeTab === 'blocked' ? styles.activeTab : {}),
          }}
        >
          Blocked Dates
          {blockedOverrides.length > 0 && (
            <span style={styles.tabBadge}>{blockedOverrides.length}</span>
          )}
        </button>
      </div>

      {/* Weekly Schedule Tab */}
      {activeTab === 'weekly' && (
        <section style={styles.section}>
          <div style={styles.sectionHeader}>
            <h2 style={styles.sectionTitle}>Weekly Schedule</h2>
            {isEditingWeekly && (
              <div style={styles.editActions}>
                <button onClick={handleCancelWeekly} style={styles.cancelButton}>
                  Cancel
                </button>
                <button
                  onClick={handleSaveWeekly}
                  style={styles.saveButton}
                  disabled={isSaving}
                >
                  {isSaving ? 'Saving...' : 'Save Changes'}
                </button>
              </div>
            )}
          </div>

          <p style={styles.sectionDescription}>
            Set your regular weekly hours. Clients will see these times when booking.
          </p>

          <div style={styles.weeklySchedule}>
            {DAYS_OF_WEEK.map((day) => {
              const daySlots = getSlotsForDay(day.value)
              return (
                <div key={day.value} style={styles.dayRow}>
                  <div style={styles.dayLabel}>
                    <span style={styles.dayName}>{day.label}</span>
                    <span style={styles.dayShort}>{day.short}</span>
                  </div>
                  <div style={styles.daySlots}>
                    {daySlots.length === 0 ? (
                      <span style={styles.noSlots}>Not available</span>
                    ) : (
                      daySlots.map((slot) => (
                        <div key={slot.originalIndex} style={styles.timeSlot}>
                          <select
                            value={slot.startTime}
                            onChange={(e) => handleUpdateSlot(slot.originalIndex, 'startTime', e.target.value)}
                            style={styles.timeSelect}
                          >
                            {TIME_SLOTS.map((time) => (
                              <option key={time} value={time}>
                                {formatTime(time)}
                              </option>
                            ))}
                          </select>
                          <span style={styles.timeSeparator}>to</span>
                          <select
                            value={slot.endTime}
                            onChange={(e) => handleUpdateSlot(slot.originalIndex, 'endTime', e.target.value)}
                            style={styles.timeSelect}
                          >
                            {TIME_SLOTS.map((time) => (
                              <option key={time} value={time}>
                                {formatTime(time)}
                              </option>
                            ))}
                          </select>
                          <button
                            onClick={() => handleRemoveSlot(slot.originalIndex)}
                            style={styles.removeSlotButton}
                            title="Remove time slot"
                          >
                            &times;
                          </button>
                        </div>
                      ))
                    )}
                    <button
                      onClick={() => handleAddSlot(day.value)}
                      style={styles.addSlotButton}
                    >
                      + Add slot
                    </button>
                  </div>
                </div>
              )
            })}
          </div>

          {/* Quick Templates */}
          <div style={styles.templates}>
            <span style={styles.templatesLabel}>Quick templates:</span>
            <button
              onClick={() => {
                // Weekdays 9-5
                const slots: WeeklySlot[] = [0, 1, 2, 3, 4].map((day) => ({
                  dayOfWeek: day as DayOfWeek,
                  startTime: '09:00',
                  endTime: '17:00',
                }))
                setWeeklySlots(slots)
                setIsEditingWeekly(true)
              }}
              style={styles.templateButton}
            >
              Weekdays 9-5
            </button>
            <button
              onClick={() => {
                // All week 10-8
                const slots: WeeklySlot[] = [0, 1, 2, 3, 4, 5, 6].map((day) => ({
                  dayOfWeek: day as DayOfWeek,
                  startTime: '10:00',
                  endTime: '20:00',
                }))
                setWeeklySlots(slots)
                setIsEditingWeekly(true)
              }}
              style={styles.templateButton}
            >
              Every day 10-8
            </button>
            <button
              onClick={() => {
                // Weekends only
                const slots: WeeklySlot[] = [5, 6].map((day) => ({
                  dayOfWeek: day as DayOfWeek,
                  startTime: '10:00',
                  endTime: '18:00',
                }))
                setWeeklySlots(slots)
                setIsEditingWeekly(true)
              }}
              style={styles.templateButton}
            >
              Weekends only
            </button>
            <button
              onClick={() => {
                setWeeklySlots([])
                setIsEditingWeekly(true)
              }}
              style={styles.templateButton}
            >
              Clear all
            </button>
          </div>
        </section>
      )}

      {/* One-Time Slots Tab */}
      {activeTab === 'overrides' && (
        <section style={styles.section}>
          <div style={styles.sectionHeader}>
            <h2 style={styles.sectionTitle}>One-Time Available Slots</h2>
            <button
              onClick={() => {
                setNewOverrideType('available')
                setShowAddOverride(true)
              }}
              style={styles.addButton}
            >
              + Add Slot
            </button>
          </div>

          <p style={styles.sectionDescription}>
            Add availability for specific dates outside your regular schedule.
          </p>

          {availableOverrides.length === 0 ? (
            <div style={styles.emptyState}>
              <p style={styles.emptyText}>No one-time slots added</p>
              <p style={styles.emptySubtext}>
                Add extra availability for specific dates
              </p>
            </div>
          ) : (
            <div style={styles.overridesList}>
              {availableOverrides.map((override) => (
                <div key={override.id} style={styles.overrideCard}>
                  <div style={styles.overrideInfo}>
                    <span style={styles.overrideDate}>{formatDate(override.override_date)}</span>
                    <span style={styles.overrideTime}>
                      {override.all_day
                        ? 'All day'
                        : `${formatTime(override.start_time ?? '09:00')} - ${formatTime(override.end_time ?? '17:00')}`}
                    </span>
                    {override.reason && (
                      <span style={styles.overrideReason}>{override.reason}</span>
                    )}
                  </div>
                  <button
                    onClick={() => handleDeleteOverride(override.id)}
                    style={styles.deleteOverrideButton}
                    disabled={isSaving}
                  >
                    Remove
                  </button>
                </div>
              ))}
            </div>
          )}
        </section>
      )}

      {/* Blocked Dates Tab */}
      {activeTab === 'blocked' && (
        <section style={styles.section}>
          <div style={styles.sectionHeader}>
            <h2 style={styles.sectionTitle}>Blocked Dates</h2>
            <button
              onClick={() => {
                setNewOverrideType('blocked')
                setShowAddOverride(true)
              }}
              style={styles.addButton}
            >
              + Block Time
            </button>
          </div>

          <p style={styles.sectionDescription}>
            Block dates when you&apos;re unavailable (vacation, appointments, etc.).
          </p>

          {blockedOverrides.length === 0 ? (
            <div style={styles.emptyState}>
              <p style={styles.emptyText}>No blocked dates</p>
              <p style={styles.emptySubtext}>
                Block dates when you&apos;re not available
              </p>
            </div>
          ) : (
            <div style={styles.overridesList}>
              {blockedOverrides.map((override) => (
                <div key={override.id} style={{ ...styles.overrideCard, ...styles.blockedCard }}>
                  <div style={styles.overrideInfo}>
                    <span style={styles.overrideDate}>{formatDate(override.override_date)}</span>
                    <span style={styles.overrideTime}>
                      {override.all_day
                        ? 'All day'
                        : `${formatTime(override.start_time ?? '09:00')} - ${formatTime(override.end_time ?? '17:00')}`}
                    </span>
                    {override.reason && (
                      <span style={styles.overrideReason}>{override.reason}</span>
                    )}
                  </div>
                  <button
                    onClick={() => handleDeleteOverride(override.id)}
                    style={styles.deleteOverrideButton}
                    disabled={isSaving}
                  >
                    Remove
                  </button>
                </div>
              ))}
            </div>
          )}

          {/* Simple Calendar View for Blocked Dates */}
          <div style={styles.calendarSection}>
            <h3 style={styles.calendarTitle}>Calendar View</h3>
            <div style={styles.calendarGrid}>
              {blockedOverrides.slice(0, 7).map((override) => {
                const date = new Date(override.override_date + 'T00:00:00')
                return (
                  <div key={override.id} style={styles.calendarDay}>
                    <span style={styles.calendarDayName}>
                      {date.toLocaleDateString('en-US', { weekday: 'short' })}
                    </span>
                    <span style={styles.calendarDayNumber}>
                      {date.getDate()}
                    </span>
                    <span style={styles.calendarDayMonth}>
                      {date.toLocaleDateString('en-US', { month: 'short' })}
                    </span>
                  </div>
                )
              })}
              {blockedOverrides.length > 7 && (
                <div style={styles.calendarMore}>
                  +{blockedOverrides.length - 7} more
                </div>
              )}
            </div>
          </div>
        </section>
      )}

      {/* Add Override Modal */}
      {showAddOverride && (
        <div style={styles.modal}>
          <div style={styles.modalContent}>
            <h3 style={styles.modalTitle}>
              {newOverrideType === 'available' ? 'Add Available Slot' : 'Block Time'}
            </h3>

            <div style={styles.formGroup}>
              <label style={styles.label}>Date</label>
              <input
                type="date"
                value={newOverrideDate}
                onChange={(e) => setNewOverrideDate(e.target.value)}
                min={new Date().toISOString().split('T')[0]}
                style={styles.input}
              />
            </div>

            <div style={styles.formGroup}>
              <label style={styles.checkboxLabel}>
                <input
                  type="checkbox"
                  checked={newOverrideAllDay}
                  onChange={(e) => setNewOverrideAllDay(e.target.checked)}
                  style={styles.checkbox}
                />
                All day
              </label>
            </div>

            {!newOverrideAllDay && (
              <div style={styles.timeRow}>
                <div style={styles.formGroup}>
                  <label style={styles.label}>Start Time</label>
                  <select
                    value={newOverrideStartTime}
                    onChange={(e) => setNewOverrideStartTime(e.target.value)}
                    style={styles.select}
                  >
                    {TIME_SLOTS.map((time) => (
                      <option key={time} value={time}>
                        {formatTime(time)}
                      </option>
                    ))}
                  </select>
                </div>
                <div style={styles.formGroup}>
                  <label style={styles.label}>End Time</label>
                  <select
                    value={newOverrideEndTime}
                    onChange={(e) => setNewOverrideEndTime(e.target.value)}
                    style={styles.select}
                  >
                    {TIME_SLOTS.map((time) => (
                      <option key={time} value={time}>
                        {formatTime(time)}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            )}

            <div style={styles.formGroup}>
              <label style={styles.label}>
                Reason <span style={styles.optional}>(optional)</span>
              </label>
              <input
                type="text"
                value={newOverrideReason}
                onChange={(e) => setNewOverrideReason(e.target.value)}
                placeholder={newOverrideType === 'blocked' ? 'e.g., Vacation, Doctor appointment' : 'e.g., Special event'}
                maxLength={500}
                style={styles.input}
              />
            </div>

            <div style={styles.modalActions}>
              <button
                onClick={() => {
                  setShowAddOverride(false)
                  setSaveError(null)
                }}
                style={styles.cancelButton}
              >
                Cancel
              </button>
              <button
                onClick={handleAddOverride}
                style={styles.primaryButton}
                disabled={isSaving || !newOverrideDate}
              >
                {isSaving ? 'Adding...' : newOverrideType === 'available' ? 'Add Slot' : 'Block Time'}
              </button>
            </div>
          </div>
        </div>
      )}
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
    padding: '2rem',
    textAlign: 'center',
    backgroundColor: '#fef2f2',
    borderRadius: '12px',
    marginTop: '2rem',
  },
  errorText: {
    color: '#dc2626',
    margin: 0,
    marginBottom: '1rem',
  },
  retryButton: {
    padding: '0.5rem 1rem',
    backgroundColor: '#e11d48',
    color: 'white',
    border: 'none',
    borderRadius: '8px',
    cursor: 'pointer',
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
  backLink: {
    color: '#6b7280',
    textDecoration: 'none',
    fontSize: '0.875rem',
    display: 'inline-block',
    marginBottom: '0.5rem',
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
    fontSize: '0.9375rem',
  },
  successBanner: {
    padding: '1rem',
    backgroundColor: '#d1fae5',
    color: '#065f46',
    borderRadius: '8px',
    marginBottom: '1rem',
    textAlign: 'center',
    fontWeight: 500,
  },
  errorBanner: {
    padding: '1rem',
    backgroundColor: '#fee2e2',
    color: '#991b1b',
    borderRadius: '8px',
    marginBottom: '1rem',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  dismissButton: {
    background: 'none',
    border: 'none',
    color: '#991b1b',
    fontSize: '1.25rem',
    cursor: 'pointer',
    padding: '0 0.5rem',
  },
  tabs: {
    display: 'flex',
    gap: '0.5rem',
    marginBottom: '1.5rem',
    overflowX: 'auto',
    paddingBottom: '0.25rem',
  },
  tab: {
    padding: '0.75rem 1rem',
    backgroundColor: 'white',
    border: '1px solid #e5e7eb',
    borderRadius: '8px',
    fontSize: '0.875rem',
    fontWeight: 500,
    color: '#6b7280',
    cursor: 'pointer',
    whiteSpace: 'nowrap',
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
    transition: 'all 0.2s',
  },
  activeTab: {
    backgroundColor: '#e11d48',
    borderColor: '#e11d48',
    color: 'white',
  },
  tabBadge: {
    padding: '0.125rem 0.375rem',
    backgroundColor: 'rgba(255,255,255,0.2)',
    borderRadius: '4px',
    fontSize: '0.75rem',
  },
  section: {
    backgroundColor: 'white',
    borderRadius: '12px',
    boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
    padding: '1.5rem',
    marginBottom: '1.5rem',
  },
  sectionHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '0.5rem',
    flexWrap: 'wrap',
    gap: '0.5rem',
  },
  sectionTitle: {
    fontSize: '1.125rem',
    fontWeight: 600,
    color: '#1f2937',
    margin: 0,
  },
  sectionDescription: {
    color: '#6b7280',
    marginTop: 0,
    marginBottom: '1.5rem',
    fontSize: '0.875rem',
  },
  editActions: {
    display: 'flex',
    gap: '0.5rem',
  },
  addButton: {
    padding: '0.5rem 1rem',
    backgroundColor: '#e11d48',
    color: 'white',
    border: 'none',
    borderRadius: '8px',
    fontSize: '0.875rem',
    fontWeight: 500,
    cursor: 'pointer',
  },
  weeklySchedule: {
    display: 'flex',
    flexDirection: 'column',
    gap: '0.75rem',
  },
  dayRow: {
    display: 'flex',
    gap: '1rem',
    padding: '0.75rem',
    backgroundColor: '#f9fafb',
    borderRadius: '8px',
    alignItems: 'flex-start',
  },
  dayLabel: {
    width: '100px',
    flexShrink: 0,
  },
  dayName: {
    display: 'block',
    fontWeight: 600,
    color: '#1f2937',
    fontSize: '0.9375rem',
  },
  dayShort: {
    display: 'none',
    color: '#6b7280',
    fontSize: '0.875rem',
  },
  daySlots: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    gap: '0.5rem',
  },
  noSlots: {
    color: '#9ca3af',
    fontSize: '0.875rem',
    fontStyle: 'italic',
  },
  timeSlot: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
    flexWrap: 'wrap',
  },
  timeSelect: {
    padding: '0.5rem',
    border: '1px solid #d1d5db',
    borderRadius: '6px',
    fontSize: '0.875rem',
    backgroundColor: 'white',
  },
  timeSeparator: {
    color: '#6b7280',
    fontSize: '0.875rem',
  },
  removeSlotButton: {
    width: '24px',
    height: '24px',
    backgroundColor: '#fee2e2',
    color: '#991b1b',
    border: 'none',
    borderRadius: '50%',
    fontSize: '1rem',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  addSlotButton: {
    alignSelf: 'flex-start',
    padding: '0.25rem 0.5rem',
    backgroundColor: 'transparent',
    color: '#e11d48',
    border: '1px dashed #e11d48',
    borderRadius: '4px',
    fontSize: '0.75rem',
    cursor: 'pointer',
  },
  templates: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '0.5rem',
    alignItems: 'center',
    marginTop: '1.5rem',
    paddingTop: '1.5rem',
    borderTop: '1px solid #e5e7eb',
  },
  templatesLabel: {
    color: '#6b7280',
    fontSize: '0.875rem',
    marginRight: '0.5rem',
  },
  templateButton: {
    padding: '0.375rem 0.75rem',
    backgroundColor: '#f3f4f6',
    color: '#374151',
    border: '1px solid #e5e7eb',
    borderRadius: '6px',
    fontSize: '0.8125rem',
    cursor: 'pointer',
  },
  emptyState: {
    textAlign: 'center',
    padding: '2rem',
    backgroundColor: '#f9fafb',
    borderRadius: '8px',
  },
  emptyText: {
    color: '#6b7280',
    margin: 0,
    fontWeight: 500,
  },
  emptySubtext: {
    color: '#9ca3af',
    margin: 0,
    marginTop: '0.25rem',
    fontSize: '0.875rem',
  },
  overridesList: {
    display: 'flex',
    flexDirection: 'column',
    gap: '0.75rem',
  },
  overrideCard: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '1rem',
    backgroundColor: '#f0fdf4',
    borderRadius: '8px',
    border: '1px solid #86efac',
    gap: '1rem',
    flexWrap: 'wrap',
  },
  blockedCard: {
    backgroundColor: '#fef2f2',
    borderColor: '#fecaca',
  },
  overrideInfo: {
    display: 'flex',
    flexDirection: 'column',
    gap: '0.25rem',
  },
  overrideDate: {
    fontWeight: 600,
    color: '#1f2937',
    fontSize: '0.9375rem',
  },
  overrideTime: {
    color: '#6b7280',
    fontSize: '0.8125rem',
  },
  overrideReason: {
    color: '#9ca3af',
    fontSize: '0.75rem',
    fontStyle: 'italic',
  },
  deleteOverrideButton: {
    padding: '0.5rem 1rem',
    backgroundColor: 'white',
    color: '#dc2626',
    border: '1px solid #fecaca',
    borderRadius: '6px',
    fontSize: '0.8125rem',
    cursor: 'pointer',
  },
  calendarSection: {
    marginTop: '1.5rem',
    paddingTop: '1.5rem',
    borderTop: '1px solid #e5e7eb',
  },
  calendarTitle: {
    fontSize: '1rem',
    fontWeight: 600,
    color: '#1f2937',
    margin: 0,
    marginBottom: '1rem',
  },
  calendarGrid: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '0.75rem',
  },
  calendarDay: {
    width: '60px',
    padding: '0.75rem',
    backgroundColor: '#fef2f2',
    borderRadius: '8px',
    textAlign: 'center',
    border: '1px solid #fecaca',
  },
  calendarDayName: {
    display: 'block',
    fontSize: '0.625rem',
    color: '#6b7280',
    textTransform: 'uppercase',
  },
  calendarDayNumber: {
    display: 'block',
    fontSize: '1.25rem',
    fontWeight: 700,
    color: '#dc2626',
  },
  calendarDayMonth: {
    display: 'block',
    fontSize: '0.625rem',
    color: '#6b7280',
  },
  calendarMore: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '0.75rem',
    backgroundColor: '#f3f4f6',
    borderRadius: '8px',
    fontSize: '0.875rem',
    color: '#6b7280',
  },
  modal: {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0,0,0,0.5)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 1000,
    padding: '1rem',
  },
  modalContent: {
    backgroundColor: 'white',
    borderRadius: '12px',
    padding: '1.5rem',
    maxWidth: '450px',
    width: '100%',
    maxHeight: '80vh',
    overflow: 'auto',
  },
  modalTitle: {
    fontSize: '1.25rem',
    fontWeight: 600,
    margin: 0,
    marginBottom: '1.5rem',
  },
  modalActions: {
    display: 'flex',
    gap: '0.75rem',
    justifyContent: 'flex-end',
    marginTop: '1.5rem',
  },
  formGroup: {
    marginBottom: '1rem',
  },
  label: {
    display: 'block',
    fontWeight: 500,
    color: '#374151',
    marginBottom: '0.5rem',
    fontSize: '0.875rem',
  },
  optional: {
    fontWeight: 400,
    color: '#9ca3af',
  },
  input: {
    width: '100%',
    padding: '0.75rem',
    border: '1px solid #d1d5db',
    borderRadius: '8px',
    fontSize: '1rem',
    boxSizing: 'border-box',
  },
  select: {
    width: '100%',
    padding: '0.75rem',
    border: '1px solid #d1d5db',
    borderRadius: '8px',
    fontSize: '1rem',
    backgroundColor: 'white',
  },
  timeRow: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: '1rem',
  },
  checkboxLabel: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
    fontSize: '0.9375rem',
    color: '#374151',
    cursor: 'pointer',
  },
  checkbox: {
    width: '18px',
    height: '18px',
    cursor: 'pointer',
  },
  cancelButton: {
    padding: '0.75rem 1.5rem',
    backgroundColor: '#f3f4f6',
    color: '#374151',
    border: '1px solid #d1d5db',
    borderRadius: '8px',
    fontSize: '0.875rem',
    fontWeight: 500,
    cursor: 'pointer',
  },
  saveButton: {
    padding: '0.75rem 1.5rem',
    backgroundColor: '#e11d48',
    color: 'white',
    border: 'none',
    borderRadius: '8px',
    fontSize: '0.875rem',
    fontWeight: 500,
    cursor: 'pointer',
  },
  primaryButton: {
    padding: '0.75rem 1.5rem',
    backgroundColor: '#e11d48',
    color: 'white',
    border: 'none',
    borderRadius: '8px',
    fontSize: '0.875rem',
    fontWeight: 500,
    cursor: 'pointer',
  },
}
