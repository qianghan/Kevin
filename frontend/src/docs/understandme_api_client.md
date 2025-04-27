# KAI API Client Architecture

This document outlines the architecture of the API client system used in the KAI application. The system follows SOLID principles and provides a flexible, maintainable approach to API interactions.

## Overall Architecture

The API client architecture follows a layered approach:

1. **Base API Client**: Handles common HTTP functionality, request/response formatting
2. **Service-Specific Clients**: Domain-specific clients that extend the base client
3. **Interceptors**: Middleware for processing requests and responses
4. **Mock Implementations**: Test doubles implementing the same interfaces

```
┌─────────────────────────────────────────────────────────────────┐
│                         Application Code                         │
└───────────────────────────────┬─────────────────────────────────┘
                                │
┌───────────────────────────────┼─────────────────────────────────┐
│   ┌─────────────┐   ┌─────────┴───────┐   ┌─────────────────┐   │
│   │ User Client │   │ Profile Client  │   │   Chat Client   │   │
│   └──────┬──────┘   └────────┬────────┘   └────────┬────────┘   │
│          │                   │                     │            │
│   ┌──────┴───────────────────┴─────────────────────┴──────┐     │
│   │                    Base API Client                     │     │
│   └──────┬───────────────────┬─────────────────────┬──────┘     │
│          │                   │                     │            │
│   ┌──────┴──────┐   ┌────────┴────────┐   ┌────────┴─────────┐  │
│   │   Request   │   │     Response    │   │       Error      │  │
│   │ Interceptors│   │   Interceptors  │   │     Handling     │  │
│   └─────────────┘   └─────────────────┘   └──────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Base API Client

The base API client provides core HTTP functionality and handles common tasks such as request formatting, response parsing, and error handling.

```typescript
export interface APIRequestConfig extends RequestInit {
  params?: Record<string, string | number | boolean>;
  timeout?: number;
  retries?: number;
  abortSignal?: AbortSignal;
  cache?: RequestCache;
}

export interface APIResponse<T> {
  data: T;
  status: number;
  statusText: string;
  headers: Headers;
  config: APIRequestConfig;
}

export interface APIError extends Error {
  status?: number;
  statusText?: string;
  data?: any;
  config?: APIRequestConfig;
}

export interface IAPIClient {
  get<T>(url: string, config?: APIRequestConfig): Promise<APIResponse<T>>;
  post<T>(url: string, data?: any, config?: APIRequestConfig): Promise<APIResponse<T>>;
  put<T>(url: string, data?: any, config?: APIRequestConfig): Promise<APIResponse<T>>;
  patch<T>(url: string, data?: any, config?: APIRequestConfig): Promise<APIResponse<T>>;
  delete<T>(url: string, config?: APIRequestConfig): Promise<APIResponse<T>>;
}

export class BaseAPIClient implements IAPIClient {
  protected baseURL: string;
  protected defaultConfig: APIRequestConfig;
  protected requestInterceptors: Array<(config: APIRequestConfig) => APIRequestConfig>;
  protected responseInterceptors: Array<(response: APIResponse<any>) => APIResponse<any>>;
  protected errorInterceptors: Array<(error: APIError) => Promise<APIResponse<any>> | APIError>;

  constructor(baseURL: string, defaultConfig: APIRequestConfig = {}) {
    this.baseURL = baseURL;
    this.defaultConfig = defaultConfig;
    this.requestInterceptors = [];
    this.responseInterceptors = [];
    this.errorInterceptors = [];
  }

  // Methods to add interceptors
  public addRequestInterceptor(interceptor: (config: APIRequestConfig) => APIRequestConfig): void {
    this.requestInterceptors.push(interceptor);
  }

  public addResponseInterceptor(interceptor: (response: APIResponse<any>) => APIResponse<any>): void {
    this.responseInterceptors.push(interceptor);
  }

  public addErrorInterceptor(interceptor: (error: APIError) => Promise<APIResponse<any>> | APIError): void {
    this.errorInterceptors.push(interceptor);
  }

  // Implementation of HTTP methods...
  public async get<T>(url: string, config?: APIRequestConfig): Promise<APIResponse<T>> {
    return this.request<T>(url, { ...config, method: 'GET' });
  }

