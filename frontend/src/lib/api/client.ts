import createClient from 'openapi-fetch'
import type { paths } from '@/types/api.gen'

// API base URL from environment variable, defaulting to localhost:8001
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8001'

// Create the openapi-fetch client
export const client = createClient<paths>({
  baseUrl: API_BASE_URL,
})

// Helper to set authorization header
export function setAuthToken(token: string | null) {
  if (token) {
    client.use({
      onRequest: ({ request }) => {
        request.headers.set('Authorization', `Bearer ${token}`)
        return request
      },
    })
  }
}

// Token storage keys
const ACCESS_TOKEN_KEY = 'access_token'
const REFRESH_TOKEN_KEY = 'refresh_token'

// Token storage helpers
export function getAccessToken(): string | null {
  return localStorage.getItem(ACCESS_TOKEN_KEY)
}

export function getRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_TOKEN_KEY)
}

export function setTokens(accessToken: string, refreshToken: string) {
  localStorage.setItem(ACCESS_TOKEN_KEY, accessToken)
  localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken)
  setAuthToken(accessToken)
}

export function clearTokens() {
  localStorage.removeItem(ACCESS_TOKEN_KEY)
  localStorage.removeItem(REFRESH_TOKEN_KEY)
  setAuthToken(null)
}

// Initialize auth token from storage on module load
const storedToken = getAccessToken()
if (storedToken) {
  setAuthToken(storedToken)
}
