import { authService } from '../auth/auth.service';

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public data?: any
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

export interface ApiClientConfig {
  baseUrl: string;
  timeout?: number;
  headers?: Record<string, string>;
}

class ApiClient {
  private static instance: ApiClient;
  private baseUrl: string;
  private timeout: number;
  private defaultHeaders: Record<string, string>;

  private constructor(config: ApiClientConfig) {
    this.baseUrl = config.baseUrl;
    this.timeout = config.timeout || 30000;
    this.defaultHeaders = {
      'Content-Type': 'application/json',
      ...config.headers,
    };
  }

  public static getInstance(config?: ApiClientConfig): ApiClient {
    if (!ApiClient.instance && config) {
      ApiClient.instance = new ApiClient(config);
    }
    return ApiClient.instance;
  }

  public async get<T>(path: string, options: RequestInit = {}): Promise<T> {
    return this.request<T>(path, {
      ...options,
      method: 'GET',
    });
  }

  public async post<T>(path: string, data?: any, options: RequestInit = {}): Promise<T> {
    return this.request<T>(path, {
      ...options,
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  public async put<T>(path: string, data?: any, options: RequestInit = {}): Promise<T> {
    return this.request<T>(path, {
      ...options,
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  public async delete<T>(path: string, options: RequestInit = {}): Promise<T> {
    return this.request<T>(path, {
      ...options,
      method: 'DELETE',
    });
  }

  private async request<T>(path: string, options: RequestInit): Promise<T> {
    const url = this.buildUrl(path);
    const headers = this.buildHeaders(options.headers);
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

    try {
      if (process.env.NODE_ENV === 'development') {
        console.log(`API Request: ${options.method} ${url}`, {
          headers,
          body: options.body,
        });
      }

      const response = await fetch(url, {
        ...options,
        headers,
        signal: controller.signal,
      });

      if (process.env.NODE_ENV === 'development') {
        console.log(`API Response: ${response.status}`, {
          url,
          status: response.status,
          statusText: response.statusText,
        });
      }

      if (!response.ok) {
        let errorData;
        try {
          errorData = await response.json();
        } catch {
          errorData = null;
        }
        throw new ApiError(
          errorData?.message || response.statusText,
          response.status,
          errorData
        );
      }

      return response.json();
    } catch (error) {
      if (process.env.NODE_ENV === 'development') {
        console.error('API Error:', error);
      }
      if (error instanceof ApiError) {
        throw error;
      }
      throw new ApiError(
        error instanceof Error ? error.message : 'Unknown error',
        500
      );
    } finally {
      clearTimeout(timeoutId);
    }
  }

  private buildUrl(path: string): string {
    const baseUrl = this.baseUrl.endsWith('/')
      ? this.baseUrl.slice(0, -1)
      : this.baseUrl;
    const normalizedPath = path.startsWith('/') ? path : `/${path}`;
    return `${baseUrl}${normalizedPath}`;
  }

  private buildHeaders(customHeaders: HeadersInit = {}): Headers {
    const headers = new Headers({
      ...this.defaultHeaders,
      ...customHeaders,
    });

    const token = authService.getToken();
    if (token) {
      headers.set('Authorization', `Bearer ${token}`);
    }

    return headers;
  }
}

// Initialize API client with configuration
const apiConfig: ApiClientConfig = {
  baseUrl: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api',
  timeout: 30000,
};

export const apiClient = ApiClient.getInstance(apiConfig);
export default apiClient; 