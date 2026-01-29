import { useState, useRef, useCallback, useEffect } from 'react'
import { createFileRoute, Link } from '@tanstack/react-router'
import { $api } from '@/lib/api/$api'
import type { components } from '@/types/api.gen'

type HostProfileSummaryResponse = components['schemas']['HostProfileSummaryResponse']

export const Route = createFileRoute('/hosts/')({
  component: HostsPage,
})

function HostsPage() {
  // Search state
  const [searchParams, setSearchParams] = useState({
    lat: null as number | null,
    lng: null as number | null,
    radius_km: 50,
    min_rating: null as number | null,
    max_price: null as number | null,
    verified_only: false,
    sort_by: 'rating' as string,
    q: null as string | null,
    limit: 12,
  })

  // Cursor-based pagination state
  const [cursor, setCursor] = useState<string | null>(null)
  const [allHosts, setAllHosts] = useState<HostProfileSummaryResponse[]>([])
  const [hasMore, setHasMore] = useState(true)

  // Filter panel visibility
  const [showFilters, setShowFilters] = useState(false)

  // Location loading state
  const [locationLoading, setLocationLoading] = useState(false)
  const [locationError, setLocationError] = useState<string | null>(null)

  // Infinite scroll observer ref
  const loadMoreRef = useRef<HTMLDivElement>(null)

  // Fetch hosts with cursor-based pagination
  const { data, isLoading, error, isFetching } = $api.useQuery('get', '/api/v1/hosts/search', {
    params: {
      query: {
        cursor: cursor,
        lat: searchParams.lat,
        lng: searchParams.lng,
        radius_km: searchParams.radius_km,
        min_rating: searchParams.min_rating,
        max_price: searchParams.max_price,
        verified_only: searchParams.verified_only,
        sort_by: searchParams.sort_by,
        q: searchParams.q,
        limit: searchParams.limit,
      },
    },
  })

  // Handle data updates from API
  useEffect(() => {
    if (data) {
      if (cursor === null) {
        // First page - replace all hosts
        setAllHosts(data.items)
      } else {
        // Subsequent pages - append hosts
        setAllHosts((prev) => [...prev, ...data.items])
      }
      setHasMore(data.has_more)
    }
  }, [data, cursor])

  // Load more hosts (for infinite scroll)
  const handleLoadMore = useCallback(() => {
    if (data?.next_cursor && hasMore && !isFetching) {
      setCursor(data.next_cursor)
    }
  }, [data?.next_cursor, hasMore, isFetching])

  // Infinite scroll observer
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0]?.isIntersecting) {
          handleLoadMore()
        }
      },
      { threshold: 0.1 }
    )

    const currentRef = loadMoreRef.current
    if (currentRef) {
      observer.observe(currentRef)
    }

    return () => {
      if (currentRef) {
        observer.unobserve(currentRef)
      }
    }
  }, [handleLoadMore])

  // Reset pagination when filters change
  const resetPagination = useCallback(() => {
    setCursor(null)
    setAllHosts([])
    setHasMore(true)
  }, [])

  // Get user's location
  const handleUseMyLocation = () => {
    if (!navigator.geolocation) {
      setLocationError('Geolocation is not supported by your browser')
      return
    }

    setLocationLoading(true)
    setLocationError(null)

    navigator.geolocation.getCurrentPosition(
      (position) => {
        setSearchParams((prev) => ({
          ...prev,
          lat: position.coords.latitude,
          lng: position.coords.longitude,
        }))
        resetPagination()
        setLocationLoading(false)
      },
      () => {
        setLocationError('Unable to get your location')
        setLocationLoading(false)
      }
    )
  }

  // Clear location filter
  const handleClearLocation = () => {
    setSearchParams((prev) => ({
      ...prev,
      lat: null,
      lng: null,
    }))
    resetPagination()
    setLocationError(null)
  }

  // Handle filter changes
  const handleFilterChange = (key: string, value: unknown) => {
    setSearchParams((prev) => ({
      ...prev,
      [key]: value,
    }))
    resetPagination()
  }

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '1rem' }}>
      {/* Header */}
      <div style={{ marginBottom: '1.5rem' }}>
        <h1 style={{
          fontSize: 'clamp(1.5rem, 4vw, 2rem)',
          fontWeight: 'bold',
          color: '#1f2937',
          marginBottom: '0.5rem',
        }}>
          Find a Dance Host
        </h1>
        <p style={{ color: '#6b7280' }}>
          Discover qualified dance hosts in your area
        </p>
      </div>

      {/* Search Controls */}
      <div style={{
        backgroundColor: '#f9fafb',
        borderRadius: '0.5rem',
        padding: '1rem',
        marginBottom: '1.5rem',
      }}>
        {/* Location Controls */}
        <div style={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: '0.75rem',
          alignItems: 'center',
          marginBottom: '1rem',
        }}>
          <button
            onClick={handleUseMyLocation}
            disabled={locationLoading}
            style={{
              padding: '0.5rem 1rem',
              backgroundColor: searchParams.lat ? '#10b981' : '#4f46e5',
              color: 'white',
              border: 'none',
              borderRadius: '0.375rem',
              cursor: locationLoading ? 'wait' : 'pointer',
              fontSize: '0.875rem',
              fontWeight: '500',
            }}
          >
            {locationLoading
              ? 'Getting location...'
              : searchParams.lat
                ? '✓ Using your location'
                : 'Use my location'}
          </button>

          {searchParams.lat && (
            <button
              onClick={handleClearLocation}
              style={{
                padding: '0.5rem 0.75rem',
                backgroundColor: '#ef4444',
                color: 'white',
                border: 'none',
                borderRadius: '0.375rem',
                cursor: 'pointer',
                fontSize: '0.875rem',
              }}
            >
              Clear location
            </button>
          )}

          <button
            onClick={() => setShowFilters(!showFilters)}
            style={{
              padding: '0.5rem 1rem',
              backgroundColor: showFilters ? '#1f2937' : '#6b7280',
              color: 'white',
              border: 'none',
              borderRadius: '0.375rem',
              cursor: 'pointer',
              fontSize: '0.875rem',
            }}
          >
            {showFilters ? 'Hide filters' : 'Show filters'}
          </button>
        </div>

        {locationError && (
          <p style={{ color: '#ef4444', fontSize: '0.875rem', marginBottom: '0.75rem' }}>
            {locationError}
          </p>
        )}

        {/* Filter Panel */}
        {showFilters && (
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: '1rem',
            paddingTop: '1rem',
            borderTop: '1px solid #e5e7eb',
          }}>
            {/* Radius */}
            <div>
              <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: '500', color: '#374151', marginBottom: '0.25rem' }}>
                Search radius
              </label>
              <select
                value={searchParams.radius_km}
                onChange={(e) => handleFilterChange('radius_km', Number(e.target.value))}
                style={{
                  width: '100%',
                  padding: '0.5rem',
                  border: '1px solid #d1d5db',
                  borderRadius: '0.375rem',
                  fontSize: '0.875rem',
                }}
              >
                <option value={10}>10 km</option>
                <option value={25}>25 km</option>
                <option value={50}>50 km</option>
                <option value={100}>100 km</option>
                <option value={250}>250 km</option>
              </select>
            </div>

            {/* Min Rating */}
            <div>
              <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: '500', color: '#374151', marginBottom: '0.25rem' }}>
                Minimum rating
              </label>
              <select
                value={searchParams.min_rating ?? ''}
                onChange={(e) => handleFilterChange('min_rating', e.target.value ? Number(e.target.value) : null)}
                style={{
                  width: '100%',
                  padding: '0.5rem',
                  border: '1px solid #d1d5db',
                  borderRadius: '0.375rem',
                  fontSize: '0.875rem',
                }}
              >
                <option value="">Any rating</option>
                <option value="3">3+ stars</option>
                <option value="4">4+ stars</option>
                <option value="4.5">4.5+ stars</option>
              </select>
            </div>

            {/* Max Price */}
            <div>
              <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: '500', color: '#374151', marginBottom: '0.25rem' }}>
                Max hourly rate
              </label>
              <select
                value={searchParams.max_price ?? ''}
                onChange={(e) => handleFilterChange('max_price', e.target.value ? Number(e.target.value) : null)}
                style={{
                  width: '100%',
                  padding: '0.5rem',
                  border: '1px solid #d1d5db',
                  borderRadius: '0.375rem',
                  fontSize: '0.875rem',
                }}
              >
                <option value="">Any price</option>
                <option value="5000">Up to $50/hr</option>
                <option value="10000">Up to $100/hr</option>
                <option value="15000">Up to $150/hr</option>
                <option value="20000">Up to $200/hr</option>
              </select>
            </div>

            {/* Sort By */}
            <div>
              <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: '500', color: '#374151', marginBottom: '0.25rem' }}>
                Sort by
              </label>
              <select
                value={searchParams.sort_by}
                onChange={(e) => {
                  setSearchParams((prev) => ({
                    ...prev,
                    sort_by: e.target.value,
                  }))
                  resetPagination()
                }}
                style={{
                  width: '100%',
                  padding: '0.5rem',
                  border: '1px solid #d1d5db',
                  borderRadius: '0.375rem',
                  fontSize: '0.875rem',
                }}
              >
                <option value="rating">Highest rated</option>
                <option value="price">Lowest price</option>
                {searchParams.lat && <option value="distance">Closest</option>}
                {searchParams.q && <option value="relevance">Most relevant</option>}
              </select>
            </div>

            {/* Search Query */}
            <div>
              <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: '500', color: '#374151', marginBottom: '0.25rem' }}>
                Search
              </label>
              <input
                type="text"
                placeholder="Search by name..."
                value={searchParams.q ?? ''}
                onChange={(e) => handleFilterChange('q', e.target.value || null)}
                style={{
                  width: '100%',
                  padding: '0.5rem',
                  border: '1px solid #d1d5db',
                  borderRadius: '0.375rem',
                  fontSize: '0.875rem',
                }}
              />
            </div>

            {/* Verified Only */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <input
                type="checkbox"
                id="verified-only"
                checked={searchParams.verified_only}
                onChange={(e) => handleFilterChange('verified_only', e.target.checked)}
                style={{ width: '1rem', height: '1rem' }}
              />
              <label htmlFor="verified-only" style={{ fontSize: '0.875rem', color: '#374151' }}>
                Verified hosts only
              </label>
            </div>
          </div>
        )}
      </div>

      {/* Results Info */}
      {data && (
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '1rem',
          fontSize: '0.875rem',
          color: '#6b7280',
        }}>
          <span>
            {data.total} host{data.total !== 1 ? 's' : ''} found
          </span>
          <span>
            Showing {allHosts.length} of {data.total}
          </span>
        </div>
      )}

      {/* Loading State */}
      {isLoading && (
        <div style={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          minHeight: '200px',
        }}>
          <p style={{ color: '#6b7280' }}>Loading hosts...</p>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div style={{
          backgroundColor: '#fef2f2',
          border: '1px solid #fecaca',
          borderRadius: '0.5rem',
          padding: '1rem',
          color: '#dc2626',
        }}>
          <p>Failed to load hosts. Please try again.</p>
        </div>
      )}

      {/* Host Cards Grid */}
      {allHosts.length > 0 && (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
          gap: '1.5rem',
        }}>
          {allHosts.map((host) => (
            <HostCard key={host.id} host={host} />
          ))}
        </div>
      )}

      {/* Empty State */}
      {!isLoading && allHosts.length === 0 && (
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '200px',
          backgroundColor: '#f9fafb',
          borderRadius: '0.5rem',
          padding: '2rem',
        }}>
          <p style={{ color: '#6b7280', marginBottom: '0.5rem' }}>
            No hosts found matching your criteria.
          </p>
          <p style={{ color: '#9ca3af', fontSize: '0.875rem' }}>
            Try adjusting your filters or expanding your search area.
          </p>
        </div>
      )}

      {/* Infinite Scroll Trigger */}
      {hasMore && (
        <div
          ref={loadMoreRef}
          style={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            padding: '2rem',
            marginTop: '1rem',
          }}
        >
          {isFetching ? (
            <p style={{ color: '#6b7280' }}>Loading more hosts...</p>
          ) : (
            <button
              onClick={handleLoadMore}
              style={{
                padding: '0.5rem 1.5rem',
                backgroundColor: '#4f46e5',
                color: 'white',
                border: 'none',
                borderRadius: '0.375rem',
                cursor: 'pointer',
                fontSize: '0.875rem',
              }}
            >
              Load more
            </button>
          )}
        </div>
      )}
    </div>
  )
}

