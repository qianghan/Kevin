'use client';

import { useState, useEffect, useRef } from 'react';
import { useSession } from 'next-auth/react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { format } from 'date-fns';
import axios from 'axios';
import { toast } from 'react-hot-toast';

// Interface for a chat session
interface ChatSession {
  id: string;
  title: string;
  conversation_id: string;
  created_at: string;
  updated_at: string;
}

// Interface for sort options
interface SortOption {
  field: 'createdAt' | 'updatedAt';
  order: 'asc' | 'desc';
  label: string;
}

export default function SessionsPage() {
  const router = useRouter();
  const { data: session, status } = useSession();
  const [isLoading, setIsLoading] = useState(true);
  const [chatSessions, setChatSessions] = useState<ChatSession[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [sortOption, setSortOption] = useState<SortOption>({
    field: 'updatedAt',
    order: 'desc',
    label: 'Last Updated (newest first)'
  });
  const [editingSession, setEditingSession] = useState<string | null>(null);
  const [newTitle, setNewTitle] = useState('');
  const [isDeleting, setIsDeleting] = useState<string | null>(null);
  const editInputRef = useRef<HTMLInputElement>(null);

  const sortOptions: SortOption[] = [
    { field: 'updatedAt', order: 'desc', label: 'Last Updated (newest first)' },
    { field: 'updatedAt', order: 'asc', label: 'Last Updated (oldest first)' },
    { field: 'createdAt', order: 'desc', label: 'Created Date (newest first)' },
    { field: 'createdAt', order: 'asc', label: 'Created Date (oldest first)' },
  ];

  // Load sessions with search and sort parameters
  const loadSessions = async () => {
    setIsLoading(true);
    try {
      // Build query parameters
      const params = new URLSearchParams();
      if (searchQuery.trim()) {
        params.append('search', searchQuery.trim());
      }
      params.append('sortBy', sortOption.field);
      params.append('sortOrder', sortOption.order);

      // Fetch user's chat sessions from the API
      const response = await axios.get(`/api/chat/sessions?${params.toString()}`);
      if (response.data && response.data.sessions) {
        setChatSessions(response.data.sessions);
      } else {
        setChatSessions([]);
      }
    } catch (error) {
      console.error('Error loading chat sessions:', error);
      toast.error('Failed to load chat sessions');
      setChatSessions([]);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    // Check if user is authenticated
    if (status === 'unauthenticated') {
      router.push('/login');
      return;
    }

    if (status === 'authenticated') {
      loadSessions();
    }
  }, [status, router, sortOption]);

  // Focus the edit input when editing starts
  useEffect(() => {
    if (editingSession && editInputRef.current) {
      editInputRef.current.focus();
    }
  }, [editingSession]);

  const formatDate = (dateString: string) => {
    try {
      return format(new Date(dateString), 'MMM dd, yyyy h:mm a');
    } catch (error) {
      return 'Unknown date';
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    loadSessions();
  };

  const startEditing = (session: ChatSession) => {
    setEditingSession(session.id);
    setNewTitle(session.title);
  };

  const cancelEditing = () => {
    setEditingSession(null);
    setNewTitle('');
  };

  const saveTitle = async (sessionId: string) => {
    try {
      const response = await axios.patch('/api/chat/sessions', {
        sessionId,
        title: newTitle.trim() || 'Untitled Chat'
      });

      if (response.data.success) {
        // Update the local state
        setChatSessions(prev => 
          prev.map(session => 
            session.id === sessionId 
              ? { ...session, title: newTitle.trim() || 'Untitled Chat' } 
              : session
          )
        );
        toast.success('Title updated');
      } else {
        throw new Error(response.data.error || 'Failed to update title');
      }
    } catch (error) {
      console.error('Error updating session title:', error);
      toast.error('Failed to update title');
    } finally {
      setEditingSession(null);
      setNewTitle('');
    }
  };

  const deleteSession = async (sessionId: string) => {
    if (!window.confirm('Are you sure you want to delete this session?')) {
      return;
    }

    setIsDeleting(sessionId);
    try {
      const response = await axios.delete(`/api/chat/sessions?id=${sessionId}`);
      if (response.data.success) {
        // Remove from local state
        setChatSessions(prev => prev.filter(session => session.id !== sessionId));
        toast.success('Session deleted');
      } else {
        throw new Error(response.data.error || 'Failed to delete session');
      }
    } catch (error) {
      console.error('Error deleting session:', error);
      toast.error('Failed to delete session');
    } finally {
      setIsDeleting(null);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent, sessionId: string) => {
    if (e.key === 'Enter') {
      saveTitle(sessionId);
    } else if (e.key === 'Escape') {
      cancelEditing();
    }
  };

  const handleSortChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const selectedIndex = parseInt(e.target.value);
    setSortOption(sortOptions[selectedIndex]);
  };

  if (status === 'loading' || isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-800">Loading your sessions...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-6">
      <header className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Chat Sessions</h1>
        <p className="text-gray-800 mt-2">
          View and continue your previous conversations.
        </p>
      </header>

      {/* Search and sort controls */}
      <div className="mb-6 flex flex-col md:flex-row md:items-end gap-4">
        <div className="flex-grow">
          <form onSubmit={handleSearch} className="flex items-center">
            <div className="relative flex-grow">
              <input
                type="text"
                placeholder="Search by title..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full p-3 border border-gray-200 rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <button
                type="submit"
                className="absolute right-2 top-1/2 transform -translate-y-1/2 text-gray-500 hover:text-gray-700"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </button>
            </div>
          </form>
        </div>
        <div className="md:w-64">
          <label htmlFor="sort-select" className="block text-sm font-medium text-gray-700 mb-1">
            Sort by
          </label>
          <select
            id="sort-select"
            value={sortOptions.findIndex(option => 
              option.field === sortOption.field && option.order === sortOption.order
            )}
            onChange={handleSortChange}
            className="w-full p-3 border border-gray-200 rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            {sortOptions.map((option, index) => (
              <option key={index} value={index}>
                {option.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {chatSessions.length > 0 ? (
        <div className="bg-white shadow-md rounded-lg overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-900 uppercase tracking-wider">
                    Title
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-900 uppercase tracking-wider">
                    Created
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-900 uppercase tracking-wider">
                    Last Updated
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-900 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {chatSessions.map((chatSession) => (
                  <tr key={chatSession.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      {editingSession === chatSession.id ? (
                        <div className="flex items-center space-x-2">
                          <input
                            ref={editInputRef}
                            type="text"
                            value={newTitle}
                            onChange={(e) => setNewTitle(e.target.value)}
                            onKeyDown={(e) => handleKeyDown(e, chatSession.id)}
                            className="w-full p-1 border border-gray-300 rounded"
                          />
                          <button
                            onClick={() => saveTitle(chatSession.id)}
                            className="p-1 bg-green-100 text-green-700 rounded hover:bg-green-200"
                            title="Save"
                          >
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                            </svg>
                          </button>
                          <button
                            onClick={cancelEditing}
                            className="p-1 bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
                            title="Cancel"
                          >
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                            </svg>
                          </button>
                        </div>
                      ) : (
                        <div className="text-sm font-medium text-gray-900">{chatSession.title}</div>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-800">{formatDate(chatSession.created_at)}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-800">{formatDate(chatSession.updated_at)}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center space-x-3">
                        <Link
                          href={`/chat?id=${chatSession.conversation_id}`}
                          className="text-blue-600 hover:text-blue-900"
                        >
                          Continue
                        </Link>
                        <button
                          onClick={() => startEditing(chatSession)}
                          className="text-gray-600 hover:text-gray-900"
                          title="Edit title"
                          disabled={editingSession !== null}
                        >
                          <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                          </svg>
                        </button>
                        <button
                          onClick={() => deleteSession(chatSession.id)}
                          className="text-red-600 hover:text-red-900"
                          title="Delete session"
                          disabled={isDeleting !== null}
                        >
                          {isDeleting === chatSession.id ? (
                            <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                            </svg>
                          ) : (
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                            </svg>
                          )}
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        <div className="bg-white shadow-md rounded-lg p-6 text-center">
          <p className="text-gray-800 mb-4">
            {searchQuery 
              ? 'No sessions found matching your search. Try a different query.' 
              : "You don't have any chat sessions yet."
            }
          </p>
          <Link
            href="/chat"
            className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
          >
            Start a New Chat
          </Link>
        </div>
      )}
    </div>
  );
} 