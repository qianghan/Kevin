'use client';

import { useState, useEffect, useRef } from 'react';
import { WebSocketProfileService } from '@/lib/services/profile';
import { WebSocketMessage } from '@/lib/services/types';

export default function TestWebSocket() {
  const [messages, setMessages] = useState<string[]>([]);
  const [userId, setUserId] = useState<string>('test-user-1');
  const [connected, setConnected] = useState<boolean>(false);
  const [connection, setConnection] = useState<string>('not_connected');
  const [message, setMessage] = useState<string>('');
  const profileServiceRef = useRef<WebSocketProfileService | null>(null);
  
  useEffect(() => {
    // Create profile service
    const profileService = new WebSocketProfileService('localhost:8000');
    profileServiceRef.current = profileService;
    
    // Set up event listeners
    profileService.onConnect(() => {
      setConnected(true);
      setConnection('connected');
      addMessage('Connected to WebSocket');
    });
    
    profileService.onMessage((message: WebSocketMessage) => {
      addMessage(`Received: ${JSON.stringify(message)}`);
    });
    
    profileService.onError((error: Error) => {
      setConnection('error');
      addMessage(`Error: ${error.message}`);
    });
    
    profileService.on('disconnected', () => {
      setConnected(false);
      setConnection('disconnected');
      addMessage('Disconnected from WebSocket');
    });
    
    return () => {
      // Clean up
      profileService.disconnect();
      profileService.removeAllListeners();
    };
  }, []);
  
  const addMessage = (msg: string) => {
    setMessages(prev => [...prev, `[${new Date().toISOString()}] ${msg}`]);
  };
  
  const handleConnect = async () => {
    try {
      setConnection('connecting');
      addMessage(`Connecting with user ID: ${userId}`);
      await profileServiceRef.current?.connect(userId);
    } catch (error: any) {
      addMessage(`Error connecting: ${error?.message}`);
      setConnection('error');
    }
  };
  
  const handleDisconnect = () => {
    profileServiceRef.current?.disconnect();
    setConnected(false);
    setConnection('disconnected');
    addMessage('Manually disconnected');
  };
  
  const handleSendMessage = () => {
    if (!message.trim()) return;
    
    const msgObj = {
      type: 'test_message',
      data: { message: message },
      timestamp: new Date().toISOString()
    };
    
    addMessage(`Sending: ${JSON.stringify(msgObj)}`);
    profileServiceRef.current?.sendMessage(msgObj);
    setMessage('');
  };
  
  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4">WebSocket Connection Test</h1>
      
      <div className="mb-4">
        <div className="flex gap-2 mb-2">
          <input
            type="text"
            value={userId}
            onChange={(e) => setUserId(e.target.value)}
            placeholder="User ID"
            className="p-2 border rounded"
          />
          <button
            onClick={handleConnect}
            disabled={connection === 'connecting' || connected}
            className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded disabled:bg-gray-400"
          >
            Connect
          </button>
          <button
            onClick={handleDisconnect}
            disabled={!connected}
            className="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded disabled:bg-gray-400"
          >
            Disconnect
          </button>
        </div>
        
        <div className="mb-2">
          Status: <span className={`font-bold ${
            connection === 'connected' ? 'text-green-500' : 
            connection === 'connecting' ? 'text-yellow-500' : 
            connection === 'error' ? 'text-red-500' : 
            'text-gray-500'
          }`}>
            {connection.toUpperCase()}
          </span>
        </div>
      </div>
      
      {connected && (
        <div className="mb-4">
          <div className="flex gap-2">
            <input
              type="text"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Message to send"
              className="p-2 border rounded flex-1"
            />
            <button
              onClick={handleSendMessage}
              className="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded"
            >
              Send
            </button>
          </div>
        </div>
      )}
      
      <div className="border p-4 rounded bg-gray-50 h-96 overflow-y-auto">
        <h2 className="text-lg font-semibold mb-2">Messages:</h2>
        <div className="space-y-1">
          {messages.map((msg, index) => (
            <div key={index} className="text-sm font-mono">
              {msg}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
} 