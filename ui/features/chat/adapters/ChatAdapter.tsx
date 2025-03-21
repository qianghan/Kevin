'use client';

import React, { ReactNode, useEffect, useState, useCallback } from 'react';
import { ChatProvider, useChatContext } from '../context/ChatContext';
import { ChatAdapterProps } from '../types/chat-ui.types';
import { ChatMessage } from '../../../lib/types';

// ChatAdapter component that connects UI components to the chat context
export function ChatAdapter({
  components,
  initialConversationId,
  initialMessages = []
}: ChatAdapterProps) {
  // Return the provider with the inner component
  return (
    <ChatProvider 
      initialConversationId={initialConversationId}
      initialMessages={initialMessages}
    >
      <ChatAdapterInner components={components} />
    </ChatProvider>
  );
}

// Inner component to access context
function ChatAdapterInner({ 
  components
}: { 
  components: ChatAdapterProps['components']
}) {
  // State to track when sample questions should refresh
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  const {
    messages,
    isLoading,
    streamingMessage,
    thinkingSteps,
    isThinking,
    sendMessage,
    startNewChat,
    updateTitle,
    saveChatSession,
    conversationId,
    getRandomSampleQuestions,
    useWebSearch,
    toggleWebSearch
  } = useChatContext();
  
  // Get random sample questions
  const sampleQuestions = React.useMemo(() => {
    const questions = getRandomSampleQuestions();
    return questions.map(q => ({
      text: q.text,
      handler: () => sendMessage(q.query)
    }));
  }, [getRandomSampleQuestions, sendMessage, refreshTrigger]);
  
  // Handler for refreshing sample questions
  const handleRefreshQuestions = useCallback(() => {
    setRefreshTrigger(prev => prev + 1);
  }, []);
  
  // Log messages to help debug
  console.log('ChatAdapter - received messages:', messages.length, messages);
  console.log('ChatAdapter - streaming:', streamingMessage ? 'yes' : 'no', streamingMessage?.length || 0);
  console.log('ChatAdapter - thinking:', isThinking, 'steps:', thinkingSteps?.length || 0);
  console.log('ChatAdapter - conversationId:', conversationId);
  console.log('ChatAdapter - web search:', useWebSearch);

  // Derive a title from the first user message or use "New Chat"
  const title = messages.length > 0 && messages[0].role === 'user'
    ? messages[0].content.substring(0, 30) + (messages[0].content.length > 30 ? '...' : '')
    : 'New Chat';

  // Auto-save when messages change
  useEffect(() => {
    if (messages.length > 0 && conversationId) {
      console.log('Auto-saving chat after message change');
      saveChatSession(title).then(success => {
        console.log('Auto-save result:', success);
      });
    }
  }, [messages, conversationId, saveChatSession, title]);

  const { ChatContainer, ChatHeader, ChatMessageList, ChatInput } = components;

  // Handle saving a chat session manually
  const handleSaveManually = useCallback(async (): Promise<boolean> => {
    if (messages.length === 0) {
      alert("No messages to save!");
      return false;
    }
    
    const success = await saveChatSession(title);
    if (success) {
      alert("Chat session saved successfully!");
    } else {
      alert("Failed to save chat session.");
    }
    return success;
  }, [messages.length, saveChatSession, title]);

  // Render the UI components with appropriate props
  return (
    <ChatContainer>
      <ChatHeader 
        title={title}
        onUpdateTitle={updateTitle}
        onStartNewChat={startNewChat}
        onSave={handleSaveManually}
      />
      <ChatMessageList 
        messages={messages}
        streamingMessage={streamingMessage}
        isThinking={isThinking}
        isLoading={isLoading}
        thinkingSteps={thinkingSteps}
        className="flex-1 overflow-auto border-b border-gray-200"
        onStartNewChat={startNewChat}
        sampleQuestions={sampleQuestions}
        onRefreshQuestions={handleRefreshQuestions}
      />
      <ChatInput 
        onSendMessage={sendMessage}
        isDisabled={isLoading}
        placeholder="Type a message..."
        useWebSearch={useWebSearch}
        onToggleWebSearch={toggleWebSearch}
      />
    </ChatContainer>
  );
} 