  public async post<T>(url: string, data?: any, config?: APIRequestConfig): Promise<APIResponse<T>> {
    return this.request<T>(url, { ...config, method: 'POST', body: JSON.stringify(data) });
  }

  public async put<T>(url: string, data?: any, config?: APIRequestConfig): Promise<APIResponse<T>> {
    return this.request<T>(url, { ...config, method: 'PUT', body: JSON.stringify(data) });
  }

  public async patch<T>(url: string, data?: any, config?: APIRequestConfig): Promise<APIResponse<T>> {
    return this.request<T>(url, { ...config, method: 'PATCH', body: JSON.stringify(data) });
  }

  public async delete<T>(url: string, config?: APIRequestConfig): Promise<APIResponse<T>> {
    return this.request<T>(url, { ...config, method: 'DELETE' });
  }

  // Private method to handle requests
  protected async request<T>(url: string, config: APIRequestConfig): Promise<APIResponse<T>> {
    // Apply request interceptors
    let requestConfig = { ...this.defaultConfig, ...config };
    for (const interceptor of this.requestInterceptors) {
      requestConfig = interceptor(requestConfig);
    }

    // Build full URL
    const fullURL = new URL(url, this.baseURL);
    
    // Add query parameters if specified
    if (requestConfig.params) {
      Object.entries(requestConfig.params).forEach(([key, value]) => {
        fullURL.searchParams.append(key, String(value));
      });
    }

    try {
      // Create AbortController for timeout if specified
      const controller = new AbortController();
      if (requestConfig.timeout) {
        setTimeout(() => controller.abort(), requestConfig.timeout);
        requestConfig.signal = controller.signal;
      }

      // Make the request
      const response = await fetch(fullURL.toString(), requestConfig);
      
      // Parse response data
      const data = await response.json();
      
      // Create API response object
      let apiResponse: APIResponse<T> = {
        data,
        status: response.status,
        statusText: response.statusText,
        headers: response.headers,
        config: requestConfig
      };
      
      // Apply response interceptors
      for (const interceptor of this.responseInterceptors) {
        apiResponse = interceptor(apiResponse);
      }
      
      // Handle error status codes
      if (!response.ok) {
        const error: APIError = new Error(response.statusText);
        error.status = response.status;
        error.statusText = response.statusText;
        error.data = data;
        error.config = requestConfig;
        
        // Apply error interceptors
        let errorResult: APIError | APIResponse<T> = error;
        for (const interceptor of this.errorInterceptors) {
          const result = interceptor(error);
          if (result instanceof Promise) {
            try {
              // If interceptor returns a Promise, it might recover from the error
              return await result;
            } catch (e) {
              errorResult = e as APIError;
            }
          } else {
            errorResult = result;
          }
        }
        
        // If errorResult is still an error, throw it
        if (errorResult instanceof Error) {
          throw errorResult;
        }
        
        // Otherwise, it's a recovered response
        return errorResult as APIResponse<T>;
      }
      
      return apiResponse;
    } catch (error) {
      // Handle network errors and timeouts
      const apiError = error as APIError;
      apiError.config = requestConfig;
      
      // Apply error interceptors
      let errorResult: APIError | APIResponse<T> = apiError;
      for (const interceptor of this.errorInterceptors) {
        const result = interceptor(apiError);
        if (result instanceof Promise) {
          try {
            // If interceptor returns a Promise, it might recover from the error
            return await result;
          } catch (e) {
            errorResult = e as APIError;
          }
        } else {
          errorResult = result;
        }
      }
      
      // If errorResult is still an error, throw it
      if (errorResult instanceof Error) {
        throw errorResult;
      }
      
      // Otherwise, it's a recovered response
      return errorResult as APIResponse<T>;
    }
  }
}
```

## Service-Specific API Clients

Service-specific clients extend the base client, providing domain-specific methods and handling the particularities of each API endpoint.

### User API Client

```typescript
export interface IUserAPIClient {
  getCurrentUser(): Promise<APIResponse<User>>;
  updateUser(userId: string, userData: Partial<User>): Promise<APIResponse<User>>;
  getUserPreferences(): Promise<APIResponse<UserPreferences>>;
  updateUserPreferences(preferences: Partial<UserPreferences>): Promise<APIResponse<UserPreferences>>;
  // Other user-related methods...
}

