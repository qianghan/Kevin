'use client';

import React from 'react';
import { useUserContext } from '@/features/user/context/UserContext';

export function ProfileCompleteness() {
  const { profile } = useUserContext();

  const calculateCompleteness = () => {
    if (!profile) return 0;

    const requiredFields = ['name', 'email', 'image'];
    const filledFields = requiredFields.filter(field => {
      const value = profile[field as keyof typeof profile];
      return value !== undefined && value !== null && value !== '';
    });

    return Math.round((filledFields.length / requiredFields.length) * 100);
  };

  const completeness = calculateCompleteness();

  const getSuggestions = () => {
    if (!profile) return ['Complete your profile to get started'];

    const suggestions = [];
    if (!profile.name) suggestions.push('Add your name');
    if (!profile.email) suggestions.push('Add your email');
    if (!profile.image) suggestions.push('Add a profile picture');

    return suggestions.length > 0 ? suggestions : ['Your profile is complete!'];
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-4">Profile Completeness</h3>
      
      <div className="mb-4">
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm text-gray-600">Progress</span>
          <span className="text-sm font-medium text-gray-900">{completeness}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
            style={{ width: `${completeness}%` }}
          />
        </div>
      </div>

      <div>
        <h4 className="text-sm font-medium text-gray-900 mb-2">Suggestions</h4>
        <ul className="space-y-2">
          {getSuggestions().map((suggestion, index) => (
            <li key={index} className="flex items-center text-sm text-gray-600">
              <svg
                className={`w-4 h-4 mr-2 ${
                  suggestion === 'Your profile is complete!'
                    ? 'text-green-500'
                    : 'text-blue-500'
                }`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                xmlns="http://www.w3.org/2000/svg"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  d={
                    suggestion === 'Your profile is complete!'
                      ? 'M5 13l4 4L19 7'
                      : 'M12 6v6m0 0v6m0-6h6m-6 0H6'
                  }
                />
              </svg>
              {suggestion}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
} 