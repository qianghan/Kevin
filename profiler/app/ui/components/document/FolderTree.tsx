'use client';

import React, { useState } from 'react';
import { useDocumentService } from '../../lib/contexts/DocumentContext';

export interface Folder {
  id: string;
  name: string;
  parentId: string | null;
  children?: Folder[];
}

export interface DocumentFolder {
  id: string;
  folderId: string;
  documentId: string;
}

interface FolderTreeProps {
  folders: Folder[];
  documentFolders: DocumentFolder[];
  onAddFolder?: (name: string, parentId: string | null) => Promise<void>;
  onRenameFolder?: (id: string, name: string) => Promise<void>;
  onDeleteFolder?: (id: string) => Promise<void>;
  onMoveDocument?: (documentId: string, folderId: string) => Promise<void>;
  selectedFolderId?: string;
  onSelectFolder?: (folderId: string) => void;
}

const FolderTree: React.FC<FolderTreeProps> = ({
  folders,
  documentFolders,
  onAddFolder,
  onRenameFolder,
  onDeleteFolder,
  onMoveDocument,
  selectedFolderId,
  onSelectFolder
}) => {
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set(['root']));
  const [isAddingFolder, setIsAddingFolder] = useState<string | null>(null);
  const [newFolderName, setNewFolderName] = useState('');
  const [renamingFolder, setRenamingFolder] = useState<string | null>(null);
  const [renamedFolderName, setRenamedFolderName] = useState('');
  
  // Get root folders
  const rootFolders = folders.filter(folder => folder.parentId === null);
  
  // Build folder tree recursively
  const buildFolderTree = (parentId: string | null): Folder[] => {
    return folders
      .filter(folder => folder.parentId === parentId)
      .map(folder => ({
        ...folder,
        children: buildFolderTree(folder.id)
      }));
  };
  
  // Toggle folder expansion
  const toggleFolder = (folderId: string) => {
    setExpandedFolders(prev => {
      const newSet = new Set(prev);
      if (newSet.has(folderId)) {
        newSet.delete(folderId);
      } else {
        newSet.add(folderId);
      }
      return newSet;
    });
  };
  
  // Start adding a new folder
  const startAddFolder = (parentId: string | null) => {
    setIsAddingFolder(parentId === null ? 'root' : parentId);
    setNewFolderName('');
  };
  
  // Cancel adding a new folder
  const cancelAddFolder = () => {
    setIsAddingFolder(null);
    setNewFolderName('');
  };
  
  // Submit a new folder
  const submitAddFolder = async () => {
    if (newFolderName.trim() === '' || !onAddFolder) return;
    
    const parentId = isAddingFolder === 'root' ? null : isAddingFolder;
    await onAddFolder(newFolderName.trim(), parentId);
    
    setIsAddingFolder(null);
    setNewFolderName('');
  };
  
  // Start renaming a folder
  const startRenameFolder = (folder: Folder) => {
    setRenamingFolder(folder.id);
    setRenamedFolderName(folder.name);
  };
  
  // Cancel renaming a folder
  const cancelRenameFolder = () => {
    setRenamingFolder(null);
    setRenamedFolderName('');
  };
  
  // Submit folder rename
  const submitRenameFolder = async () => {
    if (renamedFolderName.trim() === '' || !renamingFolder || !onRenameFolder) return;
    
    await onRenameFolder(renamingFolder, renamedFolderName.trim());
    
    setRenamingFolder(null);
    setRenamedFolderName('');
  };
  
  // Handle folder selection
  const handleSelectFolder = (folderId: string) => {
    if (onSelectFolder) {
      onSelectFolder(folderId);
    }
  };
  
  // Delete a folder
  const handleDeleteFolder = async (folderId: string) => {
    if (!onDeleteFolder) return;
    
    if (window.confirm('Are you sure you want to delete this folder? Documents in this folder will be moved to the root.')) {
      await onDeleteFolder(folderId);
    }
  };
  
  // Count documents in a folder
  const countDocumentsInFolder = (folderId: string): number => {
    return documentFolders.filter(df => df.folderId === folderId).length;
  };
  
  // Render a folder and its children recursively
  const renderFolder = (folder: Folder, level: number = 0) => {
    const isExpanded = expandedFolders.has(folder.id);
    const isSelected = selectedFolderId === folder.id;
    const hasChildren = (folder.children && folder.children.length > 0);
    const documentCount = countDocumentsInFolder(folder.id);
    
    return (
      <div key={folder.id} className="select-none">
        <div 
          className={`flex items-center py-1 ${isSelected ? 'bg-blue-50' : 'hover:bg-gray-50'} rounded px-1 -mx-1`}
          style={{ paddingLeft: `${level * 12}px` }}
        >
          {/* Expand/collapse button */}
          <button 
            className="mr-1 w-4 h-4 flex items-center justify-center text-gray-400"
            onClick={() => toggleFolder(folder.id)}
          >
            {hasChildren && (
              <svg 
                className={`w-3 h-3 transform transition-transform ${isExpanded ? 'rotate-90' : ''}`} 
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24" 
                xmlns="http://www.w3.org/2000/svg"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            )}
          </button>
          
          {/* Folder icon */}
          <svg 
            className="w-4 h-4 mr-1 text-yellow-400" 
            fill="currentColor" 
            viewBox="0 0 20 20" 
            xmlns="http://www.w3.org/2000/svg"
          >
            <path fillRule="evenodd" d="M2 6a2 2 0 012-2h4l2 2h4a2 2 0 012 2v1H8a3 3 0 00-3 3v1.5a1.5 1.5 0 01-3 0V6z" clipRule="evenodd" />
            <path d="M6 12a2 2 0 012-2h8a2 2 0 012 2v2a2 2 0 01-2 2H2h2a2 2 0 002-2v-2z" />
          </svg>
          
          {/* Folder name or rename input */}
          {renamingFolder === folder.id ? (
            <div className="flex items-center flex-1">
              <input
                type="text"
                value={renamedFolderName}
                onChange={(e) => setRenamedFolderName(e.target.value)}
                className="block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-xs"
                autoFocus
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    submitRenameFolder();
                  } else if (e.key === 'Escape') {
                    cancelRenameFolder();
                  }
                }}
              />
              <button
                onClick={submitRenameFolder}
                className="ml-1 p-1 text-green-600 hover:text-green-800"
              >
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </button>
              <button
                onClick={cancelRenameFolder}
                className="ml-1 p-1 text-red-600 hover:text-red-800"
              >
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          ) : (
            <span 
              className="text-sm cursor-pointer flex-1"
              onClick={() => handleSelectFolder(folder.id)}
            >
              {folder.name}
              {documentCount > 0 && (
                <span className="ml-1 text-xs text-gray-500">({documentCount})</span>
              )}
            </span>
          )}
          
          {/* Folder actions */}
          {renamingFolder !== folder.id && (
            <div className="flex opacity-0 group-hover:opacity-100">
              <button
                onClick={() => startRenameFolder(folder)}
                className="p-1 text-gray-400 hover:text-gray-600"
                title="Rename folder"
              >
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                </svg>
              </button>
              <button
                onClick={() => handleDeleteFolder(folder.id)}
                className="p-1 text-gray-400 hover:text-red-600"
                title="Delete folder"
              >
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </button>
            </div>
          )}
        </div>
        
        {/* Child folders */}
        {isExpanded && folder.children && folder.children.length > 0 && (
          <div>
            {folder.children.map(childFolder => renderFolder(childFolder, level + 1))}
          </div>
        )}
        
        {/* Add folder input */}
        {isAddingFolder === folder.id && (
          <div 
            className="flex items-center py-1"
            style={{ paddingLeft: `${(level + 1) * 12}px` }}
          >
            <svg 
              className="w-4 h-4 mr-1 text-yellow-400" 
              fill="currentColor" 
              viewBox="0 0 20 20" 
              xmlns="http://www.w3.org/2000/svg"
            >
              <path fillRule="evenodd" d="M2 6a2 2 0 012-2h4l2 2h4a2 2 0 012 2v1H8a3 3 0 00-3 3v1.5a1.5 1.5 0 01-3 0V6z" clipRule="evenodd" />
              <path d="M6 12a2 2 0 012-2h8a2 2 0 012 2v2a2 2 0 01-2 2H2h2a2 2 0 002-2v-2z" />
            </svg>
            <input
              type="text"
              value={newFolderName}
              onChange={(e) => setNewFolderName(e.target.value)}
              placeholder="New folder"
              className="block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-xs"
              autoFocus
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  submitAddFolder();
                } else if (e.key === 'Escape') {
                  cancelAddFolder();
                }
              }}
            />
            <button
              onClick={submitAddFolder}
              className="ml-1 p-1 text-green-600 hover:text-green-800"
            >
              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </button>
            <button
              onClick={cancelAddFolder}
              className="ml-1 p-1 text-red-600 hover:text-red-800"
            >
              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        )}
      </div>
    );
  };
  
  return (
    <div className="bg-white rounded-lg border border-gray-200 overflow-hidden p-3">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-medium text-gray-700">Folders</h3>
        
        <button
          onClick={() => startAddFolder(null)}
          className="text-xs text-blue-600 hover:text-blue-800 flex items-center"
        >
          <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
          </svg>
          New Folder
        </button>
      </div>
      
      {/* Root folder */}
      <div 
        className={`flex items-center py-1 ${selectedFolderId === 'root' ? 'bg-blue-50' : 'hover:bg-gray-50'} rounded px-1 -mx-1 mb-1`}
        onClick={() => handleSelectFolder('root')}
      >
        <svg 
          className="w-4 h-4 mr-1 text-blue-500" 
          fill="currentColor" 
          viewBox="0 0 20 20" 
          xmlns="http://www.w3.org/2000/svg"
        >
          <path d="M10.707 2.293a1 1 0 00-1.414 0l-7 7a1 1 0 001.414 1.414L4 10.414V17a1 1 0 001 1h2a1 1 0 001-1v-2a1 1 0 011-1h2a1 1 0 011 1v2a1 1 0 001 1h2a1 1 0 001-1v-6.586l.293.293a1 1 0 001.414-1.414l-7-7z" />
        </svg>
        <span className="text-sm cursor-pointer">
          All Documents
          <span className="ml-1 text-xs text-gray-500">({documentFolders.length})</span>
        </span>
      </div>
      
      {/* Top-level folders */}
      {rootFolders.map(folder => renderFolder(folder))}
      
      {/* Add folder at root level */}
      {isAddingFolder === 'root' && (
        <div className="flex items-center py-1 mt-1">
          <svg 
            className="w-4 h-4 mr-1 text-yellow-400" 
            fill="currentColor" 
            viewBox="0 0 20 20" 
            xmlns="http://www.w3.org/2000/svg"
          >
            <path fillRule="evenodd" d="M2 6a2 2 0 012-2h4l2 2h4a2 2 0 012 2v1H8a3 3 0 00-3 3v1.5a1.5 1.5 0 01-3 0V6z" clipRule="evenodd" />
            <path d="M6 12a2 2 0 012-2h8a2 2 0 012 2v2a2 2 0 01-2 2H2h2a2 2 0 002-2v-2z" />
          </svg>
          <input
            type="text"
            value={newFolderName}
            onChange={(e) => setNewFolderName(e.target.value)}
            placeholder="New folder"
            className="block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-xs"
            autoFocus
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                submitAddFolder();
              } else if (e.key === 'Escape') {
                cancelAddFolder();
              }
            }}
          />
          <button
            onClick={submitAddFolder}
            className="ml-1 p-1 text-green-600 hover:text-green-800"
          >
            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </button>
          <button
            onClick={cancelAddFolder}
            className="ml-1 p-1 text-red-600 hover:text-red-800"
          >
            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      )}
    </div>
  );
};

export default FolderTree; 