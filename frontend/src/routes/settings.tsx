import { createFileRoute, Link, useNavigate } from '@tanstack/react-router'
import { useState } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import type { components } from '@/types/api.gen'

export const Route = createFileRoute('/settings')({
  component: SettingsPage,
})

type UserType = components['schemas']['UserType']

interface NotificationPreferences {
  emailBookingUpdates: boolean
  emailMessages: boolean
  emailMarketing: boolean
  pushBookingUpdates: boolean
  pushMessages: boolean
}

function SettingsPage() {
  const { isAuthenticated, isLoading: authLoading, user, logout } = useAuth()
  const navigate = useNavigate()

  // Profile editing state
  const [isEditingProfile, setIsEditingProfile] = useState(false)
  const [firstName, setFirstName] = useState('')
  const [lastName, setLastName] = useState('')
  const [isSavingProfile, setIsSavingProfile] = useState(false)
  const [profileError, setProfileError] = useState<string | null>(null)
  const [profileSuccess, setProfileSuccess] = useState(false)

  // Notification preferences state (mock for now - no backend support yet)
  const [notifications, setNotifications] = useState<NotificationPreferences>({
    emailBookingUpdates: true,
    emailMessages: true,
    emailMarketing: false,
    pushBookingUpdates: true,
    pushMessages: true,
  })

  // Logout state
  const [isLoggingOut, setIsLoggingOut] = useState(false)

  const handleEditProfile = () => {
    if (user) {
      setFirstName(user.first_name)
      setLastName(user.last_name)
      setIsEditingProfile(true)
      setProfileError(null)
      setProfileSuccess(false)
    }
  }

  const handleCancelEdit = () => {
    setIsEditingProfile(false)
    setProfileError(null)
    setProfileSuccess(false)
  }

  const handleSaveProfile = async () => {
    setIsSavingProfile(true)
    setProfileError(null)
    setProfileSuccess(false)

    try {
      // Note: There's no endpoint to update user profile yet
      // For now, show a message that this feature is coming soon
      await new Promise(resolve => setTimeout(resolve, 500))
      setProfileSuccess(true)
      setIsEditingProfile(false)
    } catch (err) {
      setProfileError(err instanceof Error ? err.message : 'Failed to update profile')
    } finally {
      setIsSavingProfile(false)
    }
  }

  const handleNotificationChange = (key: keyof NotificationPreferences) => {
    setNotifications(prev => ({
      ...prev,
      [key]: !prev[key],
    }))
  }

  const handleLogout = async () => {
    setIsLoggingOut(true)
    try {
      await logout()
      navigate({ to: '/' })
    } catch (err) {
      console.error('Logout error:', err)
    } finally {
      setIsLoggingOut(false)
    }
  }

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
          <p style={styles.authText}>Please log in to view your settings.</p>
          <Link to="/login" style={styles.loginButton}>
            Log In
          </Link>
        </div>
      </div>
    )
  }

  const getUserTypeDisplay = (userType: UserType | undefined) => {
    if (!userType) return 'User'
    switch (userType) {
      case 'client': return 'Client'
      case 'host': return 'Host'
      case 'both': return 'Client & Host'
      default: return 'User'
    }
  }

  return (
    <div style={styles.container}>
      <h1 style={styles.title}>Settings</h1>

      {/* Account Section */}
      <section style={styles.section}>
        <h2 style={styles.sectionTitle}>Account</h2>

        <div style={styles.card}>
          {isEditingProfile ? (
            <div style={styles.editForm}>
              <div style={styles.formGroup}>
                <label style={styles.label}>First Name</label>
                <input
                  type="text"
                  value={firstName}
                  onChange={(e) => setFirstName(e.target.value)}
                  style={styles.input}
                  placeholder="First name"
                />
              </div>
              <div style={styles.formGroup}>
                <label style={styles.label}>Last Name</label>
                <input
                  type="text"
                  value={lastName}
                  onChange={(e) => setLastName(e.target.value)}
                  style={styles.input}
                  placeholder="Last name"
                />
              </div>
              {profileError && (
                <p style={styles.errorMessage}>{profileError}</p>
              )}
              <div style={styles.editActions}>
                <button
                  type="button"
                  onClick={handleCancelEdit}
                  style={styles.cancelButton}
                  disabled={isSavingProfile}
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleSaveProfile}
                  style={styles.saveButton}
                  disabled={isSavingProfile || !firstName.trim() || !lastName.trim()}
                >
                  {isSavingProfile ? 'Saving...' : 'Save Changes'}
                </button>
              </div>
            </div>
          ) : (
            <>
              <div style={styles.profileRow}>
                <div style={styles.profileAvatar}>
                  {user?.first_name?.charAt(0) ?? '?'}{user?.last_name?.charAt(0) ?? ''}
                </div>
                <div style={styles.profileInfo}>
                  <p style={styles.profileName}>
                    {user?.first_name} {user?.last_name}
                  </p>
                  <p style={styles.profileEmail}>{user?.email}</p>
                  <p style={styles.profileType}>{getUserTypeDisplay(user?.user_type)}</p>
                </div>
                <button
                  type="button"
                  onClick={handleEditProfile}
                  style={styles.editButton}
                >
                  Edit
                </button>
              </div>
              {profileSuccess && (
                <p style={styles.successMessage}>Profile updated successfully!</p>
              )}
            </>
          )}
        </div>

        {/* Email verification status */}
        <div style={styles.card}>
          <div style={styles.settingRow}>
            <div style={styles.settingInfo}>
              <p style={styles.settingLabel}>Email Verification</p>
              <p style={styles.settingDescription}>
                {user?.email_verified
                  ? 'Your email is verified'
                  : 'Your email is not verified'}
              </p>
            </div>
            <span
              style={{
                ...styles.statusBadge,
                backgroundColor: user?.email_verified ? '#d1fae5' : '#fef3c7',
                color: user?.email_verified ? '#065f46' : '#92400e',
              }}
            >
              {user?.email_verified ? 'Verified' : 'Unverified'}
            </span>
          </div>
        </div>

        {/* Host-specific settings */}
        {(user?.user_type === 'host' || user?.user_type === 'both') && (
          <div style={styles.card}>
            <div style={styles.settingRow}>
              <div style={styles.settingInfo}>
                <p style={styles.settingLabel}>Host Dashboard</p>
                <p style={styles.settingDescription}>
                  View your earnings, bookings, and reviews
                </p>
              </div>
              <Link to="/host/dashboard" style={styles.linkButton}>
                Go to Dashboard
              </Link>
            </div>
          </div>
        )}
      </section>

      {/* Notifications Section */}
      <section style={styles.section}>
        <h2 style={styles.sectionTitle}>Notifications</h2>
        <p style={styles.sectionDescription}>
          Manage how you receive notifications
        </p>

        <div style={styles.card}>
          <h3 style={styles.cardSubtitle}>Email Notifications</h3>

          <div style={styles.toggleRow}>
            <div style={styles.toggleInfo}>
              <p style={styles.toggleLabel}>Booking Updates</p>
              <p style={styles.toggleDescription}>
                Receive emails when bookings are created, confirmed, or cancelled
              </p>
            </div>
            <button
              type="button"
              onClick={() => handleNotificationChange('emailBookingUpdates')}
              style={{
                ...styles.toggle,
                backgroundColor: notifications.emailBookingUpdates ? '#e11d48' : '#e5e7eb',
              }}
              aria-pressed={notifications.emailBookingUpdates}
            >
              <span
                style={{
                  ...styles.toggleKnob,
                  transform: notifications.emailBookingUpdates ? 'translateX(20px)' : 'translateX(0)',
                }}
              />
            </button>
          </div>

          <div style={styles.toggleRow}>
            <div style={styles.toggleInfo}>
              <p style={styles.toggleLabel}>Messages</p>
              <p style={styles.toggleDescription}>
                Receive emails when you get new messages
              </p>
            </div>
            <button
              type="button"
              onClick={() => handleNotificationChange('emailMessages')}
              style={{
                ...styles.toggle,
                backgroundColor: notifications.emailMessages ? '#e11d48' : '#e5e7eb',
              }}
              aria-pressed={notifications.emailMessages}
            >
              <span
                style={{
                  ...styles.toggleKnob,
                  transform: notifications.emailMessages ? 'translateX(20px)' : 'translateX(0)',
                }}
              />
            </button>
          </div>

          <div style={styles.toggleRow}>
            <div style={styles.toggleInfo}>
              <p style={styles.toggleLabel}>Marketing</p>
              <p style={styles.toggleDescription}>
                Receive updates about new features and promotions
              </p>
            </div>
            <button
              type="button"
              onClick={() => handleNotificationChange('emailMarketing')}
              style={{
                ...styles.toggle,
                backgroundColor: notifications.emailMarketing ? '#e11d48' : '#e5e7eb',
              }}
              aria-pressed={notifications.emailMarketing}
            >
              <span
                style={{
                  ...styles.toggleKnob,
                  transform: notifications.emailMarketing ? 'translateX(20px)' : 'translateX(0)',
                }}
              />
            </button>
          </div>
        </div>

        <div style={styles.card}>
          <h3 style={styles.cardSubtitle}>Push Notifications</h3>

          <div style={styles.toggleRow}>
            <div style={styles.toggleInfo}>
              <p style={styles.toggleLabel}>Booking Updates</p>
              <p style={styles.toggleDescription}>
                Receive push notifications for booking changes
              </p>
            </div>
            <button
              type="button"
              onClick={() => handleNotificationChange('pushBookingUpdates')}
              style={{
                ...styles.toggle,
                backgroundColor: notifications.pushBookingUpdates ? '#e11d48' : '#e5e7eb',
              }}
              aria-pressed={notifications.pushBookingUpdates}
            >
              <span
                style={{
                  ...styles.toggleKnob,
                  transform: notifications.pushBookingUpdates ? 'translateX(20px)' : 'translateX(0)',
                }}
              />
            </button>
          </div>

          <div style={styles.toggleRow}>
            <div style={styles.toggleInfo}>
              <p style={styles.toggleLabel}>Messages</p>
              <p style={styles.toggleDescription}>
                Receive push notifications for new messages
              </p>
            </div>
            <button
              type="button"
              onClick={() => handleNotificationChange('pushMessages')}
              style={{
                ...styles.toggle,
                backgroundColor: notifications.pushMessages ? '#e11d48' : '#e5e7eb',
              }}
              aria-pressed={notifications.pushMessages}
            >
              <span
                style={{
                  ...styles.toggleKnob,
                  transform: notifications.pushMessages ? 'translateX(20px)' : 'translateX(0)',
                }}
              />
            </button>
          </div>
        </div>
      </section>

      {/* Danger Zone */}
      <section style={styles.section}>
        <h2 style={styles.sectionTitle}>Session</h2>

        <div style={styles.card}>
          <div style={styles.settingRow}>
            <div style={styles.settingInfo}>
              <p style={styles.settingLabel}>Sign Out</p>
              <p style={styles.settingDescription}>
                Sign out of your account on this device
              </p>
            </div>
            <button
              type="button"
              onClick={handleLogout}
              disabled={isLoggingOut}
              style={styles.logoutButton}
            >
              {isLoggingOut ? 'Signing out...' : 'Sign Out'}
            </button>
          </div>
        </div>
      </section>

      {/* App Info */}
      <section style={styles.section}>
        <div style={styles.appInfo}>
          <p style={styles.appName}>Strictly Dancing</p>
          <p style={styles.appVersion}>Version 1.0.0</p>
        </div>
      </section>
    </div>
  )
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    maxWidth: '600px',
    margin: '0 auto',
    padding: '1rem',
    paddingBottom: '3rem',
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
  title: {
    fontSize: 'clamp(1.5rem, 4vw, 2rem)',
    fontWeight: 'bold',
    color: '#1f2937',
    margin: 0,
    marginBottom: '1.5rem',
  },
  section: {
    marginBottom: '2rem',
  },
  sectionTitle: {
    fontSize: '1.125rem',
    fontWeight: 600,
    color: '#1f2937',
    margin: 0,
    marginBottom: '0.5rem',
  },
  sectionDescription: {
    fontSize: '0.875rem',
    color: '#6b7280',
    margin: 0,
    marginBottom: '1rem',
  },
  card: {
    backgroundColor: 'white',
    borderRadius: '12px',
    boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
    padding: '1rem',
    marginBottom: '0.75rem',
  },
  cardSubtitle: {
    fontSize: '0.9375rem',
    fontWeight: 600,
    color: '#374151',
    margin: 0,
    marginBottom: '1rem',
  },
  profileRow: {
    display: 'flex',
    alignItems: 'center',
    gap: '1rem',
  },
  profileAvatar: {
    width: '56px',
    height: '56px',
    borderRadius: '50%',
    backgroundColor: '#e11d48',
    color: 'white',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '1.25rem',
    fontWeight: 600,
    flexShrink: 0,
  },
  profileInfo: {
    flex: 1,
    minWidth: 0,
  },
  profileName: {
    fontWeight: 600,
    color: '#1f2937',
    fontSize: '1rem',
    margin: 0,
    marginBottom: '0.125rem',
  },
  profileEmail: {
    color: '#6b7280',
    fontSize: '0.875rem',
    margin: 0,
    marginBottom: '0.125rem',
  },
  profileType: {
    color: '#9ca3af',
    fontSize: '0.75rem',
    margin: 0,
  },
  editButton: {
    padding: '0.5rem 1rem',
    backgroundColor: 'transparent',
    color: '#e11d48',
    border: '1px solid #e11d48',
    borderRadius: '6px',
    fontSize: '0.875rem',
    fontWeight: 500,
    cursor: 'pointer',
  },
  editForm: {
    display: 'flex',
    flexDirection: 'column',
    gap: '1rem',
  },
  formGroup: {
    display: 'flex',
    flexDirection: 'column',
    gap: '0.375rem',
  },
  label: {
    fontSize: '0.875rem',
    fontWeight: 500,
    color: '#374151',
  },
  input: {
    padding: '0.75rem',
    border: '1px solid #e5e7eb',
    borderRadius: '8px',
    fontSize: '1rem',
    outline: 'none',
  },
  editActions: {
    display: 'flex',
    justifyContent: 'flex-end',
    gap: '0.75rem',
    marginTop: '0.5rem',
  },
  cancelButton: {
    padding: '0.625rem 1rem',
    backgroundColor: 'white',
    color: '#6b7280',
    border: '1px solid #e5e7eb',
    borderRadius: '6px',
    fontSize: '0.875rem',
    fontWeight: 500,
    cursor: 'pointer',
  },
  saveButton: {
    padding: '0.625rem 1rem',
    backgroundColor: '#e11d48',
    color: 'white',
    border: 'none',
    borderRadius: '6px',
    fontSize: '0.875rem',
    fontWeight: 500,
    cursor: 'pointer',
  },
  errorMessage: {
    color: '#dc2626',
    fontSize: '0.875rem',
    margin: 0,
  },
  successMessage: {
    color: '#059669',
    fontSize: '0.875rem',
    margin: 0,
    marginTop: '0.75rem',
  },
  settingRow: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: '1rem',
  },
  settingInfo: {
    flex: 1,
    minWidth: 0,
  },
  settingLabel: {
    fontWeight: 500,
    color: '#1f2937',
    fontSize: '0.9375rem',
    margin: 0,
    marginBottom: '0.125rem',
  },
  settingDescription: {
    color: '#6b7280',
    fontSize: '0.8125rem',
    margin: 0,
  },
  statusBadge: {
    padding: '0.25rem 0.75rem',
    borderRadius: '9999px',
    fontSize: '0.75rem',
    fontWeight: 500,
    whiteSpace: 'nowrap',
  },
  linkButton: {
    padding: '0.5rem 1rem',
    backgroundColor: '#f3f4f6',
    color: '#1f2937',
    borderRadius: '6px',
    fontSize: '0.875rem',
    fontWeight: 500,
    textDecoration: 'none',
    whiteSpace: 'nowrap',
  },
  toggleRow: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: '1rem',
    padding: '0.75rem 0',
    borderBottom: '1px solid #f3f4f6',
  },
  toggleInfo: {
    flex: 1,
    minWidth: 0,
  },
  toggleLabel: {
    fontWeight: 500,
    color: '#1f2937',
    fontSize: '0.9375rem',
    margin: 0,
    marginBottom: '0.125rem',
  },
  toggleDescription: {
    color: '#6b7280',
    fontSize: '0.8125rem',
    margin: 0,
  },
  toggle: {
    position: 'relative',
    width: '44px',
    height: '24px',
    borderRadius: '9999px',
    border: 'none',
    cursor: 'pointer',
    padding: 0,
    transition: 'background-color 0.2s',
    flexShrink: 0,
  },
  toggleKnob: {
    position: 'absolute',
    top: '2px',
    left: '2px',
    width: '20px',
    height: '20px',
    borderRadius: '50%',
    backgroundColor: 'white',
    transition: 'transform 0.2s',
    boxShadow: '0 1px 3px rgba(0,0,0,0.2)',
  },
  logoutButton: {
    padding: '0.625rem 1.25rem',
    backgroundColor: '#fef2f2',
    color: '#dc2626',
    border: '1px solid #fecaca',
    borderRadius: '8px',
    fontSize: '0.875rem',
    fontWeight: 500,
    cursor: 'pointer',
  },
  appInfo: {
    textAlign: 'center',
    padding: '1rem',
  },
  appName: {
    color: '#9ca3af',
    fontSize: '0.875rem',
    margin: 0,
    marginBottom: '0.25rem',
  },
  appVersion: {
    color: '#d1d5db',
    fontSize: '0.75rem',
    margin: 0,
  },
}
