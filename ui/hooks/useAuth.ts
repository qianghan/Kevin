import { useState, useEffect, useCallback, createContext, useContext, ReactNode } from 'react';
import { useRouter } from 'next/navigation';
import { userServiceFactory } from '@/lib/services/user/UserServiceFactory';
import { LoginCredentials, RegistrationData, User } from '@/lib/interfaces/services/user.service';

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  error: string | null;
  login: (credentials: LoginCredentials) => Promise<boolean>;
  register: (data: RegistrationData) => Promise<boolean>;
  logout: () => Promise<void>;
  requestPasswordReset: (email: string) => Promise<boolean>;
  resetPassword: (token: string, newPassword: string) => Promise<boolean>;
  verifyEmail: (token: string) => Promise<boolean>;
  changePassword: (currentPassword: string, newPassword: string) => Promise<boolean>;
}

// Default context value
const defaultAuthContext: AuthContextType = {
  user: null,
  isLoading: false,
  isAuthenticated: false,
  error: null,
  login: async () => false,
  register: async () => false,
  logout: async () => {},
  requestPasswordReset: async () => false,
  resetPassword: async () => false,
  verifyEmail: async () => false,
  changePassword: async () => false,
};

// Create a context for auth state
const AuthContext = createContext<AuthContextType>(defaultAuthContext);

// Hook to manage auth state and methods
export const useAuthState = () => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  // Get the authentication service from our factory
  const authService = userServiceFactory.createAuthService();

  // Check if user is authenticated on initial load
  useEffect(() => {
    const initAuth = async () => {
      setIsLoading(true);
      try {
        const currentUser = await authService.getCurrentUser();
        setUser(currentUser);
      } catch (err) {
        console.error('Authentication initialization error:', err);
        setError('Failed to initialize authentication');
      } finally {
        setIsLoading(false);
      }
    };

    initAuth();
  }, []);

  // Login function
  const login = useCallback(async (credentials: LoginCredentials): Promise<boolean> => {
    setIsLoading(true);
    setError(null);
    
    try {
      const authResponse = await authService.login(credentials);
      if (authResponse && authResponse.user) {
        setUser(authResponse.user);
        return true;
      }
      return false;
    } catch (err) {
      console.error('Login error:', err);
      setError(err instanceof Error ? err.message : 'Login failed');
      return false;
    } finally {
      setIsLoading(false);
    }
  }, [authService]);

  // Registration function
  const register = useCallback(async (data: RegistrationData): Promise<boolean> => {
    setIsLoading(true);
    setError(null);
    
    try {
      const authResponse = await authService.register(data);
      if (authResponse && authResponse.user) {
        setUser(authResponse.user);
        return true;
      }
      return false;
    } catch (err) {
      console.error('Registration error:', err);
      setError(err instanceof Error ? err.message : 'Registration failed');
      return false;
    } finally {
      setIsLoading(false);
    }
  }, [authService]);

  // Logout function
  const logout = useCallback(async (): Promise<void> => {
    setIsLoading(true);
    setError(null);
    
    try {
      await authService.logout();
      setUser(null);
      router.push('/login');
    } catch (err) {
      console.error('Logout error:', err);
      setError(err instanceof Error ? err.message : 'Logout failed');
    } finally {
      setIsLoading(false);
    }
  }, [authService, router]);

  // Request password reset
  const requestPasswordReset = useCallback(async (email: string): Promise<boolean> => {
    setIsLoading(true);
    setError(null);
    
    try {
      await authService.requestPasswordReset({ email });
      return true;
    } catch (err) {
      console.error('Password reset request error:', err);
      setError(err instanceof Error ? err.message : 'Password reset request failed');
      return false;
    } finally {
      setIsLoading(false);
    }
  }, [authService]);

  // Reset password with token
  const resetPassword = useCallback(async (token: string, newPassword: string): Promise<boolean> => {
    setIsLoading(true);
    setError(null);
    
    try {
      return await authService.resetPassword(token, newPassword);
    } catch (err) {
      console.error('Password reset error:', err);
      setError(err instanceof Error ? err.message : 'Password reset failed');
      return false;
    } finally {
      setIsLoading(false);
    }
  }, [authService]);

  // Verify email with token
  const verifyEmail = useCallback(async (token: string): Promise<boolean> => {
    setIsLoading(true);
    setError(null);
    
    try {
      const result = await authService.verifyEmail(token);
      if (result) {
        // Refresh the user to update verification status
        const currentUser = await authService.getCurrentUser();
        setUser(currentUser);
      }
      return result;
    } catch (err) {
      console.error('Email verification error:', err);
      setError(err instanceof Error ? err.message : 'Email verification failed');
      return false;
    } finally {
      setIsLoading(false);
    }
  }, [authService]);

  // Change password
  const changePassword = useCallback(async (currentPassword: string, newPassword: string): Promise<boolean> => {
    setIsLoading(true);
    setError(null);
    
    try {
      return await authService.changePassword({
        currentPassword,
        newPassword
      });
    } catch (err) {
      console.error('Password change error:', err);
      setError(err instanceof Error ? err.message : 'Password change failed');
      return false;
    } finally {
      setIsLoading(false);
    }
  }, [authService]);

  return {
    user,
    isLoading,
    isAuthenticated: !!user,
    error,
    login,
    register,
    logout,
    requestPasswordReset,
    resetPassword,
    verifyEmail,
    changePassword,
  };
};

// Custom hook for using auth context
export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

// Export the context so it can be used in a provider component
export { AuthContext }; 