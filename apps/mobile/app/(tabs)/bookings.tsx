import { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  ActivityIndicator,
  RefreshControl,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { router } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { apiClient } from '@/lib/api/client';
import { useAuthStore } from '@/stores/auth';
import type { components } from '@/types/api.gen';

type BookingListCursorResponse = components['schemas']['BookingListCursorResponse'];
type BookingWithDetailsResponse = components['schemas']['BookingWithDetailsResponse'];
type BookingStatus = components['schemas']['BookingStatus'];

// Tab types
type TabType = 'upcoming' | 'past' | 'cancelled';

// Status colors
const statusColors: Record<BookingStatus, { bg: string; text: string }> = {
  pending: { bg: '#fef3c7', text: '#92400e' },
  confirmed: { bg: '#dbeafe', text: '#1e40af' },
  in_progress: { bg: '#dcfce7', text: '#166534' },
  completed: { bg: '#e5e7eb', text: '#374151' },
  cancelled: { bg: '#fee2e2', text: '#991b1b' },
  disputed: { bg: '#fce7f3', text: '#9d174d' },
};

// Status labels
const statusLabels: Record<BookingStatus, string> = {
  pending: 'Pending',
  confirmed: 'Confirmed',
  in_progress: 'In Progress',
  completed: 'Completed',
  cancelled: 'Cancelled',
  disputed: 'Disputed',
};

export default function BookingsScreen() {
  const { isAuthenticated, user } = useAuthStore();

  // State
  const [activeTab, setActiveTab] = useState<TabType>('upcoming');
  const [bookings, setBookings] = useState<BookingWithDetailsResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);

  // Get status filters for current tab
  const getStatusFilter = (tab: TabType): BookingStatus[] => {
    switch (tab) {
      case 'upcoming':
        return ['pending', 'confirmed', 'in_progress'];
      case 'past':
        return ['completed'];
      case 'cancelled':
        return ['cancelled', 'disputed'];
    }
  };

  // Fetch bookings
  const fetchBookings = useCallback(
    async (cursor?: string | null) => {
      if (!isAuthenticated) return;

      if (!cursor) {
        setIsLoading(true);
      } else {
        setLoadingMore(true);
      }

      try {
        const statuses = getStatusFilter(activeTab);
        const params = new URLSearchParams();
        params.set('limit', '20');
        statuses.forEach((status) => params.append('status', status));
        if (cursor) {
          params.set('cursor', cursor);
        }

        const data = await apiClient.get<BookingListCursorResponse>(
          `/api/v1/bookings?${params.toString()}`
        );

        if (cursor) {
          setBookings((prev) => [...prev, ...data.items]);
        } else {
          setBookings(data.items);
        }

        setNextCursor(data.next_cursor ?? null);
        setHasMore(data.has_more);
      } catch (err) {
        console.error('Failed to fetch bookings:', err);
      } finally {
        setIsLoading(false);
        setRefreshing(false);
        setLoadingMore(false);
      }
    },
    [isAuthenticated, activeTab]
  );

  // Initial load and tab change
  useEffect(() => {
    setBookings([]);
    setNextCursor(null);
    fetchBookings();
  }, [activeTab, fetchBookings]);

  // Handle refresh
  const onRefresh = useCallback(() => {
    setRefreshing(true);
    setBookings([]);
    setNextCursor(null);
    fetchBookings();
  }, [fetchBookings]);

  // Load more
  const loadMore = useCallback(() => {
    if (!loadingMore && hasMore && nextCursor) {
      fetchBookings(nextCursor);
    }
  }, [loadingMore, hasMore, nextCursor, fetchBookings]);

  // Format date
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
    });
  };

  // Format time
  const formatTime = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
    });
  };

  // Format price
  const formatPrice = (cents: number) => `$${(cents / 100).toFixed(2)}`;

  // Get partner name (host or client depending on user role)
  const getPartnerName = (booking: BookingWithDetailsResponse) => {
    if (booking.client_id === user?.id) {
      // User is client, show host
      return booking.host
        ? `${booking.host.first_name} ${booking.host.last_name}`
        : 'Unknown Host';
    }
    // User is host, show client
    return booking.client
      ? `${booking.client.first_name} ${booking.client.last_name}`
      : 'Unknown Client';
  };

  // Get partner initials
  const getPartnerInitials = (booking: BookingWithDetailsResponse) => {
    if (booking.client_id === user?.id) {
      return booking.host
        ? `${booking.host.first_name.charAt(0)}${booking.host.last_name.charAt(0)}`
        : '?';
    }
    return booking.client
      ? `${booking.client.first_name.charAt(0)}${booking.client.last_name.charAt(0)}`
      : '?';
  };

  // Navigate to booking detail
  const handleBookingPress = (booking: BookingWithDetailsResponse) => {
    // Booking detail screen will be implemented in a future task
    // For now, we'll show an alert or navigate to a placeholder
    router.push(`/bookings/${booking.id}` as any);
  };

  // Render booking card
  const renderBookingCard = ({ item }: { item: BookingWithDetailsResponse }) => {
    const statusStyle = statusColors[item.status];
    const isClient = item.client_id === user?.id;

    return (
      <TouchableOpacity
        style={styles.bookingCard}
        onPress={() => handleBookingPress(item)}
      >
        <View style={styles.cardHeader}>
          <View style={styles.partnerInfo}>
            <View style={styles.partnerAvatar}>
              <Text style={styles.partnerAvatarText}>
                {getPartnerInitials(item)}
              </Text>
            </View>
            <View style={styles.partnerDetails}>
              <Text style={styles.partnerName}>{getPartnerName(item)}</Text>
              <Text style={styles.roleLabel}>
                {isClient ? 'Host' : 'Client'}
              </Text>
            </View>
          </View>
          <View style={[styles.statusBadge, { backgroundColor: statusStyle.bg }]}>
            <Text style={[styles.statusText, { color: statusStyle.text }]}>
              {statusLabels[item.status]}
            </Text>
          </View>
        </View>

        <View style={styles.cardBody}>
          <View style={styles.infoRow}>
            <Ionicons name="calendar-outline" size={16} color="#6b7280" />
            <Text style={styles.infoText}>{formatDate(item.scheduled_start)}</Text>
          </View>
          <View style={styles.infoRow}>
            <Ionicons name="time-outline" size={16} color="#6b7280" />
            <Text style={styles.infoText}>
              {formatTime(item.scheduled_start)} • {item.duration_minutes} min
            </Text>
          </View>
          {item.dance_style && (
            <View style={styles.infoRow}>
              <Ionicons name="musical-notes-outline" size={16} color="#6b7280" />
              <Text style={styles.infoText}>{item.dance_style.name}</Text>
            </View>
          )}
        </View>

        <View style={styles.cardFooter}>
          <Text style={styles.priceText}>{formatPrice(item.amount_cents)}</Text>
          <View style={styles.viewButton}>
            <Text style={styles.viewButtonText}>View Details</Text>
            <Ionicons name="chevron-forward" size={16} color="#e11d48" />
          </View>
        </View>
      </TouchableOpacity>
    );
  };

  // Render empty state
  const renderEmptyState = () => {
    if (isLoading) return null;

    const emptyMessages: Record<TabType, { title: string; subtitle: string; icon: keyof typeof Ionicons.glyphMap }> = {
      upcoming: {
        title: 'No Upcoming Bookings',
        subtitle: 'Find a host and book your first dance session!',
        icon: 'calendar-outline',
      },
      past: {
        title: 'No Past Bookings',
        subtitle: 'Your completed sessions will appear here.',
        icon: 'checkmark-circle-outline',
      },
      cancelled: {
        title: 'No Cancelled Bookings',
        subtitle: 'No bookings have been cancelled.',
        icon: 'close-circle-outline',
      },
    };

    const message = emptyMessages[activeTab];

    return (
      <View style={styles.emptyState}>
        <Ionicons name={message.icon} size={64} color="#9ca3af" />
        <Text style={styles.emptyTitle}>{message.title}</Text>
        <Text style={styles.emptySubtitle}>{message.subtitle}</Text>
        {activeTab === 'upcoming' && (
          <TouchableOpacity
            style={styles.findHostButton}
            onPress={() => router.push('/(tabs)/discover')}
          >
            <Text style={styles.findHostButtonText}>Find a Host</Text>
          </TouchableOpacity>
        )}
      </View>
    );
  };

  // Render footer (loading more)
  const renderFooter = () => {
    if (!loadingMore) return null;
    return (
      <View style={styles.footerLoader}>
        <ActivityIndicator size="small" color="#e11d48" />
      </View>
    );
  };

  // Auth required state
  if (!isAuthenticated) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.authRequired}>
          <Ionicons name="lock-closed-outline" size={64} color="#9ca3af" />
          <Text style={styles.authTitle}>Login Required</Text>
          <Text style={styles.authText}>
            Please log in to view your bookings.
          </Text>
          <TouchableOpacity
            style={styles.loginButton}
            onPress={() => router.push('/(auth)/login')}
          >
            <Text style={styles.loginButtonText}>Log In</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.title}>Bookings</Text>
      </View>

      {/* Tabs */}
      <View style={styles.tabs}>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'upcoming' && styles.tabActive]}
          onPress={() => setActiveTab('upcoming')}
        >
          <Text
            style={[
              styles.tabText,
              activeTab === 'upcoming' && styles.tabTextActive,
            ]}
          >
            Upcoming
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'past' && styles.tabActive]}
          onPress={() => setActiveTab('past')}
        >
          <Text
            style={[
              styles.tabText,
              activeTab === 'past' && styles.tabTextActive,
            ]}
          >
            Past
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'cancelled' && styles.tabActive]}
          onPress={() => setActiveTab('cancelled')}
        >
          <Text
            style={[
              styles.tabText,
              activeTab === 'cancelled' && styles.tabTextActive,
            ]}
          >
            Cancelled
          </Text>
        </TouchableOpacity>
      </View>

      {/* Bookings List */}
      {isLoading ? (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#e11d48" />
          <Text style={styles.loadingText}>Loading bookings...</Text>
        </View>
      ) : (
        <FlatList
          data={bookings}
          keyExtractor={(item) => item.id}
          renderItem={renderBookingCard}
          contentContainerStyle={styles.listContent}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
          }
          onEndReached={loadMore}
          onEndReachedThreshold={0.5}
          ListEmptyComponent={renderEmptyState}
          ListFooterComponent={renderFooter}
        />
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f3f4f6',
  },
  header: {
    backgroundColor: '#fff',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#e5e7eb',
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#1a1a1a',
  },
  tabs: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e5e7eb',
  },
  tab: {
    flex: 1,
    paddingVertical: 14,
    alignItems: 'center',
    borderBottomWidth: 2,
    borderBottomColor: 'transparent',
  },
  tabActive: {
    borderBottomColor: '#e11d48',
  },
  tabText: {
    fontSize: 14,
    fontWeight: '500',
    color: '#6b7280',
  },
  tabTextActive: {
    color: '#e11d48',
    fontWeight: '600',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 12,
    fontSize: 14,
    color: '#6b7280',
  },
  listContent: {
    padding: 16,
    paddingBottom: 32,
  },
  bookingCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 1,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  partnerInfo: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  partnerAvatar: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: '#e11d48',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  partnerAvatarText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#fff',
  },
  partnerDetails: {
    justifyContent: 'center',
  },
  partnerName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1f2937',
  },
  roleLabel: {
    fontSize: 12,
    color: '#9ca3af',
    marginTop: 2,
  },
  statusBadge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  statusText: {
    fontSize: 12,
    fontWeight: '600',
  },
  cardBody: {
    marginBottom: 12,
    paddingBottom: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f3f4f6',
  },
  infoRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 6,
  },
  infoText: {
    marginLeft: 8,
    fontSize: 14,
    color: '#6b7280',
  },
  cardFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  priceText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1f2937',
  },
  viewButton: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  viewButtonText: {
    fontSize: 14,
    fontWeight: '500',
    color: '#e11d48',
    marginRight: 4,
  },
  emptyState: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 64,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1f2937',
    marginTop: 16,
  },
  emptySubtitle: {
    fontSize: 14,
    color: '#6b7280',
    marginTop: 8,
    textAlign: 'center',
  },
  findHostButton: {
    marginTop: 24,
    paddingVertical: 12,
    paddingHorizontal: 24,
    backgroundColor: '#e11d48',
    borderRadius: 8,
  },
  findHostButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
  },
  footerLoader: {
    paddingVertical: 16,
    alignItems: 'center',
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
});
