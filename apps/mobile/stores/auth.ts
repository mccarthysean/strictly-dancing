import { create } from 'zustand';
import * as SecureStore from 'expo-secure-store';

const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL ?? 'http://localhost:8001';

// User type from API
interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  user_type: 'client' | 'host' | 'both';
  email_verified: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// Registration data (legacy password-based)
interface RegisterData {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  user_type: 'client' | 'host' | 'both';
}

// Registration data for magic link (passwordless)
interface RegisterWithMagicLinkData {
  email: string;
  first_name: string;
  last_name: string;
  user_type?: 'client' | 'host' | 'both';
}

// Token response from API
interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

// Auth store state
interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

// Auth store actions
interface AuthActions {
  initialize: () => Promise<void>;
  login: (email: string, password: string) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => Promise<void>;
  refreshAccessToken: () => Promise<boolean>;
  fetchUser: () => Promise<void>;
  clearError: () => void;
  // Magic link authentication
  requestMagicLink: (email: string) => Promise<void>;
  verifyMagicLink: (email: string, code: string) => Promise<void>;
  registerWithMagicLink: (data: RegisterWithMagicLinkData) => Promise<void>;
  verifyRegistration: (email: string, code: string) => Promise<void>;
}

type AuthStore = AuthState & AuthActions;

// Secure storage keys
const ACCESS_TOKEN_KEY = 'strictly_dancing_access_token';
const REFRESH_TOKEN_KEY = 'strictly_dancing_refresh_token';

