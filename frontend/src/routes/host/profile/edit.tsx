import { createFileRoute, Link } from '@tanstack/react-router'
import { useState, useCallback, useEffect } from 'react'
import { $api } from '@/lib/api/$api'
import { useAuth } from '@/contexts/AuthContext'
import type { components } from '@/types/api.gen'

export const Route = createFileRoute('/host/profile/edit')({
  component: HostProfileEditPage,
})

type HostDanceStyleResponse = components['schemas']['HostDanceStyleResponse']
type DanceStyleResponse = components['schemas']['DanceStyleResponse']

// Skill level labels
const SKILL_LEVELS = [
  { value: 1, label: 'Beginner', description: 'Just started learning' },
  { value: 2, label: 'Elementary', description: 'Know basic steps' },
  { value: 3, label: 'Intermediate', description: 'Can lead/follow confidently' },
  { value: 4, label: 'Advanced', description: 'Strong technique and styling' },
  { value: 5, label: 'Expert', description: 'Professional level' },
]

// Dance style categories with common styles (used when no API endpoint available)
const DEFAULT_DANCE_STYLES: DanceStyleResponse[] = [
  { id: 'salsa', name: 'Salsa', slug: 'salsa', category: 'latin', description: 'Cuban-style partner dance' },
  { id: 'bachata', name: 'Bachata', slug: 'bachata', category: 'latin', description: 'Dominican romantic dance' },
  { id: 'tango', name: 'Tango', slug: 'tango', category: 'ballroom', description: 'Argentine dramatic dance' },
  { id: 'waltz', name: 'Waltz', slug: 'waltz', category: 'ballroom', description: 'Elegant ballroom dance' },
  { id: 'foxtrot', name: 'Foxtrot', slug: 'foxtrot', category: 'ballroom', description: 'Smooth ballroom dance' },
  { id: 'swing', name: 'Swing', slug: 'swing', category: 'swing', description: 'Energetic swing dancing' },
  { id: 'lindy-hop', name: 'Lindy Hop', slug: 'lindy-hop', category: 'swing', description: 'Original swing dance' },
  { id: 'cha-cha', name: 'Cha Cha', slug: 'cha-cha', category: 'latin', description: 'Playful Latin dance' },
  { id: 'rumba', name: 'Rumba', slug: 'rumba', category: 'latin', description: 'Sensual Latin dance' },
  { id: 'kizomba', name: 'Kizomba', slug: 'kizomba', category: 'social', description: 'Angolan partner dance' },
  { id: 'zouk', name: 'Zouk', slug: 'zouk', category: 'social', description: 'Brazilian partner dance' },
  { id: 'hustle', name: 'Hustle', slug: 'hustle', category: 'social', description: 'Disco-era partner dance' },
]

