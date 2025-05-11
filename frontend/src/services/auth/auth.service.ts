import { serviceDiscovery } from '../discovery/service-discovery';

export interface User {
  id: string;
  name: string;
  email: string;
  role: 'admin' | 'user';
}

export interface AuthResponse {
  user: User;
  token: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

class AuthService {
  private static instance: AuthService;
  private token: string | null = null;
  private user: User | null = null;

  private constructor() {
    // Initialize from localStorage if available
    if (typeof window !== 'undefined') {
      this.token = localStorage.getItem('auth_token');
      const userStr = localStorage.getItem('user');
      if (userStr) {
        try {
          this.user = JSON.parse(userStr);
        } catch (e) {
          console.error('Failed to parse stored user:', e);
        }
      }
    }
  }

  public static getInstance(): AuthService {
    if (!AuthService.instance) {
      AuthService.instance = new AuthService();
    }
    return AuthService.instance;
  }

  public async login(credentials: LoginCredentials): Promise<AuthResponse> {
    // Development bypass
    if (process.env.NEXT_PUBLIC_AUTH_BYPASS === 'true') {
      console.log('Development mode: Auth bypass enabled');
      const devUser: User = {
        id: 'dev-1',
        name: 'Development User',
        email: credentials.email,
        role: 'admin',
      };
      const devResponse: AuthResponse = {
        user: devUser,
        token: 'dev-token',
      };
      this.handleAuthSuccess(devResponse);
      return devResponse;
    }

    const response = await fetch(`${serviceDiscovery.getServiceStatus().auth.url}/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(credentials),
    });

    if (!response.ok) {
      throw new Error('Authentication failed');
    }

    const authResponse: AuthResponse = await response.json();
    this.handleAuthSuccess(authResponse);
    return authResponse;
  }

  public logout(): void {
    this.token = null;
    this.user = null;
    if (typeof window !== 'undefined') {
      localStorage.removeItem('auth_token');
      localStorage.removeItem('user');
    }
  }

  public getToken(): string | null {
    return this.token;
  }

  public getUser(): User | null {
    return this.user;
  }

  public isAuthenticated(): boolean {
    return !!this.token && !!this.user;
  }

  private handleAuthSuccess(response: AuthResponse): void {
    this.token = response.token;
    this.user = response.user;
    if (typeof window !== 'undefined') {
      localStorage.setItem('auth_token', response.token);
      localStorage.setItem('user', JSON.stringify(response.user));
    }
  }
}

export const authService = AuthService.getInstance();
export default authService; 