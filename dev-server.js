#!/usr/bin/env node

/**
 * Development server to mock backend APIs
 */
const express = require('express');
const cors = require('cors');
const app = express();
const port = 4000;
const uiPort = 3002; // Different from frontend port to avoid conflicts

// Enable CORS
app.use(cors());
app.use(express.json());

// Health check endpoint
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', timestamp: Date.now() / 1000 });
});

// Auth bypass for development
app.get('/api/auth/session', (req, res) => {
  res.json({
    user: {
      id: 'dev-user-1',
      name: 'Development User',
      email: 'dev@example.com',
      role: 'admin',
      image: 'https://via.placeholder.com/150'
    },
    expires: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString()
  });
});

// Handle auth signin for development
app.post('/api/auth/signin', (req, res) => {
  res.json({
    status: 'success',
    user: {
      id: 'dev-user-1',
      name: 'Development User',
      email: req.body.email || 'dev@example.com',
      role: 'admin'
    },
    token: 'mock-jwt-token'
  });
});

// Mock chat API
app.post('/api/chat/query', (req, res) => {
  const { query } = req.body;
  
  res.json({
    answer: `This is a development response to: "${query}"`,
    conversation_id: 'mock-' + Date.now(),
    thinking_steps: [
      {
        type: 'thinking',
        description: 'Processing query',
        time: new Date().toISOString(),
        duration_ms: 300
      }
    ],
    documents: [],
    duration_seconds: 0.5
  });
});

// Mock UI service endpoints
const uiApp = express();
uiApp.use(cors());
uiApp.use(express.json());

// UI Health check
uiApp.get('/health', (req, res) => {
  res.json({ status: 'ok', service: 'ui' });
});

// Mock chat sessions
uiApp.get('/api/chat/sessions', (req, res) => {
  res.json({
    sessions: [
      {
        id: 'session-1',
        title: 'First Chat Session',
        updated_at: new Date().toISOString(),
        message_count: 5
      },
      {
        id: 'session-2',
        title: 'Second Chat Session',
        updated_at: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
        message_count: 3
      }
    ]
  });
});

// Start servers
app.listen(port, () => {
  console.log(`Backend mock server running at http://localhost:${port}`);
});

uiApp.listen(uiPort, () => {
  console.log(`UI mock server running at http://localhost:${uiPort}`);
});

console.log('\nDevelopment Environment Started');
console.log('------------------------------');
console.log('1. Frontend service: http://localhost:3001');
console.log(`2. Backend mock API: http://localhost:${port}`);
console.log(`3. UI mock service: http://localhost:${uiPort}`);
console.log('\nPress Ctrl+C to stop all services'); 