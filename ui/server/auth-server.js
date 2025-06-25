/**
 * Authentication server
 */

const express = require('express');
const cors = require('cors');
const app = express();
const PORT = 8001;

// Middleware
app.use(express.json());
app.use(cors({
  origin: ['http://localhost:3000', 'http://localhost:8000'],
  credentials: true
}));

// Root endpoint
app.get('/', (req, res) => {
  res.json({
    name: 'Authentication API',
    version: '1.0.0',
    endpoints: {
      auth: '/api/auth',
      user: '/api/user'
    }
  });
});

// Health check endpoint
app.get('/api/health', (req, res) => {
  res.json({
    status: 'ok',
    timestamp: Date.now() / 1000
  });
});

// Forward auth requests to user management service
const forwardAuthRequest = async (req, res, endpoint) => {
  try {
    const response = await fetch(`http://localhost:8000/api/auth/${endpoint}`, {
      method: req.method,
      headers: {
        'Content-Type': 'application/json',
        ...(req.headers.authorization && { 'Authorization': req.headers.authorization })
      },
      body: req.method !== 'GET' ? JSON.stringify(req.body) : undefined,
    });

    const data = await response.json();
    res.status(response.status).json(data);
  } catch (error) {
    console.error(`Error forwarding ${endpoint} request:`, error);
    res.status(500).json({ message: 'Internal server error' });
  }
};

// Login endpoint
app.post('/api/auth/login', (req, res) => forwardAuthRequest(req, res, 'login'));

// Register endpoint
app.post('/api/auth/register', (req, res) => forwardAuthRequest(req, res, 'register'));

// Verify email endpoint
app.post('/api/auth/verify-email', (req, res) => forwardAuthRequest(req, res, 'verify-email'));

// Forgot password endpoint
app.post('/api/auth/forgot-password', (req, res) => forwardAuthRequest(req, res, 'forgot-password'));

// Reset password endpoint
app.post('/api/auth/reset-password', (req, res) => forwardAuthRequest(req, res, 'reset-password'));

// Get user profile endpoint
app.get('/api/user/profile', (req, res) => {
  // Forward the request with authorization header
  forwardAuthRequest(req, res, 'profile');
});

// Start server
app.listen(PORT, () => {
  console.log(`Authentication API running on port ${PORT}`);
  console.log(`Access at http://localhost:${PORT}`);
}); 