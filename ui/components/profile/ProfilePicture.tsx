'use client';

import React, { useState, useRef } from 'react';
import { useUserProfile } from '@/hooks/useUserProfile';
import Image from 'next/image';

export function ProfilePicture() {
  const { user, uploadProfilePicture, isLoading, error } = useUserProfile();
  const [isDragging, setIsDragging] = useState(false);
  const [success, setSuccess] = useState(false);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!isDragging) {
      setIsDragging(true);
    }
  };

  const processFile = async (file: File) => {
    // Make sure it's an image
    if (!file.type.startsWith('image/')) {
      alert('Please upload an image file.');
      return;
    }
    
    // Preview the image
    const reader = new FileReader();
    reader.onload = (e) => {
      if (e.target?.result) {
        setPreviewUrl(e.target.result as string);
      }
    };
    reader.readAsDataURL(file);
    
    // Upload the image
    setSuccess(false);
    const result = await uploadProfilePicture(file);
    if (result) {
      setSuccess(true);
      // Hide success message after 3 seconds
      setTimeout(() => setSuccess(false), 3000);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      processFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      processFile(e.target.files[0]);
    }
  };

  const handleButtonClick = () => {
    fileInputRef.current?.click();
  };

  const profileImage = previewUrl || user?.profilePicture || '/default-avatar.png';

  return (
    <div className="p-4 max-w-md mx-auto">
      <h2 className="text-2xl font-bold mb-6">Profile Picture</h2>
      
      {success && (
        <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded mb-4">
          Profile picture updated successfully!
        </div>
      )}
      
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}
      
      <div className="flex flex-col items-center space-y-6">
        <div className="relative w-40 h-40 rounded-full overflow-hidden border-4 border-gray-200">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={profileImage}
            alt="Profile"
            className="w-full h-full object-cover"
          />
        </div>
        
        <div
          className={`border-2 border-dashed rounded-lg p-6 w-full text-center cursor-pointer ${
            isDragging ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-blue-400'
          }`}
          onDragEnter={handleDragEnter}
          onDragLeave={handleDragLeave}
          onDragOver={handleDragOver}
          onDrop={handleDrop}
          onClick={handleButtonClick}
        >
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileSelect}
            accept="image/*"
            className="hidden"
          />
          
          <div className="flex flex-col items-center">
            <svg
              className="w-10 h-10 text-gray-400 mb-3"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="2"
                d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
              ></path>
            </svg>
            <p className="mb-2 text-sm text-gray-600">
              <span className="font-semibold">Click to upload</span> or drag and drop
            </p>
            <p className="text-xs text-gray-500">PNG, JPG, GIF up to 5MB</p>
          </div>
        </div>
        
        <button
          type="button"
          disabled={isLoading}
          className="bg-blue-600 text-white py-2 px-6 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:bg-blue-300"
          onClick={handleButtonClick}
        >
          {isLoading ? 'Uploading...' : 'Change Profile Picture'}
        </button>
      </div>
    </div>
  );
} 