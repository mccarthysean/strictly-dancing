import * as SecureStore from 'expo-secure-store';
import { useAuthStore } from '../stores/auth';

// Mock fetch globally
const mockFetch = jest.fn();
global.fetch = mockFetch;

// Mock SecureStore
jest.mock('expo-secure-store', () => ({
  getItemAsync: jest.fn(),
  setItemAsync: jest.fn(),
  deleteItemAsync: jest.fn(),
}));

describe('Auth Store', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Reset store state
    useAuthStore.setState({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      isLoading: true,
      error: null,
    });
  });

  describe('initialize', () => {
    it('should set isLoading to false when no tokens stored', async () => {
      (SecureStore.getItemAsync as jest.Mock).mockResolvedValue(null);

      await useAuthStore.getState().initialize();

      expect(useAuthStore.getState().isLoading).toBe(false);
      expect(useAuthStore.getState().isAuthenticated).toBe(false);
    });

    it('should restore auth state from stored tokens', async () => {
      (SecureStore.getItemAsync as jest.Mock)
        .mockResolvedValueOnce('stored-access-token')
        .mockResolvedValueOnce('stored-refresh-token');

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () =>
          Promise.resolve({
            id: 'user-123',
            email: 'test@example.com',
            first_name: 'Test',
            last_name: 'User',
            user_type: 'client',
            email_verified: true,
            is_active: true,
            created_at: '2026-01-01T00:00:00Z',
            updated_at: '2026-01-01T00:00:00Z',
          }),
      });

      await useAuthStore.getState().initialize();

      expect(useAuthStore.getState().isLoading).toBe(false);
      expect(useAuthStore.getState().isAuthenticated).toBe(true);
      expect(useAuthStore.getState().user?.email).toBe('test@example.com');
    });
  });

  describe('login', () => {
    it('should store tokens and fetch user on successful login', async () => {
      mockFetch
        .mockResolvedValueOnce({
          ok: true,
          json: () =>
            Promise.resolve({
              access_token: 'new-access-token',
              refresh_token: 'new-refresh-token',
              token_type: 'Bearer',
              expires_in: 900,
            }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () =>
            Promise.resolve({
              id: 'user-123',
              email: 'test@example.com',
              first_name: 'Test',
              last_name: 'User',
              user_type: 'client',
              email_verified: true,
              is_active: true,
              created_at: '2026-01-01T00:00:00Z',
              updated_at: '2026-01-01T00:00:00Z',
            }),
        });

      await useAuthStore.getState().login('test@example.com', 'password123');

      expect(SecureStore.setItemAsync).toHaveBeenCalledWith(
        'strictly_dancing_access_token',
        'new-access-token'
      );
      expect(SecureStore.setItemAsync).toHaveBeenCalledWith(
        'strictly_dancing_refresh_token',
        'new-refresh-token'
      );
      expect(useAuthStore.getState().isAuthenticated).toBe(true);
    });

    it('should throw error on invalid credentials', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        json: () =>
          Promise.resolve({
            detail: 'Invalid email or password',
          }),
      });

      await expect(useAuthStore.getState().login('test@example.com', 'wrong')).rejects.toThrow(
        'Invalid email or password'
      );

      expect(useAuthStore.getState().isAuthenticated).toBe(false);
    });
  });

  describe('logout', () => {
    it('should clear tokens and user state', async () => {
      // Set up authenticated state
      useAuthStore.setState({
        user: {
          id: 'user-123',
          email: 'test@example.com',
          first_name: 'Test',
          last_name: 'User',
          user_type: 'client',
          email_verified: true,
          is_active: true,
          created_at: '2026-01-01T00:00:00Z',
          updated_at: '2026-01-01T00:00:00Z',
        },
        accessToken: 'token',
        refreshToken: 'refresh',
        isAuthenticated: true,
        isLoading: false,
        error: null,
      });

      mockFetch.mockResolvedValueOnce({ ok: true });

      await useAuthStore.getState().logout();

      expect(SecureStore.deleteItemAsync).toHaveBeenCalledWith('strictly_dancing_access_token');
      expect(SecureStore.deleteItemAsync).toHaveBeenCalledWith('strictly_dancing_refresh_token');
      expect(useAuthStore.getState().isAuthenticated).toBe(false);
      expect(useAuthStore.getState().user).toBeNull();
      expect(useAuthStore.getState().accessToken).toBeNull();
    });
  });

  describe('refreshAccessToken', () => {
    it('should refresh access token successfully', async () => {
      useAuthStore.setState({
        refreshToken: 'valid-refresh-token',
        accessToken: 'old-access-token',
        isLoading: false,
      });

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () =>
          Promise.resolve({
            access_token: 'new-access-token',
          }),
      });

      const result = await useAuthStore.getState().refreshAccessToken();

      expect(result).toBe(true);
      expect(SecureStore.setItemAsync).toHaveBeenCalledWith(
        'strictly_dancing_access_token',
        'new-access-token'
      );
      expect(useAuthStore.getState().accessToken).toBe('new-access-token');
    });

    it('should return false when no refresh token available', async () => {
      useAuthStore.setState({
        refreshToken: null,
        isLoading: false,
      });

      const result = await useAuthStore.getState().refreshAccessToken();

      expect(result).toBe(false);
    });

    it('should return false when refresh fails', async () => {
      useAuthStore.setState({
        refreshToken: 'expired-token',
        isLoading: false,
      });

      mockFetch.mockResolvedValueOnce({
        ok: false,
      });

      const result = await useAuthStore.getState().refreshAccessToken();

      expect(result).toBe(false);
    });
  });

  describe('register', () => {
    it('should register user successfully', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () =>
          Promise.resolve({
            id: 'new-user-123',
            email: 'new@example.com',
            first_name: 'New',
            last_name: 'User',
          }),
      });

      await useAuthStore.getState().register({
        email: 'new@example.com',
        password: 'Password123',
        first_name: 'New',
        last_name: 'User',
        user_type: 'client',
      });

      // Registration doesn't auto-login
      expect(useAuthStore.getState().isAuthenticated).toBe(false);
    });

    it('should throw error on registration failure', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        json: () =>
          Promise.resolve({
            detail: 'Email already registered',
          }),
      });

      await expect(
        useAuthStore.getState().register({
          email: 'existing@example.com',
          password: 'Password123',
          first_name: 'Test',
          last_name: 'User',
          user_type: 'client',
        })
      ).rejects.toThrow('Email already registered');
    });
  });
});
