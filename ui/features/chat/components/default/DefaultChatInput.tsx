'use client';

import React, { useState, useRef, useEffect } from 'react';
import { ChatInputProps } from '../../types/chat-ui.types';

export function DefaultChatInput({
  onSendMessage,
  isDisabled,
  placeholder = 'Ask me anything...',
  className = '',
  useWebSearch = false,
  onToggleWebSearch
}: ChatInputProps) {
  const [input, setInput] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  
  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  }, [input]);
  
  // Handle form submission
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim() && !isDisabled) {
      onSendMessage(input);
      setInput('');
    }
  };
  
  // Handle key press
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className={`bg-gray-50 p-4 border-t border-gray-100 ${className}`}>
      <div className="max-w-4xl mx-auto relative">
        <form onSubmit={handleSubmit} className="flex space-x-3">
          <div className="relative flex-1 flex items-start">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyPress}
              disabled={isDisabled}
              placeholder={placeholder}
              style={{ 
                minHeight: '56px', 
                maxHeight: '200px',
                resize: 'none', 
                height: 'auto',
                paddingRight: '3rem' 
              }}
              className="w-full p-4 pr-12 border rounded-xl shadow-md bg-white border-gray-200 focus:bg-white focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none transition-all text-gray-700"
            />
            
            {/* Web search toggle button */}
            {onToggleWebSearch && (
              <button
                type="button"
                onClick={onToggleWebSearch}
                disabled={isDisabled}
                className={`absolute right-3 top-3 p-1.5 rounded-full transition-all ${
                  isDisabled 
                    ? "text-gray-400 cursor-not-allowed" 
                    : "text-gray-500 hover:bg-gray-100"
                } ${useWebSearch ? "text-blue-500 bg-blue-50" : ""}`}
                title={useWebSearch ? "Web search enabled" : "Web search disabled"}
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </button>
            )}
          </div>
          <button
            type="submit"
            disabled={isDisabled || !input.trim()}
            className={`p-4 rounded-xl w-14 h-auto flex-shrink-0 flex items-center justify-center transition-all ${
              isDisabled 
                ? "bg-gray-300 text-gray-500 cursor-not-allowed" 
                : "bg-gradient-to-r from-indigo-500 to-purple-600 text-white hover:shadow-md shadow-sm hover:from-indigo-600 hover:to-purple-700"
            }`}
            style={{ alignSelf: 'flex-start' }}
          >
            {isDisabled ? (
              <span className="animate-pulse">...</span>
            ) : (
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 5l7 7-7 7M5 5l7 7-7 7" />
              </svg>
            )}
          </button>
        </form>
        
        <div className="text-xs text-gray-500 mt-3 text-center flex items-center justify-center">
          {useWebSearch && (
            <span className="inline-flex items-center mr-2 text-blue-500">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              Web search enabled
            </span>
          )}
          <span>AI responses may not always be accurate. Verify important information.</span>
        </div>
      </div>
    </div>
  );
} 