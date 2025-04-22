# Sample Code for Service Integration

This document provides sample code and examples for integrating with the User Management System.

## React Frontend Integration

### Authentication Hook (TypeScript)

```typescript
import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';

// Types
export interface User {
  id: string;
  email: string;
  name: string;
  role: 'student' | 'parent' | 'admin' | 'support';
  emailVerified: boolean;
  profileCompleteness: number;
  preferences: {
    theme: 'light' | 'dark' | 'system';
    language: string;
    emailNotifications: boolean;
  };
}

interface AuthState {
  isAuthenticated: boolean;
  user: User | null;
  loading: boolean;
  error: string | null;
}

interface UseAuthReturn extends AuthState {
  login: (email: string, password: string) => Promise<boolean>;
  register: (userData: RegisterData) => Promise<boolean>;
  logout: () => Promise<void>;
  updateProfile: (profileData: Partial<User>) => Promise<boolean>;
}

interface RegisterData {
  email: string;
  password: string;
  name: string;
}

// API Client
const API_BASE_URL = '/api/userman';
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
});

// Add token to all requests
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Handle 401 errors
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Clear token if it's invalid or expired
      localStorage.removeItem('auth_token');
      localStorage.removeItem('user');
      // Redirect to login if needed
      if (window.location.pathname !== '/login') {
        window.location.href = `/login?redirect=${encodeURIComponent(window.location.pathname)}`;
      }
    }
    return Promise.reject(error);
  }
);

// Auth Hook
export function useAuth(): UseAuthReturn {
  const [state, setState] = useState<AuthState>({
    isAuthenticated: false,
    user: null,
    loading: true,
    error: null,
  });

  // Check if user is already authenticated
  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('auth_token');
      const userJson = localStorage.getItem('user');
      
      if (token && userJson) {
        try {
          // Verify the token is still valid
          const response = await apiClient.get('/users/profile');
          setState({
            isAuthenticated: true,
            user: response.data,
            loading: false,
            error: null,
          });
        } catch (error) {
          setState({
            isAuthenticated: false,
            user: null,
            loading: false,
            error: 'Authentication failed',
          });
        }
      } else {
        setState({
          isAuthenticated: false,
          user: null,
          loading: false,
          error: null,
        });
      }
    };

    checkAuth();
  }, []);

  // Login function
  const login = useCallback(async (email: string, password: string): Promise<boolean> => {
    setState((prevState) => ({ ...prevState, loading: true, error: null }));
    
    try {
      const response = await apiClient.post('/auth/login', { email, password });
      const { token, user } = response.data;
      
      localStorage.setItem('auth_token', token);
      localStorage.setItem('user', JSON.stringify(user));
      
      setState({
        isAuthenticated: true,
        user,
        loading: false,
        error: null,
      });
      
      return true;
    } catch (error) {
      setState((prevState) => ({
        ...prevState,
        loading: false,
        error: error.response?.data?.message || 'Login failed',
      }));
      return false;
    }
  }, []);

  // Register function
  const register = useCallback(async (userData: RegisterData): Promise<boolean> => {
    setState((prevState) => ({ ...prevState, loading: true, error: null }));
    
    try {
      await apiClient.post('/auth/register', userData);
      setState((prevState) => ({ ...prevState, loading: false }));
      return true;
    } catch (error) {
      setState((prevState) => ({
        ...prevState,
        loading: false,
        error: error.response?.data?.message || 'Registration failed',
      }));
      return false;
    }
  }, []);

  // Logout function
  const logout = useCallback(async (): Promise<void> => {
    try {
      await apiClient.post('/auth/logout');
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      localStorage.removeItem('auth_token');
      localStorage.removeItem('user');
      setState({
        isAuthenticated: false,
        user: null,
        loading: false,
        error: null,
      });
    }
  }, []);

  // Update profile function
  const updateProfile = useCallback(async (profileData: Partial<User>): Promise<boolean> => {
    setState((prevState) => ({ ...prevState, loading: true, error: null }));
    
    try {
      const response = await apiClient.put('/users/profile', profileData);
      const updatedUser = response.data;
      
      localStorage.setItem('user', JSON.stringify(updatedUser));
      
      setState((prevState) => ({
        ...prevState,
        user: updatedUser,
        loading: false,
      }));
      
      return true;
    } catch (error) {
      setState((prevState) => ({
        ...prevState,
        loading: false,
        error: error.response?.data?.message || 'Failed to update profile',
      }));
      return false;
    }
  }, []);

  return {
    ...state,
    login,
    register,
    logout,
    updateProfile,
  };
}
```

