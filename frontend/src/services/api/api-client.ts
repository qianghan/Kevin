import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse, AxiosError, InternalAxiosRequestConfig } from 'axios';

// Define interfaces for API client (ISP - Interface Segregation Principle)
export interface IRequestConfig extends AxiosRequestConfig {}
export interface IResponse<T = any> extends AxiosResponse<T> {}

// Base API client interface (DIP - Dependency Inversion Principle)
export interface IApiClient {
  get<T = any>(url: string, config?: IRequestConfig): Promise<IResponse<T>>;
  post<T = any>(url: string, data?: any, config?: IRequestConfig): Promise<IResponse<T>>;
  put<T = any>(url: string, data?: any, config?: IRequestConfig): Promise<IResponse<T>>;
  delete<T = any>(url: string, config?: IRequestConfig): Promise<IResponse<T>>;
}

// Base error handling for API responses
export class ApiError extends Error {
  code: number;
  responseData?: any;

  constructor(message: string, code: number, responseData?: any) {
    super(message);
    this.name = 'ApiError';
    this.code = code;
    this.responseData = responseData;
  }
}

// Implementation of the API client (SRP - Single Responsibility Principle)
export class ApiClient implements IApiClient {
  private client: AxiosInstance;
  
  constructor(baseURL: string, timeout: number = 30000) {
    this.client = axios.create({
      baseURL,
      timeout,
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    // Add request interceptor
    this.client.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => {
        // You can add auth tokens here
        const token = localStorage.getItem('auth_token');
        if (token && config.headers) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error: any) => {
        return Promise.reject(error);
      }
    );
    
    // Add response interceptor
    this.client.interceptors.response.use(
      (response: AxiosResponse) => {
        return response;
      },
      (error: AxiosError) => {
        if (error.response) {
          // The request was made and the server responded with a status code
          // that falls out of the range of 2xx
          const { data, status } = error.response;
          const errorMessage = typeof data === 'object' && data !== null 
            ? (data as any).message || 'An error occurred with the API request'
            : 'An error occurred with the API request';
            
          throw new ApiError(
            errorMessage,
            status,
            data
          );
        } else if (error.request) {
          // The request was made but no response was received
          throw new ApiError('No response received from server', 0);
        } else {
          // Something happened in setting up the request that triggered an Error
          throw new ApiError(error.message || 'Unknown error', 0);
        }
      }
    );
  }
  
  // Implement the interface methods
  public async get<T = any>(url: string, config?: IRequestConfig): Promise<IResponse<T>> {
    return this.client.get<T>(url, config);
  }
  
  public async post<T = any>(url: string, data?: any, config?: IRequestConfig): Promise<IResponse<T>> {
    return this.client.post<T>(url, data, config);
  }
  
  public async put<T = any>(url: string, data?: any, config?: IRequestConfig): Promise<IResponse<T>> {
    return this.client.put<T>(url, data, config);
  }
  
  public async delete<T = any>(url: string, config?: IRequestConfig): Promise<IResponse<T>> {
    return this.client.delete<T>(url, config);
  }
}

// Factory to create API clients (OCP - Open/Closed Principle)
export const createApiClient = (baseURL: string): IApiClient => {
  return new ApiClient(baseURL);
};

// Default API client instance with environment variables
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3001/api';
export const apiClient = createApiClient(API_BASE_URL); 