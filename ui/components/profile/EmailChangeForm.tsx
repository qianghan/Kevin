'use client';

import React, { useState } from 'react';
import { useUserProfile } from '@/hooks/useUserProfile';
import { EmailChangeRequest } from '@/lib/interfaces/services/userProfile.service';

export function EmailChangeForm() {
  const { user, requestEmailChange, isLoading, error } = useUserProfile();
  const [formData, setFormData] = useState<EmailChangeRequest>({
    newEmail: '',
    password: ''
  });
  const [submitted, setSubmitted] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    
    // Clear errors on input change
    setFormError(null);
  };

  const validateEmail = (email: string): boolean => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Reset states
    setFormError(null);
    setSubmitted(false);
    
    // Validate email
    if (!validateEmail(formData.newEmail)) {
      setFormError('Please enter a valid email address');
      return;
    }
    
    // Check if new email is same as current email
    if (user?.email === formData.newEmail) {
      setFormError('New email must be different from your current email');
      return;
    }
    
    // Validate password
    if (!formData.password || formData.password.length < 6) {
      setFormError('Please enter your current password (at least 6 characters)');
      return;
    }
    
    const result = await requestEmailChange(formData);
    if (result) {
      setSubmitted(true);
      setFormData({ newEmail: '', password: '' });
    }
  };

  if (submitted) {
    return (
      <div className="p-4 max-w-md mx-auto">
        <div className="bg-green-50 border border-green-200 rounded-md p-6 text-center">
          <h3 className="text-lg font-medium text-green-800 mb-2">
            Verification Email Sent
          </h3>
          <p className="text-sm text-green-700 mb-4">
            We've sent a verification email to <strong>{formData.newEmail}</strong>.
            Please check your inbox and follow the instructions to complete the email change.
          </p>
          <p className="text-xs text-green-600">
            The verification link will expire in 24 hours.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 max-w-md mx-auto">
      <h2 className="text-2xl font-bold mb-6">Change Email Address</h2>
      
      <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-md">
        <p className="text-sm text-blue-700">
          Your current email address is: <strong>{user?.email}</strong>
        </p>
      </div>
      
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}
      
      {formError && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {formError}
        </div>
      )}
      
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="newEmail" className="block text-sm font-medium mb-1">
            New Email Address
          </label>
          <input
            type="email"
            id="newEmail"
            name="newEmail"
            value={formData.newEmail}
            onChange={handleChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            required
          />
        </div>
        
        <div>
          <label htmlFor="password" className="block text-sm font-medium mb-1">
            Current Password
          </label>
          <input
            type="password"
            id="password"
            name="password"
            value={formData.password}
            onChange={handleChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            required
          />
          <p className="mt-1 text-xs text-gray-500">
            For security, please enter your current password to confirm this change
          </p>
        </div>
        
        <div className="mt-6">
          <button
            type="submit"
            disabled={isLoading}
            className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:bg-blue-300"
          >
            {isLoading ? 'Processing...' : 'Change Email Address'}
          </button>
        </div>
      </form>
    </div>
  );
} 