### Auth Provider Component

```tsx
import React, { createContext, useContext, ReactNode } from 'react';
import { useAuth, User } from './useAuth';

// Create auth context
interface AuthContextType {
  isAuthenticated: boolean;
  user: User | null;
  loading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<boolean>;
  register: (userData: { email: string; password: string; name: string }) => Promise<boolean>;
  logout: () => Promise<void>;
  updateProfile: (profileData: Partial<User>) => Promise<boolean>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Auth provider component
export function AuthProvider({ children }: { children: ReactNode }) {
  const auth = useAuth();
  
  return (
    <AuthContext.Provider value={auth}>
      {children}
    </AuthContext.Provider>
  );
}

// Custom hook to use auth context
export function useAuthContext() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuthContext must be used within an AuthProvider');
  }
  return context;
}
```

### Private Route Component

```tsx
import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuthContext } from './AuthProvider';

interface PrivateRouteProps {
  children: React.ReactNode;
  requiredRole?: 'student' | 'parent' | 'admin' | 'support';
}

export function PrivateRoute({ children, requiredRole }: PrivateRouteProps) {
  const { isAuthenticated, user, loading } = useAuthContext();
  const location = useLocation();

  // Show loading state
  if (loading) {
    return <div>Loading...</div>;
  }

  // Redirect to login if not authenticated
  if (!isAuthenticated || !user) {
    return <Navigate to={`/login?redirect=${encodeURIComponent(location.pathname)}`} replace />;
  }

  // Check role if required
  if (requiredRole && user.role !== requiredRole) {
    // Redirect to unauthorized page
    return <Navigate to="/unauthorized" replace />;
  }

  // Render the protected content
  return <>{children}</>;
}
```

## Node.js Service Integration

### Express Middleware for Authentication

```javascript
const axios = require('axios');

// Configuration
const config = {
  userManagementBaseUrl: process.env.USER_MANAGEMENT_API_URL || 'http://api.example.com/api/userman',
  apiKey: process.env.USER_MANAGEMENT_API_KEY,
  apiSecret: process.env.USER_MANAGEMENT_API_SECRET,
};

// Service token cache
let serviceToken = null;
let tokenExpiration = null;

// Get service token
async function getServiceToken() {
  // Return cached token if valid
  if (serviceToken && tokenExpiration && Date.now() < tokenExpiration) {
    return serviceToken;
  }
  
  try {
    const response = await axios.post(
      `${config.userManagementBaseUrl}/auth/service-token`,
      {
        apiKey: config.apiKey,
        apiSecret: config.apiSecret,
      }
    );
    
    // Cache the token with expiration
    serviceToken = response.data.token;
    // Set expiration 5 minutes before actual expiry to avoid edge cases
    tokenExpiration = Date.now() + ((response.data.expiresIn || 3600) - 300) * 1000;
    
    return serviceToken;
  } catch (error) {
    console.error('Failed to get service token:', error.response?.data || error.message);
    throw new Error('Service authentication failed');
  }
}

// Validate user token
async function validateToken(userToken) {
  try {
    const token = await getServiceToken();
    
    const response = await axios.post(
      `${config.userManagementBaseUrl}/auth/validate-token`,
      { token: userToken },
      {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      }
    );
    
    return response.data;
  } catch (error) {
    console.error('Token validation failed:', error.response?.data || error.message);
    return null;
  }
}

// Check service access
async function checkServiceAccess(userId, endpoint) {
  try {
    const token = await getServiceToken();
    
    const response = await axios.post(
      `${config.userManagementBaseUrl}/services/access`,
      {
        userId,
        serviceId: config.apiKey,
        endpoint,
      },
      {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      }
    );
    
    return response.data.hasAccess === true;
  } catch (error) {
    console.error('Service access check failed:', error.response?.data || error.message);
    return false;
  }
}

// Authentication middleware
function requireAuth(req, res, next) {
  const authHeader = req.headers.authorization;
  
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ error: 'Authentication required' });
  }
  
  const token = authHeader.split(' ')[1];
  
  validateToken(token)
    .then(userData => {
      if (!userData) {
        return res.status(401).json({ error: 'Invalid or expired token' });
      }
      
      // Attach user data to request
      req.user = userData;
      next();
    })
    .catch(error => {
      console.error('Auth middleware error:', error);
      res.status(500).json({ error: 'Authentication service unavailable' });
    });
}

// Role-based authorization middleware
function requireRole(role) {
  return (req, res, next) => {
    // Make sure auth middleware ran first
    if (!req.user) {
      return res.status(401).json({ error: 'Authentication required' });
    }
    
    if (req.user.role !== role) {
      return res.status(403).json({ error: `${role} role required` });
    }
    
    next();
  };
}

// Service access middleware
function requireServiceAccess(endpoint) {
  return async (req, res, next) => {
    // Make sure auth middleware ran first
    if (!req.user) {
      return res.status(401).json({ error: 'Authentication required' });
    }
    
    try {
      const hasAccess = await checkServiceAccess(req.user.id, endpoint);
      
      if (!hasAccess) {
        return res.status(403).json({ error: 'Service access denied' });
      }
      
      next();
    } catch (error) {
      console.error('Service access middleware error:', error);
      res.status(500).json({ error: 'Authorization service unavailable' });
    }
  };
}

module.exports = {
  requireAuth,
  requireRole,
  requireServiceAccess,
  validateToken,
  checkServiceAccess,
};
```