export const useAuthStore = create<AuthStore>((set, get) => ({
  // Initial state
  user: null,
  accessToken: null,
  refreshToken: null,
  isAuthenticated: false,
  isLoading: true,
  error: null,

  // Initialize auth state from secure storage
  initialize: async () => {
    try {
      const accessToken = await SecureStore.getItemAsync(ACCESS_TOKEN_KEY);
      const refreshToken = await SecureStore.getItemAsync(REFRESH_TOKEN_KEY);

      if (accessToken && refreshToken) {
        set({ accessToken, refreshToken });

        // Try to fetch user with existing token
        try {
          await get().fetchUser();
        } catch {
          // Token might be expired, try to refresh
          const refreshed = await get().refreshAccessToken();
          if (refreshed) {
            await get().fetchUser();
          } else {
            // Refresh failed, clear tokens
            await SecureStore.deleteItemAsync(ACCESS_TOKEN_KEY);
            await SecureStore.deleteItemAsync(REFRESH_TOKEN_KEY);
            set({
              accessToken: null,
              refreshToken: null,
              user: null,
              isAuthenticated: false,
            });
          }
        }
      }
    } catch (error) {
      console.error('Failed to initialize auth:', error);
    } finally {
      set({ isLoading: false });
    }
  },

  // Login with email and password
  login: async (email: string, password: string) => {
    set({ isLoading: true, error: null });

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail ?? 'Login failed');
      }

      const tokens: TokenResponse = await response.json();

      // Store tokens securely
      await SecureStore.setItemAsync(ACCESS_TOKEN_KEY, tokens.access_token);
      await SecureStore.setItemAsync(REFRESH_TOKEN_KEY, tokens.refresh_token);

      set({
        accessToken: tokens.access_token,
        refreshToken: tokens.refresh_token,
      });

      // Fetch user data
      await get().fetchUser();
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Login failed';
      set({ error: message });
      throw error;
    } finally {
      set({ isLoading: false });
    }
  },

  // Register a new user
  register: async (data: RegisterData) => {
    set({ isLoading: true, error: null });

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail ?? 'Registration failed');
      }

      // Registration successful - user needs to login
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Registration failed';
      set({ error: message });
      throw error;
    } finally {
      set({ isLoading: false });
    }
  },

  // Logout and clear tokens
  logout: async () => {
    try {
      const { accessToken } = get();

      // Call logout endpoint (optional, for audit purposes)
      if (accessToken) {
        await fetch(`${API_BASE_URL}/api/v1/auth/logout`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${accessToken}`,
          },
        }).catch(() => {
          // Ignore errors - we're logging out anyway
        });
      }

      // Clear secure storage
      await SecureStore.deleteItemAsync(ACCESS_TOKEN_KEY);
      await SecureStore.deleteItemAsync(REFRESH_TOKEN_KEY);
    } catch {
      // Ignore errors during cleanup
    } finally {
      // Always clear local state
      set({
        user: null,
        accessToken: null,
        refreshToken: null,
        isAuthenticated: false,
        error: null,
      });
    }
  },

  // Refresh access token using refresh token
  refreshAccessToken: async () => {
    const { refreshToken } = get();

    if (!refreshToken) {
      return false;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });

      if (!response.ok) {
        return false;
      }

      const data = await response.json();
      const newAccessToken = data.access_token;

      // Update secure storage and state
      await SecureStore.setItemAsync(ACCESS_TOKEN_KEY, newAccessToken);
      set({ accessToken: newAccessToken });

      return true;
    } catch {
      return false;
    }
  },

  // Fetch current user data
  fetchUser: async () => {
    const { accessToken } = get();

    if (!accessToken) {
      throw new Error('No access token');
    }

    const response = await fetch(`${API_BASE_URL}/api/v1/auth/me`, {
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    });

    if (!response.ok) {
      throw new Error('Failed to fetch user');
    }

    const user: User = await response.json();

    set({
      user,
      isAuthenticated: true,
    });
  },

  // Clear error state
  clearError: () => {
    set({ error: null });
  },

  // Request magic link for login
  requestMagicLink: async (email: string) => {
    set({ isLoading: true, error: null });

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/auth/magic-link/request`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail ?? 'Failed to send magic link');
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to send magic link';
      set({ error: message });
      throw error;
    } finally {
      set({ isLoading: false });
    }
  },

  // Verify magic link code for login
  verifyMagicLink: async (email: string, code: string) => {
    set({ isLoading: true, error: null });

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/auth/magic-link/verify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, code }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail ?? 'Invalid or expired code');
      }

      const tokens: TokenResponse = await response.json();

      // Store tokens securely
      await SecureStore.setItemAsync(ACCESS_TOKEN_KEY, tokens.access_token);
      await SecureStore.setItemAsync(REFRESH_TOKEN_KEY, tokens.refresh_token);

      set({
        accessToken: tokens.access_token,
        refreshToken: tokens.refresh_token,
      });

      // Fetch user data
      await get().fetchUser();
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Invalid or expired code';
      set({ error: message });
      throw error;
    } finally {
      set({ isLoading: false });
    }
  },

  // Register with magic link (passwordless)
  registerWithMagicLink: async (data: RegisterWithMagicLinkData) => {
    set({ isLoading: true, error: null });

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/auth/register/magic-link`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: data.email,
          first_name: data.first_name,
          last_name: data.last_name,
          user_type: data.user_type ?? 'client',
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail ?? 'Registration failed');
      }

      // Registration initiated - user needs to verify with code
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Registration failed';
      set({ error: message });
      throw error;
    } finally {
      set({ isLoading: false });
    }
  },

  // Verify registration magic link
  verifyRegistration: async (email: string, code: string) => {
    set({ isLoading: true, error: null });

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/auth/register/verify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, code }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail ?? 'Invalid or expired code');
      }

      const tokens: TokenResponse = await response.json();

      // Store tokens securely
      await SecureStore.setItemAsync(ACCESS_TOKEN_KEY, tokens.access_token);
      await SecureStore.setItemAsync(REFRESH_TOKEN_KEY, tokens.refresh_token);

      set({
        accessToken: tokens.access_token,
        refreshToken: tokens.refresh_token,
      });

      // Fetch user data
      await get().fetchUser();
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Invalid or expired code';
      set({ error: message });
      throw error;
    } finally {
      set({ isLoading: false });
    }
  },
}));