export class UserAPIClient extends BaseAPIClient implements IUserAPIClient {
  constructor(baseURL: string = '/api/users', defaultConfig: APIRequestConfig = {}) {
    super(baseURL, defaultConfig);
  }

  public async getCurrentUser(): Promise<APIResponse<User>> {
    return this.get<User>('/me');
  }

  public async updateUser(userId: string, userData: Partial<User>): Promise<APIResponse<User>> {
    return this.patch<User>(`/${userId}`, userData);
  }

  public async getUserPreferences(): Promise<APIResponse<UserPreferences>> {
    return this.get<UserPreferences>('/me/preferences');
  }

  public async updateUserPreferences(preferences: Partial<UserPreferences>): Promise<APIResponse<UserPreferences>> {
    return this.patch<UserPreferences>('/me/preferences', preferences);
  }
}
```

### Profile API Client

```typescript
export interface IProfileAPIClient {
  getProfile(userId: string): Promise<APIResponse<Profile>>;
  updateProfile(userId: string, profileData: Partial<Profile>): Promise<APIResponse<Profile>>;
  addExperience(userId: string, experience: Experience): Promise<APIResponse<Profile>>;
  // Other profile-related methods...
}

export class ProfileAPIClient extends BaseAPIClient implements IProfileAPIClient {
  constructor(baseURL: string = '/api/profiles', defaultConfig: APIRequestConfig = {}) {
    super(baseURL, defaultConfig);
  }

  public async getProfile(userId: string): Promise<APIResponse<Profile>> {
    return this.get<Profile>(`/${userId}`);
  }

  public async updateProfile(userId: string, profileData: Partial<Profile>): Promise<APIResponse<Profile>> {
    return this.patch<Profile>(`/${userId}`, profileData);
  }

  public async addExperience(userId: string, experience: Experience): Promise<APIResponse<Profile>> {
    return this.post<Profile>(`/${userId}/experiences`, experience);
  }
}
```

### Chat API Client

```typescript
export interface IChatAPIClient {
  getConversations(): Promise<APIResponse<Conversation[]>>;
  getConversation(conversationId: string): Promise<APIResponse<Conversation>>;
  sendMessage(conversationId: string, message: Omit<Message, 'id' | 'timestamp'>): Promise<APIResponse<Message>>;
  // Other chat-related methods...
}

export class ChatAPIClient extends BaseAPIClient implements IChatAPIClient {
  constructor(baseURL: string = '/api/chat', defaultConfig: APIRequestConfig = {}) {
    super(baseURL, defaultConfig);
  }

  public async getConversations(): Promise<APIResponse<Conversation[]>> {
    return this.get<Conversation[]>('/conversations');
  }

  public async getConversation(conversationId: string): Promise<APIResponse<Conversation>> {
    return this.get<Conversation>(`/conversations/${conversationId}`);
  }

