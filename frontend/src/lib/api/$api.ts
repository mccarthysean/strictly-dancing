import createFetchClient from 'openapi-fetch'
import createClient from 'openapi-react-query'
import type { paths } from '@/types/api.gen'

// API base URL from environment variable, defaulting to localhost:8001
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8001'

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
}

export function clearTokens() {
  localStorage.removeItem(ACCESS_TOKEN_KEY)
  localStorage.removeItem(REFRESH_TOKEN_KEY)
}

// Create the fetch client with auth interceptor
const fetchClient = createFetchClient<paths>({
  baseUrl: API_BASE_URL,
})

// Add auth interceptor
fetchClient.use({
  onRequest: ({ request }) => {
    const token = getAccessToken()
    if (token) {
      request.headers.set('Authorization', `Bearer ${token}`)
    }
    return request
  },
})

// Create the React Query client
export const $api = createClient(fetchClient)
