'use client';

import React, { useRef, useEffect, useState } from 'react';
import { ChatMessageListProps } from '../../types/chat-ui.types';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

export function DefaultChatMessageList({
  messages,
  streamingMessage = '',
  thinkingSteps = [],
  isThinking = false,
  isLoading = false,
  className = '',
  onStartNewChat,
  sampleQuestions = [],
  onRefreshQuestions
}: ChatMessageListProps) {
  // Reference to the messages end to auto-scroll
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  // State to track if sample questions have been refreshed
  const [refreshed, setRefreshed] = useState(false);

  // Function to refresh sample questions - would trigger parent to get new ones
  const refreshSampleQuestions = () => {
    setRefreshed(!refreshed);
    if (onRefreshQuestions) {
      onRefreshQuestions();
    }
  };
  
  // Auto-scroll to the bottom when messages change
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, streamingMessage, isThinking, thinkingSteps]);

  // Group messages into exchanges (user + assistant pairs)
  const messageExchanges = React.useMemo(() => {
    const exchanges: typeof messages[] = [];
    let currentExchange: typeof messages = [];
    
    messages.forEach(message => {
      currentExchange.push(message);
      if (message.role === 'assistant') {
        exchanges.push([...currentExchange]);
        currentExchange = [];
      }
    });
    
    // Add any remaining messages
    if (currentExchange.length > 0) {
      exchanges.push(currentExchange);
    }
    
    return exchanges;
  }, [messages]);

  // Function to copy message content to clipboard
  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
      .then(() => {
        console.log('Text copied to clipboard');
      })
      .catch(err => {
        console.error('Failed to copy text: ', err);
      });
  };

  return (
    <div className={`flex-1 overflow-y-auto p-4 space-y-6 relative bg-gray-50 w-full ${className}`}>
      {/* Welcome message when no messages exist */}
      {messages.length === 0 && !streamingMessage && !isThinking ? (
        <div className="flex items-center justify-center h-full">
          <div className="text-center max-w-md mx-auto p-8 rounded-xl bg-white shadow-lg border border-gray-100 bg-gradient-to-b from-white to-gray-50">
            <div className="mb-6 bg-gradient-to-br from-indigo-500 to-purple-600 text-white w-20 h-20 rounded-full flex items-center justify-center mx-auto shadow-md">
              <span className="text-3xl font-bold" style={{ textShadow: '0px 2px 3px rgba(0, 0, 0, 0.3)' }}>K</span>
            </div>
            <h3 className="text-2xl font-semibold text-gray-800 mb-3">Welcome to University Assistant</h3>
            <p className="text-gray-600 mb-8 leading-relaxed">Your AI guide for Canadian university information, admissions, programs, and campus life.</p>
            <div className="flex flex-col sm:flex-row justify-center gap-3">
              {sampleQuestions.length > 0 && (
                <>
                  <button 
                    onClick={sampleQuestions[0].handler}
                    className="px-4 py-3 bg-gray-100 hover:bg-gray-200 rounded-xl text-sm text-gray-700 transition-colors font-medium shadow-sm hover:shadow"
                  >
                    {sampleQuestions[0].text}
                  </button>
                  {sampleQuestions.length > 1 && (
                    <button 
                      onClick={sampleQuestions[1].handler}
                      className="px-4 py-3 bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 rounded-xl text-sm text-white transition-colors font-medium shadow-sm hover:shadow"
                    >
                      {sampleQuestions[1].text}
                    </button>
                  )}
                </>
              )}
            </div>
            <div className="mt-4">
              <button
                onClick={refreshSampleQuestions}
                className="text-indigo-500 hover:text-indigo-700 text-sm font-medium flex items-center justify-center mx-auto"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                Show different questions
              </button>
            </div>
          </div>
        </div>
      ) : (
        <>
          {/* Show date separator for messages */}
          {messages.length > 0 && (
            <div className="flex justify-center">
              <span className="text-xs text-gray-600 bg-white px-3 py-1.5 rounded-full shadow-md border border-gray-100 font-medium">
                {new Date(messages[0].timestamp).toLocaleDateString(undefined, {
                  weekday: 'long',
                  year: 'numeric',
                  month: 'long',
                  day: 'numeric'
                })}
              </span>
            </div>
          )}
          
          {/* Show all message exchanges */}
          {messageExchanges.map((exchange, exchangeIndex) => (
            <div key={`exchange-${exchangeIndex}`} className="space-y-6 mb-6">
              {exchange.map((message, messageIndex) => (
                <div 
                  key={`message-${exchangeIndex}-${messageIndex}-${message.timestamp.getTime()}`} 
                  className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  {/* Role indicator for assistant */}
                  {message.role === 'assistant' && (
                    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-teal-500 to-emerald-600 text-white flex items-center justify-center mr-2 flex-shrink-0 mt-1 shadow-md">
                      <span className="text-lg font-bold" style={{ textShadow: '0px 1px 2px rgba(0, 0, 0, 0.2)' }}>K</span>
                    </div>
                  )}
                  
                  <div 
                    className={`p-5 rounded-2xl max-w-[85%] md:max-w-[75%] relative group ${
                      message.role === 'user' 
                        ? 'bg-gradient-to-br from-indigo-600 to-purple-700 text-white shadow-lg'
                        : 'bg-white text-gray-800 border border-gray-100 shadow-md hover:shadow-lg transition-shadow'
                    }`}
                  >
                    {/* Copy button - only visible on hover */}
                    <button
                      onClick={() => copyToClipboard(message.content)}
                      className={`absolute top-3 right-3 p-1.5 rounded-full opacity-0 group-hover:opacity-100 transition-opacity text-xs ${
                        message.role === 'user' 
                          ? 'bg-indigo-400/50 hover:bg-indigo-400 text-white backdrop-blur-sm' 
                          : 'bg-gray-100 hover:bg-gray-200 text-gray-600'
                      }`}
                      title="Copy message"
                      aria-label="Copy message"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3" />
                      </svg>
                    </button>
                    
                    <div className={`whitespace-pre-wrap markdown-content text-base leading-relaxed ${
                      message.role === 'user' 
                        ? 'text-white !important font-medium' 
                        : 'text-gray-700'
                    }`}
                    style={message.role === 'user' 
                      ? { 
                          color: 'white', 
                          textShadow: '0px 1px 2px rgba(0, 0, 0, 0.25)'
                        } 
                      : undefined
                    }
                    >
                      {message.role === 'assistant' ? (
                        <div className="prose max-w-none">
                          <ReactMarkdown 
                            remarkPlugins={[remarkGfm]}
                            components={{
                              a: ({ node, ...props }) => (
                                <a 
                                  {...props} 
                                  target="_blank" 
                                  rel="noopener noreferrer"
                                  className="text-blue-600 hover:text-blue-800 hover:underline"
                                />
                              )
                            }}
                          >
                            {message.content}
                          </ReactMarkdown>
                        </div>
                      ) : (
                        message.content
                      )}
                    </div>

                    {/* Message timestamp */}
                    <div className={`text-xs mt-3 flex items-center ${
                      message.role === 'user' 
                        ? 'text-indigo-100/75' 
                        : 'text-gray-400'
                    }`}>
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      {message.timestamp.toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'})}
                    </div>
                  </div>
                  
                  {/* Role indicator for user */}
                  {message.role === 'user' && (
                    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 text-white flex items-center justify-center ml-2 flex-shrink-0 mt-1 shadow-md">
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                      </svg>
                    </div>
                  )}
                </div>
              ))}
            </div>
          ))}
          
          {/* Simple loading indicator when waiting for response */}
          {isThinking && !streamingMessage && !isLoading && (
            <div className="flex justify-center my-6">
              <div className="flex items-center space-x-2 bg-white px-5 py-3 rounded-full shadow-md border border-gray-100">
                <div className="animate-pulse flex items-center">
                  <div className="h-2.5 w-2.5 mr-1 bg-indigo-500 rounded-full"></div>
                  <div className="h-2.5 w-2.5 mr-1 bg-indigo-500 rounded-full animation-delay-200"></div>
                  <div className="h-2.5 w-2.5 bg-indigo-500 rounded-full animation-delay-500"></div>
                </div>
                <span className="text-sm text-gray-600 font-medium">Thinking...</span>
              </div>
            </div>
          )}
          
          {/* Streaming message - only show if there's content to display */}
          {streamingMessage && (
            <div className="flex justify-start">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-teal-500 to-emerald-600 text-white flex items-center justify-center mr-2 flex-shrink-0 mt-1 shadow-md">
                <span className="text-lg font-bold" style={{ textShadow: '0px 1px 2px rgba(0, 0, 0, 0.2)' }}>K</span>
              </div>
              <div className="p-5 rounded-2xl max-w-[85%] md:max-w-[75%] bg-white text-gray-700 border border-gray-100 relative group shadow-md hover:shadow-lg transition-shadow">
                {/* Copy button for streaming message */}
                <button
                  onClick={() => copyToClipboard(streamingMessage)}
                  className="absolute top-3 right-3 p-1.5 rounded-full bg-gray-100 hover:bg-gray-200 text-gray-600 opacity-0 group-hover:opacity-100 transition-opacity text-xs"
                  title="Copy message"
                  aria-label="Copy message"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3" />
                  </svg>
                </button>
                
                <div className="whitespace-pre-wrap markdown-content text-base leading-relaxed">
                  <div className="prose max-w-none">
                    <ReactMarkdown 
                      remarkPlugins={[remarkGfm]}
                      components={{
                        a: ({ node, ...props }) => (
                          <a 
                            {...props} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="text-blue-600 hover:text-blue-800 hover:underline"
                          />
                        )
                      }}
                    >
                      {streamingMessage}
                    </ReactMarkdown>
                  </div>
                  <span className="animate-pulse text-indigo-500 font-medium">▋</span>
                </div>
              </div>
            </div>
          )}
        </>
      )}
      
      {/* New Chat button at the bottom */}
      {messages.length > 0 && (
        <div className="flex justify-center my-4 sticky bottom-4">
          <button
            onClick={() => onStartNewChat?.()}
            disabled={isLoading}
            className={`flex items-center px-5 py-3 border border-transparent rounded-full transition-all text-white font-medium shadow-md disabled:cursor-not-allowed ${
              isLoading
                ? "bg-gradient-to-r from-indigo-300 to-purple-400 opacity-70"
                : "bg-gradient-to-r from-indigo-500 to-purple-600 hover:shadow-lg"
            }`}
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
            {isLoading ? 'Thinking...' : 'Start New Chat'}
          </button>
        </div>
      )}
      
      {/* Invisible div for auto-scrolling */}
      <div ref={messagesEndRef} />
    </div>
  );
} 