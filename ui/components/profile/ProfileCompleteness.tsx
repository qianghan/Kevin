'use client';

import React from 'react';
import { useUserProfile } from '@/hooks/useUserProfile';

export function ProfileCompleteness() {
  const { completeness, user } = useUserProfile();
  
  // Color based on completeness level
  const getColor = () => {
    if (completeness < 30) return 'bg-red-500';
    if (completeness < 70) return 'bg-yellow-500';
    return 'bg-green-500';
  };
  
  // Suggestions for profile completion
  const getSuggestions = (): string[] => {
    const suggestions: string[] = [];
    
    if (!user) return suggestions;
    
    if (!user.bio) {
      suggestions.push('Add a bio to tell others about yourself');
    }
    
    if (!user.phone) {
      suggestions.push('Add your phone number for better communication');
    }
    
    if (!user.address) {
      suggestions.push('Add your address for location-based services');
    }
    
    if (!user.profilePicture) {
      suggestions.push('Upload a profile picture to personalize your account');
    }
    
    return suggestions;
  };
  
  return (
    <div className="p-4 max-w-lg mx-auto">
      <h2 className="text-2xl font-bold mb-4">Profile Completeness</h2>
      
      <div className="mb-6">
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm font-medium text-gray-700">
            {completeness}% Complete
          </span>
          <span className="text-sm font-medium text-gray-500">
            {completeness < 100 ? 'In Progress' : 'Complete!'}
          </span>
        </div>
        
        <div className="w-full bg-gray-200 rounded-full h-2.5">
          <div 
            className={`h-2.5 rounded-full ${getColor()}`} 
            style={{ width: `${completeness}%` }}
          ></div>
        </div>
      </div>
      
      {completeness < 100 && (
        <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
          <h3 className="text-lg font-medium text-blue-800 mb-2">
            Complete your profile
          </h3>
          <p className="text-sm text-blue-700 mb-4">
            Complete your profile to get the most out of the platform and help others know you better.
          </p>
          
          {getSuggestions().length > 0 && (
            <ul className="list-disc pl-5 text-sm text-blue-700 space-y-1">
              {getSuggestions().map((suggestion, i) => (
                <li key={i}>{suggestion}</li>
              ))}
            </ul>
          )}
        </div>
      )}
      
      {completeness === 100 && (
        <div className="bg-green-50 border border-green-200 rounded-md p-4">
          <h3 className="text-lg font-medium text-green-800 mb-2">
            Profile complete!
          </h3>
          <p className="text-sm text-green-700">
            Your profile is fully completed. Thank you for providing all your information.
          </p>
        </div>
      )}
    </div>
  );
} 