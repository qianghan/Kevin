'use client';

import React, { useState, useEffect, useRef } from 'react';
import { useDocumentService } from '../../lib/contexts/DocumentContext';

export interface Tag {
  id: string;
  name: string;
  color?: string;
  count?: number;
}

export interface Category {
  id: string;
  name: string;
  color?: string;
  count?: number;
}

interface DocumentCategorizationProps {
  documentIds: string[];
  selectedCategories?: string[];
  selectedTags?: string[];
  availableCategories: Category[];
  availableTags: Tag[];
  onCategorySelect?: (categoryIds: string[]) => void;
  onTagSelect?: (tagIds: string[]) => void;
  onCategoryCreate?: (name: string, color: string) => Promise<string>;
  onTagCreate?: (name: string, color: string) => Promise<string>;
  onCategoryEdit?: (id: string, name: string, color: string) => Promise<void>;
  onTagEdit?: (id: string, name: string, color: string) => Promise<void>;
  onCategoryDelete?: (id: string) => Promise<void>;
  onTagDelete?: (id: string) => Promise<void>;
  readOnly?: boolean;
}

const DocumentCategorization: React.FC<DocumentCategorizationProps> = ({
  documentIds,
  selectedCategories = [],
  selectedTags = [],
  availableCategories,
  availableTags,
  onCategorySelect,
  onTagSelect,
  onCategoryCreate,
  onTagCreate,
  onCategoryEdit,
  onTagEdit,
  onCategoryDelete,
  onTagDelete,
  readOnly = false
}) => {
  // Local state for selections
  const [localSelectedCategories, setLocalSelectedCategories] = useState<string[]>(selectedCategories);
  const [localSelectedTags, setLocalSelectedTags] = useState<string[]>(selectedTags);
  
  // State for adding new items
  const [isAddingCategory, setIsAddingCategory] = useState(false);
  const [isAddingTag, setIsAddingTag] = useState(false);
  const [newCategoryName, setNewCategoryName] = useState('');
  const [newCategoryColor, setNewCategoryColor] = useState('#3B82F6'); // Default blue
  const [newTagName, setNewTagName] = useState('');
  const [newTagColor, setNewTagColor] = useState('#10B981'); // Default green
  
  // State for editing existing items
  const [editingCategoryId, setEditingCategoryId] = useState<string | null>(null);
  const [editingTagId, setEditingTagId] = useState<string | null>(null);
  const [editCategoryName, setEditCategoryName] = useState('');
  const [editCategoryColor, setEditCategoryColor] = useState('');
  const [editTagName, setEditTagName] = useState('');
  const [editTagColor, setEditTagColor] = useState('');
  
  const { documentService } = useDocumentService();
  
  // Refs for click outside handling
  const categoryFormRef = useRef<HTMLDivElement>(null);
  const tagFormRef = useRef<HTMLDivElement>(null);
  
  // Update local state when props change
  useEffect(() => {
    setLocalSelectedCategories(selectedCategories);
  }, [selectedCategories]);
  
  useEffect(() => {
    setLocalSelectedTags(selectedTags);
  }, [selectedTags]);
  
  // Handle clicks outside the forms
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (categoryFormRef.current && !categoryFormRef.current.contains(event.target as Node)) {
        setIsAddingCategory(false);
        setEditingCategoryId(null);
      }
      if (tagFormRef.current && !tagFormRef.current.contains(event.target as Node)) {
        setIsAddingTag(false);
        setEditingTagId(null);
      }
    };
    
    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);
  
  // Toggle category selection
  const toggleCategory = (categoryId: string) => {
    setLocalSelectedCategories(prev => {
      const newSelection = prev.includes(categoryId)
        ? prev.filter(id => id !== categoryId)
        : [...prev, categoryId];
      
      if (onCategorySelect) {
        onCategorySelect(newSelection);
      }
      
      return newSelection;
    });
  };
  
  // Toggle tag selection
  const toggleTag = (tagId: string) => {
    setLocalSelectedTags(prev => {
      const newSelection = prev.includes(tagId)
        ? prev.filter(id => id !== tagId)
        : [...prev, tagId];
      
      if (onTagSelect) {
        onTagSelect(newSelection);
      }
      
      return newSelection;
    });
  };
  
  // Create a new category
  const handleCreateCategory = async () => {
    if (!onCategoryCreate || !newCategoryName.trim()) return;
    
    try {
      const newCategoryId = await onCategoryCreate(newCategoryName.trim(), newCategoryColor);
      setNewCategoryName('');
      setIsAddingCategory(false);
      
      // Automatically select the new category
      setLocalSelectedCategories(prev => {
        const newSelection = [...prev, newCategoryId];
        if (onCategorySelect) {
          onCategorySelect(newSelection);
        }
        return newSelection;
      });
    } catch (error) {
      console.error('Error creating category:', error);
    }
  };
  
  // Create a new tag
  const handleCreateTag = async () => {
    if (!onTagCreate || !newTagName.trim()) return;
    
    try {
      const newTagId = await onTagCreate(newTagName.trim(), newTagColor);
      setNewTagName('');
      setIsAddingTag(false);
      
      // Automatically select the new tag
      setLocalSelectedTags(prev => {
        const newSelection = [...prev, newTagId];
        if (onTagSelect) {
          onTagSelect(newSelection);
        }
        return newSelection;
      });
    } catch (error) {
      console.error('Error creating tag:', error);
    }
  };
  
  // Start editing a category
  const startEditCategory = (category: Category, event: React.MouseEvent) => {
    event.stopPropagation();
    setEditingCategoryId(category.id);
    setEditCategoryName(category.name);
    setEditCategoryColor(category.color || '#3B82F6');
  };
  
  // Start editing a tag
  const startEditTag = (tag: Tag, event: React.MouseEvent) => {
    event.stopPropagation();
    setEditingTagId(tag.id);
    setEditTagName(tag.name);
    setEditTagColor(tag.color || '#10B981');
  };
  
  // Save category edits
  const handleEditCategory = async (categoryId: string) => {
    if (!onCategoryEdit || !editCategoryName.trim()) return;
    
    try {
      await onCategoryEdit(categoryId, editCategoryName.trim(), editCategoryColor);
      setEditingCategoryId(null);
    } catch (error) {
      console.error('Error editing category:', error);
    }
  };
  
  // Save tag edits
  const handleEditTag = async (tagId: string) => {
    if (!onTagEdit || !editTagName.trim()) return;
    
    try {
      await onTagEdit(tagId, editTagName.trim(), editTagColor);
      setEditingTagId(null);
    } catch (error) {
      console.error('Error editing tag:', error);
    }
  };
  
  // Delete a category
  const handleDeleteCategory = async (categoryId: string, event: React.MouseEvent) => {
    event.stopPropagation();
    
    if (!onCategoryDelete) return;
    
    // Confirm deletion
    const category = availableCategories.find(c => c.id === categoryId);
    const hasDocuments = category?.count && category.count > 0;
    
    if (hasDocuments) {
      if (!window.confirm(`This category is used by ${category!.count} document(s). Are you sure you want to delete it?`)) {
        return;
      }
    } else if (!window.confirm('Are you sure you want to delete this category?')) {
      return;
    }
    
    try {
      await onCategoryDelete(categoryId);
      
      // Remove from selection if it was selected
      if (localSelectedCategories.includes(categoryId)) {
        setLocalSelectedCategories(prev => {
          const newSelection = prev.filter(id => id !== categoryId);
          if (onCategorySelect) {
            onCategorySelect(newSelection);
          }
          return newSelection;
        });
      }
    } catch (error) {
      console.error('Error deleting category:', error);
    }
  };
  
  // Delete a tag
  const handleDeleteTag = async (tagId: string, event: React.MouseEvent) => {
    event.stopPropagation();
    
    if (!onTagDelete) return;
    
    // Confirm deletion
    const tag = availableTags.find(t => t.id === tagId);
    const hasDocuments = tag?.count && tag.count > 0;
    
    if (hasDocuments) {
      if (!window.confirm(`This tag is used by ${tag!.count} document(s). Are you sure you want to delete it?`)) {
        return;
      }
    } else if (!window.confirm('Are you sure you want to delete this tag?')) {
      return;
    }
    
    try {
      await onTagDelete(tagId);
      
      // Remove from selection if it was selected
      if (localSelectedTags.includes(tagId)) {
        setLocalSelectedTags(prev => {
          const newSelection = prev.filter(id => id !== tagId);
          if (onTagSelect) {
            onTagSelect(newSelection);
          }
          return newSelection;
        });
      }
    } catch (error) {
      console.error('Error deleting tag:', error);
    }
  };
  
  // Cancel editing or adding operations
  const cancelCategoryEdit = (event: React.MouseEvent) => {
    event.stopPropagation();
    setEditingCategoryId(null);
  };
  
  const cancelTagEdit = (event: React.MouseEvent) => {
    event.stopPropagation();
    setEditingTagId(null);
  };
  
  const cancelAddCategory = (event: React.MouseEvent) => {
    event.stopPropagation();
    setIsAddingCategory(false);
    setNewCategoryName('');
  };
  
  const cancelAddTag = (event: React.MouseEvent) => {
    event.stopPropagation();
    setIsAddingTag(false);
    setNewTagName('');
  };
  
  // Handle key presses (for Enter to submit)
  const handleKeyDown = (e: React.KeyboardEvent, action: () => void) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      action();
    }
  };
  
  return (
    <div className="bg-white rounded-lg border border-gray-200">
      {/* Categories Section */}
      <div className="p-3 border-b border-gray-200">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-sm font-medium text-gray-700">Categories</h3>
          
          {!readOnly && !isAddingCategory && (
            <button
              onClick={() => setIsAddingCategory(true)}
              className="text-xs text-blue-600 hover:text-blue-800 flex items-center"
            >
              <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              </svg>
              Add Category
            </button>
          )}
        </div>
        
        {/* Category list */}
        <div className="space-y-1 max-h-36 overflow-y-auto">
          {availableCategories.length === 0 && !isAddingCategory && (
            <div className="text-center py-2">
              <p className="text-sm text-gray-500">No categories</p>
              {!readOnly && (
                <button
                  onClick={() => setIsAddingCategory(true)}
                  className="mt-1 text-xs text-blue-600 hover:text-blue-800"
                >
                  Create your first category
                </button>
              )}
            </div>
          )}
          
          {availableCategories.map(category => (
            <div
              key={category.id}
              className={`group flex items-center justify-between py-1 px-2 rounded-md cursor-pointer ${
                editingCategoryId === category.id
                  ? 'bg-gray-100'
                  : localSelectedCategories.includes(category.id)
                  ? 'bg-blue-50 hover:bg-blue-100'
                  : 'hover:bg-gray-50'
              }`}
              onClick={() => !readOnly && toggleCategory(category.id)}
            >
              {editingCategoryId === category.id ? (
                <div className="flex-1" ref={categoryFormRef} onClick={e => e.stopPropagation()}>
                  <div className="flex items-center">
                    <input
                      type="color"
                      value={editCategoryColor}
                      onChange={e => setEditCategoryColor(e.target.value)}
                      className="w-5 h-5 mr-2 border-0 p-0 rounded-full"
                    />
                    <input
                      type="text"
                      value={editCategoryName}
                      onChange={e => setEditCategoryName(e.target.value)}
                      onKeyDown={e => handleKeyDown(e, () => handleEditCategory(category.id))}
                      className="w-full text-sm border-gray-300 rounded-sm py-0.5 focus:ring-blue-500 focus:border-blue-500"
                      autoFocus
                    />
                  </div>
                  <div className="flex mt-1 space-x-1">
                    <button
                      onClick={() => handleEditCategory(category.id)}
                      className="px-1.5 py-0.5 text-xs text-white bg-blue-600 rounded-sm hover:bg-blue-700"
                    >
                      Save
                    </button>
                    <button
                      onClick={cancelCategoryEdit}
                      className="px-1.5 py-0.5 text-xs text-gray-700 bg-white border border-gray-300 rounded-sm hover:bg-gray-50"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              ) : (
                <>
                  <div className="flex items-center">
                    <span
                      className="w-3 h-3 rounded-full mr-2"
                      style={{ backgroundColor: category.color || '#3B82F6' }}
                    />
                    <span className="text-sm text-gray-700">{category.name}</span>
                    {category.count !== undefined && category.count > 0 && (
                      <span className="ml-1 text-xs text-gray-500">({category.count})</span>
                    )}
                  </div>
                  
                  {!readOnly && (
                    <div className="opacity-0 group-hover:opacity-100 flex space-x-1">
                      <button
                        onClick={e => startEditCategory(category, e)}
                        className="p-1 text-gray-400 hover:text-gray-600"
                        title="Edit category"
                      >
                        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                        </svg>
                      </button>
                      <button
                        onClick={e => handleDeleteCategory(category.id, e)}
                        className="p-1 text-gray-400 hover:text-red-600"
                        title="Delete category"
                      >
                        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                      </button>
                    </div>
                  )}
                </>
              )}
            </div>
          ))}
          
          {/* Add category form */}
          {isAddingCategory && (
            <div
              className="p-2 bg-gray-50 rounded-md"
              ref={categoryFormRef}
              onClick={e => e.stopPropagation()}
            >
              <div className="flex items-center">
                <input
                  type="color"
                  value={newCategoryColor}
                  onChange={e => setNewCategoryColor(e.target.value)}
                  className="w-5 h-5 mr-2 border-0 p-0 rounded-full"
                />
                <input
                  type="text"
                  value={newCategoryName}
                  onChange={e => setNewCategoryName(e.target.value)}
                  onKeyDown={e => handleKeyDown(e, handleCreateCategory)}
                  placeholder="New category name"
                  className="w-full text-sm border-gray-300 rounded-sm py-0.5 focus:ring-blue-500 focus:border-blue-500"
                  autoFocus
                />
              </div>
              <div className="flex mt-1 space-x-1">
                <button
                  onClick={handleCreateCategory}
                  className="px-1.5 py-0.5 text-xs text-white bg-blue-600 rounded-sm hover:bg-blue-700"
                >
                  Add
                </button>
                <button
                  onClick={cancelAddCategory}
                  className="px-1.5 py-0.5 text-xs text-gray-700 bg-white border border-gray-300 rounded-sm hover:bg-gray-50"
                >
                  Cancel
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
      
      {/* Tags Section */}
      <div className="p-3">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-sm font-medium text-gray-700">Tags</h3>
          
          {!readOnly && !isAddingTag && (
            <button
              onClick={() => setIsAddingTag(true)}
              className="text-xs text-blue-600 hover:text-blue-800 flex items-center"
            >
              <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              </svg>
              Add Tag
            </button>
          )}
        </div>
        
        {/* Tag list */}
        <div className="flex flex-wrap gap-1 max-h-36 overflow-y-auto">
          {availableTags.length === 0 && !isAddingTag && (
            <div className="text-center py-2 w-full">
              <p className="text-sm text-gray-500">No tags</p>
              {!readOnly && (
                <button
                  onClick={() => setIsAddingTag(true)}
                  className="mt-1 text-xs text-blue-600 hover:text-blue-800"
                >
                  Create your first tag
                </button>
              )}
            </div>
          )}
          
          {availableTags.map(tag => (
            <div
              key={tag.id}
              className={`group relative ${
                editingTagId === tag.id ? 'mb-10' : ''
              }`}
            >
              <div
                className={`flex items-center py-1 px-2 rounded-md ${
                  !readOnly ? 'cursor-pointer' : ''
                } ${
                  editingTagId === tag.id
                    ? 'bg-gray-100'
                    : localSelectedTags.includes(tag.id)
                    ? 'bg-blue-50 hover:bg-blue-100'
                    : 'bg-gray-100 hover:bg-gray-200'
                }`}
                onClick={() => !readOnly && toggleTag(tag.id)}
                style={{ borderLeft: `3px solid ${tag.color || '#10B981'}` }}
              >
                <span className="text-sm text-gray-700">{tag.name}</span>
                {tag.count !== undefined && tag.count > 0 && (
                  <span className="ml-1 text-xs text-gray-500">({tag.count})</span>
                )}
                
                {!readOnly && !editingTagId && (
                  <div className="ml-1 opacity-0 group-hover:opacity-100 flex space-x-1">
                    <button
                      onClick={e => startEditTag(tag, e)}
                      className="p-0.5 text-gray-400 hover:text-gray-600"
                      title="Edit tag"
                    >
                      <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                      </svg>
                    </button>
                    <button
                      onClick={e => handleDeleteTag(tag.id, e)}
                      className="p-0.5 text-gray-400 hover:text-red-600"
                      title="Delete tag"
                    >
                      <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </button>
                  </div>
                )}
              </div>
              
              {/* Tag edit form */}
              {editingTagId === tag.id && (
                <div
                  className="absolute top-full left-0 w-48 mt-1 p-2 bg-white rounded-md shadow-md z-10"
                  ref={tagFormRef}
                  onClick={e => e.stopPropagation()}
                >
                  <div className="flex items-center">
                    <input
                      type="color"
                      value={editTagColor}
                      onChange={e => setEditTagColor(e.target.value)}
                      className="w-5 h-5 mr-2 border-0 p-0 rounded-full"
                    />
                    <input
                      type="text"
                      value={editTagName}
                      onChange={e => setEditTagName(e.target.value)}
                      onKeyDown={e => handleKeyDown(e, () => handleEditTag(tag.id))}
                      className="w-full text-sm border-gray-300 rounded-sm py-0.5 focus:ring-blue-500 focus:border-blue-500"
                      autoFocus
                    />
                  </div>
                  <div className="flex mt-1 space-x-1">
                    <button
                      onClick={() => handleEditTag(tag.id)}
                      className="px-1.5 py-0.5 text-xs text-white bg-blue-600 rounded-sm hover:bg-blue-700"
                    >
                      Save
                    </button>
                    <button
                      onClick={cancelTagEdit}
                      className="px-1.5 py-0.5 text-xs text-gray-700 bg-white border border-gray-300 rounded-sm hover:bg-gray-50"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              )}
            </div>
          ))}
          
          {/* Add tag form */}
          {isAddingTag && (
            <div
              className="p-2 bg-white border border-gray-200 rounded-md shadow-sm w-48"
              ref={tagFormRef}
              onClick={e => e.stopPropagation()}
            >
              <div className="flex items-center">
                <input
                  type="color"
                  value={newTagColor}
                  onChange={e => setNewTagColor(e.target.value)}
                  className="w-5 h-5 mr-2 border-0 p-0 rounded-full"
                />
                <input
                  type="text"
                  value={newTagName}
                  onChange={e => setNewTagName(e.target.value)}
                  onKeyDown={e => handleKeyDown(e, handleCreateTag)}
                  placeholder="New tag name"
                  className="w-full text-sm border-gray-300 rounded-sm py-0.5 focus:ring-blue-500 focus:border-blue-500"
                  autoFocus
                />
              </div>
              <div className="flex mt-1 space-x-1">
                <button
                  onClick={handleCreateTag}
                  className="px-1.5 py-0.5 text-xs text-white bg-blue-600 rounded-sm hover:bg-blue-700"
                >
                  Add
                </button>
                <button
                  onClick={cancelAddTag}
                  className="px-1.5 py-0.5 text-xs text-gray-700 bg-white border border-gray-300 rounded-sm hover:bg-gray-50"
                >
                  Cancel
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default DocumentCategorization; 