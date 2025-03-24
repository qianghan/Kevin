'use client';

import React, { useState, useEffect } from 'react';
import { UserPreferenceFormProps } from '../types/user-ui.types';

export function PreferenceForm({
  preferences,
  isLoading,
  error,
  onUpdatePreferences
}: UserPreferenceFormProps) {
  const [theme, setTheme] = useState(preferences?.theme || 'system');
  const [emailNotifications, setEmailNotifications] = useState(preferences?.emailNotifications ?? true);
  const [language, setLanguage] = useState(preferences?.language || 'en');
  const [isSaving, setIsSaving] = useState(false);
  const [message, setMessage] = useState('');

  // Update local state when preferences prop changes
  useEffect(() => {
    if (preferences) {
      setTheme(preferences.theme || 'system');
      setEmailNotifications(preferences.emailNotifications ?? true);
      setLanguage(preferences.language || 'en');
    }
  }, [preferences]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    setMessage('');

    try {
      const success = await onUpdatePreferences({
        theme,
        emailNotifications,
        language
      });

      if (success) {
        setMessage('Preferences updated successfully!');
      } else {
        setMessage('Failed to update preferences. Please try again.');
      }
    } catch (err) {
      setMessage('An error occurred while updating preferences.');
      console.error('Preference update error:', err);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="bg-white shadow-md rounded-lg p-6 mb-6">
      <h2 className="text-xl font-bold text-gray-900 mb-4">Preferences</h2>
      
      {message && (
        <div className={`border px-4 py-3 rounded-md text-sm mb-4 ${
          message.includes('successfully') 
            ? 'bg-green-50 border-green-200 text-green-700' 
            : 'bg-red-50 border-red-200 text-red-700'
        }`}>
          {message}
        </div>
      )}
      
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md text-sm mb-4">
          {error}
        </div>
      )}
      
      <form onSubmit={handleSubmit}>
        <div className="mb-4">
          <label htmlFor="theme" className="block text-sm font-medium text-gray-900 mb-1">
            Theme
          </label>
          <select
            id="theme"
            value={theme}
            onChange={(e) => setTheme(e.target.value as 'light' | 'dark' | 'system')}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            disabled={isLoading || isSaving}
          >
            <option value="light">Light</option>
            <option value="dark">Dark</option>
            <option value="system">System Default</option>
          </select>
        </div>
        
        <div className="mb-4">
          <label htmlFor="language" className="block text-sm font-medium text-gray-900 mb-1">
            Language
          </label>
          <select
            id="language"
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            disabled={isLoading || isSaving}
          >
            <option value="en">English</option>
            <option value="es">Spanish</option>
            <option value="fr">French</option>
            <option value="de">German</option>
            <option value="zh">Chinese</option>
          </select>
        </div>
        
        <div className="mb-6">
          <div className="flex items-start">
            <div className="flex items-center h-5">
              <input
                id="emailNotifications"
                type="checkbox"
                checked={emailNotifications}
                onChange={(e) => setEmailNotifications(e.target.checked)}
                className="focus:ring-blue-500 h-4 w-4 text-blue-600 border-gray-300 rounded"
                disabled={isLoading || isSaving}
              />
            </div>
            <div className="ml-3 text-sm">
              <label htmlFor="emailNotifications" className="font-medium text-gray-900">
                Email Notifications
              </label>
              <p className="text-gray-700">Receive email updates about your account activity.</p>
            </div>
          </div>
        </div>
        
        <button
          type="submit"
          disabled={isLoading || isSaving}
          className="w-full sm:w-auto px-4 py-2 bg-blue-600 text-white rounded-md shadow-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          {isSaving ? 'Saving...' : 'Save Preferences'}
        </button>
      </form>
    </div>
  );
} 