  public async sendMessage(conversationId: string, message: Omit<Message, 'id' | 'timestamp'>): Promise<APIResponse<Message>> {
    return this.post<Message>(`/conversations/${conversationId}/messages`, message);
  }
}
```

## Request Interceptors

Request interceptors modify outgoing requests before they are sent. Common use cases include adding authentication tokens, formatting request data, and adding headers.

### Authentication Interceptor

```typescript
export const createAuthInterceptor = (authService: IAuthService) => {
  return (config: APIRequestConfig): APIRequestConfig => {
    const token = authService.getAccessToken();
    if (token) {
      const headers = new Headers(config.headers || {});
      headers.set('Authorization', `Bearer ${token}`);
      return { ...config, headers };
    }
    return config;
  };
};
```

### Request Logger Interceptor

```typescript
export const createRequestLoggerInterceptor = (logger: ILogger) => {
  return (config: APIRequestConfig): APIRequestConfig => {
    logger.debug('API Request', {
      url: config.url,
      method: config.method,
      params: config.params,
      body: config.body
    });
    return config;
  };
};
```

## Response Interceptors

Response interceptors process responses after they are received. They can transform response data, handle specific status codes, or log response information.

### Response Logger Interceptor

```typescript
export const createResponseLoggerInterceptor = (logger: ILogger) => {
  return (response: APIResponse<any>): APIResponse<any> => {
    logger.debug('API Response', {
      url: response.config.url,
      status: response.status,
      data: response.data
    });
    return response;
  };
};
```

### Response Data Transformer

```typescript
export const createResponseTransformer = <T, R>(transformer: (data: T) => R) => {
  return (response: APIResponse<T>): APIResponse<R> => {
    return {
      ...response,
      data: transformer(response.data)
    };
  };
};
```

## Error Interceptors

Error interceptors handle exceptions thrown during API calls. They can retry failed requests, transform error data, or perform recovery actions.

### Retry Interceptor

```typescript
export const createRetryInterceptor = (maxRetries: number = 3, retryableStatuses: number[] = [408, 429, 500, 502, 503, 504]) => {
  return async (error: APIError): Promise<APIResponse<any>> => {
    if (!error.config || !error.status || error.config.retries === undefined || error.config.retries >= maxRetries) {
      throw error;
    }

    if (retryableStatuses.includes(error.status)) {
      // Increment retry count
      const config = {
        ...error.config,
        retries: (error.config.retries || 0) + 1
      };

      // Exponential backoff
      const delay = Math.pow(2, config.retries) * 100;
      await new Promise(resolve => setTimeout(resolve, delay));

      // Retry the request
      const client = new BaseAPIClient('');
      return client.request(error.config.url || '', config);
    }

    throw error;
  };
};
```

### Authentication Error Handler

```typescript
export const createAuthErrorInterceptor = (authService: IAuthService, refreshCallback: () => Promise<string>) => {
  return async (error: APIError): Promise<APIResponse<any>> => {
    if (error.status === 401 && error.config) {
      try {
        // Try to refresh the token
        const newToken = await refreshCallback();
        
        // Update the request with the new token
        const headers = new Headers(error.config.headers || {});
        headers.set('Authorization', `Bearer ${newToken}`);
        
        // Retry the request with the new token
        const client = new BaseAPIClient('');
        return client.request(error.config.url || '', { ...error.config, headers });
      } catch (refreshError) {
        // If token refresh fails, log out the user
        authService.logout();
        throw error;
      }
    }
    
    throw error;
  };
};
```

## Request Batching and Deduplication

The API client supports batching multiple requests into a single HTTP request and deduplicating identical concurrent requests.

### Request Batcher

```typescript
export interface BatchRequest {
  id: string;
  method: string;
  url: string;
  body?: any;
}

export interface BatchResponse {
  id: string;
  status: number;
  data: any;
}

export class RequestBatcher {
  private batchSize: number;
  private batchTimeout: number;
  private pendingRequests: Map<string, { request: BatchRequest, resolve: (value: any) => void, reject: (error: any) => void }>;
  private batchTimeoutId: NodeJS.Timeout | null;
  private apiClient: IAPIClient;

  constructor(apiClient: IAPIClient, batchSize: number = 10, batchTimeout: number = 50) {
    this.apiClient = apiClient;
    this.batchSize = batchSize;
    this.batchTimeout = batchTimeout;
    this.pendingRequests = new Map();
    this.batchTimeoutId = null;
  }

  public async add<T>(method: string, url: string, body?: any): Promise<T> {
    const requestId = this.generateRequestId(method, url, body);
    
    // Check for duplicates
    const existingRequest = this.pendingRequests.get(requestId);
    if (existingRequest) {
      return new Promise<T>((resolve, reject) => {
        existingRequest.resolve = (value) => resolve(value as T);
        existingRequest.reject = reject;
      });
    }
    
    // Create a new request
    return new Promise<T>((resolve, reject) => {
      this.pendingRequests.set(requestId, {
        request: { id: requestId, method, url, body },
        resolve: (value) => resolve(value as T),
        reject
      });
      
      // Schedule a batch send if not already scheduled
      if (!this.batchTimeoutId) {
        this.batchTimeoutId = setTimeout(() => this.sendBatch(), this.batchTimeout);
      }
      
      // Send immediately if we've reached batch size
      if (this.pendingRequests.size >= this.batchSize) {
        if (this.batchTimeoutId) {
          clearTimeout(this.batchTimeoutId);
          this.batchTimeoutId = null;
        }
        this.sendBatch();
      }
    });
  }

