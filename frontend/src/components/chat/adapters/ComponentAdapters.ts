/**
 * Chat Component Adapters
 * 
 * This file provides adapter functions to map between the frontend components
 * and UI library components, enabling a gradual transition between systems.
 */

import {
  ComponentAdapter,
  ComponentAdapterFactory,
  ChatContainerProps,
  ChatHeaderProps,
  ChatMessageListProps,
  UserMessageProps,
  AIMessageProps,
  StreamingMessageProps,
  ThinkingStepsProps,
  ChatInputProps
} from '../../../interfaces/components/chat.components';

/**
 * Creates an adapter that maps frontend ChatContainer props to UI library props
 */
export const createChatContainerAdapter = (): ComponentAdapter<any, ChatContainerProps> => {
  return (props: ChatContainerProps) => {
    // Transform frontend props to UI props
    return {
      children: props.children,
      isLoading: props.isLoading,
      fullHeight: props.isFullHeight,
      testId: props.testId,
      // Any additional transformations needed
    };
  };
};

/**
 * Creates an adapter that maps frontend ChatHeader props to UI library props
 */
export const createChatHeaderAdapter = (): ComponentAdapter<any, ChatHeaderProps> => {
  return (props: ChatHeaderProps) => {
    // Transform frontend props to UI props
    return {
      title: props.session?.name || 'New Chat',
      onRenameClick: props.onRenameSession ? () => props.onRenameSession?.(props.session?.id || '', '') : undefined,
      onSaveClick: props.onExportSession ? () => props.onExportSession?.('json') : undefined,
      onDeleteClick: props.onDeleteSession ? () => props.onDeleteSession?.(props.session?.id || '') : undefined,
      isEditable: true,
      testId: props.testId,
      // Additional transformations as needed
    };
  };
};

/**
 * Creates an adapter that maps frontend ChatMessageList props to UI library props
 */
export const createChatMessageListAdapter = (): ComponentAdapter<any, ChatMessageListProps> => {
  return (props: ChatMessageListProps) => {
    // Transform frontend props to UI props
    return {
      messages: props.messages.map(msg => ({
        id: msg.id,
        content: msg.content,
        timestamp: msg.timestamp,
        // Map other message properties
      })),
      isLoading: props.isLoading,
      testId: props.testId,
      // Additional transformations as needed
    };
  };
};

/**
 * Creates an adapter that maps frontend UserMessage props to UI library props
 */
export const createUserMessageAdapter = (): ComponentAdapter<any, UserMessageProps> => {
  return (props: UserMessageProps) => {
    // Transform frontend props to UI props
    return {
      id: props.message.id,
      content: props.message.content,
      timestamp: props.message.timestamp,
      username: props.message.sender,
      avatarUrl: props.avatarUrl,
      testId: props.testId,
      // Additional transformations as needed
    };
  };
};

/**
 * Creates an adapter that maps frontend AIMessage props to UI library props
 */
export const createAIMessageAdapter = (): ComponentAdapter<any, AIMessageProps> => {
  return (props: AIMessageProps) => {
    // Transform frontend props to UI props
    return {
      id: props.message.id,
      content: props.message.content,
      timestamp: props.message.timestamp,
      modelName: props.message.sender,
      thinkingSteps: props.thinkingSteps?.map(step => step.content) || [],
      showThinking: props.showThinkingSteps,
      testId: props.testId,
      // Additional transformations as needed
    };
  };
};

/**
 * Creates an adapter that maps frontend StreamingMessage props to UI library props
 */
export const createStreamingMessageAdapter = (): ComponentAdapter<any, StreamingMessageProps> => {
  return (props: StreamingMessageProps) => {
    // Transform frontend props to UI props
    return {
      content: props.content,
      showCursor: !props.isComplete,
      testId: props.testId,
      // Additional transformations as needed
    };
  };
};

/**
 * Creates an adapter that maps frontend ThinkingSteps props to UI library props
 */
export const createThinkingStepsAdapter = (): ComponentAdapter<any, ThinkingStepsProps> => {
  return (props: ThinkingStepsProps) => {
    // Transform frontend props to UI props
    return {
      steps: props.steps.map(step => step.content),
      animate: true,
      testId: props.testId,
      // Additional transformations as needed
    };
  };
};

/**
 * Creates an adapter that maps frontend ChatInput props to UI library props
 */
export const createChatInputAdapter = (): ComponentAdapter<any, ChatInputProps> => {
  return (props: ChatInputProps) => {
    // Transform frontend props to UI props
    return {
      value: props.initialValue || '',
      onChange: (value: string) => {}, // This would be handled differently in the UI implementation
      onSubmit: async (value: string, attachments?: File[]) => {
        if (attachments && attachments.length > 0 && props.onSendAttachments) {
          // Convert File[] to Attachment[]
          const mappedAttachments = attachments.map(file => ({
            id: `attachment-${Date.now()}-${file.name}`,
            name: file.name,
            type: file.type,
            size: file.size,
            content: file
          }));
          await props.onSendAttachments(value, mappedAttachments);
        } else {
          await props.onSendMessage(value);
        }
      },
      placeholder: props.placeholder,
      isDisabled: props.isDisabled,
      isLoading: props.isLoading,
      enableAttachments: !!props.onSendAttachments,
      allowedFileTypes: props.supportedAttachmentTypes,
      maxFileSize: props.maxAttachmentSize,
      testId: props.testId,
      // Additional transformations as needed
    };
  };
};

/**
 * Factory for creating all component adapters
 */
export const createComponentAdapterFactory = (): ComponentAdapterFactory => {
  return {
    createChatContainerAdapter,
    createChatHeaderAdapter,
    createChatMessageListAdapter,
    createUserMessageAdapter,
    createAIMessageAdapter,
    createStreamingMessageAdapter,
    createThinkingStepsAdapter,
    createChatInputAdapter
  };
}; 