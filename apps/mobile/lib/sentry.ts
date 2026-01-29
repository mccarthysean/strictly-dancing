/**
 * Sentry SDK initialization for error tracking and performance monitoring.
 */

import * as Sentry from '@sentry/react-native'
import Constants from 'expo-constants'

/**
 * Initialize Sentry SDK with configured settings.
 * Call this function once at application startup.
 * Sentry will be disabled if EXPO_PUBLIC_SENTRY_DSN is not set.
 */
export function initSentry(): void {
  const dsn = process.env.EXPO_PUBLIC_SENTRY_DSN

  if (!dsn) {
    console.log('Sentry DSN not configured, error tracking disabled')
    return
  }

  Sentry.init({
    dsn,
    environment: process.env.EXPO_PUBLIC_SENTRY_ENVIRONMENT ?? 'development',
    // Performance monitoring
    tracesSampleRate: 0.1, // 10% of transactions
    // Profile performance
    profilesSampleRate: 0.1, // 10% of sampled transactions
    // Enable native crash handling
    enableNativeCrashHandling: true,
    // Enable auto session tracking
    enableAutoSessionTracking: true,
    // Session tracking interval (30 seconds)
    sessionTrackingIntervalMillis: 30000,
    // Release version from Expo constants
    release: `strictly-dancing-mobile@${Constants.expoConfig?.version ?? '1.0.0'}`,
    // Distribution (build number)
    dist: Constants.expoConfig?.ios?.buildNumber ?? Constants.expoConfig?.android?.versionCode?.toString() ?? '1',
    // Don't send PII
    sendDefaultPii: false,
    // Enable attachments for debugging
    attachStacktrace: true,
    // Enable debug in development
    debug: __DEV__,
  })
}

/**
 * Capture an exception and send it to Sentry.
 */
export function captureException(error: Error, context?: Record<string, unknown>): string | undefined {
  return Sentry.captureException(error, { extra: context })
}

/**
 * Capture a message and send it to Sentry.
 */
export function captureMessage(message: string, level: Sentry.SeverityLevel = 'info'): string | undefined {
  return Sentry.captureMessage(message, level)
}

/**
 * Set the current user for Sentry error tracking.
 */
export function setUser(userId: string, email?: string): void {
  Sentry.setUser({ id: userId, email })
}

/**
 * Clear the current user (on logout).
 */
export function clearUser(): void {
  Sentry.setUser(null)
}

/**
 * Set a tag on the current scope.
 */
export function setTag(key: string, value: string): void {
  Sentry.setTag(key, value)
}

/**
 * Set context data on the current scope.
 */
export function setContext(name: string, data: Record<string, unknown>): void {
  Sentry.setContext(name, data)
}

/**
 * Wrap the app component with Sentry's error boundary.
 */
export const SentryProvider = Sentry.wrap

// Export Sentry for direct access if needed
export { Sentry }
