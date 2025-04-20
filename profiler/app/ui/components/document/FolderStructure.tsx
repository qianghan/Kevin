'use client';

import React, { useState, useEffect } from 'react';
import { useDocumentService } from '../../lib/contexts/DocumentContext';

export interface Folder {
  id: string;
  name: string;
  parentId: string | null;
  path?: string;
  children?: Folder[];
  documentCount?: number;
}

interface FolderStructureProps {
  selectedFolderId?: string;
  folders: Folder[];
  onFolderSelect?: (folderId: string) => void;
  onCreateFolder?: (name: string, parentId: string | null) => Promise<string>;
  onRenameFolder?: (id: string, name: string) => Promise<void>;
  onDeleteFolder?: (id: string) => Promise<void>;
  onMoveFolder?: (id: string, newParentId: string | null) => Promise<void>;
  readOnly?: boolean;
}

const FolderStructure: React.FC<FolderStructureProps> = ({
  selectedFolderId,
  folders,
  onFolderSelect,
  onCreateFolder,
  onRenameFolder,
  onDeleteFolder,
  onMoveFolder,
  readOnly = false
}) => {
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set());
  const [isCreatingFolder, setIsCreatingFolder] = useState<string | null>(null); // null or parentId
  const [newFolderName, setNewFolderName] = useState('');
  const [folderBeingRenamed, setFolderBeingRenamed] = useState<string | null>(null);
  const [renameFolderValue, setRenameFolderValue] = useState('');
  const [draggedFolderId, setDraggedFolderId] = useState<string | null>(null);
  const [dropTargetId, setDropTargetId] = useState<string | null>(null);
  
  const { documentService } = useDocumentService();
  
  // Build folder hierarchy
  const buildFolderTree = (items: Folder[]): Folder[] => {
    const map = new Map<string, Folder>();
    const roots: Folder[] = [];
    
    // Create a map of all folders by ID
    items.forEach(item => {
      map.set(item.id, { ...item, children: [] });
    });
    
    // Add children to their parents
    items.forEach(item => {
      if (item.parentId === null) {
        // Root folder
        roots.push(map.get(item.id)!);
      } else if (map.has(item.parentId)) {
        // Add to parent's children
        map.get(item.parentId)!.children!.push(map.get(item.id)!);
      } else {
        // Orphaned folder (parent doesn't exist) - add to root
        roots.push(map.get(item.id)!);
      }
    });
    
    return roots;
  };
  
  const folderTree = buildFolderTree(folders);
  
  // Toggle folder expanded state
  const toggleExpanded = (folderId: string, event: React.MouseEvent) => {
    event.stopPropagation();
    
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
  
  // Select a folder
  const handleSelectFolder = (folderId: string) => {
    if (onFolderSelect) {
      onFolderSelect(folderId);
    }
  };
  
  // Start folder creation
  const startFolderCreation = (parentId: string | null, event: React.MouseEvent) => {
    event.stopPropagation();
    setIsCreatingFolder(parentId);
    setNewFolderName('');
    
    // Ensure parent folder is expanded
    if (parentId) {
      setExpandedFolders(prev => {
        const newSet = new Set(prev);
        newSet.add(parentId);
        return newSet;
      });
    }
  };
  
  // Create a new folder
  const handleCreateFolder = async (parentId: string | null) => {
    if (!onCreateFolder || !newFolderName.trim()) return;
    
    try {
      const newFolderId = await onCreateFolder(newFolderName.trim(), parentId);
      setIsCreatingFolder(null);
      setNewFolderName('');
      
      // Select the new folder
      if (onFolderSelect) {
        onFolderSelect(newFolderId);
      }
    } catch (error) {
      console.error('Error creating folder:', error);
    }
  };
  
  // Start folder rename
  const startFolderRename = (folder: Folder, event: React.MouseEvent) => {
    event.stopPropagation();
    setFolderBeingRenamed(folder.id);
    setRenameFolderValue(folder.name);
  };
  
  // Rename a folder
  const handleRenameFolder = async (folderId: string) => {
    if (!onRenameFolder || !renameFolderValue.trim()) return;
    
    try {
      await onRenameFolder(folderId, renameFolderValue.trim());
      setFolderBeingRenamed(null);
      setRenameFolderValue('');
    } catch (error) {
      console.error('Error renaming folder:', error);
    }
  };
  
  // Delete a folder
  const handleDeleteFolder = async (folderId: string, event: React.MouseEvent) => {
    event.stopPropagation();
    
    if (!onDeleteFolder) return;
    
    // Check if folder has documents
    const folder = folders.find(f => f.id === folderId);
    if (folder && folder.documentCount && folder.documentCount > 0) {
      if (!window.confirm(`This folder contains ${folder.documentCount} document(s). Are you sure you want to delete it?`)) {
        return;
      }
    } else if (!window.confirm('Are you sure you want to delete this folder?')) {
      return;
    }
    
    try {
      await onDeleteFolder(folderId);
      
      // If the deleted folder was selected, select its parent or root
      if (selectedFolderId === folderId && onFolderSelect) {
        const folder = folders.find(f => f.id === folderId);
        if (folder && folder.parentId) {
          onFolderSelect(folder.parentId);
        } else {
          // Select first root folder or null
          const firstRoot = folders.find(f => f.parentId === null);
          onFolderSelect(firstRoot ? firstRoot.id : '');
        }
      }
    } catch (error) {
      console.error('Error deleting folder:', error);
    }
  };
  
  // Drag and drop handlers
  const handleDragStart = (folderId: string, event: React.DragEvent) => {
    setDraggedFolderId(folderId);
    event.dataTransfer.setData('text/plain', folderId);
    event.dataTransfer.effectAllowed = 'move';
  };
  
  const handleDragOver = (folderId: string | null, event: React.DragEvent) => {
    event.preventDefault();
    
    // Don't allow dropping on itself or its children
    if (folderId === draggedFolderId) {
      return;
    }
    
    // Check if target is a child of dragged folder
    const isChildOfDragged = (targetId: string, draggedId: string): boolean => {
      const folder = folders.find(f => f.id === targetId);
      if (!folder) return false;
      if (folder.parentId === draggedId) return true;
      if (folder.parentId) return isChildOfDragged(folder.parentId, draggedId);
      return false;
    };
    
    if (folderId && draggedFolderId && isChildOfDragged(folderId, draggedFolderId)) {
      return;
    }
    
    setDropTargetId(folderId);
    event.dataTransfer.dropEffect = 'move';
  };
  
  const handleDragLeave = () => {
    setDropTargetId(null);
  };
  
  const handleDrop = async (targetFolderId: string | null, event: React.DragEvent) => {
    event.preventDefault();
    const folderId = event.dataTransfer.getData('text/plain');
    
    // Don't allow dropping on itself or its children
    if (targetFolderId === folderId) {
      setDraggedFolderId(null);
      setDropTargetId(null);
      return;
    }
    
    // Check if target is a child of dragged folder
    const isChildOfDragged = (targetId: string, draggedId: string): boolean => {
      const folder = folders.find(f => f.id === targetId);
      if (!folder) return false;
      if (folder.parentId === draggedId) return true;
      if (folder.parentId) return isChildOfDragged(folder.parentId, draggedId);
      return false;
    };
    
    if (targetFolderId && isChildOfDragged(targetFolderId, folderId)) {
      setDraggedFolderId(null);
      setDropTargetId(null);
      return;
    }
    
    // Move the folder
    if (onMoveFolder) {
      try {
        await onMoveFolder(folderId, targetFolderId);
        
        // Expand target folder
        if (targetFolderId) {
          setExpandedFolders(prev => {
            const newSet = new Set(prev);
            newSet.add(targetFolderId);
            return newSet;
          });
        }
      } catch (error) {
        console.error('Error moving folder:', error);
      }
    }
    
    setDraggedFolderId(null);
    setDropTargetId(null);
  };
  
  // Cancel operations
  const cancelFolderCreation = (event: React.MouseEvent) => {
    event.stopPropagation();
    setIsCreatingFolder(null);
    setNewFolderName('');
  };
  
  const cancelFolderRename = (event: React.MouseEvent) => {
    event.stopPropagation();
    setFolderBeingRenamed(null);
    setRenameFolderValue('');
  };
  
  // Prevent default behavior when pressing Enter in input fields
  const handleKeyDown = (e: React.KeyboardEvent, action: () => void) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      action();
    }
  };
  
  // Render a folder and its children recursively
  const renderFolder = (folder: Folder, depth = 0) => {
    const isExpanded = expandedFolders.has(folder.id);
    const isSelected = selectedFolderId === folder.id;
    const hasChildren = folder.children && folder.children.length > 0;
    const isRenaming = folderBeingRenamed === folder.id;
    const isDropTarget = dropTargetId === folder.id;
    
    return (
      <div key={folder.id} className="select-none">
        <div
          className={`flex items-center py-1 px-2 cursor-pointer hover:bg-gray-100 ${
            isSelected ? 'bg-blue-100 hover:bg-blue-100' : ''
          } ${isDropTarget ? 'bg-blue-50 border border-blue-300' : ''}`}
          onClick={() => handleSelectFolder(folder.id)}
          style={{ paddingLeft: `${depth * 16 + 8}px` }}
          draggable={!readOnly}
          onDragStart={e => !readOnly && handleDragStart(folder.id, e)}
          onDragOver={e => !readOnly && handleDragOver(folder.id, e)}
          onDragLeave={() => !readOnly && handleDragLeave()}
          onDrop={e => !readOnly && handleDrop(folder.id, e)}
        >
          {/* Expand/collapse button */}
          <button
            className="w-5 h-5 flex items-center justify-center mr-1 text-gray-500"
            onClick={e => hasChildren && toggleExpanded(folder.id, e)}
          >
            {hasChildren ? (
              <svg
                className={`w-3 h-3 transform ${isExpanded ? 'rotate-90' : ''}`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            ) : (
              <span className="w-3" />
            )}
          </button>
          
          {/* Folder icon */}
          <svg 
            className="w-4 h-4 mr-1.5 text-yellow-500" 
            fill="currentColor" 
            viewBox="0 0 20 20"
          >
            <path
              fillRule="evenodd"
              d="M2 6a2 2 0 012-2h4l2 2h4a2 2 0 012 2v6a2 2 0 01-2 2H4a2 2 0 01-2-2V6z"
              clipRule="evenodd"
            />
          </svg>
          
          {/* Folder name */}
          {isRenaming ? (
            <div className="flex-1">
              <input
                type="text"
                value={renameFolderValue}
                onChange={e => setRenameFolderValue(e.target.value)}
                onKeyDown={e => handleKeyDown(e, () => handleRenameFolder(folder.id))}
                className="w-full text-sm border-gray-300 rounded-sm py-0 focus:ring-blue-500 focus:border-blue-500"
                autoFocus
                onClick={e => e.stopPropagation()}
              />
              <div className="flex mt-1 space-x-1">
                <button
                  onClick={e => {
                    e.stopPropagation();
                    handleRenameFolder(folder.id);
                  }}
                  className="px-1.5 py-0.5 text-xs text-white bg-blue-600 rounded-sm hover:bg-blue-700"
                >
                  Save
                </button>
                <button
                  onClick={cancelFolderRename}
                  className="px-1.5 py-0.5 text-xs text-gray-700 bg-white border border-gray-300 rounded-sm hover:bg-gray-50"
                >
                  Cancel
                </button>
              </div>
            </div>
          ) : (
            <span className="text-sm flex-1">
              {folder.name}
              {folder.documentCount !== undefined && folder.documentCount > 0 && (
                <span className="ml-1 text-xs text-gray-500">({folder.documentCount})</span>
              )}
            </span>
          )}
          
          {/* Folder actions */}
          {!readOnly && !isRenaming && (
            <div className="opacity-0 group-hover:opacity-100 flex space-x-1">
              <button
                onClick={e => startFolderRename(folder, e)}
                className="p-1 text-gray-400 hover:text-gray-600"
                title="Rename folder"
              >
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                </svg>
              </button>
              <button
                onClick={e => handleDeleteFolder(folder.id, e)}
                className="p-1 text-gray-400 hover:text-red-600"
                title="Delete folder"
              >
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </button>
              <button
                onClick={e => startFolderCreation(folder.id, e)}
                className="p-1 text-gray-400 hover:text-blue-600"
                title="Create subfolder"
              >
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                </svg>
              </button>
            </div>
          )}
        </div>
        
        {/* New subfolder creation form */}
        {isCreatingFolder === folder.id && (
          <div
            className="flex flex-col py-1 px-2"
            style={{ paddingLeft: `${depth * 16 + 29}px` }}
            onClick={e => e.stopPropagation()}
          >
            <input
              type="text"
              value={newFolderName}
              onChange={e => setNewFolderName(e.target.value)}
              onKeyDown={e => handleKeyDown(e, () => handleCreateFolder(folder.id))}
              placeholder="New folder name"
              className="w-full text-sm border-gray-300 rounded-sm py-0 focus:ring-blue-500 focus:border-blue-500"
              autoFocus
            />
            <div className="flex mt-1 space-x-1">
              <button
                onClick={() => handleCreateFolder(folder.id)}
                className="px-1.5 py-0.5 text-xs text-white bg-blue-600 rounded-sm hover:bg-blue-700"
              >
                Create
              </button>
              <button
                onClick={cancelFolderCreation}
                className="px-1.5 py-0.5 text-xs text-gray-700 bg-white border border-gray-300 rounded-sm hover:bg-gray-50"
              >
                Cancel
              </button>
            </div>
          </div>
        )}
        
        {/* Children */}
        {isExpanded && hasChildren && (
          <div>
            {folder.children!.map(child => renderFolder(child, depth + 1))}
          </div>
        )}
      </div>
    );
  };
  
  return (
    <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
      <div className="flex items-center justify-between px-3 py-2 border-b border-gray-200">
        <h3 className="text-sm font-medium text-gray-700">Folders</h3>
        
        {!readOnly && (
          <button
            onClick={e => startFolderCreation(null, e)}
            className="text-xs text-blue-600 hover:text-blue-800 flex items-center"
          >
            <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
            New Folder
          </button>
        )}
      </div>
      
      <div
        className="p-1 max-h-60 overflow-y-auto"
        onDragOver={e => !readOnly && handleDragOver(null, e)}
        onDrop={e => !readOnly && handleDrop(null, e)}
      >
        {folderTree.length === 0 && (
          <div className="text-center py-4">
            <p className="text-sm text-gray-500">No folders yet</p>
            {!readOnly && (
              <button
                onClick={e => startFolderCreation(null, e)}
                className="mt-1 text-xs text-blue-600 hover:text-blue-800"
              >
                Create your first folder
              </button>
            )}
          </div>
        )}
        
        {folderTree.map(folder => renderFolder(folder))}
        
        {/* Root level new folder creation form */}
        {isCreatingFolder === null && (
          <div
            className="flex flex-col py-1 px-2 ml-8"
            onClick={e => e.stopPropagation()}
          >
            <input
              type="text"
              value={newFolderName}
              onChange={e => setNewFolderName(e.target.value)}
              onKeyDown={e => handleKeyDown(e, () => handleCreateFolder(null))}
              placeholder="New folder name"
              className="w-full text-sm border-gray-300 rounded-sm py-0 focus:ring-blue-500 focus:border-blue-500"
              autoFocus
            />
            <div className="flex mt-1 space-x-1">
              <button
                onClick={() => handleCreateFolder(null)}
                className="px-1.5 py-0.5 text-xs text-white bg-blue-600 rounded-sm hover:bg-blue-700"
              >
                Create
              </button>
              <button
                onClick={cancelFolderCreation}
                className="px-1.5 py-0.5 text-xs text-gray-700 bg-white border border-gray-300 rounded-sm hover:bg-gray-50"
              >
                Cancel
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default FolderStructure; 