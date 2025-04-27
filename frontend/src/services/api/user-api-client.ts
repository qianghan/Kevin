import { IApiClient, apiClient, IResponse } from './api-client';

// User data model interface (ISP)
export interface IUser {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  role: string;
  preferences?: {
    theme?: 'light' | 'dark' | 'system';
    language?: string;
    notifications?: boolean;
  };
  createdAt: string;
  updatedAt: string;
}

// Define specific user API methods (ISP)
export interface IUserApiClient {
  getCurrentUser(): Promise<IUser>;
  getUserById(id: string): Promise<IUser>;
  updateUser(id: string, userData: Partial<IUser>): Promise<IUser>;
  updateUserPreferences(id: string, preferences: Partial<IUser['preferences']>): Promise<IUser>;
}

// Implement user API client (SRP - Single Responsibility Principle)
export class UserApiClient implements IUserApiClient {
  private apiClient: IApiClient;
  private baseUrl: string = '/users';
  
  constructor(apiClient: IApiClient) {
    this.apiClient = apiClient;
  }
  
  public async getCurrentUser(): Promise<IUser> {
    const response = await this.apiClient.get<{ data: IUser }>(`${this.baseUrl}/me`);
    return response.data.data;
  }
  
  public async getUserById(id: string): Promise<IUser> {
    const response = await this.apiClient.get<{ data: IUser }>(`${this.baseUrl}/${id}`);
    return response.data.data;
  }
  
  public async updateUser(id: string, userData: Partial<IUser>): Promise<IUser> {
    const response = await this.apiClient.put<{ data: IUser }>(`${this.baseUrl}/${id}`, userData);
    return response.data.data;
  }
  
  public async updateUserPreferences(id: string, preferences: Partial<IUser['preferences']>): Promise<IUser> {
    const response = await this.apiClient.put<{ data: IUser }>(`${this.baseUrl}/${id}/preferences`, preferences);
    return response.data.data;
  }
}

// Factory to create user API client (OCP - Open/Closed Principle)
export const createUserApiClient = (client: IApiClient = apiClient): IUserApiClient => {
  return new UserApiClient(client);
};

// Default user API client instance
export const userApiClient = createUserApiClient(); 