### Express Route Example

```javascript
const express = require('express');
const { requireAuth, requireRole, requireServiceAccess } = require('./auth-middleware');

const router = express.Router();

// Public routes
router.get('/public-data', (req, res) => {
  res.json({ message: 'This is public data' });
});

// Protected routes with authentication
router.get('/user-data', requireAuth, (req, res) => {
  res.json({
    message: 'This is protected user data',
    user: {
      id: req.user.id,
      name: req.user.name,
      email: req.user.email,
      role: req.user.role,
    },
  });
});

// Role-based routes
router.get('/admin-data', requireAuth, requireRole('admin'), (req, res) => {
  res.json({
    message: 'This is admin-only data',
    adminInfo: {
      secretCode: 'admin123',
      dashboardAccess: true,
    },
  });
});

// Service endpoint access
router.get('/premium-feature', 
  requireAuth, 
  requireServiceAccess('/premium-feature'),
  (req, res) => {
    res.json({
      message: 'This is a premium feature',
      featureData: {
        special: true,
        unlocked: true,
      },
    });
  }
);

// Parent accessing student data
router.get('/student/:studentId/data', requireAuth, async (req, res) => {
  const { studentId } = req.params;
  
  // Check if user is the student or a parent of the student
  if (req.user.id === studentId) {
    // Direct access
    return res.json({ studentData: 'Student accessing own data' });
  }
  
  // Check parent relationship
  try {
    const token = await getServiceToken();
    
    const response = await axios.get(
      `${config.userManagementBaseUrl}/admin/users/${req.user.id}/relationships/student`,
      {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      }
    );
    
    const relatedStudents = response.data;
    const isParentOfStudent = relatedStudents.some(student => student.id === studentId);
    
    if (!isParentOfStudent) {
      return res.status(403).json({ error: 'Access denied. Not authorized to view this student data' });
    }
    
    res.json({ studentData: 'Parent accessing student data' });
  } catch (error) {
    console.error('Error checking parent-student relationship:', error);
    res.status(500).json({ error: 'Failed to verify relationship' });
  }
});

module.exports = router;
```

## Python Service Integration

### FastAPI Integration Example

