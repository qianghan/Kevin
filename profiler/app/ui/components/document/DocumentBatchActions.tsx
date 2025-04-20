'use client';

import React, { useState } from 'react';
import { useDocumentService } from '../../lib/contexts/DocumentContext';

export interface DocumentInfo {
  id: string;
  name: string;
  contentType: string;
  size: number;
  category?: string;
  dateUploaded: string;
}

interface DocumentBatchActionsProps {
  documents: DocumentInfo[];
  onDelete: (documentIds: string[]) => void;
  onCategorize: (documentIds: string[], category: string) => void;
  onSelectionChange?: (selectedIds: string[]) => void;
  categories?: string[];
}

const DocumentBatchActions: React.FC<DocumentBatchActionsProps> = ({
  documents,
  onDelete,
  onCategorize,
  onSelectionChange,
  categories = ['Academic', 'Personal', 'Professional', 'Other']
}) => {
  const [selectedDocuments, setSelectedDocuments] = useState<Set<string>>(new Set());
  const [selectAll, setSelectAll] = useState(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [isCategoryModalOpen, setIsCategoryModalOpen] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  
  // Handle select all checkbox
  const handleSelectAll = () => {
    if (selectAll) {
      setSelectedDocuments(new Set());
    } else {
      setSelectedDocuments(new Set(documents.map(doc => doc.id)));
    }
    setSelectAll(!selectAll);
    
    if (onSelectionChange) {
      if (!selectAll) {
        onSelectionChange(documents.map(doc => doc.id));
      } else {
        onSelectionChange([]);
      }
    }
  };
  
  // Handle individual document selection
  const handleSelectDocument = (documentId: string) => {
    const newSelection = new Set(selectedDocuments);
    
    if (newSelection.has(documentId)) {
      newSelection.delete(documentId);
    } else {
      newSelection.add(documentId);
    }
    
    setSelectedDocuments(newSelection);
    setSelectAll(newSelection.size === documents.length);
    
    if (onSelectionChange) {
      onSelectionChange(Array.from(newSelection));
    }
  };
  
  // Prepare batch download
  const handleBatchDownload = async () => {
    if (selectedDocuments.size === 0) return;
    
    setIsProcessing(true);
    
    try {
      // In a real app, you would call an API to get download URLs
      // For now, just log the selected document IDs
      console.log('Downloading documents:', Array.from(selectedDocuments));
      
      // Simulate API delay
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // In a real implementation, you might create a zip file on the server
      // and then download it, or trigger individual downloads
      alert(`${selectedDocuments.size} documents prepared for download`);
    } catch (error) {
      console.error('Error preparing downloads:', error);
      alert('Failed to prepare downloads');
    } finally {
      setIsProcessing(false);
    }
  };
  
  // Delete selected documents
  const handleBatchDelete = async () => {
    if (selectedDocuments.size === 0) return;
    
    setIsProcessing(true);
    
    try {
      // Call the onDelete callback with selected document IDs
      onDelete(Array.from(selectedDocuments));
      
      // Close the modal and clear selection
      setIsDeleteModalOpen(false);
      setSelectedDocuments(new Set());
      setSelectAll(false);
    } catch (error) {
      console.error('Error deleting documents:', error);
      alert('Failed to delete documents');
    } finally {
      setIsProcessing(false);
    }
  };
  
  // Categorize selected documents
  const handleBatchCategorize = async () => {
    if (selectedDocuments.size === 0 || !selectedCategory) return;
    
    setIsProcessing(true);
    
    try {
      // Call the onCategorize callback with selected document IDs and category
      onCategorize(Array.from(selectedDocuments), selectedCategory);
      
      // Close the modal and clear category
      setIsCategoryModalOpen(false);
      setSelectedCategory('');
    } catch (error) {
      console.error('Error categorizing documents:', error);
      alert('Failed to categorize documents');
    } finally {
      setIsProcessing(false);
    }
  };
  
  return (
    <div className="mb-6">
      {/* Batch actions toolbar */}
      <div className="bg-white rounded-lg border border-gray-200 p-4 shadow-sm">
        <div className="flex flex-wrap items-center gap-4">
          {/* Selection checkbox */}
          <div className="flex items-center">
            <input
              type="checkbox"
              id="select-all"
              checked={selectAll}
              onChange={handleSelectAll}
              className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
            />
            <label htmlFor="select-all" className="ml-2 text-sm text-gray-700">
              Select All
            </label>
          </div>
          
          <div className="h-6 border-l border-gray-300"></div>
          
          {/* Selected count */}
          <div className="text-sm text-gray-600">
            {selectedDocuments.size} of {documents.length} selected
          </div>
          
          <div className="flex-grow"></div>
          
          {/* Action buttons */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => setIsCategoryModalOpen(true)}
              disabled={selectedDocuments.size === 0 || isProcessing}
              className="px-3 py-1.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Categorize
            </button>
            
            <button
              onClick={handleBatchDownload}
              disabled={selectedDocuments.size === 0 || isProcessing}
              className="px-3 py-1.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Download
            </button>
            
            <button
              onClick={() => setIsDeleteModalOpen(true)}
              disabled={selectedDocuments.size === 0 || isProcessing}
              className="px-3 py-1.5 text-sm font-medium text-white bg-red-600 border border-transparent rounded-md shadow-sm hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Delete
            </button>
          </div>
        </div>
      </div>
      
      {/* Document list with checkboxes */}
      <div className="mt-4 bg-white rounded-lg border border-gray-200 overflow-hidden shadow-sm">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th scope="col" className="w-12 px-3 py-3">
                <span className="sr-only">Select</span>
              </th>
              <th scope="col" className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Name
              </th>
              <th scope="col" className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Type
              </th>
              <th scope="col" className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Size
              </th>
              <th scope="col" className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Category
              </th>
              <th scope="col" className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Date Uploaded
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {documents.map((document) => (
              <tr 
                key={document.id}
                className={selectedDocuments.has(document.id) ? 'bg-blue-50' : 'hover:bg-gray-50'}
              >
                <td className="px-3 py-4 whitespace-nowrap">
                  <input
                    type="checkbox"
                    checked={selectedDocuments.has(document.id)}
                    onChange={() => handleSelectDocument(document.id)}
                    className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  />
                </td>
                <td className="px-3 py-4 whitespace-nowrap">
                  <div className="flex items-center">
                    {/* File icon based on type */}
                    <svg className="w-5 h-5 mr-2 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    <div className="text-sm font-medium text-gray-900 truncate max-w-xs">
                      {document.name}
                    </div>
                  </div>
                </td>
                <td className="px-3 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-500">
                    {document.contentType}
                  </div>
                </td>
                <td className="px-3 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-500">
                    {(document.size / 1024).toFixed(1)} KB
                  </div>
                </td>
                <td className="px-3 py-4 whitespace-nowrap">
                  <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                    {document.category || 'Uncategorized'}
                  </span>
                </td>
                <td className="px-3 py-4 whitespace-nowrap text-sm text-gray-500">
                  {new Date(document.dateUploaded).toLocaleDateString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      
      {/* Delete confirmation modal */}
      {isDeleteModalOpen && (
        <div className="fixed inset-0 z-10 overflow-y-auto">
          <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 transition-opacity" aria-hidden="true">
              <div className="absolute inset-0 bg-gray-500 opacity-75"></div>
            </div>
            
            <span className="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>
            
            <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
              <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                <div className="sm:flex sm:items-start">
                  <div className="mx-auto flex-shrink-0 flex items-center justify-center h-12 w-12 rounded-full bg-red-100 sm:mx-0 sm:h-10 sm:w-10">
                    <svg className="h-6 w-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                  </div>
                  <div className="mt-3 text-center sm:mt-0 sm:ml-4 sm:text-left">
                    <h3 className="text-lg leading-6 font-medium text-gray-900">
                      Delete documents
                    </h3>
                    <div className="mt-2">
                      <p className="text-sm text-gray-500">
                        Are you sure you want to delete the selected {selectedDocuments.size} documents? This action cannot be undone.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
              <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                <button 
                  type="button" 
                  onClick={handleBatchDelete}
                  disabled={isProcessing}
                  className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-red-600 text-base font-medium text-white hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 sm:ml-3 sm:w-auto sm:text-sm disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isProcessing ? 'Deleting...' : 'Delete'}
                </button>
                <button 
                  type="button" 
                  onClick={() => setIsDeleteModalOpen(false)}
                  disabled={isProcessing}
                  className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
      
      {/* Categorize modal */}
      {isCategoryModalOpen && (
        <div className="fixed inset-0 z-10 overflow-y-auto">
          <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 transition-opacity" aria-hidden="true">
              <div className="absolute inset-0 bg-gray-500 opacity-75"></div>
            </div>
            
            <span className="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>
            
            <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
              <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                <div className="sm:flex sm:items-start">
                  <div className="mx-auto flex-shrink-0 flex items-center justify-center h-12 w-12 rounded-full bg-blue-100 sm:mx-0 sm:h-10 sm:w-10">
                    <svg className="h-6 w-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
                    </svg>
                  </div>
                  <div className="mt-3 text-center sm:mt-0 sm:ml-4 sm:text-left w-full">
                    <h3 className="text-lg leading-6 font-medium text-gray-900">
                      Categorize documents
                    </h3>
                    <div className="mt-2">
                      <p className="text-sm text-gray-500 mb-4">
                        Select a category for the {selectedDocuments.size} selected documents.
                      </p>
                      
                      <div className="w-full">
                        <label htmlFor="category" className="block text-sm font-medium text-gray-700 mb-1">
                          Category
                        </label>
                        <select
                          id="category"
                          value={selectedCategory}
                          onChange={(e) => setSelectedCategory(e.target.value)}
                          className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
                        >
                          <option value="">Select a category</option>
                          {categories.map((category) => (
                            <option key={category} value={category}>
                              {category}
                            </option>
                          ))}
                        </select>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                <button 
                  type="button" 
                  onClick={handleBatchCategorize}
                  disabled={isProcessing || !selectedCategory}
                  className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-blue-600 text-base font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:ml-3 sm:w-auto sm:text-sm disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isProcessing ? 'Saving...' : 'Save'}
                </button>
                <button 
                  type="button" 
                  onClick={() => setIsCategoryModalOpen(false)}
                  disabled={isProcessing}
                  className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DocumentBatchActions; 