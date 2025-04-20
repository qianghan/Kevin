'use client';

import React, { useState, useEffect } from 'react';

interface DocumentPreviewProps {
  documentId: string;
  filename: string;
  contentType: string;
  url?: string;
  thumbnailUrl?: string;
  previewContent?: string;
}

const DocumentPreview: React.FC<DocumentPreviewProps> = ({
  documentId,
  filename,
  contentType,
  url,
  thumbnailUrl,
  previewContent
}) => {
  const [isLoading, setIsLoading] = useState(true);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  
  // File type determination
  const fileExtension = filename.split('.').pop()?.toLowerCase() || '';
  const isImage = /^image\//i.test(contentType) || ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg'].includes(fileExtension);
  const isPdf = contentType === 'application/pdf' || fileExtension === 'pdf';
  const isText = contentType === 'text/plain' || fileExtension === 'txt';
  const isOffice = ['doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx'].includes(fileExtension);
  
  useEffect(() => {
    // If we already have a preview URL, use it
    if (url) {
      setPreviewUrl(url);
      setIsLoading(false);
      return;
    }
    
    // If we have a thumbnail URL for non-displayable files, use it
    if (thumbnailUrl && !isImage && !isPdf) {
      setPreviewUrl(thumbnailUrl);
      setIsLoading(false);
      return;
    }
    
    // If direct preview isn't available, we would fetch it from the server
    const fetchPreview = async () => {
      try {
        setIsLoading(true);
        
        // This would be a real API call in a production environment
        // For now, we'll simulate a delay
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        // In a real app, call your API to get preview URL
        // const response = await fetch(`/api/documents/${documentId}/preview`);
        // if (!response.ok) throw new Error('Failed to load preview');
        // const data = await response.json();
        // setPreviewUrl(data.previewUrl);
        
        // For demo purposes, set a placeholder
        if (isImage) {
          setPreviewUrl(`https://via.placeholder.com/800x600?text=Image:+${encodeURIComponent(filename)}`);
        } else if (isPdf) {
          setPreviewUrl(`https://via.placeholder.com/800x600?text=PDF:+${encodeURIComponent(filename)}`);
        } else {
          setPreviewUrl(`https://via.placeholder.com/800x600?text=File:+${encodeURIComponent(filename)}`);
        }
        
        setIsLoading(false);
      } catch (err) {
        console.error('Error loading preview:', err);
        setError('Failed to load preview');
        setIsLoading(false);
      }
    };
    
    fetchPreview();
  }, [documentId, filename, url, thumbnailUrl, contentType, isImage, isPdf]);
  
  // Handle error state
  if (error) {
    return (
      <div className="w-full rounded-lg bg-red-50 border border-red-200 p-4 flex flex-col items-center justify-center">
        <svg className="w-12 h-12 text-red-400 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
        <p className="text-red-800 font-medium">{error}</p>
        <p className="text-red-600 text-sm mt-1">{filename}</p>
      </div>
    );
  }
  
  // Loading state
  if (isLoading) {
    return (
      <div className="w-full rounded-lg bg-gray-50 border border-gray-200 p-4 flex flex-col items-center justify-center min-h-[300px]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mb-3"></div>
        <p className="text-gray-600">Loading preview...</p>
      </div>
    );
  }
  
  // Render different preview based on file type
  return (
    <div className="w-full rounded-lg border border-gray-200 overflow-hidden">
      <div className="bg-gray-100 px-4 py-2 border-b border-gray-200 flex justify-between items-center">
        <div className="font-medium text-gray-700 truncate flex-1">{filename}</div>
        {url && (
          <a 
            href={url} 
            target="_blank" 
            rel="noopener noreferrer"
            className="ml-2 text-blue-500 hover:text-blue-700 text-sm"
          >
            Open
          </a>
        )}
      </div>
      
      <div className="bg-white">
        {isImage && previewUrl && (
          <div className="w-full flex justify-center p-4">
            <img 
              src={previewUrl} 
              alt={filename} 
              className="max-w-full object-contain max-h-[500px]" 
            />
          </div>
        )}
        
        {isPdf && previewUrl && (
          <div className="w-full h-[500px] p-4">
            <iframe 
              src={previewUrl} 
              title={filename}
              className="w-full h-full border-0" 
            />
          </div>
        )}
        
        {isText && previewContent && (
          <div className="p-4 overflow-auto max-h-[500px]">
            <pre className="whitespace-pre-wrap font-mono text-sm">{previewContent}</pre>
          </div>
        )}
        
        {isOffice && (
          <div className="p-8 text-center">
            <svg className="w-16 h-16 mx-auto text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <h3 className="text-lg font-medium text-gray-900 mb-1">{filename}</h3>
            <p className="text-sm text-gray-500 mb-4">This document type cannot be previewed directly.</p>
            {url && (
              <a 
                href={url}
                target="_blank" 
                rel="noopener noreferrer"
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                Download to View
              </a>
            )}
          </div>
        )}
        
        {!isImage && !isPdf && !isText && !isOffice && previewUrl && (
          <div className="p-8 text-center">
            <img 
              src={previewUrl}
              alt={`Thumbnail for ${filename}`}
              className="max-w-full mx-auto mb-4 max-h-[300px] object-contain"
            />
            <h3 className="text-lg font-medium text-gray-900 mb-1">{filename}</h3>
            <p className="text-sm text-gray-500 mb-4">Preview not available for this file type.</p>
            {url && (
              <a 
                href={url}
                target="_blank" 
                rel="noopener noreferrer"
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                Download
              </a>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default DocumentPreview; 