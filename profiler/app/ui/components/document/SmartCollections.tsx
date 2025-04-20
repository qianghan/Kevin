'use client';

import React, { useState, useEffect } from 'react';
import { useDocumentService } from '../../lib/contexts/DocumentContext';

export interface SmartCollection {
  id: string;
  name: string;
  description?: string;
  query: string;
  documentCount: number;
  lastUpdated?: Date;
  icon?: string;
}

interface SmartCollectionsProps {
  collections: SmartCollection[];
  selectedCollectionId?: string;
  onCollectionSelect: (collectionId: string) => void;
  onCreateCollection: (collection: Omit<SmartCollection, 'id' | 'documentCount' | 'lastUpdated'>) => Promise<string>;
  onUpdateCollection: (id: string, updates: Partial<SmartCollection>) => Promise<void>;
  onDeleteCollection: (id: string) => Promise<void>;
  onRunCollection: (id: string) => Promise<void>;
  readOnly?: boolean;
}

const SmartCollections: React.FC<SmartCollectionsProps> = ({
  collections,
  selectedCollectionId,
  onCollectionSelect,
  onCreateCollection,
  onUpdateCollection,
  onDeleteCollection,
  onRunCollection,
  readOnly = false
}) => {
  const [isCreating, setIsCreating] = useState(false);
  const [editingCollectionId, setEditingCollectionId] = useState<string | null>(null);
  
  // New collection form state
  const [newName, setNewName] = useState('');
  const [newDescription, setNewDescription] = useState('');
  const [newQuery, setNewQuery] = useState('');
  const [newIcon, setNewIcon] = useState('📄');
  
  // Edit collection form state
  const [editName, setEditName] = useState('');
  const [editDescription, setEditDescription] = useState('');
  const [editQuery, setEditQuery] = useState('');
  const [editIcon, setEditIcon] = useState('');
  
  const { documentService } = useDocumentService();
  
  const icons = ['📄', '📋', '📁', '📚', '📊', '📈', '🔍', '⭐', '📅', '💼', '🏢', '🗂️'];
  
  // Reset form when not creating
  useEffect(() => {
    if (!isCreating) {
      setNewName('');
      setNewDescription('');
      setNewQuery('');
      setNewIcon('📄');
    }
  }, [isCreating]);
  
  // Start editing a collection
  const startEditing = (collection: SmartCollection) => {
    setEditingCollectionId(collection.id);
    setEditName(collection.name);
    setEditDescription(collection.description || '');
    setEditQuery(collection.query);
    setEditIcon(collection.icon || '📄');
  };
  
  // Cancel editing
  const cancelEditing = () => {
    setEditingCollectionId(null);
  };
  
  // Handle create smart collection
  const handleCreateCollection = async () => {
    if (!newName.trim() || !newQuery.trim()) return;
    
    try {
      const newId = await onCreateCollection({
        name: newName.trim(),
        description: newDescription.trim() || undefined,
        query: newQuery.trim(),
        icon: newIcon
      });
      
      setIsCreating(false);
      onCollectionSelect(newId);
    } catch (error) {
      console.error('Error creating smart collection:', error);
    }
  };
  
  // Handle update smart collection
  const handleUpdateCollection = async (id: string) => {
    if (!editName.trim() || !editQuery.trim()) return;
    
    try {
      await onUpdateCollection(id, {
        name: editName.trim(),
        description: editDescription.trim() || undefined,
        query: editQuery.trim(),
        icon: editIcon
      });
      
      setEditingCollectionId(null);
    } catch (error) {
      console.error('Error updating smart collection:', error);
    }
  };
  
  // Handle delete smart collection
  const handleDeleteCollection = async (id: string) => {
    if (!window.confirm('Are you sure you want to delete this smart collection?')) {
      return;
    }
    
    try {
      await onDeleteCollection(id);
      
      // If the deleted collection was selected, clear selection
      if (selectedCollectionId === id) {
        onCollectionSelect('');
      }
    } catch (error) {
      console.error('Error deleting smart collection:', error);
    }
  };
  
  // Handle run smart collection query
  const handleRunCollection = async (id: string) => {
    try {
      await onRunCollection(id);
    } catch (error) {
      console.error('Error running smart collection:', error);
    }
  };
  
  // Format date to readable format
  const formatDate = (date?: Date) => {
    if (!date) return 'Never';
    return new Date(date).toLocaleDateString(undefined, {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };
  
  return (
    <div className="bg-white rounded-lg border border-gray-200">
      <div className="p-3 border-b border-gray-200">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-sm font-medium text-gray-700">Smart Collections</h3>
          
          {!readOnly && !isCreating && (
            <button
              onClick={() => setIsCreating(true)}
              className="text-xs text-blue-600 hover:text-blue-800 flex items-center"
            >
              <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              </svg>
              Create Collection
            </button>
          )}
        </div>
        
        {/* Create Collection Form */}
        {isCreating && (
          <div className="mb-3 p-3 bg-gray-50 rounded-md">
            <h4 className="text-xs font-medium text-gray-700 mb-2">New Smart Collection</h4>
            
            <div className="space-y-2">
              <div className="flex space-x-2 items-center">
                <div className="relative">
                  <button
                    type="button"
                    className="inline-flex items-center justify-center w-8 h-8 text-lg border border-gray-300 rounded-md hover:bg-gray-50"
                  >
                    {newIcon}
                  </button>
                  <div className="absolute top-full left-0 mt-1 p-2 bg-white rounded-md shadow-md z-10 grid grid-cols-4 gap-1">
                    {icons.map((icon) => (
                      <button
                        key={icon}
                        type="button"
                        className="w-8 h-8 text-lg hover:bg-gray-100 rounded"
                        onClick={() => setNewIcon(icon)}
                      >
                        {icon}
                      </button>
                    ))}
                  </div>
                </div>
                
                <input
                  type="text"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  placeholder="Collection name"
                  className="flex-1 w-full text-sm border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              
              <textarea
                value={newDescription}
                onChange={(e) => setNewDescription(e.target.value)}
                placeholder="Description (optional)"
                rows={2}
                className="w-full text-sm border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
              />
              
              <textarea
                value={newQuery}
                onChange={(e) => setNewQuery(e.target.value)}
                placeholder="Query (e.g. 'type:pdf AND created:>2023-01-01')"
                rows={2}
                className="w-full text-sm border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
              />
              
              <div className="flex justify-end space-x-2">
                <button
                  onClick={() => setIsCreating(false)}
                  className="px-2 py-1 text-xs text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  onClick={handleCreateCollection}
                  disabled={!newName.trim() || !newQuery.trim()}
                  className={`px-2 py-1 text-xs text-white bg-blue-600 rounded-md hover:bg-blue-700 ${
                    !newName.trim() || !newQuery.trim() ? 'opacity-50 cursor-not-allowed' : ''
                  }`}
                >
                  Create
                </button>
              </div>
            </div>
          </div>
        )}
        
        {/* Collections List */}
        <div className="space-y-1 max-h-64 overflow-y-auto">
          {collections.length === 0 && !isCreating && (
            <div className="text-center py-4">
              <p className="text-sm text-gray-500">No smart collections yet</p>
              {!readOnly && (
                <button
                  onClick={() => setIsCreating(true)}
                  className="mt-1 text-xs text-blue-600 hover:text-blue-800"
                >
                  Create your first smart collection
                </button>
              )}
            </div>
          )}
          
          {collections.map((collection) => (
            <div key={collection.id}>
              {editingCollectionId === collection.id ? (
                // Edit Collection Form
                <div className="mb-3 p-3 bg-gray-50 rounded-md">
                  <div className="space-y-2">
                    <div className="flex space-x-2 items-center">
                      <div className="relative">
                        <button
                          type="button"
                          className="inline-flex items-center justify-center w-8 h-8 text-lg border border-gray-300 rounded-md hover:bg-gray-50"
                        >
                          {editIcon}
                        </button>
                        <div className="absolute top-full left-0 mt-1 p-2 bg-white rounded-md shadow-md z-10 grid grid-cols-4 gap-1">
                          {icons.map((icon) => (
                            <button
                              key={icon}
                              type="button"
                              className="w-8 h-8 text-lg hover:bg-gray-100 rounded"
                              onClick={() => setEditIcon(icon)}
                            >
                              {icon}
                            </button>
                          ))}
                        </div>
                      </div>
                      
                      <input
                        type="text"
                        value={editName}
                        onChange={(e) => setEditName(e.target.value)}
                        placeholder="Collection name"
                        className="flex-1 w-full text-sm border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                      />
                    </div>
                    
                    <textarea
                      value={editDescription}
                      onChange={(e) => setEditDescription(e.target.value)}
                      placeholder="Description (optional)"
                      rows={2}
                      className="w-full text-sm border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                    />
                    
                    <textarea
                      value={editQuery}
                      onChange={(e) => setEditQuery(e.target.value)}
                      placeholder="Query (e.g. 'type:pdf AND created:>2023-01-01')"
                      rows={2}
                      className="w-full text-sm border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                    />
                    
                    <div className="flex justify-end space-x-2">
                      <button
                        onClick={cancelEditing}
                        className="px-2 py-1 text-xs text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
                      >
                        Cancel
                      </button>
                      <button
                        onClick={() => handleUpdateCollection(collection.id)}
                        disabled={!editName.trim() || !editQuery.trim()}
                        className={`px-2 py-1 text-xs text-white bg-blue-600 rounded-md hover:bg-blue-700 ${
                          !editName.trim() || !editQuery.trim() ? 'opacity-50 cursor-not-allowed' : ''
                        }`}
                      >
                        Update
                      </button>
                    </div>
                  </div>
                </div>
              ) : (
                // Collection Item
                <div
                  className={`group flex items-center justify-between p-2 rounded-md cursor-pointer ${
                    selectedCollectionId === collection.id
                      ? 'bg-blue-50 hover:bg-blue-100'
                      : 'hover:bg-gray-50'
                  }`}
                  onClick={() => onCollectionSelect(collection.id)}
                >
                  <div className="flex-1">
                    <div className="flex items-center">
                      <span className="text-lg mr-2">{collection.icon || '📄'}</span>
                      <div>
                        <div className="text-sm font-medium text-gray-700">{collection.name}</div>
                        {collection.description && (
                          <p className="text-xs text-gray-500">{collection.description}</p>
                        )}
                        <div className="flex items-center text-xs text-gray-500 mt-0.5">
                          <span>{collection.documentCount} document{collection.documentCount !== 1 ? 's' : ''}</span>
                          <span className="mx-1">•</span>
                          <span>Last updated: {formatDate(collection.lastUpdated)}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  {!readOnly && (
                    <div className="opacity-0 group-hover:opacity-100 flex space-x-1">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleRunCollection(collection.id);
                        }}
                        className="p-1 text-gray-400 hover:text-blue-600"
                        title="Run collection query"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          startEditing(collection);
                        }}
                        className="p-1 text-gray-400 hover:text-gray-600"
                        title="Edit collection"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                        </svg>
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDeleteCollection(collection.id);
                        }}
                        className="p-1 text-gray-400 hover:text-red-600"
                        title="Delete collection"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default SmartCollections; 