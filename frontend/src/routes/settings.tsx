import { createFileRoute, Link, useNavigate } from '@tanstack/react-router'
import { useState } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import type { components } from '@/types/api.gen'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Switch } from '@/components/ui/switch'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Separator } from '@/components/ui/separator'
import { cn } from '@/lib/utils'
import { Loader2, Check, X, ExternalLink } from 'lucide-react'

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
      <div className="flex min-h-[60vh] flex-col items-center justify-center">
        <Loader2 className="h-10 w-10 animate-spin text-primary" />
        <p className="mt-4 text-muted-foreground">Loading...</p>
      </div>
    )
  }

  // Not authenticated
  if (!isAuthenticated) {
    return (
      <div className="mx-auto max-w-xl p-4">
        <Card className="mx-auto max-w-md">
          <CardContent className="p-8 text-center">
            <h2 className="mb-2 font-display text-xl font-semibold text-foreground">Login Required</h2>
            <p className="mb-6 text-muted-foreground">Please log in to view your settings.</p>
            <Button asChild className="w-full">
              <Link to="/login" className="no-underline">
                Log In
              </Link>
            </Button>
          </CardContent>
        </Card>
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
    <div className="mx-auto max-w-xl p-4 pb-12">
      <h1 className="mb-6 font-display text-[clamp(1.5rem,4vw,2rem)] font-bold text-foreground">
        Settings
      </h1>

      {/* Account Section */}
      <section className="mb-8">
        <h2 className="mb-3 text-lg font-semibold text-foreground">Account</h2>

        <Card className="mb-3">
          <CardContent className="p-4">
            {isEditingProfile ? (
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="firstName">First Name</Label>
                  <Input
                    id="firstName"
                    type="text"
                    value={firstName}
                    onChange={(e) => setFirstName(e.target.value)}
                    placeholder="First name"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="lastName">Last Name</Label>
                  <Input
                    id="lastName"
                    type="text"
                    value={lastName}
                    onChange={(e) => setLastName(e.target.value)}
                    placeholder="Last name"
                  />
                </div>
                {profileError && (
                  <p className="text-sm text-destructive">{profileError}</p>
                )}
                <div className="flex justify-end gap-3">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={handleCancelEdit}
                    disabled={isSavingProfile}
                  >
                    Cancel
                  </Button>
                  <Button
                    type="button"
                    onClick={handleSaveProfile}
                    disabled={isSavingProfile || !firstName.trim() || !lastName.trim()}
                  >
                    {isSavingProfile ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Saving...
                      </>
                    ) : (
                      'Save Changes'
                    )}
                  </Button>
                </div>
              </div>
            ) : (
              <>
                <div className="flex items-center gap-4">
                  <Avatar className="h-14 w-14">
                    <AvatarFallback className="bg-rose-600 text-lg text-white dark:bg-rose-gold-400 dark:text-foreground">
                      {user?.first_name?.charAt(0) ?? '?'}{user?.last_name?.charAt(0) ?? ''}
                    </AvatarFallback>
                  </Avatar>
                  <div className="min-w-0 flex-1">
                    <p className="font-semibold text-foreground">
                      {user?.first_name} {user?.last_name}
                    </p>
                    <p className="text-sm text-muted-foreground">{user?.email}</p>
                    <p className="text-xs text-muted-foreground/70">{getUserTypeDisplay(user?.user_type)}</p>
                  </div>
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={handleEditProfile}
                  >
                    Edit
                  </Button>
                </div>
                {profileSuccess && (
                  <p className="mt-3 text-sm text-green-600 dark:text-green-400">
                    Profile updated successfully!
                  </p>
                )}
              </>
            )}
          </CardContent>
        </Card>

        {/* Email verification status */}
        <Card className="mb-3">
          <CardContent className="flex items-center justify-between p-4">
            <div>
              <p className="font-medium text-foreground">Email Verification</p>
              <p className="text-sm text-muted-foreground">
                {user?.email_verified
                  ? 'Your email is verified'
                  : 'Your email is not verified'}
              </p>
            </div>
            <Badge
              variant={user?.email_verified ? 'default' : 'secondary'}
              className={cn(
                user?.email_verified
                  ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400"
                  : "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400"
              )}
            >
              {user?.email_verified ? (
                <>
                  <Check className="mr-1 h-3 w-3" />
                  Verified
                </>
              ) : (
                <>
                  <X className="mr-1 h-3 w-3" />
                  Unverified
                </>
              )}
            </Badge>
          </CardContent>
        </Card>

        {/* Host-specific settings */}
        {(user?.user_type === 'host' || user?.user_type === 'both') && (
          <Card className="mb-3">
            <CardContent className="flex items-center justify-between p-4">
              <div>
                <p className="font-medium text-foreground">Host Dashboard</p>
                <p className="text-sm text-muted-foreground">
                  View your earnings, bookings, and reviews
                </p>
              </div>
              <Button asChild variant="outline" size="sm">
                <Link to="/host/dashboard" className="no-underline">
                  <ExternalLink className="mr-2 h-4 w-4" />
                  Dashboard
                </Link>
              </Button>
            </CardContent>
          </Card>
        )}
      </section>

      {/* Notifications Section */}
      <section className="mb-8">
        <h2 className="mb-1 text-lg font-semibold text-foreground">Notifications</h2>
        <p className="mb-4 text-sm text-muted-foreground">
          Manage how you receive notifications
        </p>

        <Card className="mb-3">
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Email Notifications</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between gap-4">
              <div className="min-w-0 flex-1">
                <p className="font-medium text-foreground">Booking Updates</p>
                <p className="text-sm text-muted-foreground">
                  Receive emails when bookings are created, confirmed, or cancelled
                </p>
              </div>
              <Switch
                checked={notifications.emailBookingUpdates}
                onCheckedChange={() => handleNotificationChange('emailBookingUpdates')}
              />
            </div>
            <Separator />
            <div className="flex items-center justify-between gap-4">
              <div className="min-w-0 flex-1">
                <p className="font-medium text-foreground">Messages</p>
                <p className="text-sm text-muted-foreground">
                  Receive emails when you get new messages
                </p>
              </div>
              <Switch
                checked={notifications.emailMessages}
                onCheckedChange={() => handleNotificationChange('emailMessages')}
              />
            </div>
            <Separator />
            <div className="flex items-center justify-between gap-4">
              <div className="min-w-0 flex-1">
                <p className="font-medium text-foreground">Marketing</p>
                <p className="text-sm text-muted-foreground">
                  Receive updates about new features and promotions
                </p>
              </div>
              <Switch
                checked={notifications.emailMarketing}
                onCheckedChange={() => handleNotificationChange('emailMarketing')}
              />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Push Notifications</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between gap-4">
              <div className="min-w-0 flex-1">
                <p className="font-medium text-foreground">Booking Updates</p>
                <p className="text-sm text-muted-foreground">
                  Receive push notifications for booking changes
                </p>
              </div>
              <Switch
                checked={notifications.pushBookingUpdates}
                onCheckedChange={() => handleNotificationChange('pushBookingUpdates')}
              />
            </div>
            <Separator />
            <div className="flex items-center justify-between gap-4">
              <div className="min-w-0 flex-1">
                <p className="font-medium text-foreground">Messages</p>
                <p className="text-sm text-muted-foreground">
                  Receive push notifications for new messages
                </p>
              </div>
              <Switch
                checked={notifications.pushMessages}
                onCheckedChange={() => handleNotificationChange('pushMessages')}
              />
            </div>
          </CardContent>
        </Card>
      </section>

      {/* Session Section */}
      <section className="mb-8">
        <h2 className="mb-3 text-lg font-semibold text-foreground">Session</h2>

        <Card>
          <CardContent className="flex items-center justify-between p-4">
            <div>
              <p className="font-medium text-foreground">Sign Out</p>
              <p className="text-sm text-muted-foreground">
                Sign out of your account on this device
              </p>
            </div>
            <Button
              variant="outline"
              onClick={handleLogout}
              disabled={isLoggingOut}
              className="border-destructive/50 text-destructive hover:bg-destructive/10"
            >
              {isLoggingOut ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Signing out...
                </>
              ) : (
                'Sign Out'
              )}
            </Button>
          </CardContent>
        </Card>
      </section>

      {/* App Info */}
      <div className="text-center">
        <p className="text-sm text-muted-foreground/70">Strictly Dancing</p>
        <p className="text-xs text-muted-foreground/50">Version 1.0.0</p>
      </div>
    </div>
  )
}