  private generateRequestId(method: string, url: string, body?: any): string {
    // Simple hash function for request deduplication
    const bodyStr = body ? JSON.stringify(body) : '';
    return `${method}:${url}:${bodyStr}`;
  }

  private async sendBatch(): Promise<void> {
    // No pending requests
    if (this.pendingRequests.size === 0) {
      return;
    }
    
    // Get all pending requests
    const requestEntries = Array.from(this.pendingRequests.entries());
    this.pendingRequests.clear();
    this.batchTimeoutId = null;
    
    // Create batch request
    const batchedRequests = requestEntries.map(([, { request }]) => request);
    
    try {
      // Send the batched request
      const response = await this.apiClient.post<BatchResponse[]>('/batch', {
        requests: batchedRequests
      });
      
      // Process responses
      const responseMap = new Map(response.data.map(res => [res.id, res]));
      
      for (const [requestId, { resolve, reject }] of requestEntries) {
        const requestResponse = responseMap.get(requestId);
        
        if (requestResponse) {
          if (requestResponse.status >= 200 && requestResponse.status < 300) {
            resolve(requestResponse.data);
          } else {
            const error = new Error(`Request failed with status ${requestResponse.status}`);
            (error as APIError).status = requestResponse.status;
            (error as APIError).data = requestResponse.data;
            reject(error);
          }
        } else {
          reject(new Error(`No response found for request ${requestId}`));
        }
      }
    } catch (error) {
      // If the batch request itself fails, reject all requests
      for (const [, { reject }] of requestEntries) {
        reject(error);
      }
    }
  }
}
```

## API Versioning Support

The API client supports working with versioned APIs through versioning interceptors and configuration.

```typescript
export interface VersionConfig {
  header?: string;
  queryParam?: string;
  path?: boolean;
}

export const createVersionInterceptor = (version: string, config: VersionConfig = {}) => {
  return (requestConfig: APIRequestConfig): APIRequestConfig => {
    const newConfig = { ...requestConfig };
    
    // Add version as header
    if (config.header) {
      const headers = new Headers(newConfig.headers || {});
      headers.set(config.header, version);
      newConfig.headers = headers;
    }
    
    // Add version as query parameter
    if (config.queryParam) {
      newConfig.params = {
        ...(newConfig.params || {}),
        [config.queryParam]: version
      };
    }
    
    // Add version to path
    if (config.path && newConfig.url) {
      if (!newConfig.url.startsWith('/')) {
        newConfig.url = `/${newConfig.url}`;
      }
      newConfig.url = `/v${version}${newConfig.url}`;
    }
    
    return newConfig;
  };
};
```

## Mock API Clients

For testing and development, mock implementations of the API clients are provided. These follow the same interfaces but return predefined data.

```typescript
export class MockUserAPIClient implements IUserAPIClient {
  private mockUsers: User[] = [/* sample data */];
  private mockPreferences: UserPreferences = {/* sample data */};
  
  public async getCurrentUser(): Promise<APIResponse<User>> {
    return this.createResponse(this.mockUsers[0]);
  }
  
  public async updateUser(userId: string, userData: Partial<User>): Promise<APIResponse<User>> {
    const user = this.mockUsers.find(u => u.id === userId);
    if (!user) {
      return this.createErrorResponse(404, 'User not found');
    }
    
    const updatedUser = { ...user, ...userData, updatedAt: new Date().toISOString() };
    return this.createResponse(updatedUser);
  }
  
  public async getUserPreferences(): Promise<APIResponse<UserPreferences>> {
    return this.createResponse(this.mockPreferences);
  }
  
  public async updateUserPreferences(preferences: Partial<UserPreferences>): Promise<APIResponse<UserPreferences>> {
    this.mockPreferences = { ...this.mockPreferences, ...preferences };
    return this.createResponse(this.mockPreferences);
  }
  
  private createResponse<T>(data: T): APIResponse<T> {
    return {
      data,
      status: 200,
      statusText: 'OK',
      headers: new Headers(),
      config: {}
    };
  }
  
  private createErrorResponse<T>(status: number, message: string): Promise<APIResponse<T>> {
    const error = new Error(message) as APIError;
    error.status = status;
    return Promise.reject(error);
  }
}
```

## Usage Examples

### Setting Up API Clients

```typescript
// Create auth service
const authService = new AuthService();

