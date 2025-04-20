'use client';

import React, { useState, useRef, useCallback, useEffect } from 'react';
import { useDocumentService } from '../../lib/contexts/DocumentContext';

interface FileWithPreview extends File {
  preview?: string;
}

interface DropzoneUploaderProps {
  onUploadComplete?: (documentIds: string[]) => void;
  maxFileSize?: number; // in MB
  maxFiles?: number;
  acceptedFileTypes?: string[];
  showPreview?: boolean;
}

const DropzoneUploader: React.FC<DropzoneUploaderProps> = ({
  onUploadComplete,
  maxFileSize = 10, // Default 10MB
  maxFiles = 5, // Default max 5 files
  acceptedFileTypes = ['.pdf', '.doc', '.docx', '.txt', '.jpg', '.jpeg', '.png'],
  showPreview = true,
}) => {
  const dropzoneRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const [isDragging, setIsDragging] = useState(false);
  const [files, setFiles] = useState<FileWithPreview[]>([]);
  const [fileErrors, setFileErrors] = useState<{[key: string]: string}>({});
  const [uploadingFiles, setUploadingFiles] = useState<{[key: string]: {progress: number, status: string}}>({});
  
  const { documentService } = useDocumentService();

  // Generate accept string for file input
  const acceptString = acceptedFileTypes.join(',');
  
  // Handle drag events
  const handleDrag = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setIsDragging(true);
    } else if (e.type === 'dragleave' || e.type === 'drop') {
      setIsDragging(false);
    }
  }, []);
  
  // Handle dropped files
  const handleDrop = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    
    const droppedFiles = Array.from(e.dataTransfer.files);
    validateAndAddFiles(droppedFiles);
  }, [maxFiles, maxFileSize, acceptedFileTypes]);
  
  // Handle file input change
  const handleFileInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    
    if (e.target.files && e.target.files.length > 0) {
      validateAndAddFiles(Array.from(e.target.files));
    }
  }, [maxFiles, maxFileSize, acceptedFileTypes]);
  
  // Validate files and add to state
  const validateAndAddFiles = (newFiles: File[]) => {
    const errors: {[key: string]: string} = {};
    
    // Check max files limit
    if (files.length + newFiles.length > maxFiles) {
      alert(`You can only upload a maximum of ${maxFiles} files at once.`);
      return;
    }
    
    // Validate each file
    const validFiles = newFiles.filter(file => {
      // Check file size
      if (file.size > maxFileSize * 1024 * 1024) {
        errors[file.name] = `File size exceeds ${maxFileSize}MB limit`;
        return false;
      }
      
      // Check file type
      const fileExtension = `.${file.name.split('.').pop()?.toLowerCase()}`;
      if (!acceptedFileTypes.includes(fileExtension) && !acceptedFileTypes.includes(file.type)) {
        errors[file.name] = `File type not supported`;
        return false;
      }
      
      return true;
    });
    
    // Add previews for images
    const filesWithPreviews = validFiles.map(file => {
      const fileWithPreview = file as FileWithPreview;
      if (file.type.startsWith('image/') && showPreview) {
        fileWithPreview.preview = URL.createObjectURL(file);
      }
      return fileWithPreview;
    });
    
    // Update state
    setFiles(prevFiles => [...prevFiles, ...filesWithPreviews]);
    setFileErrors({...fileErrors, ...errors});
  };
  
  // Remove file from list
  const removeFile = (index: number) => {
    setFiles(prevFiles => {
      const newFiles = [...prevFiles];
      
      // Revoke object URL if preview exists
      if (newFiles[index].preview) {
        URL.revokeObjectURL(newFiles[index].preview!);
      }
      
      newFiles.splice(index, 1);
      return newFiles;
    });
  };
  
  // Upload files
  const uploadFiles = async () => {
    if (files.length === 0) return;
    
    const documentIds: string[] = [];
    const uploadingStatus: {[key: string]: {progress: number, status: string}} = {};
    
    // Initialize upload status for each file
    files.forEach(file => {
      uploadingStatus[file.name] = { progress: 0, status: 'pending' };
    });
    setUploadingFiles(uploadingStatus);
    
    // Use Promise.all to upload files concurrently
    const uploadPromises = files.map(async (file, index) => {
      try {
        // Update status to uploading
        setUploadingFiles(prev => ({
          ...prev, 
          [file.name]: { progress: 0, status: 'uploading' }
        }));
        
        // Set up progress tracking
        const progressTracker = (progress: number) => {
          setUploadingFiles(prev => ({
            ...prev, 
            [file.name]: { progress, status: 'uploading' }
          }));
        };
        
        // Start upload with custom progress tracking
        const documentId = await documentService.uploadDocument(file, progressTracker);
        documentIds.push(documentId);
        
        // Update status to completed
        setUploadingFiles(prev => ({
          ...prev, 
          [file.name]: { progress: 100, status: 'completed' }
        }));
        
        return documentId;
      } catch (error) {
        console.error(`Error uploading ${file.name}:`, error);
        
        // Update status to error
        setUploadingFiles(prev => ({
          ...prev, 
          [file.name]: { progress: 0, status: 'error' }
        }));
        
        throw error;
      }
    });
    
    try {
      // Wait for all uploads to complete
      await Promise.all(uploadPromises);
      
      // Call the completion callback with document IDs
      if (onUploadComplete) {
        onUploadComplete(documentIds);
      }
      
      // Clear the file list after successful upload
      setTimeout(() => {
        setFiles([]);
        setUploadingFiles({});
      }, 2000);
    } catch (error) {
      console.error('Some files failed to upload:', error);
    }
  };
  
  // Clean up previews on unmount
  useEffect(() => {
    return () => {
      files.forEach(file => {
        if (file.preview) {
          URL.revokeObjectURL(file.preview);
        }
      });
    };
  }, [files]);

  // Open file dialog when clicking the dropzone
  const openFileDialog = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };
  
  return (
    <div className="w-full mb-8">
      <div 
        ref={dropzoneRef}
        className={`border-2 border-dashed rounded-lg p-6 flex flex-col items-center justify-center transition-colors ${
          isDragging 
            ? 'border-blue-500 bg-blue-50' 
            : 'border-gray-300 hover:border-blue-400 hover:bg-blue-50'
        }`}
        onDragEnter={handleDrag}
        onDragOver={handleDrag}
        onDragLeave={handleDrag}
        onDrop={handleDrop}
        onClick={openFileDialog}
      >
        <input 
          ref={fileInputRef}
          type="file" 
          multiple
          className="hidden"
          accept={acceptString}
          onChange={handleFileInputChange}
        />
        
        <svg 
          className="w-12 h-12 mb-3 text-blue-500" 
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
        
        <p className="mb-2 text-sm font-medium text-gray-700">
          <span className="font-semibold">Click to upload</span> or drag and drop
        </p>
        <p className="text-xs text-gray-500">
          {acceptedFileTypes.join(', ')} (Max {maxFiles} files, {maxFileSize}MB each)
        </p>
      </div>
      
      {/* File List */}
      {files.length > 0 && (
        <div className="mt-4">
          <div className="flex justify-between items-center mb-2">
            <h3 className="text-sm font-medium text-gray-700">Selected Files</h3>
            <button
              onClick={uploadFiles}
              disabled={Object.keys(uploadingFiles).length > 0}
              className="px-4 py-2 bg-blue-500 text-white rounded-md text-sm font-medium disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              Upload All Files
            </button>
          </div>
          
          <ul className="space-y-2">
            {files.map((file, index) => (
              <li 
                key={`${file.name}-${index}`} 
                className="p-3 bg-white border rounded-md shadow-sm"
              >
                <div className="flex justify-between items-center mb-2">
                  <div className="flex items-center">
                    {/* File icon or preview */}
                    {file.preview ? (
                      <img 
                        src={file.preview} 
                        alt={file.name}
                        className="w-10 h-10 mr-3 object-cover rounded"
                      />
                    ) : (
                      <svg 
                        className="w-10 h-10 mr-3 text-gray-400" 
                        fill="none" 
                        stroke="currentColor" 
                        viewBox="0 0 24 24" 
                        xmlns="http://www.w3.org/2000/svg"
                      >
                        <path 
                          strokeLinecap="round" 
                          strokeLinejoin="round" 
                          strokeWidth={2} 
                          d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" 
                        />
                      </svg>
                    )}
                    
                    {/* File details */}
                    <div className="text-sm">
                      <p className="font-medium text-gray-700 truncate max-w-xs">{file.name}</p>
                      <p className="text-gray-500">{(file.size / (1024 * 1024)).toFixed(2)} MB</p>
                    </div>
                  </div>
                  
                  {/* Remove button or status indicator */}
                  {uploadingFiles[file.name] ? (
                    <div className="flex items-center">
                      {uploadingFiles[file.name].status === 'completed' ? (
                        <span className="text-green-500 flex items-center">
                          <svg className="w-5 h-5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                          </svg>
                          Uploaded
                        </span>
                      ) : uploadingFiles[file.name].status === 'error' ? (
                        <span className="text-red-500 flex items-center">
                          <svg className="w-5 h-5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                          </svg>
                          Error
                        </span>
                      ) : (
                        <span className="text-blue-500 flex items-center">
                          {uploadingFiles[file.name].progress}%
                        </span>
                      )}
                    </div>
                  ) : (
                    <button 
                      onClick={(e) => {
                        e.stopPropagation();
                        removeFile(index);
                      }}
                      className="p-1 text-gray-500 hover:text-red-500"
                    >
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  )}
                </div>
                
                {/* Error message */}
                {fileErrors[file.name] && (
                  <p className="text-xs text-red-500 mt-1">{fileErrors[file.name]}</p>
                )}
                
                {/* Progress bar */}
                {uploadingFiles[file.name] && (
                  <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                    <div 
                      className={`h-2 rounded-full ${
                        uploadingFiles[file.name].status === 'completed' 
                          ? 'bg-green-500' 
                          : uploadingFiles[file.name].status === 'error'
                            ? 'bg-red-500'
                            : 'bg-blue-500'
                      }`}
                      style={{ width: `${uploadingFiles[file.name].progress}%` }}
                    />
                  </div>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default DropzoneUploader; 