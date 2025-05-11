/**
 * Chat Component Interfaces
 * 
 * This file defines interfaces for chat-related components in the frontend application.
 * These interfaces are aligned with the existing UI implementations to ensure compatibility
 * while allowing for frontend-specific adaptations.
 */

import { ReactNode } from 'react';
import { BoxProps, FlexProps, ButtonProps } from '@chakra-ui/react';
import { 
  ChatSession, 
  ChatMessage, 
  Attachment, 
  ThinkingStep,
  ChatOptions 
} from '../services/chat.service';
import { IconType } from 'react-icons';

/**
 * Base props interface for all chat components
 */
export interface ChatComponentBaseProps {
  className?: string;
  testId?: string;
}

/**
 * Chat Container Component Props
 */
export interface ChatContainerProps extends ChatComponentBaseProps, BoxProps {
  children: ReactNode;
  isLoading?: boolean;
  isFullHeight?: boolean;
}

/**
 * Chat Header Component Props
 */
export interface ChatHeaderProps extends ChatComponentBaseProps, FlexProps {
  session: ChatSession | null;
  onRenameSession?: (sessionId: string, newName: string) => Promise<void>;
  onExportSession?: (format: 'json' | 'text' | 'markdown' | 'pdf') => Promise<void>;
  onDeleteSession?: (sessionId: string) => Promise<void>;
  onCreateNewSession?: () => Promise<void>;
  isRenaming?: boolean;
}

/**
 * Chat Message List Component Props
 */
export interface ChatMessageListProps extends ChatComponentBaseProps, BoxProps {
  messages: ChatMessage[];
  isLoading?: boolean;
  showThinkingSteps?: boolean;
  onFetchThinkingSteps?: (messageId: string) => Promise<ThinkingStep[]>;
  scrollBehavior?: 'auto' | 'smooth';
  emptyStateMessage?: string;
  isFullHeight?: boolean;
}

/**
 * Chat Message Component Base Props
 */
export interface ChatMessageBaseProps extends ChatComponentBaseProps, BoxProps {
  message: ChatMessage;
  isLast?: boolean;
  showTimestamp?: boolean;
  highlightText?: string;
}

/**
 * User Message Component Props
 */
export interface UserMessageProps extends ChatMessageBaseProps {
  // Specific props for user messages
  avatarUrl?: string;
}

/**
 * AI Message Component Props
 */
export interface AIMessageProps extends ChatMessageBaseProps {
  // Specific props for AI messages
  onFetchThinkingSteps?: (messageId: string) => Promise<ThinkingStep[]>;
  showThinkingSteps?: boolean;
  thinkingSteps?: ThinkingStep[];
  isThinkingStepsLoading?: boolean;
}

/**
 * Streaming Message Component Props
 */
export interface StreamingMessageProps extends ChatComponentBaseProps, BoxProps {
  content: string;
  isComplete?: boolean;
  cursorBlinkSpeed?: number; // in ms
  typingIndicator?: boolean;
}

/**
 * Thinking Steps Component Props
 */
export interface ThinkingStepsProps extends ChatComponentBaseProps, BoxProps {
  steps: ThinkingStep[];
  isLoading?: boolean;
  isExpanded?: boolean;
  onToggleExpand?: () => void;
}

/**
 * Chat Input Component Props
 */
export interface ChatInputProps extends ChatComponentBaseProps, Omit<BoxProps, 'onChange'> {
  onSendMessage: (content: string, options?: ChatOptions) => Promise<void>;
  onSendAttachments?: (content: string, attachments: Attachment[], options?: ChatOptions) => Promise<void>;
  isDisabled?: boolean;
  isLoading?: boolean;
  placeholder?: string;
  initialValue?: string;
  supportedAttachmentTypes?: string[];
  maxAttachmentSize?: number; // in bytes
  showOptionsMenu?: boolean;
  availableOptions?: ChatOptions;
  onChange?: (value: string) => void;
}

/**
 * Attachment Preview Component Props
 */
export interface AttachmentPreviewProps extends ChatComponentBaseProps, BoxProps {
  attachment: Attachment;
  onRemove?: () => void;
  isRemovable?: boolean;
  showFileInfo?: boolean;
}

/**
 * Attachment Upload Component Props
 */
export interface AttachmentUploadProps extends ChatComponentBaseProps, ButtonProps {
  onFilesSelected: (files: File[]) => void;
  acceptedFileTypes?: string;
  maxFileSize?: number; // in bytes
  multiple?: boolean;
  children?: ReactNode;
}

/**
 * Chat Session List Component Props
 */
export interface ChatSessionListProps extends ChatComponentBaseProps, BoxProps {
  sessions: ChatSession[];
  currentSessionId?: string;
  onSelectSession: (sessionId: string) => void;
  onCreateSession?: () => Promise<void>;
  isLoading?: boolean;
  emptyStateMessage?: string;
}

/**
 * Chat Session Card Component Props
 */
export interface ChatSessionCardProps extends ChatComponentBaseProps, BoxProps {
  session: ChatSession;
  isActive?: boolean;
  onSelect: () => void;
  showLastMessage?: boolean;
  showTimestamp?: boolean;
}

/**
 * Component adapters to map between UI and frontend implementations
 */
export type ComponentAdapter<UIProps, FrontendProps> = (props: FrontendProps) => UIProps;

/**
 * Factory for creating component adapters
 */
