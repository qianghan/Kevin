'use client';

import React from 'react';
import { ChatAdapter } from './adapters/ChatAdapter';
import { DefaultChatContainer } from './components/default/DefaultChatContainer';
import { DefaultChatHeader } from './components/default/DefaultChatHeader';
import { DefaultChatMessageList } from './components/default/DefaultChatMessageList';
import { DefaultChatInput } from './components/default/DefaultChatInput';
import { ChatMessage } from '../../lib/types';

interface ChatInterfaceProps {
  initialConversationId?: string;
  initialMessages?: ChatMessage[];
}

export function ChatInterface({ 
  initialConversationId,
  initialMessages = [] 
}: ChatInterfaceProps) {
  // Define the default components to use
  const defaultComponents = {
    ChatContainer: DefaultChatContainer,
    ChatHeader: DefaultChatHeader,
    ChatMessageList: DefaultChatMessageList,
    ChatInput: DefaultChatInput,
  };

  return (
    <div className="flex flex-col h-full w-full overflow-hidden">
      <ChatAdapter
        components={defaultComponents}
        initialConversationId={initialConversationId}
        initialMessages={initialMessages}
      />
    </div>
  );
} 