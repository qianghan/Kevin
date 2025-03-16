// Mock API server for Kevin UI development
const express = require('express');
const cors = require('cors');
const app = express();
const port = 8000;

// Enable CORS
app.use(cors());
app.use(express.json());

// Health check endpoint
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', timestamp: Date.now() / 1000 });
});

// Root endpoint
app.get('/', (req, res) => {
  res.json({
    name: 'Kevin API (Mock)',
    version: '1.0.0',
    description: 'Mock API for Kevin.AI',
    docs_url: '/docs'
  });
});

// Stream response for chat queries
app.get('/api/chat/query/stream', (req, res) => {
  const query = req.query.query || '';
  
  // Set headers for SSE
  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');
  
  // Send thinking start event
  res.write('event: thinking_start\n');
  res.write(`data: ${JSON.stringify({ timestamp: new Date().toISOString() })}\n\n`);
  
  // Send a thinking step event
  setTimeout(() => {
    res.write('event: thinking_update\n');
    res.write(`data: ${JSON.stringify({
      type: 'thinking',
      description: 'Processing your query',
      time: new Date().toISOString(),
      duration_ms: 500
    })}\n\n`);
  }, 1000);
  
  // Send another thinking step event
  setTimeout(() => {
    res.write('event: thinking_update\n');
    res.write(`data: ${JSON.stringify({
      type: 'thinking',
      description: 'Generating response',
      time: new Date().toISOString(),
      duration_ms: 800
    })}\n\n`);
  }, 2000);
  
  // Send thinking end event
  setTimeout(() => {
    res.write('event: thinking_end\n');
    res.write(`data: ${JSON.stringify({ timestamp: new Date().toISOString() })}\n\n`);
  }, 3000);
  
  // Send answer start event
  setTimeout(() => {
    res.write('event: answer_start\n');
    res.write(`data: ${JSON.stringify({ timestamp: new Date().toISOString() })}\n\n`);
  }, 3200);
  
  // Send answer chunks
  const response = `I'm a mock response from the Kevin API server. You asked: "${query}".`;
  const chunks = response.split(' ');
  
  chunks.forEach((chunk, index) => {
    setTimeout(() => {
      res.write('event: answer_chunk\n');
      res.write(`data: ${JSON.stringify({ chunk: chunk + ' ' })}\n\n`);
    }, 3500 + (index * 100));
  });
  
  // Send done event
  setTimeout(() => {
    res.write('event: done\n');
    res.write(`data: ${JSON.stringify({
      conversation_id: 'mock-' + Date.now(),
      duration_seconds: 5.2
    })}\n\n`);
    res.end();
  }, 3500 + (chunks.length * 100) + 500);
});

// Handle standard chat queries
app.post('/api/chat/query', (req, res) => {
  const { query, use_web_search, stream } = req.body;
  
  // If streaming is requested, redirect to stream endpoint
  if (stream) {
    const redirectUrl = `/api/chat/query/stream?query=${encodeURIComponent(query)}`;
    if (use_web_search) {
      redirectUrl += '&use_web_search=true';
    }
    if (req.body.conversation_id) {
      redirectUrl += `&conversation_id=${encodeURIComponent(req.body.conversation_id)}`;
    }
    
    return res.redirect(307, redirectUrl);
  }
  
  // Standard response
  res.json({
    answer: `This is a mock response to your query: "${query}"`,
    conversation_id: 'mock-' + Date.now(),
    thinking_steps: [
      {
        type: 'thinking',
        description: 'Processing query',
        time: new Date().toISOString(),
        duration_ms: 300
      },
      {
        type: 'thinking',
        description: 'Generating response',
        time: new Date().toISOString(),
        duration_ms: 700
      }
    ],
    documents: [],
    duration_seconds: 1.0
  });
});

// Start the server
app.listen(port, () => {
  console.log(`Mock API server running at http://localhost:${port}`);
}); 