import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { ChatService } from '@/services/ChatService';
import { ChatMessage } from '@/models/ChatSession';

interface SavedConversation {
  id: string;
  title: string;
  conversation_id: string;
  created_at: Date;
  updated_at: Date;
}

interface SavedConversationsSidebarProps {
  onSelectConversation: (conversationId: string) => void;
  currentConversationId?: string;
  onStartNewChat: () => void;
  isCollapsed?: boolean;
  onToggleCollapse?: () => void;
}

export function SavedConversationsSidebar({
  onSelectConversation,
  currentConversationId,
  onStartNewChat,
  isCollapsed = false,
  onToggleCollapse
}: SavedConversationsSidebarProps) {
  const { t } = useTranslation();
  const [conversations, setConversations] = useState<SavedConversation[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch conversations on mount and when search query changes
  useEffect(() => {
    const fetchConversations = async () => {
      try {
        setIsLoading(true);
        setError(null);
        console.log('Fetching conversations...');
        const results = await ChatService.listConversations({
          search: searchQuery,
          sortBy: 'updated_at',
          sortOrder: 'desc'
        });
        console.log('Received conversations:', results);
        setConversations(results);
      } catch (err) {
        console.error('Error loading conversations:', err);
        setError(err instanceof Error ? err.message : 'Failed to load conversations');
      } finally {
        setIsLoading(false);
      }
    };

    fetchConversations();
  }, [searchQuery]);

  return (
    <div className="h-full flex flex-col bg-gray-50">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 bg-white">
        <div className="flex items-center justify-between mb-4">
          {!isCollapsed && (
            <h2 className="text-lg font-semibold text-gray-900">
              {t('chat.savedChats')}
            </h2>
          )}
          <div className="flex items-center gap-2">
            {!isCollapsed && (
              <button
                onClick={onStartNewChat}
                className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
                title={t('chat.newChat')}
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clipRule="evenodd" />
                </svg>
              </button>
            )}
            <button
              onClick={onToggleCollapse}
              className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
              title={isCollapsed ? t('chat.expand') : t('chat.collapse')}
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-5 w-5"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d={isCollapsed ? "M13 5l7 7-7 7M5 5l7 7-7 7" : "M11 19l-7-7 7-7m8 14l-7-7 7-7"}
                />
              </svg>
            </button>
          </div>
        </div>
        {!isCollapsed && (
          <div className="relative">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder={t('chat.searchConversations')}
              className="w-full px-4 py-2 pl-10 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            />
            <svg
              className="absolute left-3 top-2.5 h-5 w-5 text-gray-400"
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 20 20"
              fill="currentColor"
            >
              <path
                fillRule="evenodd"
                d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z"
                clipRule="evenodd"
              />
            </svg>
          </div>
        )}
      </div>

      {/* Conversation List */}
      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="flex items-center justify-center h-full">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
          </div>
        ) : error ? (
          <div className="p-4 text-red-600 text-sm">{error}</div>
        ) : conversations.length === 0 ? (
          <div className="p-4 text-gray-500 text-sm text-center">
            {t('chat.noConversations')}
          </div>
        ) : (
          <div className="py-2">
            {conversations.map((conversation) => (
              <button
                key={conversation.id}
                onClick={() => onSelectConversation(conversation.id)}
                className={`w-full px-4 py-3 text-left transition-colors duration-200 ${
                  conversation.id === currentConversationId
                    ? 'bg-indigo-50 text-indigo-600'
                    : 'hover:bg-gray-100 text-gray-700'
                }`}
              >
                <div className="flex items-center gap-3">
                  <svg
                    className={`w-5 h-5 ${
                      conversation.id === currentConversationId
                        ? 'text-indigo-600'
                        : 'text-gray-400'
                    }`}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                    />
                  </svg>
                  {!isCollapsed && (
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">
                        {conversation.title || t('chat.untitled')}
                      </p>
                      <p className="text-xs text-gray-500 truncate">
                        {new Date(conversation.updated_at).toLocaleDateString()}
                      </p>
                    </div>
                  )}
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
} 