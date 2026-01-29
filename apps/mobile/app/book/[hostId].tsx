import { useState, useEffect, useCallback, useMemo } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  TextInput,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useLocalSearchParams, Stack, router } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { apiClient, ApiError } from '@/lib/api/client';
import { useAuthStore } from '@/stores/auth';
import type { components } from '@/types/api.gen';

type HostProfileWithUserResponse = components['schemas']['HostProfileWithUserResponse'];
type AvailabilityForDateRangeResponse = components['schemas']['AvailabilityForDateRangeResponse'];
type AvailabilityForDateResponse = components['schemas']['AvailabilityForDateResponse'];
type AvailabilitySlot = components['schemas']['AvailabilitySlot'];
type CreateBookingRequest = components['schemas']['CreateBookingRequest'];
type BookingWithDetailsResponse = components['schemas']['BookingWithDetailsResponse'];

// Duration options
const DURATION_OPTIONS = [
  { value: 30, label: '30 min' },
  { value: 60, label: '1 hour' },
  { value: 90, label: '1.5 hrs' },
  { value: 120, label: '2 hours' },
  { value: 180, label: '3 hours' },
  { value: 240, label: '4 hours' },
];

export default function BookingFlowScreen() {
  const { hostId } = useLocalSearchParams<{ hostId: string }>();
  const { isAuthenticated } = useAuthStore();

  // State
  const [host, setHost] = useState<HostProfileWithUserResponse | null>(null);
  const [availability, setAvailability] = useState<AvailabilityForDateRangeResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [availabilityLoading, setAvailabilityLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Booking state
  const [selectedDate, setSelectedDate] = useState<string | null>(null);
  const [selectedTime, setSelectedTime] = useState<string | null>(null);
  const [durationMinutes, setDurationMinutes] = useState(60);
  const [clientNotes, setClientNotes] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [bookingError, setBookingError] = useState<string | null>(null);

  // Calculate date range (today + 30 days)
  const today = useMemo(() => new Date(), []);
  const startDateStr = useMemo(
    () => today.toISOString().split('T')[0] ?? '',
    [today]
  );
  const endDateStr = useMemo(() => {
    const endDate = new Date(today.getTime() + 30 * 24 * 60 * 60 * 1000);
    return endDate.toISOString().split('T')[0] ?? '';
  }, [today]);

  // Fetch host profile
  const fetchHost = useCallback(async () => {
    if (!hostId) return;

    try {
      const data = await apiClient.get<HostProfileWithUserResponse>(
        `/api/v1/hosts/${hostId}`
      );
      setHost(data);
      setError(null);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.detail);
      } else {
        setError('Failed to load host profile');
      }
    } finally {
      setIsLoading(false);
    }
  }, [hostId]);

  // Fetch availability
  const fetchAvailability = useCallback(async () => {
    if (!hostId) return;

    setAvailabilityLoading(true);
    try {
      const data = await apiClient.get<AvailabilityForDateRangeResponse>(
        `/api/v1/hosts/${hostId}/availability?start_date=${startDateStr}&end_date=${endDateStr}`
      );
      setAvailability(data);
    } catch (err) {
      console.error('Failed to fetch availability:', err);
    } finally {
      setAvailabilityLoading(false);
    }
  }, [hostId, startDateStr, endDateStr]);

  // Initial load
  useEffect(() => {
    fetchHost();
    fetchAvailability();
  }, [fetchHost, fetchAvailability]);

  // Get available dates
  const availableDates = useMemo(() => {
    if (!availability?.availability) return new Set<string>();
    return new Set(
      availability.availability
        .filter(
          (day: AvailabilityForDateResponse) =>
            day.slots && day.slots.length > 0
        )
        .map((day: AvailabilityForDateResponse) => day.availability_date)
    );
  }, [availability]);

  // Get available slots for selected date
  const availableSlots = useMemo(() => {
    if (!selectedDate || !availability?.availability) return [];
    const dayAvailability = availability.availability.find(
      (day: AvailabilityForDateResponse) =>
        day.availability_date === selectedDate
    );
    return dayAvailability?.slots ?? [];
  }, [selectedDate, availability]);

  // Filter slots that can fit the selected duration
  const validTimeSlots = useMemo(() => {
    return availableSlots.filter((slot: AvailabilitySlot) => {
      const startMinutes = timeToMinutes(slot.start_time);
      const endMinutes = timeToMinutes(slot.end_time);
      return endMinutes - startMinutes >= durationMinutes;
    });
  }, [availableSlots, durationMinutes]);

  // Generate calendar days
  const calendarDays = useMemo(() => {
    const days: {
      date: string;
      dayNum: number;
      dayName: string;
      monthName: string;
      isAvailable: boolean;
    }[] = [];
    const currentDate = new Date(today);

    for (let i = 0; i < 30; i++) {
      const dateStr = currentDate.toISOString().split('T')[0] ?? '';
      days.push({
        date: dateStr,
        dayNum: currentDate.getDate(),
        dayName: currentDate.toLocaleDateString('en-US', { weekday: 'short' }),
        monthName: currentDate.toLocaleDateString('en-US', { month: 'short' }),
        isAvailable: availableDates.has(dateStr),
      });
      currentDate.setDate(currentDate.getDate() + 1);
    }
    return days;
  }, [today, availableDates]);

  // Calculate price breakdown
  const priceBreakdown = useMemo(() => {
    if (!host) return null;
    const hourlyRate = host.hourly_rate_cents;
    const subtotal = Math.round((hourlyRate * durationMinutes) / 60);
    const platformFee = Math.round(subtotal * 0.15); // 15% platform fee
    const total = subtotal + platformFee;
    return { hourlyRate, subtotal, platformFee, total };
  }, [host, durationMinutes]);

  // Helper functions
  const formatPrice = (cents: number) => `$${(cents / 100).toFixed(2)}`;

  const formatTime = (timeStr: string) => {
    const [hours, minutes] = timeStr.split(':').map(Number);
    if (hours === undefined || minutes === undefined) return timeStr;
    const period = hours >= 12 ? 'PM' : 'AM';
    const displayHours = hours % 12 || 12;
    return `${displayHours}:${minutes.toString().padStart(2, '0')} ${period}`;
  };

  const timeToMinutes = (timeStr: string) => {
    const [hours, minutes] = timeStr.split(':').map(Number);
    return (hours ?? 0) * 60 + (minutes ?? 0);
  };

  const handleDateSelect = (date: string) => {
    setSelectedDate(date);
    setSelectedTime(null);
  };

  const handleDurationSelect = (duration: number) => {
    setDurationMinutes(duration);
    setSelectedTime(null);
  };

  // Generate time options within a slot
  const getTimeOptions = (slot: AvailabilitySlot) => {
    const startMinutes = timeToMinutes(slot.start_time);
    const endMinutes = timeToMinutes(slot.end_time);
    const times: string[] = [];

    for (let t = startMinutes; t + durationMinutes <= endMinutes; t += 30) {
      const hours = Math.floor(t / 60);
      const mins = t % 60;
      times.push(
        `${hours.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}`
      );
    }
    return times;
  };

  // Handle booking submission
  const handleBookNow = useCallback(async () => {
    if (!selectedDate || !selectedTime || !hostId) return;

    setIsSubmitting(true);
    setBookingError(null);

    try {
      const scheduledStart = `${selectedDate}T${selectedTime}:00`;

      const bookingRequest: CreateBookingRequest = {
        host_id: hostId,
        scheduled_start: scheduledStart,
        duration_minutes: durationMinutes,
        client_notes: clientNotes || null,
      };

      await apiClient.post<BookingWithDetailsResponse>(
        '/api/v1/bookings',
        bookingRequest
      );

      // Show success alert and navigate
      Alert.alert(
        'Booking Requested!',
        'Your booking has been submitted. The host will review and confirm your request.',
        [
          {
            text: 'View Bookings',
            onPress: () => router.replace('/(tabs)/bookings'),
          },
          {
            text: 'OK',
            onPress: () => router.back(),
          },
        ]
      );
    } catch (err) {
      if (err instanceof ApiError) {
        setBookingError(err.detail);
      } else {
        setBookingError('Failed to create booking. Please try again.');
      }
    } finally {
      setIsSubmitting(false);
    }
  }, [selectedDate, selectedTime, hostId, durationMinutes, clientNotes]);

  // Loading state
  if (isLoading) {
    return (
      <>
        <Stack.Screen
          options={{
            headerShown: true,
            title: 'Book Session',
            headerBackTitle: 'Back',
          }}
        />
        <SafeAreaView style={styles.container} edges={['bottom']}>
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color="#e11d48" />
            <Text style={styles.loadingText}>Loading...</Text>
          </View>
        </SafeAreaView>
      </>
    );
  }

  // Error state
  if (error || !host) {
    return (
      <>
        <Stack.Screen
          options={{
            headerShown: true,
            title: 'Book Session',
            headerBackTitle: 'Back',
          }}
        />
        <SafeAreaView style={styles.container} edges={['bottom']}>
          <View style={styles.errorContainer}>
            <Ionicons name="alert-circle-outline" size={64} color="#9ca3af" />
            <Text style={styles.errorTitle}>Host Not Found</Text>
            <Text style={styles.errorText}>
              {error ?? "The host you're trying to book doesn't exist."}
            </Text>
            <TouchableOpacity
              style={styles.retryButton}
              onPress={() => router.back()}
            >
              <Text style={styles.retryButtonText}>Go Back</Text>
            </TouchableOpacity>
          </View>
        </SafeAreaView>
      </>
    );
  }

  // Auth required state
  if (!isAuthenticated) {
    return (
      <>
        <Stack.Screen
          options={{
            headerShown: true,
            title: 'Book Session',
            headerBackTitle: 'Back',
          }}
        />
        <SafeAreaView style={styles.container} edges={['bottom']}>
          <View style={styles.authRequired}>
            <Ionicons name="lock-closed-outline" size={64} color="#9ca3af" />
            <Text style={styles.authTitle}>Login Required</Text>
            <Text style={styles.authText}>
              Please log in to book a session with {host.first_name}.
            </Text>
            <TouchableOpacity
              style={styles.loginButton}
              onPress={() => router.push('/(auth)/login')}
            >
              <Text style={styles.loginButtonText}>Log In</Text>
            </TouchableOpacity>
          </View>
        </SafeAreaView>
      </>
    );
  }

  return (
    <>
      <Stack.Screen
        options={{
          headerShown: true,
          title: `Book ${host.first_name}`,
          headerBackTitle: 'Back',
        }}
      />
      <SafeAreaView style={styles.container} edges={['bottom']}>
        <ScrollView
          style={styles.scrollView}
          contentContainerStyle={styles.scrollContent}
        >
          {/* Host Summary */}
          <View style={styles.hostSummary}>
            <View style={styles.hostAvatar}>
              <Text style={styles.hostAvatarText}>
                {host.first_name.charAt(0)}
                {host.last_name.charAt(0)}
              </Text>
            </View>
            <View style={styles.hostInfo}>
              <Text style={styles.hostName}>
                {host.first_name} {host.last_name}
              </Text>
              <Text style={styles.hostRate}>
                {formatPrice(host.hourly_rate_cents)} / hour
              </Text>
            </View>
          </View>

          {/* Duration Selection */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Select Duration</Text>
            <ScrollView
              horizontal
              showsHorizontalScrollIndicator={false}
              contentContainerStyle={styles.durationScroll}
            >
              {DURATION_OPTIONS.map((option) => (
                <TouchableOpacity
                  key={option.value}
                  style={[
                    styles.durationButton,
                    durationMinutes === option.value &&
                      styles.durationButtonActive,
                  ]}
                  onPress={() => handleDurationSelect(option.value)}
                >
                  <Text
                    style={[
                      styles.durationButtonText,
                      durationMinutes === option.value &&
                        styles.durationButtonTextActive,
                    ]}
                  >
                    {option.label}
                  </Text>
                </TouchableOpacity>
              ))}
            </ScrollView>
          </View>

          {/* Date Selection */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Select Date</Text>
            {availabilityLoading ? (
              <View style={styles.loadingCalendar}>
                <ActivityIndicator size="small" color="#e11d48" />
                <Text style={styles.loadingCalendarText}>
                  Loading availability...
                </Text>
              </View>
            ) : (
              <ScrollView
                horizontal
                showsHorizontalScrollIndicator={false}
                contentContainerStyle={styles.dateScroll}
              >
                {calendarDays.map((day) => (
                  <TouchableOpacity
                    key={day.date}
                    style={[
                      styles.dateCard,
                      day.isAvailable
                        ? styles.dateCardAvailable
                        : styles.dateCardUnavailable,
                      selectedDate === day.date && styles.dateCardSelected,
                    ]}
                    disabled={!day.isAvailable}
                    onPress={() => handleDateSelect(day.date)}
                  >
                    <Text
                      style={[
                        styles.dateDayName,
                        !day.isAvailable && styles.dateDayNameUnavailable,
                        selectedDate === day.date && styles.dateDayNameSelected,
                      ]}
                    >
                      {day.dayName}
                    </Text>
                    <Text
                      style={[
                        styles.dateDayNum,
                        !day.isAvailable && styles.dateDayNumUnavailable,
                        selectedDate === day.date && styles.dateDayNumSelected,
                      ]}
                    >
                      {day.dayNum}
                    </Text>
                    <Text
                      style={[
                        styles.dateMonth,
                        !day.isAvailable && styles.dateMonthUnavailable,
                        selectedDate === day.date && styles.dateMonthSelected,
                      ]}
                    >
                      {day.monthName}
                    </Text>
                  </TouchableOpacity>
                ))}
              </ScrollView>
            )}
          </View>

          {/* Time Selection */}
          {selectedDate && (
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>Select Time</Text>
              {validTimeSlots.length === 0 ? (
                <View style={styles.noSlotsContainer}>
                  <Text style={styles.noSlotsText}>
                    No available time slots for {durationMinutes} minutes on
                    this date.
                  </Text>
                  <Text style={styles.noSlotsSubtext}>
                    Try a shorter duration or different date.
                  </Text>
                </View>
              ) : (
                <View style={styles.timeSlotGrid}>
                  {validTimeSlots.flatMap((slot, slotIndex) =>
                    getTimeOptions(slot).map((time) => (
                      <TouchableOpacity
                        key={`${slotIndex}-${time}`}
                        style={[
                          styles.timeSlotButton,
                          selectedTime === time && styles.timeSlotButtonActive,
                        ]}
                        onPress={() => setSelectedTime(time)}
                      >
                        <Text
                          style={[
                            styles.timeSlotText,
                            selectedTime === time && styles.timeSlotTextActive,
                          ]}
                        >
                          {formatTime(time)}
                        </Text>
                      </TouchableOpacity>
                    ))
                  )}
                </View>
              )}
            </View>
          )}

          {/* Notes */}
          {selectedTime && (
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>Notes (Optional)</Text>
              <TextInput
                style={styles.notesInput}
                placeholder="Add any notes for your host..."
                placeholderTextColor="#9ca3af"
                value={clientNotes}
                onChangeText={setClientNotes}
                multiline
                maxLength={1000}
                textAlignVertical="top"
              />
            </View>
          )}

          {/* Price Breakdown */}
          {priceBreakdown && (
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>Price Breakdown</Text>
              <View style={styles.priceRow}>
                <Text style={styles.priceLabel}>
                  {formatPrice(priceBreakdown.hourlyRate)}/hr ×{' '}
                  {durationMinutes >= 60
                    ? `${durationMinutes / 60} hr${durationMinutes > 60 ? 's' : ''}`
                    : `${durationMinutes} min`}
                </Text>
                <Text style={styles.priceValue}>
                  {formatPrice(priceBreakdown.subtotal)}
                </Text>
              </View>
              <View style={styles.priceRow}>
                <Text style={styles.priceLabel}>Service fee (15%)</Text>
                <Text style={styles.priceValue}>
                  {formatPrice(priceBreakdown.platformFee)}
                </Text>
              </View>
              <View style={styles.priceDivider} />
              <View style={styles.priceRow}>
                <Text style={styles.priceTotalLabel}>Total</Text>
                <Text style={styles.priceTotalValue}>
                  {formatPrice(priceBreakdown.total)}
                </Text>
              </View>
            </View>
          )}

          {/* Booking Summary */}
          {selectedDate && selectedTime && (
            <View style={styles.summaryCard}>
              <Text style={styles.summaryTitle}>Booking Summary</Text>
              <View style={styles.summaryRow}>
                <Ionicons name="calendar-outline" size={18} color="#6b7280" />
                <Text style={styles.summaryText}>
                  {new Date(selectedDate + 'T00:00:00').toLocaleDateString(
                    'en-US',
                    {
                      weekday: 'long',
                      month: 'long',
                      day: 'numeric',
                    }
                  )}
                </Text>
              </View>
              <View style={styles.summaryRow}>
                <Ionicons name="time-outline" size={18} color="#6b7280" />
                <Text style={styles.summaryText}>
                  {formatTime(selectedTime)} •{' '}
                  {durationMinutes >= 60
                    ? `${durationMinutes / 60} hour${durationMinutes > 60 ? 's' : ''}`
                    : `${durationMinutes} minutes`}
                </Text>
              </View>
            </View>
          )}

          {/* Error Message */}
          {bookingError && (
            <View style={styles.errorBox}>
              <Text style={styles.errorBoxText}>{bookingError}</Text>
            </View>
          )}

          {/* Book Button */}
          <TouchableOpacity
            style={[
              styles.bookButton,
              (!selectedDate || !selectedTime || isSubmitting) &&
                styles.bookButtonDisabled,
            ]}
            onPress={handleBookNow}
            disabled={!selectedDate || !selectedTime || isSubmitting}
          >
            {isSubmitting ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <>
                <Ionicons name="calendar-outline" size={20} color="#fff" />
                <Text style={styles.bookButtonText}>Confirm Booking</Text>
              </>
            )}
          </TouchableOpacity>

          <Text style={styles.disclaimer}>
            You won't be charged until the host confirms your booking.
          </Text>

          {/* Note about Stripe - to be implemented */}
          <View style={styles.paymentNote}>
            <Ionicons name="card-outline" size={20} color="#6b7280" />
            <Text style={styles.paymentNoteText}>
              Payment processing will be enabled when the host confirms.
            </Text>
          </View>
        </ScrollView>
      </SafeAreaView>
    </>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f3f4f6',
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    padding: 16,
    paddingBottom: 32,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 12,
    fontSize: 16,
    color: '#6b7280',
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  errorTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#1f2937',
    marginTop: 16,
    marginBottom: 8,
  },
  errorText: {
    fontSize: 14,
    color: '#6b7280',
    textAlign: 'center',
    marginBottom: 24,
  },
  retryButton: {
    paddingVertical: 12,
    paddingHorizontal: 24,
    backgroundColor: '#e11d48',
    borderRadius: 8,
  },
  retryButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
  },
  authRequired: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  authTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#1f2937',
    marginTop: 16,
    marginBottom: 8,
  },
  authText: {
    fontSize: 14,
    color: '#6b7280',
    textAlign: 'center',
    marginBottom: 24,
  },
  loginButton: {
    paddingVertical: 14,
    paddingHorizontal: 32,
    backgroundColor: '#e11d48',
    borderRadius: 8,
  },
  loginButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
  },
  hostSummary: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fff',
    padding: 16,
    borderRadius: 12,
    marginBottom: 16,
  },
  hostAvatar: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: '#e11d48',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 16,
  },
  hostAvatarText: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#fff',
  },
  hostInfo: {
    flex: 1,
  },
  hostName: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1f2937',
  },
  hostRate: {
    fontSize: 14,
    color: '#6b7280',
    marginTop: 2,
  },
  section: {
    backgroundColor: '#fff',
    padding: 16,
    borderRadius: 12,
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1f2937',
    marginBottom: 12,
  },
  durationScroll: {
    paddingRight: 8,
  },
  durationButton: {
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderWidth: 2,
    borderColor: '#e5e7eb',
    borderRadius: 8,
    marginRight: 8,
  },
  durationButtonActive: {
    borderColor: '#e11d48',
    backgroundColor: '#fdf2f4',
  },
  durationButtonText: {
    fontSize: 14,
    fontWeight: '500',
    color: '#4b5563',
  },
  durationButtonTextActive: {
    color: '#e11d48',
  },
  loadingCalendar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
  },
  loadingCalendarText: {
    marginLeft: 8,
    fontSize: 14,
    color: '#6b7280',
  },
  dateScroll: {
    paddingRight: 8,
  },
  dateCard: {
    width: 70,
    paddingVertical: 12,
    borderRadius: 10,
    alignItems: 'center',
    marginRight: 8,
  },
  dateCardAvailable: {
    backgroundColor: '#dcfce7',
  },
  dateCardUnavailable: {
    backgroundColor: '#f3f4f6',
  },
  dateCardSelected: {
    backgroundColor: '#e11d48',
  },
  dateDayName: {
    fontSize: 12,
    color: '#166534',
    marginBottom: 4,
  },
  dateDayNameUnavailable: {
    color: '#9ca3af',
  },
  dateDayNameSelected: {
    color: '#fff',
  },
  dateDayNum: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#166534',
    marginBottom: 2,
  },
  dateDayNumUnavailable: {
    color: '#9ca3af',
  },
  dateDayNumSelected: {
    color: '#fff',
  },
  dateMonth: {
    fontSize: 12,
    color: '#166534',
  },
  dateMonthUnavailable: {
    color: '#9ca3af',
  },
  dateMonthSelected: {
    color: '#fff',
  },
  noSlotsContainer: {
    alignItems: 'center',
    padding: 16,
  },
  noSlotsText: {
    fontSize: 14,
    color: '#6b7280',
    textAlign: 'center',
  },
  noSlotsSubtext: {
    fontSize: 12,
    color: '#9ca3af',
    marginTop: 4,
    textAlign: 'center',
  },
  timeSlotGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  timeSlotButton: {
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderWidth: 2,
    borderColor: '#e5e7eb',
    borderRadius: 8,
  },
  timeSlotButtonActive: {
    borderColor: '#e11d48',
    backgroundColor: '#fdf2f4',
  },
  timeSlotText: {
    fontSize: 14,
    fontWeight: '500',
    color: '#4b5563',
  },
  timeSlotTextActive: {
    color: '#e11d48',
  },
  notesInput: {
    borderWidth: 2,
    borderColor: '#e5e7eb',
    borderRadius: 8,
    padding: 12,
    fontSize: 14,
    minHeight: 80,
    color: '#1f2937',
  },
  priceRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  priceLabel: {
    fontSize: 14,
    color: '#6b7280',
  },
  priceValue: {
    fontSize: 14,
    color: '#4b5563',
  },
  priceDivider: {
    height: 1,
    backgroundColor: '#e5e7eb',
    marginVertical: 8,
  },
  priceTotalLabel: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1f2937',
  },
  priceTotalValue: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1f2937',
  },
  summaryCard: {
    backgroundColor: '#f0fdf4',
    padding: 16,
    borderRadius: 12,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#bbf7d0',
  },
  summaryTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#166534',
    marginBottom: 12,
  },
  summaryRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  summaryText: {
    marginLeft: 8,
    fontSize: 14,
    color: '#166534',
  },
  errorBox: {
    backgroundColor: '#fef2f2',
    borderWidth: 1,
    borderColor: '#fecaca',
    borderRadius: 8,
    padding: 12,
    marginBottom: 16,
  },
  errorBoxText: {
    fontSize: 14,
    color: '#dc2626',
  },
  bookButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#e11d48',
    paddingVertical: 16,
    borderRadius: 10,
    gap: 8,
  },
  bookButtonDisabled: {
    backgroundColor: '#d1d5db',
  },
  bookButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
  },
  disclaimer: {
    fontSize: 12,
    color: '#9ca3af',
    textAlign: 'center',
    marginTop: 12,
  },
  paymentNote: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 16,
    padding: 12,
    backgroundColor: '#f9fafb',
    borderRadius: 8,
  },
  paymentNoteText: {
    marginLeft: 8,
    fontSize: 12,
    color: '#6b7280',
  },
});
