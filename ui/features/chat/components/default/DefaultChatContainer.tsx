'use client';

import React from 'react';
import { ChatContainerProps } from '../../types/chat-ui.types';

export function DefaultChatContainer({ children, className = '' }: ChatContainerProps) {
  return (
    <div className={`flex flex-col h-full w-full overflow-hidden ${className}`}>
      {children}
    </div>
  );
} 