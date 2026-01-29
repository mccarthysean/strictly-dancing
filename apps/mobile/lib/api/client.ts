import { useAuthStore } from '@/stores/auth';

const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL ?? 'http://localhost:8001';

// Request options type
interface RequestOptions extends RequestInit {
  skipAuth?: boolean;
}

// API error class
export class ApiError extends Error {
  constructor(
    public statusCode: number,
    public detail: string,
    public originalError?: unknown
  ) {
    super(detail);
    this.name = 'ApiError';
  }
}

// Fetch wrapper with auth token injection and refresh
async function fetchWithAuth(
  endpoint: string,
  options: RequestOptions = {}
): Promise<Response> {
  const { skipAuth = false, ...fetchOptions } = options;

  const headers = new Headers(fetchOptions.headers);

  // Set Content-Type for JSON requests if not already set
  if (!headers.has('Content-Type') && fetchOptions.body) {
    headers.set('Content-Type', 'application/json');
  }

  // Inject auth token if not skipped
  if (!skipAuth) {
    const { accessToken } = useAuthStore.getState();
    if (accessToken) {
      headers.set('Authorization', `Bearer ${accessToken}`);
    }
  }

  const url = `${API_BASE_URL}${endpoint}`;

  const response = await fetch(url, {
    ...fetchOptions,
    headers,
  });

  // Handle 401 Unauthorized - try to refresh token
  if (response.status === 401 && !skipAuth) {
    const refreshed = await useAuthStore.getState().refreshAccessToken();

    if (refreshed) {
      // Retry the request with new token
      const { accessToken: newToken } = useAuthStore.getState();
      if (newToken) {
        headers.set('Authorization', `Bearer ${newToken}`);
      }

      const retryResponse = await fetch(url, {
        ...fetchOptions,
        headers,
      });

      return retryResponse;
    }

    // Refresh failed - logout user
    await useAuthStore.getState().logout();
  }

  return response;
}

// Parse API response
async function parseResponse<T>(response: Response): Promise<T> {
  const contentType = response.headers.get('content-type');

  if (response.status === 204) {
    return undefined as T;
  }

  if (!contentType?.includes('application/json')) {
    throw new ApiError(
      response.status,
      'Unexpected response format',
      await response.text()
    );
  }

  const data = await response.json();

  if (!response.ok) {
    throw new ApiError(
      response.status,
      data.detail ?? data.message ?? 'An error occurred',
      data
    );
  }

  return data as T;
}

// API client with typed methods
export const apiClient = {
  // GET request
  async get<T>(endpoint: string, options?: RequestOptions): Promise<T> {
    const response = await fetchWithAuth(endpoint, {
      ...options,
      method: 'GET',
    });
    return parseResponse<T>(response);
  },

  // POST request
  async post<T>(
    endpoint: string,
    body?: unknown,
    options?: RequestOptions
  ): Promise<T> {
    const response = await fetchWithAuth(endpoint, {
      ...options,
      method: 'POST',
      body: body ? JSON.stringify(body) : undefined,
    });
    return parseResponse<T>(response);
  },

  // PUT request
  async put<T>(
    endpoint: string,
    body?: unknown,
    options?: RequestOptions
  ): Promise<T> {
    const response = await fetchWithAuth(endpoint, {
      ...options,
      method: 'PUT',
      body: body ? JSON.stringify(body) : undefined,
    });
    return parseResponse<T>(response);
  },

  // PATCH request
  async patch<T>(
    endpoint: string,
    body?: unknown,
    options?: RequestOptions
  ): Promise<T> {
    const response = await fetchWithAuth(endpoint, {
      ...options,
      method: 'PATCH',
      body: body ? JSON.stringify(body) : undefined,
    });
    return parseResponse<T>(response);
  },

  // DELETE request
  async delete<T>(endpoint: string, options?: RequestOptions): Promise<T> {
    const response = await fetchWithAuth(endpoint, {
      ...options,
      method: 'DELETE',
    });
    return parseResponse<T>(response);
  },

  // Raw fetch with auth
  fetch: fetchWithAuth,
};

export default apiClient;
