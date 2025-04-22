# User Management System - Integration Examples

This document provides examples of how to integrate with the User Management System from various services.

## Authentication Flow

### TypeScript Example (React)

```typescript
// Example of integrating with the User Management System for authentication
import axios from 'axios';

// API client setup
const API_BASE_URL = '/api/userman';
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to all requests that require authentication
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

// Authentication service
export const AuthService = {
  // Login user
  async login(email: string, password: string) {
    try {
      const response = await apiClient.post('/auth/login', { email, password });
      const { token, user } = response.data;
      
      // Store token in localStorage
      localStorage.setItem('auth_token', token);
      localStorage.setItem('user', JSON.stringify(user));
      
      return { success: true, user };
    } catch (error) {
      return { 
        success: false, 
        error: error.response?.data?.message || 'Failed to login' 
      };
    }
  },

  // Register new user
  async register(userData: { name: string; email: string; password: string }) {
    try {
      const response = await apiClient.post('/auth/register', userData);
      return { success: true, user: response.data };
    } catch (error) {
      return { 
        success: false, 
        error: error.response?.data?.message || 'Failed to register' 
      };
    }
  },

  // Logout user
  async logout() {
    try {
      await apiClient.post('/auth/logout');
      localStorage.removeItem('auth_token');
      localStorage.removeItem('user');
      return { success: true };
    } catch (error) {
      return { 
        success: false, 
        error: error.response?.data?.message || 'Failed to logout' 
      };
    }
  },

  // Get current authenticated user
  async getCurrentUser() {
    try {
      const response = await apiClient.get('/users/profile');
      return { success: true, user: response.data };
    } catch (error) {
      // Clear invalid auth data
      if (error.response?.status === 401) {
        localStorage.removeItem('auth_token');
        localStorage.removeItem('user');
      }
      return { 
        success: false, 
        error: error.response?.data?.message || 'Failed to get user profile' 
      };
    }
  },

  // Check if user is authenticated
  isAuthenticated() {
    return !!localStorage.getItem('auth_token');
  }
};
```

### Python Example (Service Backend)

```python
import requests
import json
from typing import Dict, Any, Optional

class UserManagementClient:
    """Client for interacting with the User Management System API."""
    
    def __init__(self, base_url: str, api_key: str, api_secret: str):
        """Initialize the client with the API base URL and credentials.
        
        Args:
            base_url: Base URL for the User Management API
            api_key: API key for service authentication
            api_secret: API secret for service authentication
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.api_secret = api_secret
        self.service_token = None
    
    def _get_service_token(self) -> str:
        """Get a service token for API authentication."""
        if not self.service_token:
            response = requests.post(
                f"{self.base_url}/auth/service-token",
                json={
                    "apiKey": self.api_key,
                    "apiSecret": self.api_secret
                }
            )
            response.raise_for_status()
            self.service_token = response.json().get("token")
        return self.service_token
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers with authentication token."""
        return {
            "Authorization": f"Bearer {self._get_service_token()}",
            "Content-Type": "application/json"
        }
    
    def validate_token(self, user_token: str) -> Dict[str, Any]:
        """Validate a user's JWT token.
        
        Args:
            user_token: The JWT token to validate
            
        Returns:
            Dict containing user information if token is valid
        """
        response = requests.post(
            f"{self.base_url}/auth/validate-token",
            headers=self._get_headers(),
            json={"token": user_token}
        )
        response.raise_for_status()
        return response.json()
    
    def check_service_access(self, user_id: str, endpoint: str) -> bool:
        """Check if a user has access to a specific service endpoint.
        
        Args:
            user_id: The ID of the user
            endpoint: The service endpoint to check access for
            
        Returns:
            True if the user has access, False otherwise
        """
        response = requests.post(
            f"{self.base_url}/services/access",
            headers=self._get_headers(),
            json={
                "userId": user_id,
                "serviceId": self.api_key,
                "endpoint": endpoint
            }
        )
        response.raise_for_status()
        return response.json().get("hasAccess", False)
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user details by user ID.
        
        Args:
            user_id: The ID of the user
            
        Returns:
            Dict containing user information or None if not found
        """
        try:
            response = requests.get(
                f"{self.base_url}/admin/users/{user_id}",
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return None
            raise e
    
    def get_related_users(self, user_id: str, relationship_type: str) -> list:
        """Get users related to the specified user.
        
        Args:
            user_id: The ID of the user
            relationship_type: Type of relationship (parent, student, coparent)
            
        Returns:
            List of related users
        """
        response = requests.get(
            f"{self.base_url}/admin/users/{user_id}/relationships/{relationship_type}",
            headers=self._get_headers()
        )
        response.raise_for_status()
        return response.json()
```

## Service Integration

### Node.js Service Registration Example

