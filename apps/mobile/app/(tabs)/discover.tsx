import { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  TextInput,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  ActivityIndicator,
  Modal,
  ScrollView,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import * as Location from 'expo-location';
import { useRouter } from 'expo-router';
import { apiClient } from '@/lib/api/client';
import type { components } from '@/types/api.gen';

type HostProfile = components['schemas']['HostProfileSummaryResponse'];
type HostSearchResponse = components['schemas']['HostSearchResponse'];

// View mode type
type ViewMode = 'list' | 'map';

// Filter state
interface FilterState {
  minRating: number | null;
  maxPrice: number | null;
  verifiedOnly: boolean;
  danceStyles: string[];
  radius: number;
}

const defaultFilters: FilterState = {
  minRating: null,
  maxPrice: null,
  verifiedOnly: false,
  danceStyles: [],
  radius: 25,
};

export default function DiscoverScreen() {
  const router = useRouter();

  // State
  const [viewMode, setViewMode] = useState<ViewMode>('list');
  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState<FilterState>(defaultFilters);
  const [showFilters, setShowFilters] = useState(false);
  const [hosts, setHosts] = useState<HostProfile[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [location, setLocation] = useState<{ lat: number; lng: number } | null>(null);
  const [locationLoading, setLocationLoading] = useState(true);
  const [locationError, setLocationError] = useState<string | null>(null);

  // Get user location on mount
  useEffect(() => {
    (async () => {
      try {
        const { status } = await Location.requestForegroundPermissionsAsync();
        if (status !== 'granted') {
          setLocationError('Location permission not granted');
          setLocationLoading(false);
          return;
        }

        const currentLocation = await Location.getCurrentPositionAsync({});
        setLocation({
          lat: currentLocation.coords.latitude,
          lng: currentLocation.coords.longitude,
        });
      } catch (err) {
        setLocationError('Failed to get location');
        console.error('Location error:', err);
      } finally {
        setLocationLoading(false);
      }
    })();
  }, []);

  // Fetch hosts when location or filters change
  const fetchHosts = useCallback(async () => {
    if (!location) return;

    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams({
        lat: location.lat.toString(),
        lng: location.lng.toString(),
        radius_km: filters.radius.toString(),
        limit: '20',
      });

      if (filters.minRating) {
        params.append('min_rating', filters.minRating.toString());
      }
      if (filters.maxPrice) {
        params.append('max_hourly_rate', filters.maxPrice.toString());
      }
      if (filters.verifiedOnly) {
        params.append('verified_only', 'true');
      }
      if (filters.danceStyles.length > 0) {
        filters.danceStyles.forEach((style) => params.append('dance_styles', style));
      }

      const response = await apiClient.get<HostSearchResponse>(
        `/api/v1/hosts/search?${params.toString()}`
      );
      setHosts(response.items);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch hosts';
      setError(message);
    } finally {
      setLoading(false);
    }
  }, [location, filters]);

  useEffect(() => {
    if (location) {
      fetchHosts();
    }
  }, [location, fetchHosts]);

  // Render host card
  const renderHostCard = ({ item }: { item: HostProfile }) => (
    <TouchableOpacity
      style={styles.hostCard}
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      onPress={() => router.push(`/hosts/${item.id}` as any)}
    >
      <View style={styles.hostAvatar}>
        <Text style={styles.avatarText}>
          {item.first_name?.[0] ?? ''}
          {item.last_name?.[0] ?? ''}
        </Text>
      </View>
      <View style={styles.hostInfo}>
        <View style={styles.hostHeader}>
          <Text style={styles.hostName}>
            {item.first_name} {item.last_name}
          </Text>
          {item.verification_status === 'verified' && (
            <Ionicons name="checkmark-circle" size={16} color="#10B981" />
          )}
        </View>
        {item.headline && (
          <Text style={styles.hostHeadline} numberOfLines={1}>
            {item.headline}
          </Text>
        )}
        <View style={styles.hostMeta}>
          {item.rating_average != null && (
            <View style={styles.ratingContainer}>
              <Ionicons name="star" size={14} color="#F59E0B" />
              <Text style={styles.ratingText}>
                {item.rating_average.toFixed(1)}
              </Text>
              <Text style={styles.reviewCount}>({item.total_reviews})</Text>
            </View>
          )}
          {item.hourly_rate_cents != null && (
            <Text style={styles.priceText}>
              ${(item.hourly_rate_cents / 100).toFixed(0)}/hr
            </Text>
          )}
        </View>
        {/* Distance if available */}
        {item.distance_km != null && (
          <Text style={styles.distanceText}>
            {item.distance_km.toFixed(1)} km away
          </Text>
        )}
      </View>
      <Ionicons name="chevron-forward" size={20} color="#9CA3AF" />
    </TouchableOpacity>
  );

  // Filter modal
  const renderFilterModal = () => (
    <Modal
      visible={showFilters}
      animationType="slide"
      presentationStyle="pageSheet"
      onRequestClose={() => setShowFilters(false)}
    >
      <SafeAreaView style={styles.filterModal}>
        <View style={styles.filterHeader}>
          <TouchableOpacity onPress={() => setShowFilters(false)}>
            <Text style={styles.filterCancel}>Cancel</Text>
          </TouchableOpacity>
          <Text style={styles.filterTitle}>Filters</Text>
          <TouchableOpacity
            onPress={() => {
              setFilters(defaultFilters);
            }}
          >
            <Text style={styles.filterReset}>Reset</Text>
          </TouchableOpacity>
        </View>

        <ScrollView style={styles.filterContent}>
          {/* Search Radius */}
          <View style={styles.filterSection}>
            <Text style={styles.filterLabel}>Search Radius</Text>
            <View style={styles.radiusButtons}>
              {[10, 25, 50, 100].map((r) => (
                <TouchableOpacity
                  key={r}
                  style={[
                    styles.radiusButton,
                    filters.radius === r && styles.radiusButtonActive,
                  ]}
                  onPress={() => setFilters({ ...filters, radius: r })}
                >
                  <Text
                    style={[
                      styles.radiusButtonText,
                      filters.radius === r && styles.radiusButtonTextActive,
                    ]}
                  >
                    {r} km
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>

          {/* Minimum Rating */}
          <View style={styles.filterSection}>
            <Text style={styles.filterLabel}>Minimum Rating</Text>
            <View style={styles.ratingButtons}>
              {[null, 3, 4, 4.5].map((r, idx) => (
                <TouchableOpacity
                  key={idx}
                  style={[
                    styles.ratingButton,
                    filters.minRating === r && styles.ratingButtonActive,
                  ]}
                  onPress={() => setFilters({ ...filters, minRating: r })}
                >
                  <Text
                    style={[
                      styles.ratingButtonText,
                      filters.minRating === r && styles.ratingButtonTextActive,
                    ]}
                  >
                    {r === null ? 'Any' : `${r}+`}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>

          {/* Max Price */}
          <View style={styles.filterSection}>
            <Text style={styles.filterLabel}>Max Hourly Rate</Text>
            <View style={styles.priceButtons}>
              {[null, 5000, 10000, 15000].map((p, idx) => (
                <TouchableOpacity
                  key={idx}
                  style={[
                    styles.priceButton,
                    filters.maxPrice === p && styles.priceButtonActive,
                  ]}
                  onPress={() => setFilters({ ...filters, maxPrice: p })}
                >
                  <Text
                    style={[
                      styles.priceButtonText,
                      filters.maxPrice === p && styles.priceButtonTextActive,
                    ]}
                  >
                    {p === null ? 'Any' : `≤$${p / 100}`}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>

          {/* Verified Only */}
          <View style={styles.filterSection}>
            <TouchableOpacity
              style={styles.checkboxRow}
              onPress={() =>
                setFilters({ ...filters, verifiedOnly: !filters.verifiedOnly })
              }
            >
              <View
                style={[
                  styles.checkbox,
                  filters.verifiedOnly && styles.checkboxChecked,
                ]}
              >
                {filters.verifiedOnly && (
                  <Ionicons name="checkmark" size={16} color="#fff" />
                )}
              </View>
              <Text style={styles.checkboxLabel}>Verified hosts only</Text>
            </TouchableOpacity>
          </View>
        </ScrollView>

        <View style={styles.filterFooter}>
          <TouchableOpacity
            style={styles.applyButton}
            onPress={() => {
              setShowFilters(false);
              fetchHosts();
            }}
          >
            <Text style={styles.applyButtonText}>Apply Filters</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    </Modal>
  );

  // Map placeholder (map would require react-native-maps)
  const renderMapView = () => (
    <View style={styles.mapPlaceholder}>
      <Ionicons name="map" size={48} color="#9CA3AF" />
      <Text style={styles.mapPlaceholderText}>
        Map view requires native integration
      </Text>
      <Text style={styles.mapPlaceholderSubtext}>
        {hosts.length} hosts found in your area
      </Text>
    </View>
  );

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.title}>Discover</Text>
        <View style={styles.viewToggle}>
          <TouchableOpacity
            style={[styles.toggleButton, viewMode === 'list' && styles.toggleActive]}
            onPress={() => setViewMode('list')}
          >
            <Ionicons
              name="list"
              size={20}
              color={viewMode === 'list' ? '#8B5CF6' : '#9CA3AF'}
            />
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.toggleButton, viewMode === 'map' && styles.toggleActive]}
            onPress={() => setViewMode('map')}
          >
            <Ionicons
              name="map"
              size={20}
              color={viewMode === 'map' ? '#8B5CF6' : '#9CA3AF'}
            />
          </TouchableOpacity>
        </View>
      </View>

      {/* Search Bar */}
      <View style={styles.searchContainer}>
        <View style={styles.searchBar}>
          <Ionicons name="search" size={20} color="#9CA3AF" />
          <TextInput
            style={styles.searchInput}
            placeholder="Search by name or style..."
            placeholderTextColor="#9CA3AF"
            value={searchQuery}
            onChangeText={setSearchQuery}
          />
        </View>
        <TouchableOpacity
          style={styles.filterButton}
          onPress={() => setShowFilters(true)}
        >
          <Ionicons name="options" size={20} color="#374151" />
        </TouchableOpacity>
      </View>

      {/* Location status */}
      {locationLoading ? (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#8B5CF6" />
          <Text style={styles.loadingText}>Getting your location...</Text>
        </View>
      ) : locationError ? (
        <View style={styles.errorContainer}>
          <Ionicons name="location-outline" size={48} color="#9CA3AF" />
          <Text style={styles.errorTitle}>Location Required</Text>
          <Text style={styles.errorText}>{locationError}</Text>
          <TouchableOpacity
            style={styles.retryButton}
            onPress={() => {
              setLocationLoading(true);
              setLocationError(null);
            }}
          >
            <Text style={styles.retryButtonText}>Try Again</Text>
          </TouchableOpacity>
        </View>
      ) : viewMode === 'map' ? (
        renderMapView()
      ) : (
        /* Host List */
        <FlatList
          data={hosts}
          renderItem={renderHostCard}
          keyExtractor={(item) => item.id}
          contentContainerStyle={styles.listContent}
          ListHeaderComponent={
            loading ? (
              <View style={styles.listLoading}>
                <ActivityIndicator size="small" color="#8B5CF6" />
              </View>
            ) : error ? (
              <View style={styles.listError}>
                <Text style={styles.listErrorText}>{error}</Text>
              </View>
            ) : null
          }
          ListEmptyComponent={
            !loading ? (
              <View style={styles.emptyContainer}>
                <Ionicons name="people-outline" size={48} color="#9CA3AF" />
                <Text style={styles.emptyTitle}>No hosts found</Text>
                <Text style={styles.emptyText}>
                  Try adjusting your filters or search radius
                </Text>
              </View>
            ) : null
          }
          refreshing={loading}
          onRefresh={fetchHosts}
        />
      )}

      {renderFilterModal()}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#1a1a1a',
  },
  viewToggle: {
    flexDirection: 'row',
    backgroundColor: '#F3F4F6',
    borderRadius: 8,
    padding: 4,
  },
  toggleButton: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
  },
  toggleActive: {
    backgroundColor: '#fff',
  },
  searchContainer: {
    flexDirection: 'row',
    paddingHorizontal: 16,
    paddingBottom: 12,
    gap: 8,
  },
  searchBar: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F3F4F6',
    borderRadius: 8,
    paddingHorizontal: 12,
    height: 44,
    gap: 8,
  },
  searchInput: {
    flex: 1,
    fontSize: 16,
    color: '#1a1a1a',
  },
  filterButton: {
    width: 44,
    height: 44,
    backgroundColor: '#F3F4F6',
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    gap: 16,
  },
  loadingText: {
    fontSize: 16,
    color: '#6B7280',
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
    gap: 12,
  },
  errorTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1a1a1a',
  },
  errorText: {
    fontSize: 14,
    color: '#6B7280',
    textAlign: 'center',
  },
  retryButton: {
    marginTop: 8,
    paddingHorizontal: 24,
    paddingVertical: 12,
    backgroundColor: '#8B5CF6',
    borderRadius: 8,
  },
  retryButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  listContent: {
    paddingHorizontal: 16,
    paddingBottom: 24,
  },
  listLoading: {
    padding: 16,
    alignItems: 'center',
  },
  listError: {
    padding: 16,
    backgroundColor: '#FEF2F2',
    borderRadius: 8,
    marginBottom: 16,
  },
  listErrorText: {
    color: '#DC2626',
    textAlign: 'center',
  },
  hostCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 12,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  hostAvatar: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: '#8B5CF6',
    justifyContent: 'center',
    alignItems: 'center',
  },
  avatarText: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
  },
  hostInfo: {
    flex: 1,
    marginLeft: 12,
    marginRight: 8,
  },
  hostHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  hostName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1a1a1a',
  },
  hostHeadline: {
    fontSize: 14,
    color: '#6B7280',
    marginTop: 2,
  },
  hostMeta: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 4,
    gap: 12,
  },
  ratingContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  ratingText: {
    fontSize: 14,
    fontWeight: '500',
    color: '#1a1a1a',
  },
  reviewCount: {
    fontSize: 12,
    color: '#9CA3AF',
  },
  priceText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#8B5CF6',
  },
  distanceText: {
    fontSize: 12,
    color: '#9CA3AF',
    marginTop: 4,
  },
  emptyContainer: {
    flex: 1,
    paddingVertical: 48,
    alignItems: 'center',
    gap: 8,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1a1a1a',
  },
  emptyText: {
    fontSize: 14,
    color: '#6B7280',
    textAlign: 'center',
  },
  mapPlaceholder: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#F3F4F6',
    gap: 12,
  },
  mapPlaceholderText: {
    fontSize: 16,
    color: '#6B7280',
  },
  mapPlaceholderSubtext: {
    fontSize: 14,
    color: '#9CA3AF',
  },
  filterModal: {
    flex: 1,
    backgroundColor: '#fff',
  },
  filterHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  filterCancel: {
    fontSize: 16,
    color: '#6B7280',
  },
  filterTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1a1a1a',
  },
  filterReset: {
    fontSize: 16,
    color: '#8B5CF6',
  },
  filterContent: {
    flex: 1,
    padding: 16,
  },
  filterSection: {
    marginBottom: 24,
  },
  filterLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#374151',
    marginBottom: 12,
  },
  radiusButtons: {
    flexDirection: 'row',
    gap: 8,
  },
  radiusButton: {
    flex: 1,
    paddingVertical: 12,
    backgroundColor: '#F3F4F6',
    borderRadius: 8,
    alignItems: 'center',
  },
  radiusButtonActive: {
    backgroundColor: '#8B5CF6',
  },
  radiusButtonText: {
    fontSize: 14,
    color: '#6B7280',
  },
  radiusButtonTextActive: {
    color: '#fff',
    fontWeight: '600',
  },
  ratingButtons: {
    flexDirection: 'row',
    gap: 8,
  },
  ratingButton: {
    flex: 1,
    paddingVertical: 12,
    backgroundColor: '#F3F4F6',
    borderRadius: 8,
    alignItems: 'center',
  },
  ratingButtonActive: {
    backgroundColor: '#8B5CF6',
  },
  ratingButtonText: {
    fontSize: 14,
    color: '#6B7280',
  },
  ratingButtonTextActive: {
    color: '#fff',
    fontWeight: '600',
  },
  priceButtons: {
    flexDirection: 'row',
    gap: 8,
  },
  priceButton: {
    flex: 1,
    paddingVertical: 12,
    backgroundColor: '#F3F4F6',
    borderRadius: 8,
    alignItems: 'center',
  },
  priceButtonActive: {
    backgroundColor: '#8B5CF6',
  },
  priceButtonText: {
    fontSize: 14,
    color: '#6B7280',
  },
  priceButtonTextActive: {
    color: '#fff',
    fontWeight: '600',
  },
  checkboxRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  checkbox: {
    width: 24,
    height: 24,
    borderWidth: 2,
    borderColor: '#D1D5DB',
    borderRadius: 4,
    justifyContent: 'center',
    alignItems: 'center',
  },
  checkboxChecked: {
    backgroundColor: '#8B5CF6',
    borderColor: '#8B5CF6',
  },
  checkboxLabel: {
    fontSize: 16,
    color: '#374151',
  },
  filterFooter: {
    padding: 16,
    borderTopWidth: 1,
    borderTopColor: '#E5E7EB',
  },
  applyButton: {
    backgroundColor: '#8B5CF6',
    borderRadius: 8,
    paddingVertical: 16,
    alignItems: 'center',
  },
  applyButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
});
