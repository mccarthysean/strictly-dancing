import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  type ReactNode,
} from 'react'
import { setTokens, clearTokens, getAccessToken, getRefreshToken } from '@/lib/api/$api'
import type { components } from '@/types/api.gen'

type User = components['schemas']['UserResponse']
type UserType = components['schemas']['UserType']

interface AuthContextValue {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => Promise<void>
  register: (data: RegisterData) => Promise<void>
  refreshAuth: () => Promise<void>
}

interface RegisterData {
  email: string
  password: string
  first_name: string
  last_name: string
  user_type?: UserType
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

interface AuthProviderProps {
  children: ReactNode
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  const isAuthenticated = user !== null

  // Fetch current user profile
  const fetchUser = useCallback(async () => {
    const token = getAccessToken()
    if (!token) {
      setUser(null)
      setIsLoading(false)
      return
    }

    try {
      const response = await fetch(
        `${import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8001'}/api/v1/auth/me`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      )

      if (response.ok) {
        const userData = (await response.json()) as User
        setUser(userData)
      } else if (response.status === 401) {
        // Token expired, try to refresh
        await refreshAuth()
      } else {
        setUser(null)
        clearTokens()
      }
    } catch {
      setUser(null)
      clearTokens()
    } finally {
      setIsLoading(false)
    }
  }, [])

  // Refresh authentication using refresh token
  const refreshAuth = useCallback(async () => {
    const refreshToken = getRefreshToken()
    if (!refreshToken) {
      setUser(null)
      setIsLoading(false)
      return
    }

    try {
      const response = await fetch(
        `${import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8001'}/api/v1/auth/refresh`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ refresh_token: refreshToken }),
        }
      )

      if (response.ok) {
        const data = (await response.json()) as { access_token: string }
        // Keep the existing refresh token, only update access token
        setTokens(data.access_token, refreshToken)
        // Fetch user with new token
        await fetchUser()
      } else {
        setUser(null)
        clearTokens()
        setIsLoading(false)
      }
    } catch {
      setUser(null)
      clearTokens()
      setIsLoading(false)
    }
  }, [fetchUser])

  // Login function
  const login = useCallback(async (email: string, password: string) => {
    const response = await fetch(
      `${import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8001'}/api/v1/auth/login`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      }
    )

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail ?? 'Login failed')
    }

    const data = (await response.json()) as {
      access_token: string
      refresh_token: string
    }
    setTokens(data.access_token, data.refresh_token)

    // Fetch user profile after login
    await fetchUser()
  }, [fetchUser])

  // Logout function
  const logout = useCallback(async () => {
    const token = getAccessToken()
    if (token) {
      try {
        await fetch(
          `${import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8001'}/api/v1/auth/logout`,
          {
            method: 'POST',
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        )
      } catch {
        // Ignore errors during logout
      }
    }

    clearTokens()
    setUser(null)
  }, [])

  // Register function
  const register = useCallback(async (data: RegisterData) => {
    const response = await fetch(
      `${import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8001'}/api/v1/auth/register`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: data.email,
          password: data.password,
          first_name: data.first_name,
          last_name: data.last_name,
          user_type: data.user_type ?? 'client',
        }),
      }
    )

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail ?? 'Registration failed')
    }

    // Registration successful - user should login
  }, [])

  // Auto-refresh on page load if token exists
  useEffect(() => {
    fetchUser()
  }, [fetchUser])

  const value: AuthContextValue = {
    user,
    isAuthenticated,
    isLoading,
    login,
    logout,
    register,
    refreshAuth,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
