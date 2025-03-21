'use client';

import React from 'react';
import { ChatUIProps } from '../../types/chat-ui.types';
import { DefaultChatContainer } from './DefaultChatContainer';
import { DefaultChatHeader } from './DefaultChatHeader';
import { DefaultChatMessageList } from './DefaultChatMessageList';
import { DefaultChatInput } from './DefaultChatInput';

export function DefaultChatUI({
  messages,
  isLoading,
  streamingMessage,
  thinkingSteps,
  isThinking,
  onSendMessage,
  onStartNewChat,
  onUpdateTitle,
  title,
  className = ''
}: ChatUIProps) {
  return (
    <DefaultChatContainer className={className}>
      <DefaultChatHeader
        title={title}
        onStartNewChat={onStartNewChat}
        onUpdateTitle={onUpdateTitle}
        className="border-b border-gray-200"
      />
      <DefaultChatMessageList
        messages={messages}
        streamingMessage={streamingMessage}
        thinkingSteps={thinkingSteps}
        isThinking={isThinking}
        className="flex-1 overflow-auto"
      />
      <DefaultChatInput
        onSendMessage={onSendMessage}
        isDisabled={isLoading}
        className="mt-auto"
      />
    </DefaultChatContainer>
  );
} 