```javascript
// Example of registering a service with the User Management System
const axios = require('axios');

async function registerService() {
  try {
    // Admin credentials
    const adminCredentials = {
      email: 'admin@example.com',
      password: 'adminPassword123'
    };
    
    // Login as admin
    const loginResponse = await axios.post(
      'http://api.example.com/api/userman/auth/login',
      adminCredentials
    );
    
    const { token } = loginResponse.data;
    
    // Service definition
    const serviceDefinition = {
      name: 'essay-service',
      displayName: 'Essay Evaluation Service',
      description: 'Service for essay submissions and evaluations',
      baseUrl: 'http://api.example.com/api/essays',
      iconUrl: 'http://assets.example.com/icons/essay-service.png',
      accessType: 'role_based',
      allowedRoles: ['student', 'parent', 'admin'],
      endpoints: [
        {
          path: '/essays',
          method: 'GET',
          requiredPermissions: ['essay:read']
        },
        {
          path: '/essays',
          method: 'POST',
          requiredPermissions: ['essay:create']
        },
        {
          path: '/essays/:id',
          method: 'GET',
          requiredPermissions: ['essay:read']
        },
        {
          path: '/essays/:id',
          method: 'PUT',
          requiredPermissions: ['essay:update']
        },
        {
          path: '/essays/:id/feedback',
          method: 'POST',
          requiredPermissions: ['essay:feedback']
        }
      ]
    };
    
    // Register the service
    const registerResponse = await axios.post(
      'http://api.example.com/api/userman/services',
      serviceDefinition,
      {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      }
    );
    
    console.log('Service registered successfully:', registerResponse.data);
    
    // Store the service credentials securely
    const { apiKey, apiSecret } = registerResponse.data;
    // Save these securely in environment variables or a secrets manager
    
    return {
      success: true,
      service: registerResponse.data
    };
  } catch (error) {
    console.error('Error registering service:', error.response?.data || error.message);
    return {
      success: false,
      error: error.response?.data?.message || 'Failed to register service'
    };
  }
}

module.exports = { registerService };
```

### Java Example (Service Access Check)

```java
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.util.HashMap;
import java.util.Map;
import org.json.JSONObject;

/**
 * Client for integrating with User Management System
 */
public class UserManagementClient {
    private final String baseUrl;
    private final String apiKey;
    private final String apiSecret;
    private String serviceToken;
    private final HttpClient httpClient;
    
    /**
     * Constructor for the User Management client
     * 
     * @param baseUrl Base URL for the User Management API
     * @param apiKey API key for service authentication
     * @param apiSecret API secret for service authentication
     */
    public UserManagementClient(String baseUrl, String apiKey, String apiSecret) {
        this.baseUrl = baseUrl.endsWith("/") ? baseUrl.substring(0, baseUrl.length() - 1) : baseUrl;
        this.apiKey = apiKey;
        this.apiSecret = apiSecret;
        this.httpClient = HttpClient.newBuilder().build();
    }
    
    /**
     * Get a service token for API authentication
     * 
     * @return Service authentication token
     * @throws Exception If authentication fails
     */
    private String getServiceToken() throws Exception {
        if (serviceToken == null) {
            Map<String, String> data = new HashMap<>();
            data.put("apiKey", apiKey);
            data.put("apiSecret", apiSecret);
            
            JSONObject requestBody = new JSONObject(data);
            
            HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(baseUrl + "/auth/service-token"))
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(requestBody.toString()))
                .build();
                
            HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
            
            if (response.statusCode() != 200) {
                throw new Exception("Failed to get service token: " + response.body());
            }
            
            JSONObject responseJson = new JSONObject(response.body());
            serviceToken = responseJson.getString("token");
        }
        
        return serviceToken;
    }
    
    /**
     * Check if a user has access to a specific service endpoint
     * 
     * @param userId User ID to check
     * @param endpoint Service endpoint to check access for
     * @return true if user has access, false otherwise
     * @throws Exception If the request fails
     */
    public boolean checkServiceAccess(String userId, String endpoint) throws Exception {
        Map<String, String> data = new HashMap<>();
        data.put("userId", userId);
        data.put("serviceId", apiKey);
        data.put("endpoint", endpoint);
        
        JSONObject requestBody = new JSONObject(data);
        
        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create(baseUrl + "/services/access"))
            .header("Content-Type", "application/json")
            .header("Authorization", "Bearer " + getServiceToken())
            .POST(HttpRequest.BodyPublishers.ofString(requestBody.toString()))
            .build();
            
        HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
        
        if (response.statusCode() != 200) {
            throw new Exception("Failed to check service access: " + response.body());
        }
        
        JSONObject responseJson = new JSONObject(response.body());
        return responseJson.getBoolean("hasAccess");
    }
    
    /**
     * Validate a user's JWT token
     * 
     * @param userToken JWT token to validate
     * @return User information if token is valid
     * @throws Exception If token validation fails
     */
    public JSONObject validateToken(String userToken) throws Exception {
        Map<String, String> data = new HashMap<>();
        data.put("token", userToken);
        
        JSONObject requestBody = new JSONObject(data);
        
        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create(baseUrl + "/auth/validate-token"))
            .header("Content-Type", "application/json")
            .header("Authorization", "Bearer " + getServiceToken())
            .POST(HttpRequest.BodyPublishers.ofString(requestBody.toString()))
            .build();
            
        HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
        
        if (response.statusCode() != 200) {
            throw new Exception("Token validation failed: " + response.body());
        }
        
        return new JSONObject(response.body());
    }
}
```

