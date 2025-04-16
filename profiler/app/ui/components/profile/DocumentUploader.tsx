'use client';

import React, { useState, useRef, DragEvent, ChangeEvent } from 'react';
import { useDocumentService } from '../../lib/contexts/DocumentContext';

interface DocumentUploaderProps {
  onUpload?: (documentId: string) => void;
}

const DocumentUploader: React.FC<DocumentUploaderProps> = ({ onUpload }) => {
  const { documentService, isUploading, lastUploaded, uploadError, uploadProgress } = useDocumentService();
  const [dragging, setDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDrag = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragging(true);
    } else if (e.type === 'dragleave') {
      setDragging(false);
    }
  };

  const handleDrop = async (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setDragging(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      await uploadFile(file);
    }
  };

  const handleChange = async (e: ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      await uploadFile(file);
    }
  };

  const uploadFile = async (file: File) => {
    try {
      const documentId = await documentService.uploadDocument(file);
      if (onUpload) {
        onUpload(documentId);
      }
    } catch (error) {
      console.error("Upload failed:", error);
    }
  };

  const handleButtonClick = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className="mt-4 w-full">
      <div
        className={`border-2 border-dashed rounded-md p-6 flex flex-col items-center justify-center cursor-pointer transition-colors ${
          dragging 
            ? 'border-blue-500 bg-blue-50' 
            : isUploading 
              ? 'border-gray-300 bg-gray-50 opacity-75' 
              : 'border-gray-300 hover:border-blue-400 hover:bg-blue-50'
        }`}
        onDragEnter={handleDrag}
        onDragOver={handleDrag}
        onDragLeave={handleDrag}
        onDrop={handleDrop}
        onClick={handleButtonClick}
      >
        <input 
          ref={fileInputRef}
          type="file" 
          className="hidden"
          onChange={handleChange}
          accept=".pdf,.doc,.docx,.txt"
          disabled={isUploading}
        />
        
        <svg 
          className={`w-12 h-12 mb-3 ${isUploading ? 'text-gray-400' : 'text-blue-500'}`} 
          fill="none" 
          stroke="currentColor" 
          viewBox="0 0 24 24" 
          xmlns="http://www.w3.org/2000/svg"
        >
          <path 
            strokeLinecap="round" 
            strokeLinejoin="round" 
            strokeWidth={2} 
            d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" 
          />
        </svg>
        
        {isUploading ? (
          <div className="text-center">
            <div className="text-sm font-medium text-gray-700">Uploading...</div>
            <div className="mt-2 h-2 w-full bg-gray-200 rounded-full">
              <div 
                className="h-full bg-blue-500 rounded-full transition-all duration-300" 
                style={{ width: `${uploadProgress}%` }}
              />
            </div>
          </div>
        ) : (
          <div className="text-center">
            <p className="mb-2 text-sm font-medium text-gray-700">
              <span className="font-semibold">Click to upload</span> or drag and drop
            </p>
            <p className="text-xs text-gray-500">
              PDF, DOC, DOCX or TXT (MAX. 10MB)
            </p>
          </div>
        )}
      </div>
      
      {uploadError && (
        <div className="mt-2 text-sm text-red-600">
          Error: {uploadError}
        </div>
      )}
      
      {lastUploaded && !isUploading && !uploadError && (
        <div className="mt-2 text-sm text-green-600 flex items-center">
          <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
          Successfully uploaded: {lastUploaded.filename}
        </div>
      )}
    </div>
  );
};

export default DocumentUploader; 