```python
from fastapi import FastAPI, Depends, HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx
import os
from typing import Dict, Optional, List, Any
import time

# Configuration from environment variables
USER_MANAGEMENT_API_URL = os.getenv("USER_MANAGEMENT_API_URL", "http://api.example.com/api/userman")
API_KEY = os.getenv("USER_MANAGEMENT_API_KEY")
API_SECRET = os.getenv("USER_MANAGEMENT_API_SECRET")

# Security scheme
security = HTTPBearer()

# Service token cache
service_token = None
token_expiration = 0

app = FastAPI(title="Service API", description="API with User Management System integration")

async def get_service_token() -> str:
    """Get a service token for API authentication."""
    global service_token, token_expiration
    
    # Return cached token if valid
    if service_token and time.time() < token_expiration:
        return service_token
    
    # Get new token
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{USER_MANAGEMENT_API_URL}/auth/service-token",
            json={
                "apiKey": API_KEY,
                "apiSecret": API_SECRET
            }
        )
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Failed to authenticate with User Management System"
            )
        
        data = response.json()
        service_token = data.get("token")
        expires_in = data.get("expiresIn", 3600)
        # Set expiration 5 minutes before actual expiry
        token_expiration = time.time() + (expires_in - 300)
        
        return service_token

async def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)) -> Dict[str, Any]:
    """Validate user token and return user information."""
    token = credentials.credentials
    
    # Get service token
    service_token = await get_service_token()
    
    # Validate user token
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{USER_MANAGEMENT_API_URL}/auth/validate-token",
            json={"token": token},
            headers={"Authorization": f"Bearer {service_token}"}
        )
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        return response.json()

async def check_service_access(user_id: str, endpoint: str) -> bool:
    """Check if a user has access to a specific service endpoint."""
    # Get service token
    service_token = await get_service_token()
    
    # Check access
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{USER_MANAGEMENT_API_URL}/services/access",
            json={
                "userId": user_id,
                "serviceId": API_KEY,
                "endpoint": endpoint
            },
            headers={"Authorization": f"Bearer {service_token}"}
        )
        
        if response.status_code != 200:
            return False
        
        data = response.json()
        return data.get("hasAccess", False)

async def require_role(user: Dict[str, Any], role: str) -> Dict[str, Any]:
    """Check if user has the required role."""
    if user.get("role") != role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"{role} role required"
        )
    return user

async def require_service_access(user: Dict[str, Any], endpoint: str) -> Dict[str, Any]:
    """Check if user has access to the service endpoint."""
    has_access = await check_service_access(user.get("id"), endpoint)
    
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Service access denied"
        )
    
    return user

# Public endpoint
@app.get("/public-data")
async def get_public_data():
    return {"message": "This is public data"}

# Protected endpoint requiring authentication
@app.get("/user-data")
async def get_user_data(user: Dict[str, Any] = Depends(get_current_user)):
    return {
        "message": "This is protected user data",
        "user": {
            "id": user.get("id"),
            "name": user.get("name"),
            "email": user.get("email"),
            "role": user.get("role")
        }
    }

# Admin-only endpoint
@app.get("/admin-data")
async def get_admin_data(
    user: Dict[str, Any] = Depends(
        lambda u: require_role(get_current_user(), "admin")
    )
):
    return {
        "message": "This is admin-only data",
        "adminInfo": {
            "secretCode": "admin123",
            "dashboardAccess": True
        }
    }

# Premium feature endpoint
@app.get("/premium-feature")
async def get_premium_feature(
    user: Dict[str, Any] = Depends(
        lambda u: require_service_access(get_current_user(), "/premium-feature")
    )
):
    return {
        "message": "This is a premium feature",
        "featureData": {
            "special": True,
            "unlocked": True
        }
    }

# Parent accessing student data
@app.get("/student/{student_id}/data")
async def get_student_data(
    student_id: str,
    user: Dict[str, Any] = Depends(get_current_user)
):
    # Direct access for student
    if user.get("id") == student_id:
        return {"studentData": "Student accessing own data"}
    
    # Check parent relationship
    service_token = await get_service_token()
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{USER_MANAGEMENT_API_URL}/admin/users/{user.get('id')}/relationships/student",
            headers={"Authorization": f"Bearer {service_token}"}
        )
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to verify relationship"
            )
        
        related_students = response.json()
        is_parent_of_student = any(student.get("id") == student_id for student in related_students)
        
        if not is_parent_of_student:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Not authorized to view this student data"
            )
        
        return {"studentData": "Parent accessing student data"}
```

These code examples demonstrate how to integrate with the User Management System from different types of services and applications. Adapt them to your specific needs and programming language. 