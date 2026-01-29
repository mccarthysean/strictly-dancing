import { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  RefreshControl,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useLocalSearchParams, Stack } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { apiClient, ApiError } from '@/lib/api/client';
import type { components } from '@/types/api.gen';

type HostProfileWithUserResponse = components['schemas']['HostProfileWithUserResponse'];
type HostDanceStyleResponse = components['schemas']['HostDanceStyleResponse'];
type ReviewListResponse = components['schemas']['ReviewListResponse'];
type ReviewWithUserResponse = components['schemas']['ReviewWithUserResponse'];

// Skill level labels
const skillLevelLabels: Record<number, string> = {
  1: 'Beginner',
  2: 'Intermediate',
  3: 'Advanced',
  4: 'Expert',
  5: 'Master',
};

export default function HostProfileScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();

  // State
  const [host, setHost] = useState<HostProfileWithUserResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  // Reviews state
  const [reviews, setReviews] = useState<ReviewWithUserResponse[]>([]);
  const [reviewsLoading, setReviewsLoading] = useState(false);
  const [reviewsNextCursor, setReviewsNextCursor] = useState<string | null>(null);
  const [hasMoreReviews, setHasMoreReviews] = useState(false);

  // Fetch host profile
  const fetchHost = useCallback(async () => {
    if (!id) return;

    try {
      const data = await apiClient.get<HostProfileWithUserResponse>(
        `/api/v1/hosts/${id}`
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
      setRefreshing(false);
    }
  }, [id]);

  // Fetch reviews
  const fetchReviews = useCallback(
    async (cursor?: string | null) => {
      if (!id) return;

      setReviewsLoading(true);
      try {
        const params = new URLSearchParams();
        params.set('limit', '10');
        if (cursor) {
          params.set('cursor', cursor);
        }

        const data = await apiClient.get<ReviewListResponse>(
          `/api/v1/hosts/${id}/reviews?${params.toString()}`
        );

        if (cursor) {
          // Append to existing reviews
          setReviews((prev) => [...prev, ...(data.items ?? [])]);
        } else {
          // Replace reviews
          setReviews(data.items ?? []);
        }

        setReviewsNextCursor(data.next_cursor ?? null);
        setHasMoreReviews(data.has_more);
      } catch (err) {
        console.error('Failed to fetch reviews:', err);
      } finally {
        setReviewsLoading(false);
      }
    },
    [id]
  );

  // Initial load
  useEffect(() => {
    fetchHost();
    fetchReviews();
  }, [fetchHost, fetchReviews]);

  // Handle refresh
  const onRefresh = useCallback(() => {
    setRefreshing(true);
    setReviews([]);
    setReviewsNextCursor(null);
    fetchHost();
    fetchReviews();
  }, [fetchHost, fetchReviews]);

  // Load more reviews
  const loadMoreReviews = useCallback(() => {
    if (!reviewsLoading && hasMoreReviews && reviewsNextCursor) {
      fetchReviews(reviewsNextCursor);
    }
  }, [reviewsLoading, hasMoreReviews, reviewsNextCursor, fetchReviews]);

  // Navigate to booking flow
  const handleBookNow = useCallback(() => {
    // Booking flow will be implemented in T083
    Alert.alert(
      'Coming Soon',
      'The booking feature will be available soon!',
      [{ text: 'OK' }]
    );
  }, []);

  // Navigate to messages
  const handleMessage = useCallback(() => {
    // Messages flow will be implemented in T085
    Alert.alert(
      'Coming Soon',
      'The messaging feature will be available soon!',
      [{ text: 'OK' }]
    );
  }, []);

  // Format price from cents
  const formatPrice = (cents: number) => {
    return `$${(cents / 100).toFixed(0)}`;
  };

  // Format rating
  const formatRating = (rating: number | null | undefined) => {
    return rating ? rating.toFixed(1) : 'New';
  };

  // Format date
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  // Loading state
  if (isLoading) {
    return (
      <>
        <Stack.Screen
          options={{
            headerShown: true,
            title: 'Host Profile',
            headerBackTitle: 'Back',
          }}
        />
        <SafeAreaView style={styles.container} edges={['bottom']}>
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color="#e11d48" />
            <Text style={styles.loadingText}>Loading profile...</Text>
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
            title: 'Host Profile',
            headerBackTitle: 'Back',
          }}
        />
        <SafeAreaView style={styles.container} edges={['bottom']}>
          <View style={styles.errorContainer}>
            <Ionicons name="alert-circle-outline" size={64} color="#9ca3af" />
            <Text style={styles.errorTitle}>Host Not Found</Text>
            <Text style={styles.errorText}>
              {error ?? 'The host profile you\'re looking for doesn\'t exist.'}
            </Text>
            <TouchableOpacity
              style={styles.retryButton}
              onPress={fetchHost}
            >
              <Text style={styles.retryButtonText}>Try Again</Text>
            </TouchableOpacity>
          </View>
        </SafeAreaView>
      </>
    );
  }

  // Render dance style card
  const renderDanceStyle = (style: HostDanceStyleResponse) => (
    <View key={style.dance_style_id} style={styles.danceStyleCard}>
      <View style={styles.danceStyleHeader}>
        <Text style={styles.danceStyleName}>{style.dance_style.name}</Text>
        <View style={styles.categoryBadge}>
          <Text style={styles.categoryBadgeText}>{style.dance_style.category}</Text>
        </View>
      </View>
      <View style={styles.skillLevelRow}>
        <Text style={styles.skillLabel}>
          {skillLevelLabels[style.skill_level] ?? 'Unknown'}
        </Text>
        <View style={styles.skillDots}>
          {[1, 2, 3, 4, 5].map((level) => (
            <View
              key={level}
              style={[
                styles.skillDot,
                {
                  backgroundColor:
                    level <= style.skill_level ? '#e11d48' : '#e5e7eb',
                },
              ]}
            />
          ))}
        </View>
      </View>
    </View>
  );

  // Render review item
  const renderReview = ({ item }: { item: ReviewWithUserResponse }) => {
    const reviewerFirstName = item.reviewer?.first_name ?? 'Anonymous';
    const reviewerLastName = item.reviewer?.last_name ?? '';
    const reviewerInitials = `${reviewerFirstName.charAt(0)}${reviewerLastName.charAt(0) || ''}`;

    return (
      <View style={styles.reviewCard}>
        <View style={styles.reviewHeader}>
          <View style={styles.reviewerInfo}>
            <View style={styles.reviewerAvatar}>
              <Text style={styles.reviewerAvatarText}>{reviewerInitials}</Text>
            </View>
            <View>
              <Text style={styles.reviewerName}>
                {reviewerFirstName} {reviewerLastName}
              </Text>
              <Text style={styles.reviewDate}>{formatDate(item.created_at)}</Text>
            </View>
          </View>
          <View style={styles.ratingBadge}>
            <Ionicons name="star" size={14} color="#fbbf24" />
            <Text style={styles.ratingBadgeText}>{item.rating}</Text>
          </View>
        </View>
        {item.comment && <Text style={styles.reviewComment}>{item.comment}</Text>}
        {item.host_response && (
          <View style={styles.hostResponse}>
            <Text style={styles.hostResponseLabel}>Host response:</Text>
            <Text style={styles.hostResponseText}>{item.host_response}</Text>
          </View>
        )}
      </View>
    );
  };

  // Render reviews footer (load more)
  const renderReviewsFooter = () => {
    if (reviewsLoading) {
      return (
        <View style={styles.reviewsFooter}>
          <ActivityIndicator size="small" color="#e11d48" />
        </View>
      );
    }
    if (hasMoreReviews) {
      return (
        <TouchableOpacity
          style={styles.loadMoreButton}
          onPress={loadMoreReviews}
        >
          <Text style={styles.loadMoreText}>Load More Reviews</Text>
        </TouchableOpacity>
      );
    }
    return null;
  };

  return (
    <>
      <Stack.Screen
        options={{
          headerShown: true,
          title: `${host.first_name} ${host.last_name}`,
          headerBackTitle: 'Back',
        }}
      />
      <SafeAreaView style={styles.container} edges={['bottom']}>
        <ScrollView
          style={styles.scrollView}
          contentContainerStyle={styles.scrollContent}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
          }
        >
          {/* Profile Header */}
          <View style={styles.profileHeader}>
            {/* Avatar */}
            <View style={styles.avatar}>
              <Text style={styles.avatarText}>
                {host.first_name.charAt(0)}
                {host.last_name.charAt(0)}
              </Text>
            </View>

            {/* Name and verification */}
            <View style={styles.nameContainer}>
              <View style={styles.nameRow}>
                <Text style={styles.name}>
                  {host.first_name} {host.last_name}
                </Text>
                {host.verification_status === 'verified' && (
                  <Ionicons name="checkmark-circle" size={24} color="#16a34a" />
                )}
              </View>
              {host.headline && (
                <Text style={styles.headline}>{host.headline}</Text>
              )}
            </View>

            {/* Stats Row */}
            <View style={styles.statsRow}>
              <View style={styles.statItem}>
                <View style={styles.statValueRow}>
                  <Ionicons name="star" size={18} color="#fbbf24" />
                  <Text style={styles.statValue}>
                    {formatRating(host.rating_average)}
                  </Text>
                </View>
                <Text style={styles.statLabel}>
                  {host.total_reviews} review{host.total_reviews !== 1 ? 's' : ''}
                </Text>
              </View>
              <View style={styles.statDivider} />
              <View style={styles.statItem}>
                <Text style={styles.statValue}>{host.total_sessions}</Text>
                <Text style={styles.statLabel}>sessions</Text>
              </View>
              <View style={styles.statDivider} />
              <View style={styles.statItem}>
                <Text style={styles.statValue}>
                  {formatPrice(host.hourly_rate_cents)}
                </Text>
                <Text style={styles.statLabel}>per hour</Text>
              </View>
            </View>
          </View>

          {/* Action Buttons */}
          <View style={styles.actionButtons}>
            <TouchableOpacity
              style={styles.bookButton}
              onPress={handleBookNow}
            >
              <Ionicons name="calendar-outline" size={20} color="#fff" />
              <Text style={styles.bookButtonText}>Book Now</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={styles.messageButton}
              onPress={handleMessage}
            >
              <Ionicons name="chatbubble-outline" size={20} color="#1f2937" />
              <Text style={styles.messageButtonText}>Message</Text>
            </TouchableOpacity>
          </View>

          {/* Bio Section */}
          {host.bio && (
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>About</Text>
              <Text style={styles.bioText}>{host.bio}</Text>
            </View>
          )}

          {/* Dance Styles Section */}
          {host.dance_styles && host.dance_styles.length > 0 && (
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>Dance Styles</Text>
              <View style={styles.danceStylesGrid}>
                {host.dance_styles.map(renderDanceStyle)}
              </View>
            </View>
          )}

          {/* Reviews Section */}
          <View style={styles.section}>
            <View style={styles.reviewsHeader}>
              <Text style={styles.sectionTitle}>Reviews</Text>
              {host.total_reviews > 0 && (
                <Text style={styles.reviewsCount}>({host.total_reviews})</Text>
              )}
            </View>

            {reviews.length > 0 ? (
              <View>
                {reviews.map((review) => (
                  <View key={review.id}>{renderReview({ item: review })}</View>
                ))}
                {renderReviewsFooter()}
              </View>
            ) : reviewsLoading ? (
              <View style={styles.reviewsLoadingContainer}>
                <ActivityIndicator size="small" color="#e11d48" />
              </View>
            ) : (
              <View style={styles.noReviewsContainer}>
                <Ionicons
                  name="chatbubbles-outline"
                  size={48}
                  color="#9ca3af"
                />
                <Text style={styles.noReviewsText}>No reviews yet</Text>
                <Text style={styles.noReviewsSubtext}>
                  Be the first to book and review this host!
                </Text>
              </View>
            )}
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
    paddingBottom: 24,
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
  profileHeader: {
    backgroundColor: '#fff',
    padding: 20,
    alignItems: 'center',
  },
  avatar: {
    width: 100,
    height: 100,
    borderRadius: 50,
    backgroundColor: '#e11d48',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 16,
  },
  avatarText: {
    fontSize: 36,
    fontWeight: 'bold',
    color: '#fff',
  },
  nameContainer: {
    alignItems: 'center',
    marginBottom: 16,
  },
  nameRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  name: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#1f2937',
  },
  headline: {
    fontSize: 14,
    color: '#6b7280',
    marginTop: 4,
    textAlign: 'center',
  },
  statsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: '#e5e7eb',
    width: '100%',
  },
  statItem: {
    flex: 1,
    alignItems: 'center',
  },
  statValueRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  statValue: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1f2937',
  },
  statLabel: {
    fontSize: 12,
    color: '#6b7280',
    marginTop: 2,
  },
  statDivider: {
    width: 1,
    height: 32,
    backgroundColor: '#e5e7eb',
  },
  actionButtons: {
    flexDirection: 'row',
    padding: 16,
    gap: 12,
    backgroundColor: '#fff',
    borderTopWidth: 1,
    borderTopColor: '#e5e7eb',
  },
  bookButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    paddingVertical: 14,
    backgroundColor: '#e11d48',
    borderRadius: 10,
  },
  bookButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
  },
  messageButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    paddingVertical: 14,
    backgroundColor: '#fff',
    borderRadius: 10,
    borderWidth: 2,
    borderColor: '#e5e7eb',
  },
  messageButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1f2937',
  },
  section: {
    backgroundColor: '#fff',
    marginTop: 12,
    padding: 16,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1f2937',
    marginBottom: 12,
  },
  bioText: {
    fontSize: 14,
    color: '#4b5563',
    lineHeight: 22,
  },
  danceStylesGrid: {
    gap: 12,
  },
  danceStyleCard: {
    padding: 12,
    backgroundColor: '#f9fafb',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#e5e7eb',
  },
  danceStyleHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  danceStyleName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1f2937',
  },
  categoryBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    backgroundColor: '#e5e7eb',
    borderRadius: 4,
  },
  categoryBadgeText: {
    fontSize: 12,
    color: '#6b7280',
    textTransform: 'capitalize',
  },
  skillLevelRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  skillLabel: {
    fontSize: 14,
    color: '#6b7280',
  },
  skillDots: {
    flexDirection: 'row',
    gap: 4,
  },
  skillDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  reviewsHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  reviewsCount: {
    fontSize: 14,
    color: '#6b7280',
  },
  reviewCard: {
    padding: 12,
    backgroundColor: '#f9fafb',
    borderRadius: 8,
    marginBottom: 12,
  },
  reviewHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 8,
  },
  reviewerInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  reviewerAvatar: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#e5e7eb',
    justifyContent: 'center',
    alignItems: 'center',
  },
  reviewerAvatarText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#6b7280',
  },
  reviewerName: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1f2937',
  },
  reviewDate: {
    fontSize: 12,
    color: '#9ca3af',
  },
  ratingBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingHorizontal: 8,
    paddingVertical: 4,
    backgroundColor: '#fef3c7',
    borderRadius: 4,
  },
  ratingBadgeText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#92400e',
  },
  reviewComment: {
    fontSize: 14,
    color: '#4b5563',
    lineHeight: 20,
  },
  hostResponse: {
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#e5e7eb',
  },
  hostResponseLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: '#6b7280',
    marginBottom: 4,
  },
  hostResponseText: {
    fontSize: 14,
    color: '#4b5563',
    fontStyle: 'italic',
  },
  reviewsFooter: {
    alignItems: 'center',
    paddingVertical: 16,
  },
  loadMoreButton: {
    alignItems: 'center',
    paddingVertical: 12,
  },
  loadMoreText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#e11d48',
  },
  reviewsLoadingContainer: {
    alignItems: 'center',
    paddingVertical: 24,
  },
  noReviewsContainer: {
    alignItems: 'center',
    paddingVertical: 32,
  },
  noReviewsText: {
    fontSize: 16,
    fontWeight: '500',
    color: '#6b7280',
    marginTop: 12,
  },
  noReviewsSubtext: {
    fontSize: 14,
    color: '#9ca3af',
    marginTop: 4,
    textAlign: 'center',
  },
});
