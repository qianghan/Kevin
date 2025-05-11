/**
 * File Upload Service
 * 
 * This service provides a unified interface for file uploading and attachment handling
 * across frontend and /ui applications. It handles validation, preprocessing, 
 * and storage of file attachments for chat messages.
 */

import { v4 as uuidv4 } from 'uuid';
import { Attachment } from '../../interfaces/services/chat.service';
import { logError, logInfo } from '../logging/logger';

/**
 * Supported attachment types
 */
export enum AttachmentType {
  IMAGE = 'image',
  DOCUMENT = 'document',
  LINK = 'link'
}

/**
 * Attachment validation options
 */
export interface AttachmentValidationOptions {
  maxSizeBytes: number;
  allowedTypes: string[];
  maxFiles?: number;
}

/**
 * File upload result
 */
export interface FileUploadResult {
  successful: Attachment[];
  failed: Array<{
    file: File;
    reason: string;
  }>;
}

/**
 * Default validation options
 */
const DEFAULT_VALIDATION_OPTIONS: AttachmentValidationOptions = {
  maxSizeBytes: 10 * 1024 * 1024, // 10MB
  allowedTypes: [
    // Images
    '.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg',
    // Documents
    '.pdf', '.doc', '.docx', '.txt', '.md', '.csv', '.xls', '.xlsx',
    // Code
    '.js', '.ts', '.html', '.css', '.json', '.yaml', '.xml'
  ],
  maxFiles: 5
};

/**
 * File Upload Service for handling chat attachments
 */
export class FileUploadService {
  private validationOptions: AttachmentValidationOptions;
  private storageUrl: string;
  
  /**
   * Create a new FileUploadService
   */
  constructor(options?: Partial<AttachmentValidationOptions>, storageUrl?: string) {
    this.validationOptions = { ...DEFAULT_VALIDATION_OPTIONS, ...options };
    this.storageUrl = storageUrl || '/api/uploads';
  }
  
  /**
   * Update validation options
   */
  setValidationOptions(options: Partial<AttachmentValidationOptions>): void {
    this.validationOptions = { ...this.validationOptions, ...options };
  }
  
  /**
   * Validate a file for upload
   */
  private validateFile(file: File): { valid: boolean; reason?: string } {
    // Check file size
    if (file.size > this.validationOptions.maxSizeBytes) {
      return {
        valid: false,
        reason: `File size exceeds the maximum allowed size of ${this.validationOptions.maxSizeBytes / (1024 * 1024)}MB`
      };
    }
    
    // Check file type
    const fileExtension = `.${file.name.split('.').pop()?.toLowerCase()}`;
    const isAllowedType = this.validationOptions.allowedTypes.some(type => {
      if (type.startsWith('.')) {
        // Check by extension
        return fileExtension === type.toLowerCase();
      } else {
        // Check by MIME type
        return file.type.includes(type);
      }
    });
    
    if (!isAllowedType) {
      return {
        valid: false,
        reason: `File type not allowed. Allowed types: ${this.validationOptions.allowedTypes.join(', ')}`
      };
    }
    
    return { valid: true };
  }
  
  /**
   * Get the attachment type based on the file
   */
  private getAttachmentType(file: File): AttachmentType {
    if (file.type.startsWith('image/')) {
      return AttachmentType.IMAGE;
    } else {
      return AttachmentType.DOCUMENT;
    }
  }
  
  /**
   * Create an attachment from a file (without uploading)
   */
  createAttachmentFromFile(file: File): Attachment {
    const id = uuidv4();
    return {
      id,
      type: this.getAttachmentType(file),
      name: file.name,
      size: file.size,
      mimeType: file.type,
      url: URL.createObjectURL(file) // Temporary URL for preview
    };
  }
  
  /**
   * Process files for upload (validate and create attachments)
   */
  processFiles(files: File[]): FileUploadResult {
    const result: FileUploadResult = {
      successful: [],
      failed: []
    };
    
    // Check if too many files
    if (this.validationOptions.maxFiles && files.length > this.validationOptions.maxFiles) {
      const extraFiles = files.slice(this.validationOptions.maxFiles);
      extraFiles.forEach(file => {
        result.failed.push({
          file,
          reason: `Exceeded maximum number of files (${this.validationOptions.maxFiles})`
        });
      });
      
      // Only process up to the max allowed
      files = files.slice(0, this.validationOptions.maxFiles);
    }
    
    // Process each file
    for (const file of files) {
      const validation = this.validateFile(file);
      
      if (validation.valid) {
        // Create attachment
        const attachment = this.createAttachmentFromFile(file);
        result.successful.push(attachment);
      } else {
        result.failed.push({
          file,
          reason: validation.reason || 'Unknown validation error'
        });
      }
    }
    
    return result;
  }
  
  /**
   * Upload files to the server
   */
  async uploadFiles(files: File[]): Promise<FileUploadResult> {
    // First validate and process files
    const processResult = this.processFiles(files);
    
    // If no successful files to upload, return early
    if (processResult.successful.length === 0) {
      return processResult;
    }
    
    const result: FileUploadResult = {
      successful: [],
      failed: [...processResult.failed] // Start with previously failed files
    };
    
    // Upload each valid file
    const uploadPromises = processResult.successful.map(async (attachment) => {
      try {
        // Find the original file
        const file = files.find(f => f.name === attachment.name && f.size === attachment.size);
        
        if (!file) {
          throw new Error('Original file not found');
        }
        
        // Create form data
        const formData = new FormData();
        formData.append('file', file);
        formData.append('attachmentId', attachment.id);
        
        // Upload the file
        const response = await fetch(this.storageUrl, {
          method: 'POST',
          body: formData
        });
        
        if (!response.ok) {
          throw new Error(`Upload failed with status: ${response.status}`);
        }
        
        // Get the uploaded file URL
        const data = await response.json();
        
        // Update attachment with real URL
        const updatedAttachment: Attachment = {
          ...attachment,
          url: data.url
        };
        
        result.successful.push(updatedAttachment);
        logInfo(`File uploaded successfully: ${attachment.name}`);
      } catch (error) {
        // Find the original file for the failed attachment
        const file = files.find(f => f.name === attachment.name && f.size === attachment.size);
        
        if (file) {
          result.failed.push({
            file,
            reason: error instanceof Error ? error.message : 'Unknown upload error'
          });
        }
        
        logError(`File upload failed: ${attachment.name}`, error);
      }
    });
    
    // Wait for all uploads to complete
    await Promise.all(uploadPromises);
    
    return result;
  }
  
  /**
   * Create a link attachment
   */
  createLinkAttachment(url: string, title?: string): Attachment {
    return {
      id: uuidv4(),
      type: AttachmentType.LINK,
      name: title || url,
      url,
      size: 0,
      mimeType: 'text/uri-list'
    };
  }
}

/**
 * Create and export a singleton instance of the file upload service
 */
export const fileUploadService = new FileUploadService();

/**
 * Get the file upload service instance
 */
export function getFileUploadService(): FileUploadService {
  return fileUploadService;
} 