export interface ComponentAdapterFactory {
  createChatContainerAdapter: () => ComponentAdapter<any, ChatContainerProps>;
  createChatHeaderAdapter: () => ComponentAdapter<any, ChatHeaderProps>;
  createChatMessageListAdapter: () => ComponentAdapter<any, ChatMessageListProps>;
  createUserMessageAdapter: () => ComponentAdapter<any, UserMessageProps>;
  createAIMessageAdapter: () => ComponentAdapter<any, AIMessageProps>;
  createStreamingMessageAdapter: () => ComponentAdapter<any, StreamingMessageProps>;
  createThinkingStepsAdapter: () => ComponentAdapter<any, ThinkingStepsProps>;
  createChatInputAdapter: () => ComponentAdapter<any, ChatInputProps>;
}

/**
 * Menu item for chat header and other components
 */
export interface MenuItemProps {
  label: string;
  icon?: ReactNode;
  onClick: () => void;
  color?: string;
  testId?: string;
}

/**
 * Simplified Chat header component props for new implementation
 */
export interface SimpleChatHeaderProps {
  /** Title of the chat session */
  title?: string;
  /** Handler for clicking the info button */
  onInfoClick?: () => void;
  /** Handler for clicking the save option */
  onSaveClick?: () => void;
  /** Handler for clicking the delete option */
  onDeleteClick?: () => void;
  /** Handler for clicking the rename option */
  onRenameClick?: () => void;
  /** Additional menu items to display */
  menuItems?: MenuItemProps[];
  /** Whether to show controls */
  showControls?: boolean;
  /** Whether the chat title is editable */
  isEditable?: boolean;
  /** Test ID for component */
  testId?: string;
}

/**
 * Simplified Chat container component props for new implementation
 */
export interface SimpleChatContainerProps {
  /** Children components */
  children: ReactNode;
  /** Whether content is loading */
  isLoading?: boolean;
  /** Whether to use full height */
  fullHeight?: boolean;
  /** Test ID for component */
  testId?: string;
}

/**
 * Chat message props shared between user and AI messages
 */
export interface BaseMessageProps {
  /** Unique ID of the message */
  id: string;
  /** Content of the message */
  content: string | ReactNode;
  /** Timestamp of the message */
  timestamp?: Date | string;
  /** Avatar URL */
  avatarUrl?: string;
  /** Whether the message is being edited */
  isEditing?: boolean;
  /** Whether to highlight the message */
  isHighlighted?: boolean;
  /** Whether the message contains an error */
  hasError?: boolean;
  /** Additional actions for the message */
  actions?: MenuItemProps[];
  /** Test ID for component */
  testId?: string;
}

/**
 * Simplified User message component props for new implementation
 */
export interface SimpleUserMessageProps extends BaseMessageProps {
  /** Username to display */
  username?: string;
  /** Handler for editing message */
  onEdit?: (id: string, newContent: string) => void;
  /** Handler for deleting message */
  onDelete?: (id: string) => void;
}

/**
 * Simplified AI message component props for new implementation
 */
export interface SimpleAIMessageProps extends BaseMessageProps {
  /** AI model name */
  modelName?: string;
  /** Thinking steps from the AI */
  thinkingSteps?: string[] | ThinkingStep[];
  /** Whether to show thinking steps */
  showThinking?: boolean;
  /** Whether message is still being generated */
  isStreaming?: boolean;
  /** Handler for regenerating response */
  onRegenerate?: (id: string) => void;
  /** Handler for copying message content */
  onCopy?: (id: string, content: string) => void;
  /** Handler for feedback (thumbs up) */
  onPositiveFeedback?: (id: string) => void;
  /** Handler for feedback (thumbs down) */
  onNegativeFeedback?: (id: string) => void;
}

/**
 * Simplified Chat message list component props for new implementation
 */
export interface SimpleChatMessageListProps {
  /** List of messages */
  messages: Array<SimpleUserMessageProps | SimpleAIMessageProps>;
  /** Whether messages are loading */
  isLoading?: boolean;
  /** Height of the message list */
  height?: string | number;
  /** Whether to reverse message order */
  isReversed?: boolean;
  /** Test ID for component */
  testId?: string;
}

/**
 * Simplified Chat input component props for new implementation
 */
export interface SimpleChatInputProps {
  /** Value of the input */
  value: string;
  /** Handler for value change */
  onChange: (value: string) => void;
  /** Handler for submit */
  onSubmit: (value: string, attachments?: File[]) => void;
  /** Placeholder text */
  placeholder?: string;
  /** Whether the input is disabled */
  isDisabled?: boolean;
  /** Whether the input is loading/processing */
  isLoading?: boolean;
  /** Whether to enable file attachments */
  enableAttachments?: boolean;
  /** Allowed file types for attachments */
  allowedFileTypes?: string[];
  /** Maximum file size in bytes */
  maxFileSize?: number;
  /** Maximum number of attachments */
  maxAttachments?: number;
  /** Test ID for component */
  testId?: string;
}

/**
 * Simplified Thinking steps component props for new implementation
 */
export interface SimpleThinkingStepsProps {
  /** Array of thinking step strings */
  steps: string[] | ThinkingStep[];
  /** Whether to animate the steps */
  animate?: boolean;
  /** Test ID for component */
  testId?: string;
}

/**
 * Simplified Streaming message component props for new implementation
 */
export interface SimpleStreamingMessageProps {
  /** Content being streamed */
  content: string;
  /** Whether to show the cursor animation */
  showCursor?: boolean;
  /** Test ID for component */
  testId?: string;
} 