import { ReactNode } from 'react';
import { ChatMessage, ThinkingStep } from '../../../lib/types';

// Props for each component
export interface ChatContainerProps {
  children: ReactNode;
  className?: string;
}

export interface ChatHeaderProps {
  title: string;
  onStartNewChat?: () => void;
  onUpdateTitle?: (newTitle: string) => void;
  onSave?: () => Promise<boolean>;
  className?: string;
}

export interface ChatMessageListProps {
  messages: ChatMessage[];
  streamingMessage?: string;
  thinkingSteps?: ThinkingStep[];
  isThinking?: boolean;
  isLoading?: boolean;
  className?: string;
  onStartNewChat?: () => void;
  sampleQuestions?: Array<{
    text: string;
    handler: () => void;
  }>;
  onRefreshQuestions?: () => void;
}

export interface ChatInputProps {
  onSendMessage: (message: string) => void;
  isDisabled?: boolean;
  placeholder?: string;
  className?: string;
  useWebSearch?: boolean;
  onToggleWebSearch?: () => void;
}

// Props for the main ChatUI component
export interface ChatUIProps {
  messages: ChatMessage[];
  isLoading: boolean;
  streamingMessage?: string;
  thinkingSteps?: ThinkingStep[];
  isThinking?: boolean;
  onSendMessage: (message: string) => void;
  onStartNewChat: () => void;
  onUpdateTitle?: (newTitle: string) => void;
  title: string;
  className?: string;
}

// Adapter props to connect context to UI
export interface ChatAdapterProps {
  components: {
    ChatContainer: React.ComponentType<ChatContainerProps>;
    ChatHeader: React.ComponentType<ChatHeaderProps>;
    ChatMessageList: React.ComponentType<ChatMessageListProps>;
    ChatInput: React.ComponentType<ChatInputProps>;
  };
  initialConversationId?: string;
  initialMessages?: ChatMessage[];
}

// All components together
export interface ChatComponentsProps {
  ChatContainer: React.ComponentType<ChatContainerProps>;
  ChatHeader: React.ComponentType<ChatHeaderProps>;
  ChatMessageList: React.ComponentType<ChatMessageListProps>;
  ChatInput: React.ComponentType<ChatInputProps>;
} 