import { useState, useCallback } from 'react';
import { ChatMessage } from '@/models/ChatSession';
import { chatService, ChatRequest, ChatResponse } from '@/services/ChatService';

/**
 * Custom hook for chat operations
 */
export function useChat() {
  const [isSaving, setIsSaving] = useState(false);
  const [lastSavedHash, setLastSavedHash] = useState<string>('');
  const [isDeleting, setIsDeleting] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  
  /**
   * Generate a hash of the current messages to track if they've been saved
   */
  const generateMessageHash = useCallback((messages: ChatMessage[]): string => {
    return messages.map(m => `${m.role}:${m.content.substring(0, 50)}`).join('|');
  }, []);
  
  /**
   * Save conversation with duplicate detection
   */
  const saveConversation = useCallback(async (
    conversationId: string, 
    messages: ChatMessage[], 
    contextSummary: string,
    title?: string
  ): Promise<boolean> => {
    if (!messages.length) {
      console.log('No messages to save');
      return false;
    }
    
    const currentHash = generateMessageHash(messages);
    
    // Skip saving if already saved this exact set of messages within the same session
    if (currentHash === lastSavedHash) {
      console.log('Skipping save - messages already saved with same hash');
      return true;
    }
    
    console.log(`Saving conversation with ID: ${conversationId}, ${messages.length} messages, hash: ${currentHash.substring(0, 20)}...`);
    
    setIsSaving(true);
    try {
      // Extract a default title from the first user message if no title provided
      const defaultTitle = title || (messages.length > 0 && messages[0].role === 'user' 
        ? messages[0].content.substring(0, 50) 
        : 'New Chat');
      
      const success = await chatService.saveConversation(
        conversationId, 
        messages, 
        contextSummary,
        defaultTitle
      );
      
      if (success) {
        setLastSavedHash(currentHash);
        console.log('Conversation saved successfully');
      } else {
        console.warn('Conversation save returned unsuccessful status');
      }
      
      return success;
    } catch (error) {
      console.error('Error in save operation:', error instanceof Error ? error.message : String(error), {
        timestamp: new Date().toISOString(),
        conversationId,
        messageCount: messages.length
      });
      return false;
    } finally {
      setIsSaving(false);
    }
  }, [generateMessageHash, lastSavedHash, chatService]);
  
  /**
   * Get a conversation by ID
   */
  const getConversation = useCallback(async (conversationId: string) => {
    return await chatService.getConversation(conversationId);
  }, []);
  
  /**
   * List all conversations with optional search and sorting
   */
  const listConversations = useCallback(async (options?: {
    search?: string;
    sortBy?: string;
    sortOrder?: 'asc' | 'desc';
  }) => {
    setIsLoading(true);
    try {
      const conversations = await chatService.listConversations(options);
      return conversations;
    } catch (error) {
      console.error('Error listing conversations:', error);
      return [];
    } finally {
      setIsLoading(false);
    }
  }, []);
  
  /**
   * Delete a conversation by ID
   */
  const deleteConversation = useCallback(async (conversationId: string): Promise<boolean> => {
    setIsDeleting(true);
    try {
      const success = await chatService.deleteConversation(conversationId);
      return success;
    } catch (error) {
      console.error('Error deleting conversation:', error);
      return false;
    } finally {
      setIsDeleting(false);
    }
  }, []);
  
  /**
   * Update a conversation's title
   */
  const updateConversationTitle = useCallback(async (sessionId: string, title: string): Promise<boolean> => {
    setIsSaving(true);
    try {
      const success = await chatService.updateConversationTitle(sessionId, title);
      return success;
    } catch (error) {
      console.error('Error updating conversation title:', error);
      return false;
    } finally {
      setIsSaving(false);
    }
  }, []);
  
  /**
   * Send a chat query
   */
  const sendChatQuery = useCallback(async (request: ChatRequest): Promise<ChatResponse> => {
    return await chatService.query(request);
  }, []);
  
  /**
   * Get URL for streaming chat
   */
  const getStreamUrl = useCallback((request: ChatRequest): string => {
    return chatService.getStreamUrl(request);
  }, []);
  
  return {
    isSaving,
    isDeleting,
    isLoading,
    saveConversation,
    getConversation,
    listConversations,
    deleteConversation,
    updateConversationTitle,
    sendChatQuery,
    getStreamUrl,
  };
} 