import { useState, useRef, useCallback, useEffect } from 'react'
import { createFileRoute, Link } from '@tanstack/react-router'
import { $api } from '@/lib/api/$api'
import type { components } from '@/types/api.gen'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import { MapPin, Star, Check, ChevronDown, ChevronUp, X, Loader2 } from 'lucide-react'

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
    <div className="mx-auto max-w-7xl p-4">
      {/* Header */}
      <div className="mb-6">
        <h1 className="mb-2 font-display text-[clamp(1.5rem,4vw,2rem)] font-bold text-foreground">
          Find a Dance Host
        </h1>
        <p className="text-muted-foreground">
          Discover qualified dance hosts in your area
        </p>
      </div>

      {/* Search Controls */}
      <Card className="mb-6">
        <CardContent className="p-4">
          {/* Location Controls */}
          <div className="mb-4 flex flex-wrap items-center gap-3">
            <Button
              onClick={handleUseMyLocation}
              disabled={locationLoading}
              variant={searchParams.lat ? 'default' : 'secondary'}
              className={cn(
                searchParams.lat && 'bg-green-600 hover:bg-green-700'
              )}
            >
              {locationLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Getting location...
                </>
              ) : searchParams.lat ? (
                <>
                  <Check className="mr-2 h-4 w-4" />
                  Using your location
                </>
              ) : (
                <>
                  <MapPin className="mr-2 h-4 w-4" />
                  Use my location
                </>
              )}
            </Button>

            {searchParams.lat && (
              <Button
                onClick={handleClearLocation}
                variant="destructive"
                size="sm"
              >
                <X className="mr-1 h-4 w-4" />
                Clear location
              </Button>
            )}

            <Button
              onClick={() => setShowFilters(!showFilters)}
              variant={showFilters ? 'default' : 'outline'}
            >
              {showFilters ? (
                <>
                  <ChevronUp className="mr-2 h-4 w-4" />
                  Hide filters
                </>
              ) : (
                <>
                  <ChevronDown className="mr-2 h-4 w-4" />
                  Show filters
                </>
              )}
            </Button>
          </div>

          {locationError && (
            <p className="mb-3 text-sm text-destructive">{locationError}</p>
          )}

          {/* Filter Panel */}
          {showFilters && (
            <div className="grid grid-cols-1 gap-4 border-t border-border pt-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
              {/* Radius */}
              <div className="space-y-2">
                <Label>Search radius</Label>
                <select
                  value={searchParams.radius_km}
                  onChange={(e) => handleFilterChange('radius_km', Number(e.target.value))}
                  className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm"
                >
                  <option value={10}>10 km</option>
                  <option value={25}>25 km</option>
                  <option value={50}>50 km</option>
                  <option value={100}>100 km</option>
                  <option value={250}>250 km</option>
                </select>
              </div>

              {/* Min Rating */}
              <div className="space-y-2">
                <Label>Minimum rating</Label>
                <select
                  value={searchParams.min_rating ?? ''}
                  onChange={(e) => handleFilterChange('min_rating', e.target.value ? Number(e.target.value) : null)}
                  className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm"
                >
                  <option value="">Any rating</option>
                  <option value="3">3+ stars</option>
                  <option value="4">4+ stars</option>
                  <option value="4.5">4.5+ stars</option>
                </select>
              </div>

              {/* Max Price */}
              <div className="space-y-2">
                <Label>Max hourly rate</Label>
                <select
                  value={searchParams.max_price ?? ''}
                  onChange={(e) => handleFilterChange('max_price', e.target.value ? Number(e.target.value) : null)}
                  className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm"
                >
                  <option value="">Any price</option>
                  <option value="5000">Up to $50/hr</option>
                  <option value="10000">Up to $100/hr</option>
                  <option value="15000">Up to $150/hr</option>
                  <option value="20000">Up to $200/hr</option>
                </select>
              </div>

              {/* Sort By */}
              <div className="space-y-2">
                <Label>Sort by</Label>
                <select
                  value={searchParams.sort_by}
                  onChange={(e) => {
                    setSearchParams((prev) => ({
                      ...prev,
                      sort_by: e.target.value,
                    }))
                    resetPagination()
                  }}
                  className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm"
                >
                  <option value="rating">Highest rated</option>
                  <option value="price">Lowest price</option>
                  {searchParams.lat && <option value="distance">Closest</option>}
                  {searchParams.q && <option value="relevance">Most relevant</option>}
                </select>
              </div>

              {/* Search Query */}
              <div className="space-y-2">
                <Label>Search</Label>
                <Input
                  type="text"
                  placeholder="Search by name..."
                  value={searchParams.q ?? ''}
                  onChange={(e) => handleFilterChange('q', e.target.value || null)}
                />
              </div>

              {/* Verified Only */}
              <div className="flex items-center gap-2 pt-6">
                <input
                  type="checkbox"
                  id="verified-only"
                  checked={searchParams.verified_only}
                  onChange={(e) => handleFilterChange('verified_only', e.target.checked)}
                  className="h-4 w-4 rounded border-input"
                />
                <Label htmlFor="verified-only" className="cursor-pointer">
                  Verified hosts only
                </Label>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Results Info */}
      {data && (
        <div className="mb-4 flex items-center justify-between text-sm text-muted-foreground">
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
        <div className="flex min-h-[200px] items-center justify-center">
          <div className="flex items-center gap-2 text-muted-foreground">
            <Loader2 className="h-5 w-5 animate-spin" />
            Loading hosts...
          </div>
        </div>
      )}

      {/* Error State */}
      {error && (
        <Card className="border-destructive bg-destructive/10">
          <CardContent className="p-4 text-destructive">
            <p>Failed to load hosts. Please try again.</p>
          </CardContent>
        </Card>
      )}

      {/* Host Cards Grid */}
      {allHosts.length > 0 && (
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {allHosts.map((host) => (
            <HostCard key={host.id} host={host} />
          ))}
        </div>
      )}

      {/* Empty State */}
      {!isLoading && allHosts.length === 0 && (
        <Card className="bg-muted/50">
          <CardContent className="flex min-h-[200px] flex-col items-center justify-center p-8 text-center">
            <p className="mb-2 text-muted-foreground">
              No hosts found matching your criteria.
            </p>
            <p className="text-sm text-muted-foreground/70">
              Try adjusting your filters or expanding your search area.
            </p>
          </CardContent>
        </Card>
      )}

      {/* Infinite Scroll Trigger */}
      {hasMore && (
        <div
          ref={loadMoreRef}
          className="mt-6 flex items-center justify-center p-8"
        >
          {isFetching ? (
            <div className="flex items-center gap-2 text-muted-foreground">
              <Loader2 className="h-5 w-5 animate-spin" />
              Loading more hosts...
            </div>
          ) : (
            <Button onClick={handleLoadMore} variant="outline">
              Load more
            </Button>
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
      className="group no-underline"
    >
      <Card className="overflow-hidden transition-all duration-200 hover:-translate-y-1 hover:shadow-lg">
        {/* Photo placeholder */}
        <div className="relative flex h-40 items-center justify-center bg-muted">
          <span className="text-5xl text-muted-foreground/50">
            👤
          </span>

          {/* Verified badge */}
          {host.verification_status === 'verified' && (
            <Badge className="absolute right-3 top-3 bg-green-600 hover:bg-green-600">
              <Check className="mr-1 h-3 w-3" />
              Verified
            </Badge>
          )}
        </div>

        {/* Content */}
        <CardContent className="p-4">
          {/* Name */}
          <h3 className="mb-1 text-lg font-semibold text-foreground group-hover:text-primary">
            {host.first_name} {host.last_name}
          </h3>

          {/* Headline */}
          {host.headline && (
            <p className="mb-3 truncate text-sm text-muted-foreground">
              {host.headline}
            </p>
          )}

          {/* Rating and Reviews */}
          <div className="mb-2 flex items-center gap-2">
            <span className="flex items-center gap-1 text-sm font-semibold text-foreground">
              <Star className="h-4 w-4 fill-amber-400 text-amber-400" />
              {formatRating(host.rating_average)}
            </span>
            <span className="text-sm text-muted-foreground">
              ({host.total_reviews} review{host.total_reviews !== 1 ? 's' : ''})
            </span>
          </div>

          {/* Price and Distance */}
          <div className="flex items-center justify-between">
            <span className="text-base font-bold text-primary">
              {formatPrice(host.hourly_rate_cents)}
            </span>

            {host.distance_km !== null && host.distance_km !== undefined && (
              <span className="flex items-center gap-1 text-sm text-muted-foreground">
                <MapPin className="h-3 w-3" />
                {host.distance_km < 1
                  ? `${(host.distance_km * 1000).toFixed(0)}m`
                  : `${host.distance_km.toFixed(1)}km`}
              </span>
            )}
          </div>
        </CardContent>
      </Card>
    </Link>
  )
}