// Create base client with interceptors
const baseClient = new BaseAPIClient('https://api.example.com');

// Add request interceptors
baseClient.addRequestInterceptor(createVersionInterceptor('1'));
baseClient.addRequestInterceptor(createAuthInterceptor(authService));
baseClient.addRequestInterceptor(createRequestLoggerInterceptor(logger));

// Add response interceptors
baseClient.addResponseInterceptor(createResponseLoggerInterceptor(logger));

// Add error interceptors
baseClient.addErrorInterceptor(createRetryInterceptor(3));
baseClient.addErrorInterceptor(createAuthErrorInterceptor(authService, () => authService.refreshToken()));

// Create service-specific clients
const userClient = new UserAPIClient('https://api.example.com/users', baseClient.defaultConfig);
const profileClient = new ProfileAPIClient('https://api.example.com/profiles', baseClient.defaultConfig);
const chatClient = new ChatAPIClient('https://api.example.com/chat', baseClient.defaultConfig);

// Apply the same interceptors to service clients
[userClient, profileClient, chatClient].forEach(client => {
  baseClient.requestInterceptors.forEach(interceptor => client.addRequestInterceptor(interceptor));
  baseClient.responseInterceptors.forEach(interceptor => client.addResponseInterceptor(interceptor));
  baseClient.errorInterceptors.forEach(interceptor => client.addErrorInterceptor(interceptor));
});
```

### API Client Provider

```typescript
// Create a context for accessing API clients
const APIClientContext = React.createContext<{
  user: IUserAPIClient;
  profile: IProfileAPIClient;
  chat: IChatAPIClient;
} | null>(null);

export const APIClientProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  // Choose real or mock clients based on environment
  const userClient = process.env.REACT_APP_USE_MOCKS === 'true' 
    ? new MockUserAPIClient() 
    : new UserAPIClient();
    
  const profileClient = process.env.REACT_APP_USE_MOCKS === 'true'
    ? new MockProfileAPIClient()
    : new ProfileAPIClient();
    
  const chatClient = process.env.REACT_APP_USE_MOCKS === 'true'
    ? new MockChatAPIClient()
    : new ChatAPIClient();
  
  return (
    <APIClientContext.Provider value={{ user: userClient, profile: profileClient, chat: chatClient }}>
      {children}
    </APIClientContext.Provider>
  );
};

// Custom hook for accessing API clients
export const useAPIClient = () => {
  const context = React.useContext(APIClientContext);
  if (!context) {
    throw new Error('useAPIClient must be used within an APIClientProvider');
  }
  return context;
};
```

## Testing Strategy

API clients can be tested using different approaches:

1. **Unit Tests**: Testing individual client methods with mocked fetch calls
2. **Integration Tests**: Testing clients against a mock server
3. **Contract Tests**: Testing against service specifications (Swagger/OpenAPI)

Example unit test:

```typescript
describe('UserAPIClient', () => {
  let client: UserAPIClient;
  let mockFetch: jest.SpyInstance;
  
  beforeEach(() => {
    client = new UserAPIClient('https://api.example.com/users');
    mockFetch = jest.spyOn(global, 'fetch').mockImplementation();
  });
  
  afterEach(() => {
    mockFetch.mockRestore();
  });
  
  it('should get the current user', async () => {
    const mockUser = { id: '123', username: 'testuser' };
    mockFetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      statusText: 'OK',
      json: async () => mockUser,
      headers: new Headers()
    });
    
    const response = await client.getCurrentUser();
    
    expect(mockFetch).toHaveBeenCalledWith(
      'https://api.example.com/users/me',
      expect.objectContaining({ method: 'GET' })
    );
    expect(response.data).toEqual(mockUser);
    expect(response.status).toBe(200);
  });
  
  it('should handle errors', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 404,
      statusText: 'Not Found',
      json: async () => ({ message: 'User not found' }),
      headers: new Headers()
    });
    
    await expect(client.getCurrentUser()).rejects.toThrow();
  });
});
```

## Conclusion

The KAI API client architecture provides a flexible, extensible system for communicating with backend services. By following SOLID principles and implementing clear interfaces, it supports a variety of use cases including testing, mocking, and versioning. The interceptor pattern allows for separation of concerns, making the system easy to maintain and extend. 