// Host Card Component
function HostCard({ host }: { host: HostProfileSummaryResponse }) {
  const formatPrice = (cents: number) => {
    return `$${(cents / 100).toFixed(0)}/hr`
  }

  const formatRating = (rating: number | null | undefined) => {
    if (rating === null || rating === undefined) return 'New'
    return rating.toFixed(1)
  }

  return (
    <Link
      to="/hosts/$hostId"
      params={{ hostId: host.id }}
      style={{ textDecoration: 'none' }}
    >
      <div style={{
        backgroundColor: 'white',
        borderRadius: '0.75rem',
        overflow: 'hidden',
        boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
        transition: 'box-shadow 0.2s, transform 0.2s',
        cursor: 'pointer',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)'
        e.currentTarget.style.transform = 'translateY(-2px)'
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.boxShadow = '0 1px 3px rgba(0,0,0,0.1)'
        e.currentTarget.style.transform = 'translateY(0)'
      }}
      >
        {/* Photo placeholder */}
        <div style={{
          height: '160px',
          backgroundColor: '#e5e7eb',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          position: 'relative',
        }}>
          <span style={{
            fontSize: '3rem',
            color: '#9ca3af',
          }}>
            👤
          </span>

          {/* Verified badge */}
          {host.verification_status === 'verified' && (
            <div style={{
              position: 'absolute',
              top: '0.75rem',
              right: '0.75rem',
              backgroundColor: '#10b981',
              color: 'white',
              padding: '0.25rem 0.5rem',
              borderRadius: '9999px',
              fontSize: '0.75rem',
              fontWeight: '500',
            }}>
              ✓ Verified
            </div>
          )}
        </div>

        {/* Content */}
        <div style={{ padding: '1rem' }}>
          {/* Name */}
          <h3 style={{
            fontSize: '1.125rem',
            fontWeight: '600',
            color: '#1f2937',
            marginBottom: '0.25rem',
          }}>
            {host.first_name} {host.last_name}
          </h3>

          {/* Headline */}
          {host.headline && (
            <p style={{
              fontSize: '0.875rem',
              color: '#6b7280',
              marginBottom: '0.75rem',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
            }}>
              {host.headline}
            </p>
          )}

          {/* Rating and Reviews */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            marginBottom: '0.5rem',
          }}>
            <span style={{
              fontSize: '0.875rem',
              fontWeight: '600',
              color: '#1f2937',
            }}>
              ⭐ {formatRating(host.rating_average)}
            </span>
            <span style={{
              fontSize: '0.875rem',
              color: '#6b7280',
            }}>
              ({host.total_reviews} review{host.total_reviews !== 1 ? 's' : ''})
            </span>
          </div>

          {/* Price and Distance */}
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}>
            <span style={{
              fontSize: '1rem',
              fontWeight: '700',
              color: '#4f46e5',
            }}>
              {formatPrice(host.hourly_rate_cents)}
            </span>

            {host.distance_km !== null && host.distance_km !== undefined && (
              <span style={{
                fontSize: '0.875rem',
                color: '#6b7280',
              }}>
                {host.distance_km < 1
                  ? `${(host.distance_km * 1000).toFixed(0)}m away`
                  : `${host.distance_km.toFixed(1)}km away`}
              </span>
            )}
          </div>
        </div>
      </div>
    </Link>
  )
}
