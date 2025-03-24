'use client';

import React from 'react';
import { UserProfileCardProps } from '../types/user-ui.types';

export function ProfileCard({
  user,
  isLoading,
  error,
  onUpdateProfile,
  isAuthenticated
}: UserProfileCardProps) {
  if (!isAuthenticated) {
    return (
      <div className="bg-white shadow rounded-lg p-6 text-center">
        <h2 className="text-xl font-semibold mb-4">User Profile</h2>
        <p className="text-gray-500">Please sign in to view your profile</p>
      </div>
    );
  }
  
  if (isLoading) {
    return (
      <div className="bg-white shadow rounded-lg p-6">
        <div className="animate-pulse flex flex-col items-center">
          <div className="rounded-full bg-gray-200 h-20 w-20 mb-4"></div>
          <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
          <div className="h-4 bg-gray-200 rounded w-1/2"></div>
        </div>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="bg-white shadow rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4">User Profile</h2>
        <div className="bg-red-50 text-red-600 p-4 rounded-md mb-4">
          {error}
        </div>
        <button 
          onClick={() => window.location.reload()}
          className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-md"
        >
          Retry
        </button>
      </div>
    );
  }
  
  if (!user) {
    return (
      <div className="bg-white shadow rounded-lg p-6 text-center">
        <h2 className="text-xl font-semibold mb-4">User Profile</h2>
        <p className="text-gray-500">No profile data available</p>
      </div>
    );
  }
  
  return (
    <div className="bg-white shadow rounded-lg p-6">
      <div className="flex flex-col items-center">
        {user.image ? (
          <img 
            src={user.image} 
            alt={user.name || 'User'} 
            className="h-24 w-24 rounded-full object-cover mb-4"
          />
        ) : (
          <div className="h-24 w-24 rounded-full bg-blue-100 flex items-center justify-center mb-4">
            <span className="text-2xl font-bold text-blue-500">
              {user.name ? user.name.charAt(0).toUpperCase() : 'U'}
            </span>
          </div>
        )}
        
        <h2 className="text-xl font-semibold">{user.name}</h2>
        <p className="text-gray-500 mb-4">{user.email}</p>
        
        <div className="w-full p-4 bg-gray-50 rounded-md mb-4">
          <h3 className="font-medium mb-2">Account Type</h3>
          <p className="capitalize">{user.role || 'User'}</p>
        </div>
        
        {user.role === 'parent' && user.studentIds && user.studentIds.length > 0 && (
          <div className="w-full p-4 bg-gray-50 rounded-md mb-4">
            <h3 className="font-medium mb-2">Linked Students</h3>
            <p>{user.studentIds.length} student(s)</p>
          </div>
        )}
        
        {user.role === 'student' && user.parentIds && user.parentIds.length > 0 && (
          <div className="w-full p-4 bg-gray-50 rounded-md mb-4">
            <h3 className="font-medium mb-2">Linked Parents</h3>
            <p>{user.parentIds.length} parent(s)</p>
          </div>
        )}
        
        <button 
          onClick={() => onUpdateProfile({ name: user.name })}
          className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-md"
        >
          Edit Profile
        </button>
      </div>
    </div>
  );
} 