## Parent-Student Relationship Integration

### React Example (Parent-Student Linking)

```tsx
import React, { useState } from 'react';
import axios from 'axios';

// API client setup (same as in authentication example)
const API_BASE_URL = '/api/userman';
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
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

type Invitation = {
  id: string;
  fromUserId: string;
  toEmail: string;
  relationship: string;
  status: 'pending' | 'accepted' | 'rejected' | 'expired';
  createdAt: string;
  expiresAt: string;
  fromUser?: {
    id: string;
    name: string;
    email: string;
  };
};

const ParentStudentLinking: React.FC = () => {
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [invitations, setInvitations] = useState<Invitation[]>([]);

  // Fetch invitations
  const fetchInvitations = async () => {
    try {
      const response = await apiClient.get('/users/invitations');
      setInvitations(response.data);
    } catch (err) {
      setError('Failed to fetch invitations');
      console.error(err);
    }
  };

  // Send invitation
  const sendInvitation = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      await apiClient.post('/users/invitations', {
        email,
        relationship: 'student', // For a parent linking a student
        message,
      });
      
      setSuccess('Invitation sent successfully!');
      setEmail('');
      setMessage('');
      // Refresh invitations list
      fetchInvitations();
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to send invitation');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Accept invitation
  const acceptInvitation = async (invitationId: string) => {
    setLoading(true);
    try {
      await apiClient.post(`/users/invitations/${invitationId}/accept`);
      setSuccess('Invitation accepted successfully!');
      // Refresh invitations list
      fetchInvitations();
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to accept invitation');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Reject invitation
  const rejectInvitation = async (invitationId: string) => {
    setLoading(true);
    try {
      await apiClient.post(`/users/invitations/${invitationId}/reject`);
      setSuccess('Invitation rejected!');
      // Refresh invitations list
      fetchInvitations();
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to reject invitation');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Fetch invitations on component mount
  React.useEffect(() => {
    fetchInvitations();
  }, []);

  return (
    <div className="parent-student-linking">
      <h2>Link Students to Your Account</h2>
      
      {error && <div className="error-message">{error}</div>}
      {success && <div className="success-message">{success}</div>}
      
      <form onSubmit={sendInvitation}>
        <div className="form-group">
          <label htmlFor="email">Student's Email Address</label>
          <input
            type="email"
            id="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </div>
        
        <div className="form-group">
          <label htmlFor="message">Personal Message (Optional)</label>
          <textarea
            id="message"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            rows={3}
          />
        </div>
        
        <button type="submit" disabled={loading}>
          {loading ? 'Sending...' : 'Send Invitation'}
        </button>
      </form>
      
      <h3>Pending Invitations</h3>
      {invitations.length === 0 ? (
        <p>No pending invitations</p>
      ) : (
        <ul className="invitations-list">
          {invitations
            .filter((inv) => inv.status === 'pending')
            .map((invitation) => (
              <li key={invitation.id} className="invitation-item">
                <div className="invitation-details">
                  <p><strong>To:</strong> {invitation.toEmail}</p>
                  <p><strong>Relationship:</strong> {invitation.relationship}</p>
                  <p><strong>Sent:</strong> {new Date(invitation.createdAt).toLocaleString()}</p>
                  <p><strong>Expires:</strong> {new Date(invitation.expiresAt).toLocaleString()}</p>
                </div>
                <div className="invitation-actions">
                  <button 
                    onClick={() => acceptInvitation(invitation.id)}
                    disabled={loading}
                  >
                    Accept
                  </button>
                  <button 
                    onClick={() => rejectInvitation(invitation.id)} 
                    disabled={loading}
                    className="reject-button"
                  >
                    Reject
                  </button>
                </div>
              </li>
            ))}
        </ul>
      )}
    </div>
  );
};

export default ParentStudentLinking;
```

These examples demonstrate the integration of various services with the User Management System API. For more specific integration needs, please contact the platform team. 