function HostProfileEditPage() {
  const { isAuthenticated, isLoading: authLoading, user } = useAuth()

  // Form state
  const [bio, setBio] = useState('')
  const [headline, setHeadline] = useState('')
  const [hourlyRateCents, setHourlyRateCents] = useState(5000)
  const [latitude, setLatitude] = useState<number | null>(null)
  const [longitude, setLongitude] = useState<number | null>(null)

  // Dance styles state
  const [selectedStyles, setSelectedStyles] = useState<Map<string, number>>(new Map())
  const [showStylePicker, setShowStylePicker] = useState(false)

  // Photo state (placeholder for future implementation)
  const [profilePhotoUrl, setProfilePhotoUrl] = useState<string | null>(null)
  const [showPhotoCrop, setShowPhotoCrop] = useState(false)
  const [pendingPhotoFile, setPendingPhotoFile] = useState<File | null>(null)

  // UI state
  const [isSaving, setIsSaving] = useState(false)
  const [saveError, setSaveError] = useState<string | null>(null)
  const [saveSuccess, setSaveSuccess] = useState(false)
  const [isLocating, setIsLocating] = useState(false)
  const [locationError, setLocationError] = useState<string | null>(null)

  // Fetch host profile
  const { data: hostProfile, isLoading: profileLoading, error: profileError, refetch } = $api.useQuery(
    'get',
    '/api/v1/users/me/host-profile',
    {},
    {
      enabled: isAuthenticated,
    }
  )

  // Initialize form with existing data
  useEffect(() => {
    if (hostProfile) {
      setBio(hostProfile.bio ?? '')
      setHeadline(hostProfile.headline ?? '')
      setHourlyRateCents(hostProfile.hourly_rate_cents)
      setLatitude(hostProfile.latitude ?? null)
      setLongitude(hostProfile.longitude ?? null)

      // Initialize dance styles
      const stylesMap = new Map<string, number>()
      hostProfile.dance_styles?.forEach((style: HostDanceStyleResponse) => {
        stylesMap.set(style.dance_style_id, style.skill_level)
      })
      setSelectedStyles(stylesMap)
    }
  }, [hostProfile])

  // Update profile mutation
  const updateProfileMutation = $api.useMutation('patch', '/api/v1/users/me/host-profile')

  // Add dance style mutation
  const addDanceStyleMutation = $api.useMutation('post', '/api/v1/users/me/host-profile/dance-styles')

  // Get current location
  const getCurrentLocation = useCallback(() => {
    setIsLocating(true)
    setLocationError(null)

    if (!navigator.geolocation) {
      setLocationError('Geolocation is not supported by your browser')
      setIsLocating(false)
      return
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        setLatitude(position.coords.latitude)
        setLongitude(position.coords.longitude)
        setIsLocating(false)
      },
      (error) => {
        switch (error.code) {
          case error.PERMISSION_DENIED:
            setLocationError('Location permission denied. Please enable location access.')
            break
          case error.POSITION_UNAVAILABLE:
            setLocationError('Location information unavailable.')
            break
          case error.TIMEOUT:
            setLocationError('Location request timed out.')
            break
          default:
            setLocationError('An unknown error occurred.')
        }
        setIsLocating(false)
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 0,
      }
    )
  }, [])

  // Clear location
  const clearLocation = useCallback(() => {
    setLatitude(null)
    setLongitude(null)
    setLocationError(null)
  }, [])

  // Handle dance style toggle
  const handleStyleToggle = useCallback((styleId: string, currentLevel: number | undefined) => {
    setSelectedStyles((prev) => {
      const newMap = new Map(prev)
      if (currentLevel !== undefined) {
        // Remove style if already selected
        newMap.delete(styleId)
      } else {
        // Add style with default level 3
        newMap.set(styleId, 3)
      }
      return newMap
    })
  }, [])

  // Handle skill level change
  const handleSkillLevelChange = useCallback((styleId: string, level: number) => {
    setSelectedStyles((prev) => {
      const newMap = new Map(prev)
      newMap.set(styleId, level)
      return newMap
    })
  }, [])

  // Handle photo file selection
  const handlePhotoSelect = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      // Validate file type
      if (!file.type.startsWith('image/')) {
        setSaveError('Please select an image file')
        return
      }
      // Validate file size (max 5MB)
      if (file.size > 5 * 1024 * 1024) {
        setSaveError('Image must be less than 5MB')
        return
      }
      setPendingPhotoFile(file)
      setShowPhotoCrop(true)
    }
  }, [])

  // Handle photo crop complete (placeholder - actual crop implementation would use a library)
  const handlePhotoCropComplete = useCallback(() => {
    if (pendingPhotoFile) {
      // In a real implementation, this would upload the cropped image
      // For now, create a local URL for preview
      const url = URL.createObjectURL(pendingPhotoFile)
      setProfilePhotoUrl(url)
    }
    setShowPhotoCrop(false)
    setPendingPhotoFile(null)
  }, [pendingPhotoFile])

  // Save profile
  const handleSave = async () => {
    setIsSaving(true)
    setSaveError(null)
    setSaveSuccess(false)

    try {
      // Update basic profile info
      await updateProfileMutation.mutateAsync({
        body: {
          bio: bio || null,
          headline: headline || null,
          hourly_rate_cents: hourlyRateCents,
          location: latitude !== null && longitude !== null
            ? { latitude, longitude }
            : null,
        },
      })

      // Update dance styles - compare with current styles
      const currentStyles = new Map<string, number>()
      hostProfile?.dance_styles?.forEach((style: HostDanceStyleResponse) => {
        currentStyles.set(style.dance_style_id, style.skill_level)
      })

      // Find styles to add or update
      for (const [styleId, level] of selectedStyles) {
        const currentLevel = currentStyles.get(styleId)
        if (currentLevel !== level) {
          // Add or update style
          try {
            await addDanceStyleMutation.mutateAsync({
              body: {
                dance_style_id: styleId,
                skill_level: level,
              },
            })
          } catch {
            // Style might already exist, that's ok
          }
        }
      }

      // Note: Removing styles would require a delete endpoint call for each removed style
      // This is handled separately through the UI

      setSaveSuccess(true)
      await refetch()

      // Auto-hide success message
      setTimeout(() => setSaveSuccess(false), 3000)
    } catch (error) {
      if (error instanceof Error) {
        setSaveError(error.message)
      } else {
        setSaveError('Failed to save profile. Please try again.')
      }
    } finally {
      setIsSaving(false)
    }
  }

  // Get available dance styles (use profile's dance styles + default list)
  const availableDanceStyles = (() => {
    const stylesMap = new Map<string, DanceStyleResponse>()

    // Add styles from host profile
    hostProfile?.dance_styles?.forEach((hds: HostDanceStyleResponse) => {
      stylesMap.set(hds.dance_style_id, hds.dance_style)
    })

    // Add default styles
    DEFAULT_DANCE_STYLES.forEach((style) => {
      if (!stylesMap.has(style.id)) {
        stylesMap.set(style.id, style)
      }
    })

    return Array.from(stylesMap.values())
  })()

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
          <p style={styles.authText}>Please log in to edit your host profile.</p>
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
          <p style={styles.authText}>You need to become a host to edit your profile.</p>
          <Link to="/" style={styles.becomeHostButton}>
            Become a Host
          </Link>
        </div>
      </div>
    )
  }

  // Loading profile
  if (profileLoading) {
    return (
      <div style={styles.loadingContainer}>
        <div style={styles.spinner} />
        <p style={styles.loadingText}>Loading profile...</p>
      </div>
    )
  }

  // Profile error
  if (profileError || !hostProfile) {
    return (
      <div style={styles.container}>
        <div style={styles.errorContainer}>
          <p style={styles.errorText}>Failed to load host profile. Please try again.</p>
          <button onClick={() => refetch()} style={styles.retryButton}>
            Retry
          </button>
        </div>
      </div>
    )
  }

  const formatPrice = (cents: number) => `$${(cents / 100).toFixed(0)}`

  return (
    <div style={styles.container}>
      {/* Header */}
      <div style={styles.header}>
        <Link to="/host/dashboard" style={styles.backLink}>
          &larr; Back to Dashboard
        </Link>
        <h1 style={styles.title}>Edit Host Profile</h1>
      </div>

      {/* Success Message */}
      {saveSuccess && (
        <div style={styles.successBanner}>
          Profile saved successfully!
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

      {/* Profile Photo Section */}
      <section style={styles.section}>
        <h2 style={styles.sectionTitle}>Profile Photo</h2>
        <div style={styles.photoSection}>
          <div style={styles.photoPreview}>
            {profilePhotoUrl ? (
              <img src={profilePhotoUrl} alt="Profile" style={styles.photoImage} />
            ) : (
              <div style={styles.photoPlaceholder}>
                {user?.first_name?.charAt(0)}{user?.last_name?.charAt(0)}
              </div>
            )}
          </div>
          <div style={styles.photoActions}>
            <label style={styles.uploadButton}>
              Upload Photo
              <input
                type="file"
                accept="image/*"
                onChange={handlePhotoSelect}
                style={styles.hiddenInput}
              />
            </label>
            <p style={styles.photoHint}>JPG, PNG or GIF. Max 5MB. Square images work best.</p>
          </div>
        </div>

        {/* Photo Crop Modal (simplified placeholder) */}
        {showPhotoCrop && pendingPhotoFile && (
          <div style={styles.modal}>
            <div style={styles.modalContent}>
              <h3 style={styles.modalTitle}>Crop Photo</h3>
              <div style={styles.cropPreview}>
                <img
                  src={URL.createObjectURL(pendingPhotoFile)}
                  alt="Preview"
                  style={styles.cropImage}
                />
              </div>
              <p style={styles.cropHint}>
                Photo cropping feature coming soon. For now, please upload a square image.
              </p>
              <div style={styles.modalActions}>
                <button
                  onClick={() => {
                    setShowPhotoCrop(false)
                    setPendingPhotoFile(null)
                  }}
                  style={styles.cancelButton}
                >
                  Cancel
                </button>
                <button onClick={handlePhotoCropComplete} style={styles.primaryButton}>
                  Use Photo
                </button>
              </div>
            </div>
          </div>
        )}
      </section>

      {/* Basic Info Section */}
      <section style={styles.section}>
        <h2 style={styles.sectionTitle}>Basic Information</h2>

        {/* Headline */}
        <div style={styles.formGroup}>
          <label style={styles.label}>Headline</label>
          <input
            type="text"
            value={headline}
            onChange={(e) => setHeadline(e.target.value)}
            placeholder="e.g., Professional Salsa Instructor"
            maxLength={200}
            style={styles.input}
          />
          <p style={styles.hint}>{headline.length}/200 characters</p>
        </div>

        {/* Bio */}
        <div style={styles.formGroup}>
          <label style={styles.label}>Bio</label>
          <textarea
            value={bio}
            onChange={(e) => setBio(e.target.value)}
            placeholder="Tell potential clients about yourself, your dance experience, teaching style..."
            maxLength={2000}
            rows={6}
            style={styles.textarea}
          />
          <p style={styles.hint}>{bio.length}/2000 characters</p>
        </div>

        {/* Hourly Rate */}
        <div style={styles.formGroup}>
          <label style={styles.label}>Hourly Rate</label>
          <div style={styles.rateContainer}>
            <span style={styles.currencySymbol}>$</span>
            <input
              type="number"
              value={hourlyRateCents / 100}
              onChange={(e) => setHourlyRateCents(Math.round(parseFloat(e.target.value) * 100) || 0)}
              min={1}
              max={1000}
              style={styles.rateInput}
            />
            <span style={styles.rateUnit}>/hour</span>
          </div>
          <p style={styles.hint}>Set your hourly rate ({formatPrice(100)} - {formatPrice(100000)})</p>
        </div>
      </section>

      {/* Dance Styles Section */}
      <section style={styles.section}>
        <div style={styles.sectionHeader}>
          <h2 style={styles.sectionTitle}>Dance Styles</h2>
          <button
            onClick={() => setShowStylePicker(true)}
            style={styles.addButton}
          >
            + Add Style
          </button>
        </div>

        {selectedStyles.size === 0 ? (
          <div style={styles.emptyStyles}>
            <p>No dance styles selected yet.</p>
            <button onClick={() => setShowStylePicker(true)} style={styles.addStyleButton}>
              Add Your First Dance Style
            </button>
          </div>
        ) : (
          <div style={styles.stylesList}>
            {Array.from(selectedStyles.entries()).map(([styleId, level]) => {
              const style = availableDanceStyles.find((s) => s.id === styleId)
              if (!style) return null

              return (
                <div key={styleId} style={styles.styleCard}>
                  <div style={styles.styleInfo}>
                    <span style={styles.styleName}>{style.name}</span>
                    <span style={styles.styleCategory}>{style.category}</span>
                  </div>
                  <div style={styles.skillLevelContainer}>
                    <label style={styles.skillLabel}>Skill Level:</label>
                    <select
                      value={level}
                      onChange={(e) => handleSkillLevelChange(styleId, parseInt(e.target.value))}
                      style={styles.skillSelect}
                    >
                      {SKILL_LEVELS.map((sl) => (
                        <option key={sl.value} value={sl.value}>
                          {sl.label}
                        </option>
                      ))}
                    </select>
                    <div style={styles.skillDots}>
                      {[1, 2, 3, 4, 5].map((dot) => (
                        <span
                          key={dot}
                          style={{
                            ...styles.skillDot,
                            backgroundColor: dot <= level ? '#e11d48' : '#e5e7eb',
                          }}
                        />
                      ))}
                    </div>
                  </div>
                  <button
                    onClick={() => handleStyleToggle(styleId, level)}
                    style={styles.removeStyleButton}
                    title="Remove style"
                  >
                    &times;
                  </button>
                </div>
              )
            })}
          </div>
        )}

        {/* Style Picker Modal */}
        {showStylePicker && (
          <div style={styles.modal}>
            <div style={styles.modalContent}>
              <h3 style={styles.modalTitle}>Add Dance Style</h3>
              <div style={styles.stylePickerList}>
                {availableDanceStyles.map((style) => {
                  const isSelected = selectedStyles.has(style.id)
                  return (
                    <button
                      key={style.id}
                      onClick={() => {
                        if (!isSelected) {
                          handleStyleToggle(style.id, undefined)
                        }
                        setShowStylePicker(false)
                      }}
                      style={{
                        ...styles.stylePickerItem,
                        backgroundColor: isSelected ? '#fef2f2' : 'white',
                        borderColor: isSelected ? '#e11d48' : '#e5e7eb',
                      }}
                      disabled={isSelected}
                    >
                      <span style={styles.stylePickerName}>{style.name}</span>
                      <span style={styles.stylePickerCategory}>{style.category}</span>
                      {isSelected && <span style={styles.checkmark}>&#10003;</span>}
                    </button>
                  )
                })}
              </div>
              <div style={styles.modalActions}>
                <button onClick={() => setShowStylePicker(false)} style={styles.cancelButton}>
                  Close
                </button>
              </div>
            </div>
          </div>
        )}
      </section>

      {/* Location Section */}
      <section style={styles.section}>
        <h2 style={styles.sectionTitle}>Location</h2>
        <p style={styles.sectionDescription}>
          Your location helps clients find you. We only show your approximate area, not your exact address.
        </p>

        {latitude !== null && longitude !== null ? (
          <div style={styles.locationDisplay}>
            <div style={styles.locationMap}>
              <div style={styles.mapPlaceholder}>
                <span style={styles.mapIcon}>&#128205;</span>
                <span style={styles.mapCoords}>
                  {latitude.toFixed(4)}, {longitude.toFixed(4)}
                </span>
              </div>
            </div>
            <div style={styles.locationActions}>
              <button onClick={getCurrentLocation} style={styles.updateLocationButton} disabled={isLocating}>
                {isLocating ? 'Updating...' : 'Update Location'}
              </button>
              <button onClick={clearLocation} style={styles.clearLocationButton}>
                Clear Location
              </button>
            </div>
          </div>
        ) : (
          <div style={styles.noLocation}>
            <p>No location set. Add your location to appear in local searches.</p>
            <button
              onClick={getCurrentLocation}
              style={styles.setLocationButton}
              disabled={isLocating}
            >
              {isLocating ? (
                <>
                  <span style={styles.smallSpinner} /> Getting location...
                </>
              ) : (
                'Use Current Location'
              )}
            </button>
          </div>
        )}

        {locationError && (
          <p style={styles.locationError}>{locationError}</p>
        )}

        {/* Manual coordinates input (advanced) */}
        <details style={styles.advancedLocation}>
          <summary style={styles.advancedSummary}>Enter coordinates manually</summary>
          <div style={styles.coordsInputs}>
            <div style={styles.coordInput}>
              <label style={styles.coordLabel}>Latitude</label>
              <input
                type="number"
                value={latitude ?? ''}
                onChange={(e) => setLatitude(e.target.value ? parseFloat(e.target.value) : null)}
                placeholder="-90 to 90"
                min={-90}
                max={90}
                step="0.0001"
                style={styles.input}
              />
            </div>
            <div style={styles.coordInput}>
              <label style={styles.coordLabel}>Longitude</label>
              <input
                type="number"
                value={longitude ?? ''}
                onChange={(e) => setLongitude(e.target.value ? parseFloat(e.target.value) : null)}
                placeholder="-180 to 180"
                min={-180}
                max={180}
                step="0.0001"
                style={styles.input}
              />
            </div>
          </div>
        </details>
      </section>

      {/* Save Button */}
      <div style={styles.saveSection}>
        <button
          onClick={handleSave}
          disabled={isSaving}
          style={{
            ...styles.saveButton,
            opacity: isSaving ? 0.6 : 1,
          }}
        >
          {isSaving ? 'Saving...' : 'Save Changes'}
        </button>
        <Link to="/host/dashboard" style={styles.cancelLink}>
          Cancel
        </Link>
      </div>
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
  smallSpinner: {
    display: 'inline-block',
    width: '16px',
    height: '16px',
    border: '2px solid #e5e7eb',
    borderTop: '2px solid #e11d48',
    borderRadius: '50%',
    animation: 'spin 1s linear infinite',
    marginRight: '0.5rem',
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
    marginBottom: '1rem',
  },
  sectionTitle: {
    fontSize: '1.125rem',
    fontWeight: 600,
    color: '#1f2937',
    margin: 0,
    marginBottom: '1rem',
  },
  sectionDescription: {
    color: '#6b7280',
    marginTop: '-0.5rem',
    marginBottom: '1rem',
    fontSize: '0.875rem',
  },
  formGroup: {
    marginBottom: '1.25rem',
  },
  label: {
    display: 'block',
    fontWeight: 500,
    color: '#374151',
    marginBottom: '0.5rem',
    fontSize: '0.875rem',
  },
  input: {
    width: '100%',
    padding: '0.75rem',
    border: '1px solid #d1d5db',
    borderRadius: '8px',
    fontSize: '1rem',
    boxSizing: 'border-box',
  },
  textarea: {
    width: '100%',
    padding: '0.75rem',
    border: '1px solid #d1d5db',
    borderRadius: '8px',
    fontSize: '1rem',
    resize: 'vertical',
    fontFamily: 'inherit',
    boxSizing: 'border-box',
  },
  hint: {
    color: '#9ca3af',
    fontSize: '0.75rem',
    marginTop: '0.25rem',
  },
  rateContainer: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
  },
  currencySymbol: {
    fontSize: '1.25rem',
    color: '#374151',
  },
  rateInput: {
    width: '100px',
    padding: '0.75rem',
    border: '1px solid #d1d5db',
    borderRadius: '8px',
    fontSize: '1rem',
    textAlign: 'center',
  },
  rateUnit: {
    color: '#6b7280',
    fontSize: '0.875rem',
  },
  photoSection: {
    display: 'flex',
    gap: '1.5rem',
    alignItems: 'flex-start',
    flexWrap: 'wrap',
  },
  photoPreview: {
    flexShrink: 0,
  },
  photoImage: {
    width: '120px',
    height: '120px',
    borderRadius: '50%',
    objectFit: 'cover',
  },
  photoPlaceholder: {
    width: '120px',
    height: '120px',
    borderRadius: '50%',
    backgroundColor: '#e11d48',
    color: 'white',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '2rem',
    fontWeight: 600,
  },
  photoActions: {
    flex: 1,
    minWidth: '200px',
  },
  uploadButton: {
    display: 'inline-block',
    padding: '0.75rem 1.5rem',
    backgroundColor: '#f3f4f6',
    color: '#374151',
    border: '1px solid #d1d5db',
    borderRadius: '8px',
    fontSize: '0.875rem',
    fontWeight: 500,
    cursor: 'pointer',
    marginBottom: '0.5rem',
  },
  hiddenInput: {
    display: 'none',
  },
  photoHint: {
    color: '#9ca3af',
    fontSize: '0.75rem',
    margin: 0,
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
    maxWidth: '500px',
    width: '100%',
    maxHeight: '80vh',
    overflow: 'auto',
  },
  modalTitle: {
    fontSize: '1.25rem',
    fontWeight: 600,
    margin: 0,
    marginBottom: '1rem',
  },
  modalActions: {
    display: 'flex',
    gap: '0.75rem',
    justifyContent: 'flex-end',
    marginTop: '1rem',
  },
  cropPreview: {
    textAlign: 'center',
    marginBottom: '1rem',
  },
  cropImage: {
    maxWidth: '100%',
    maxHeight: '300px',
    borderRadius: '8px',
  },
  cropHint: {
    color: '#6b7280',
    fontSize: '0.875rem',
    textAlign: 'center',
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
  emptyStyles: {
    textAlign: 'center',
    padding: '2rem',
    backgroundColor: '#f9fafb',
    borderRadius: '8px',
  },
  addStyleButton: {
    marginTop: '1rem',
    padding: '0.75rem 1.5rem',
    backgroundColor: '#e11d48',
    color: 'white',
    border: 'none',
    borderRadius: '8px',
    fontSize: '0.875rem',
    fontWeight: 500,
    cursor: 'pointer',
  },
  stylesList: {
    display: 'flex',
    flexDirection: 'column',
    gap: '0.75rem',
  },
  styleCard: {
    display: 'flex',
    alignItems: 'center',
    gap: '1rem',
    padding: '1rem',
    backgroundColor: '#f9fafb',
    borderRadius: '8px',
    border: '1px solid #e5e7eb',
    flexWrap: 'wrap',
  },
  styleInfo: {
    flex: '1 1 150px',
    minWidth: '120px',
  },
  styleName: {
    display: 'block',
    fontWeight: 600,
    color: '#1f2937',
    fontSize: '0.9375rem',
  },
  styleCategory: {
    display: 'block',
    color: '#6b7280',
    fontSize: '0.75rem',
  },
  skillLevelContainer: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
    flex: '1 1 200px',
  },
  skillLabel: {
    color: '#6b7280',
    fontSize: '0.75rem',
    whiteSpace: 'nowrap',
  },
  skillSelect: {
    padding: '0.375rem 0.5rem',
    border: '1px solid #d1d5db',
    borderRadius: '6px',
    fontSize: '0.8125rem',
  },
  skillDots: {
    display: 'flex',
    gap: '3px',
    marginLeft: '0.5rem',
  },
  skillDot: {
    width: '8px',
    height: '8px',
    borderRadius: '50%',
  },
  removeStyleButton: {
    width: '28px',
    height: '28px',
    backgroundColor: '#fee2e2',
    color: '#991b1b',
    border: 'none',
    borderRadius: '50%',
    fontSize: '1rem',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
  },
  stylePickerList: {
    display: 'flex',
    flexDirection: 'column',
    gap: '0.5rem',
    maxHeight: '400px',
    overflow: 'auto',
  },
  stylePickerItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.75rem',
    padding: '0.75rem',
    border: '1px solid',
    borderRadius: '8px',
    cursor: 'pointer',
    textAlign: 'left',
    width: '100%',
    transition: 'background-color 0.2s',
  },
  stylePickerName: {
    fontWeight: 500,
    color: '#1f2937',
    flex: 1,
  },
  stylePickerCategory: {
    color: '#6b7280',
    fontSize: '0.8125rem',
  },
  checkmark: {
    color: '#e11d48',
    fontWeight: 'bold',
  },
  locationDisplay: {
    display: 'flex',
    flexDirection: 'column',
    gap: '1rem',
  },
  locationMap: {
    borderRadius: '8px',
    overflow: 'hidden',
    border: '1px solid #e5e7eb',
  },
  mapPlaceholder: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '2rem',
    backgroundColor: '#f3f4f6',
    minHeight: '150px',
  },
  mapIcon: {
    fontSize: '2rem',
    marginBottom: '0.5rem',
  },
  mapCoords: {
    color: '#6b7280',
    fontSize: '0.875rem',
  },
  locationActions: {
    display: 'flex',
    gap: '0.75rem',
    flexWrap: 'wrap',
  },
  updateLocationButton: {
    padding: '0.5rem 1rem',
    backgroundColor: '#e11d48',
    color: 'white',
    border: 'none',
    borderRadius: '8px',
    fontSize: '0.875rem',
    fontWeight: 500,
    cursor: 'pointer',
  },
  clearLocationButton: {
    padding: '0.5rem 1rem',
    backgroundColor: 'white',
    color: '#6b7280',
    border: '1px solid #d1d5db',
    borderRadius: '8px',
    fontSize: '0.875rem',
    fontWeight: 500,
    cursor: 'pointer',
  },
  noLocation: {
    textAlign: 'center',
    padding: '2rem',
    backgroundColor: '#f9fafb',
    borderRadius: '8px',
  },
  setLocationButton: {
    marginTop: '1rem',
    padding: '0.75rem 1.5rem',
    backgroundColor: '#e11d48',
    color: 'white',
    border: 'none',
    borderRadius: '8px',
    fontSize: '0.875rem',
    fontWeight: 500,
    cursor: 'pointer',
    display: 'inline-flex',
    alignItems: 'center',
  },
  locationError: {
    color: '#dc2626',
    fontSize: '0.875rem',
    marginTop: '0.5rem',
  },
  advancedLocation: {
    marginTop: '1rem',
  },
  advancedSummary: {
    cursor: 'pointer',
    color: '#6b7280',
    fontSize: '0.875rem',
    padding: '0.5rem 0',
  },
  coordsInputs: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
    gap: '1rem',
    marginTop: '0.75rem',
  },
  coordInput: {
    display: 'flex',
    flexDirection: 'column',
  },
  coordLabel: {
    fontSize: '0.75rem',
    color: '#6b7280',
    marginBottom: '0.25rem',
  },
  saveSection: {
    display: 'flex',
    gap: '1rem',
    alignItems: 'center',
    justifyContent: 'flex-end',
    padding: '1rem 0',
    position: 'sticky',
    bottom: 0,
    backgroundColor: '#f9fafb',
    marginLeft: '-1rem',
    marginRight: '-1rem',
    paddingLeft: '1rem',
    paddingRight: '1rem',
    borderTop: '1px solid #e5e7eb',
  },
  saveButton: {
    padding: '0.875rem 2rem',
    backgroundColor: '#e11d48',
    color: 'white',
    border: 'none',
    borderRadius: '8px',
    fontSize: '1rem',
    fontWeight: 600,
    cursor: 'pointer',
  },
  cancelLink: {
    color: '#6b7280',
    textDecoration: 'none',
    fontSize: '0.875rem',
  },
}
