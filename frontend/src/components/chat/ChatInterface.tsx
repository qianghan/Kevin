import React, { useRef, useCallback, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { ChatMessage } from '@/models/ChatSession';

interface ThinkingStep {
  type: string;
  description: string;
  time: string;
  duration_ms?: number;
}

const ChatInterface: React.FC = () => {
  const [streamingMessage, setStreamingMessage] = useState<string>('');
  const [thinkingSteps, setThinkingSteps] = useState<ThinkingStep[]>([]);
  const accumulatedContentRef = useRef<string>('');

  const handleAnswerChunk = (e: MessageEvent) => {
    try {
      const data = JSON.parse(e.data);
      const chunk = data.chunk || '';
      
      // Batch state updates for better performance
      requestAnimationFrame(() => {
        // Update both the state (for display) and the ref (for storage)
        accumulatedContentRef.current += chunk;
        setStreamingMessage((prev: string) => prev + chunk);
        
        // Reduce frequency of thinking steps updates
        if (accumulatedContentRef.current.length % 1000 === 0) {
          const progressStep: ThinkingStep = {
            type: 'thinking',
            description: `Generated ${accumulatedContentRef.current.length} characters`,
            time: new Date().toTimeString().split(' ')[0],
            duration_ms: 0
          };
          
          setThinkingSteps((prev: ThinkingStep[]) => {
            const hasProgressStep = prev.some((step: ThinkingStep) => 
              step.description.includes('Generated') && 
              step.description.includes('characters')
            );
            
            if (!hasProgressStep) {
              return [...prev, progressStep];
            }
            return prev;
          });
        }
      });
    } catch (err) {
      console.error('Error parsing answer_chunk event', err);
    }
  };

  // Optimize markdown rendering with memoization
  const MemoizedMarkdown = React.memo(({ content }: { content: string }) => (
    <ReactMarkdown 
      remarkPlugins={[remarkGfm]}
      components={{
        a: ({ node, ...props }: { node?: any; [key: string]: any }) => (
          <a 
            {...props} 
            target="_blank" 
            rel="noopener noreferrer"
            className="text-blue-600 hover:text-blue-800 hover:underline"
          />
        )
      }}
    >
      {content}
    </ReactMarkdown>
  ));

  const renderMessage = (message: ChatMessage) => (
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
        <MemoizedMarkdown content={message.content} />
      ) : (
        message.content
      )}
    </div>
  );

  return (
    // ... existing code ...
    {messages.map((message: ChatMessage) => renderMessage(message))}
    // ... existing code ...
  );
};

export default ChatInterface; 