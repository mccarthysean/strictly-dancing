/**
 * Sentry SDK initialization for error tracking and performance monitoring.
 */

import * as Sentry from '@sentry/react'

/**
 * Initialize Sentry SDK with configured settings.
 * Call this function once at application startup.
 * Sentry will be disabled if VITE_SENTRY_DSN is not set.
 */
export function initSentry(): void {
  const dsn = import.meta.env.VITE_SENTRY_DSN as string | undefined

  if (!dsn) {
    console.log('Sentry DSN not configured, error tracking disabled')
    return
  }

  Sentry.init({
    dsn,
    environment: import.meta.env.VITE_SENTRY_ENVIRONMENT || 'development',
    // Performance monitoring
    tracesSampleRate: 0.1, // 10% of transactions
    // Session replay for debugging
    replaysSessionSampleRate: 0.1, // 10% of sessions
    replaysOnErrorSampleRate: 1.0, // 100% of sessions with errors
    // Integrations
    integrations: [
      Sentry.browserTracingIntegration(),
      Sentry.replayIntegration({
        maskAllText: false,
        blockAllMedia: false,
      }),
    ],
    // Release version
    release: `strictly-dancing-frontend@${import.meta.env.VITE_APP_VERSION || '0.0.1'}`,
    // Don't send PII
    sendDefaultPii: false,
    // Ignore common browser extension errors
    ignoreErrors: [
      // Browser extensions
      'top.GLOBALS',
      /^chrome:\/\//,
      /^moz-extension:\/\//,
      // Network errors
      'Failed to fetch',
      'NetworkError',
      'Load failed',
      // User action interruption
      'AbortError',
    ],
    // Don't track localhost in production
    denyUrls: [/localhost:\d+/],
  })
}

/**
 * Capture an exception and send it to Sentry.
 */
export function captureException(error: Error, context?: Record<string, unknown>): string | undefined {
  if (context) {
    return Sentry.captureException(error, { extra: context })
  }
  return Sentry.captureException(error)
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
  if (email) {
    Sentry.setUser({ id: userId, email })
  } else {
    Sentry.setUser({ id: userId })
  }
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

// Export Sentry's ErrorBoundary for use in React components
export { Sentry }
