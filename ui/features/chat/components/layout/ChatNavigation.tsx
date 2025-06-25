import React, { useState } from 'react';
import { 
  ChatBubbleLeftIcon, 
  PlusIcon, 
  UserCircleIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  HomeIcon,
  DocumentTextIcon,
  Cog6ToothIcon
} from '@heroicons/react/24/outline';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

interface ChatNavigationProps {
  savedConversations: Array<{
    id: string;
    title: string;
    updated_at: string;
  }>;
  onNewChat: () => void;
  onSelectConversation: (id: string) => void;
  activeConversationId?: string;
}

export const ChatNavigation: React.FC<ChatNavigationProps> = ({
  savedConversations,
  onNewChat,
  onSelectConversation,
  activeConversationId
}) => {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const router = useRouter();

  const toggleCollapse = () => {
    setIsCollapsed(!isCollapsed);
  };

  return (
    <div className={`flex flex-col h-screen bg-gray-50 text-gray-700 transition-all duration-300 ${isCollapsed ? 'w-16' : 'w-64'}`}>
      {/* Collapse Toggle Button */}
      <button
        onClick={toggleCollapse}
        className="absolute -right-3 top-4 bg-white rounded-full p-1 hover:bg-gray-100 transition-colors shadow-sm"
      >
        {isCollapsed ? (
          <ChevronRightIcon className="h-4 w-4 text-gray-500" />
        ) : (
          <ChevronLeftIcon className="h-4 w-4 text-gray-500" />
        )}
      </button>

      {/* Main Navigation */}
      <div className="flex-1 flex flex-col">
        {/* New Chat Button */}
        <button
          onClick={onNewChat}
          className={`flex items-center gap-3 px-3 py-3 text-sm rounded-md hover:bg-gray-100 transition-colors ${
            isCollapsed ? 'justify-center' : 'justify-start'
          }`}
        >
          <PlusIcon className="h-5 w-5" />
          {!isCollapsed && <span>New Chat</span>}
        </button>

        {/* Navigation Links */}
        <nav className="mt-4 space-y-1 px-2">
          <Link
            href="/zh/chat"
            className={`flex items-center gap-3 px-3 py-2 text-sm rounded-md hover:bg-gray-100 transition-colors ${
              isCollapsed ? 'justify-center' : 'justify-start'
            }`}
          >
            <HomeIcon className="h-5 w-5" />
            {!isCollapsed && <span>Home</span>}
          </Link>
          <Link
            href="/zh/chat/history"
            className={`flex items-center gap-3 px-3 py-2 text-sm rounded-md hover:bg-gray-100 transition-colors ${
              isCollapsed ? 'justify-center' : 'justify-start'
            }`}
          >
            <DocumentTextIcon className="h-5 w-5" />
            {!isCollapsed && <span>History</span>}
          </Link>
        </nav>

        {/* Chat History Section */}
        <div className="flex-1 mt-4 overflow-y-auto">
          <div className="px-2">
            {savedConversations.map((conversation) => (
              <button
                key={conversation.id}
                onClick={() => onSelectConversation(conversation.id)}
                className={`w-full flex items-center gap-3 px-3 py-2 text-sm rounded-md hover:bg-gray-100 transition-colors ${
                  conversation.id === activeConversationId ? 'bg-gray-100' : ''
                } ${isCollapsed ? 'justify-center' : 'justify-start'}`}
              >
                <ChatBubbleLeftIcon className="h-5 w-5 flex-shrink-0" />
                {!isCollapsed && (
                  <div className="flex-1 min-w-0">
                    <p className="truncate">{conversation.title}</p>
                    <p className="text-xs text-gray-500 truncate">
                      {new Date(conversation.updated_at).toLocaleDateString()}
                    </p>
                  </div>
                )}
              </button>
            ))}
          </div>
        </div>

        {/* Account Settings Section */}
        <div className="mt-auto border-t border-gray-200">
          <Link
            href="/zh/settings"
            className={`flex items-center gap-3 px-3 py-3 text-sm hover:bg-gray-100 transition-colors ${
              isCollapsed ? 'justify-center' : 'justify-start'
            }`}
          >
            <UserCircleIcon className="h-5 w-5" />
            {!isCollapsed && <span>Account Settings</span>}
          </Link>
        </div>
      </div>
    </div>
  );
}; 