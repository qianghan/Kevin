import { NextApiRequest, NextApiResponse } from 'next';
import type { MessageEvent } from 'eventsource';
import fs from 'fs';
import path from 'path';

// We need to use dynamic import for eventsource since it's a browser API
// but we're using it in Node.js context
const EventSource = require('eventsource');

/**
 * Debug API endpoint for testing DeepSeek r1 thinking steps
 * This will make a call to the Kevin API and log all thinking steps to a file
 */
export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }
  
  const { query = 'Tell me about UBC' } = req.body;
  
  // Ensure logs directory exists
  const logsDir = path.join(process.cwd(), 'logs');
  if (!fs.existsSync(logsDir)) {
    fs.mkdirSync(logsDir, { recursive: true });
  }
  
  // Create log file for this test
  const logFile = path.join(logsDir, `thinking-debug-${Date.now()}.log`);
  const logStream = fs.createWriteStream(logFile, { flags: 'a' });
  
  // Log function that writes to console and file
  const log = (message: string) => {
    const timestamp = new Date().toISOString();
    const logLine = `[${timestamp}] ${message}\n`;
    console.log(logLine.trim());
    logStream.write(logLine);
  };
  
  log('Starting debug test for DeepSeek r1 thinking steps');
  log(`Query: ${query}`);
  
  // Create the Kevin API URL for streaming
  const apiUrl = process.env.NEXT_PUBLIC_KEVIN_API_URL || 'http://localhost:8000';
  const params = new URLSearchParams();
  params.append('query', query);
  params.append('debug_mode', 'true');
  params.append('use_web_search', 'false');
  
  const streamUrl = `${apiUrl}/api/chat/query/stream?${params.toString()}`;
  log(`Stream URL: ${streamUrl}`);
  
  // Create event source and listen to events
  const eventSource = new EventSource(streamUrl);
  
  // Set timeout to close connection after 60 seconds
  const timeout = setTimeout(() => {
    log('Timeout reached, closing connection');
    eventSource.close();
    logStream.end();
    res.status(200).json({ 
      success: true, 
      message: 'Debug test completed (timeout)',
      logFile
    });
  }, 60000);
  
  // Track thinking steps
  const thinkingSteps: any[] = [];
  
  // Listen for events
  eventSource.addEventListener('open', () => {
    log('EventSource connection opened');
  });
  
  eventSource.addEventListener('thinking_start', (e: MessageEvent) => {
    log(`Thinking START event received: ${e.data}`);
    try {
      const data = JSON.parse(e.data);
      thinkingSteps.push({ type: 'start', ...data });
    } catch (err) {
      log(`Error parsing thinking_start: ${err}`);
    }
  });
  
  eventSource.addEventListener('thinking_update', (e: MessageEvent) => {
    log(`Thinking UPDATE event received: ${e.data}`);
    try {
      const data = JSON.parse(e.data);
      thinkingSteps.push({ type: 'update', ...data });
    } catch (err) {
      log(`Error parsing thinking_update: ${err}`);
    }
  });
  
  eventSource.addEventListener('thinking_end', (e: MessageEvent) => {
    log(`Thinking END event received: ${e.data}`);
    try {
      const data = JSON.parse(e.data);
      thinkingSteps.push({ type: 'end', ...data });
    } catch (err) {
      log(`Error parsing thinking_end: ${err}`);
    }
  });
  
  eventSource.addEventListener('answer_start', () => {
    log('Answer START event received');
  });
  
  eventSource.addEventListener('answer_chunk', (e: MessageEvent) => {
    // Only log length to avoid huge logs
    try {
      const data = JSON.parse(e.data);
      const chunkLength = data.chunk?.length || 0;
      log(`Answer CHUNK received, length: ${chunkLength}`);
    } catch (err) {
      log(`Error parsing answer_chunk: ${err}`);
    }
  });
  
  eventSource.addEventListener('done', (e: MessageEvent) => {
    log(`Done event received: ${e.data}`);
    clearTimeout(timeout);
    
    // Write thinking steps to log
    log(`\n==== THINKING STEPS SUMMARY (${thinkingSteps.length} steps) ====`);
    thinkingSteps.forEach((step, i) => {
      log(`Step ${i+1}: [${step.type}] ${step.description || 'No description'}`);
    });
    
    // Close connection
    eventSource.close();
    logStream.end();
    
    // Send response
    res.status(200).json({ 
      success: true, 
      message: 'Debug test completed successfully',
      thinkingStepsCount: thinkingSteps.length,
      logFile
    });
  });
  
  eventSource.addEventListener('error', (e: Event) => {
    log(`Error event received: ${e}`);
    clearTimeout(timeout);
    eventSource.close();
    logStream.end();
    
    res.status(500).json({ 
      success: false, 
      message: 'Error during debug test',
      logFile
    });
  });
  
  // Set initial response to prevent timeout
  res.writeHead(200, {
    'Content-Type': 'application/json',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive',
  });
  
  // Note: The actual response will be sent by one of the event handlers above
} 