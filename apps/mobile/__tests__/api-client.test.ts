import { apiClient, ApiError } from '../lib/api/client';
import { useAuthStore } from '../stores/auth';

// Mock fetch globally
const mockFetch = jest.fn();
global.fetch = mockFetch;

describe('API Client', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Reset auth store state
    useAuthStore.setState({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
    });
  });

  describe('GET requests', () => {
    it('should make GET request without auth when no token', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: () => Promise.resolve({ data: 'test' }),
      });

      const result = await apiClient.get('/api/v1/test');

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8001/api/v1/test',
        expect.objectContaining({
          method: 'GET',
        })
      );
      expect(result).toEqual({ data: 'test' });
    });

    it('should include Authorization header when token exists', async () => {
      useAuthStore.setState({ accessToken: 'test-token' });

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: () => Promise.resolve({ data: 'authenticated' }),
      });

      await apiClient.get('/api/v1/protected');

      const [_, options] = mockFetch.mock.calls[0];
      expect(options.headers.get('Authorization')).toBe('Bearer test-token');
    });

    it('should skip auth when skipAuth option is true', async () => {
      useAuthStore.setState({ accessToken: 'test-token' });

      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: () => Promise.resolve({ public: true }),
      });

      await apiClient.get('/api/v1/public', { skipAuth: true });

      const [_, options] = mockFetch.mock.calls[0];
      expect(options.headers.get('Authorization')).toBeNull();
    });
  });

  describe('POST requests', () => {
    it('should make POST request with JSON body', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 201,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: () => Promise.resolve({ id: 'created' }),
      });

      const result = await apiClient.post('/api/v1/items', { name: 'test' });

      const [_, options] = mockFetch.mock.calls[0];
      expect(options.method).toBe('POST');
      expect(options.headers.get('Content-Type')).toBe('application/json');
      expect(options.body).toBe(JSON.stringify({ name: 'test' }));
      expect(result).toEqual({ id: 'created' });
    });
  });

  describe('Token refresh on 401', () => {
    it('should refresh token and retry request on 401', async () => {
      useAuthStore.setState({
        accessToken: 'expired-token',
        refreshToken: 'valid-refresh-token',
      });

      // First call returns 401
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: () => Promise.resolve({ detail: 'Unauthorized' }),
      });

      // Refresh token call succeeds
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ access_token: 'new-access-token' }),
      });

      // Retry call succeeds
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: () => Promise.resolve({ data: 'success after refresh' }),
      });

      const result = await apiClient.get('/api/v1/protected');

      expect(mockFetch).toHaveBeenCalledTimes(3);
      expect(result).toEqual({ data: 'success after refresh' });
    });

    it('should logout on failed refresh', async () => {
      const logoutSpy = jest.spyOn(useAuthStore.getState(), 'logout');

      useAuthStore.setState({
        accessToken: 'expired-token',
        refreshToken: 'invalid-refresh-token',
      });

      // First call returns 401
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: () => Promise.resolve({ detail: 'Unauthorized' }),
      });

      // Refresh token call fails
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
      });

      try {
        await apiClient.get('/api/v1/protected');
      } catch {
        // Expected to throw
      }

      expect(logoutSpy).toHaveBeenCalled();
      logoutSpy.mockRestore();
    });
  });

  describe('Error handling', () => {
    it('should throw ApiError on non-ok response', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: () => Promise.resolve({ detail: 'Not found' }),
      });

      try {
        await apiClient.get('/api/v1/missing');
        fail('Expected ApiError to be thrown');
      } catch (error) {
        expect(error).toBeInstanceOf(ApiError);
        expect((error as ApiError).statusCode).toBe(404);
        expect((error as ApiError).detail).toBe('Not found');
      }
    });

    it('should handle non-JSON responses', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        headers: new Headers({ 'content-type': 'text/plain' }),
        text: () => Promise.resolve('Plain text response'),
      });

      await expect(apiClient.get('/api/v1/text')).rejects.toThrow(
        'Unexpected response format'
      );
    });

    it('should handle 204 No Content', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 204,
        headers: new Headers({}),
      });

      const result = await apiClient.delete('/api/v1/items/1');

      expect(result).toBeUndefined();
    });
  });

  describe('Other HTTP methods', () => {
    it('should make PUT request', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: () => Promise.resolve({ updated: true }),
      });

      await apiClient.put('/api/v1/items/1', { name: 'updated' });

      const [_, options] = mockFetch.mock.calls[0];
      expect(options.method).toBe('PUT');
    });

    it('should make PATCH request', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: () => Promise.resolve({ patched: true }),
      });

      await apiClient.patch('/api/v1/items/1', { name: 'patched' });

      const [_, options] = mockFetch.mock.calls[0];
      expect(options.method).toBe('PATCH');
    });

    it('should make DELETE request', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 204,
        headers: new Headers({}),
      });

      await apiClient.delete('/api/v1/items/1');

      const [_, options] = mockFetch.mock.calls[0];
      expect(options.method).toBe('DELETE');
    });
  });
});
