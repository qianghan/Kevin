'use client';

import React from 'react';
import UserInterface from '@/features/user/UserInterface';
import { PreferenceForm } from '@/features/user/components/PreferenceForm';
import { AccountForm } from '@/features/user/components/AccountForm';
import { SecurityForm } from '@/features/user/components/SecurityForm';

export default function SettingsPage() {
  return (
    <div className="container mx-auto px-4 py-6">
      <header className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Account Settings</h1>
        <p className="text-gray-800 mt-2">
          Manage your profile and preferences.
        </p>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="md:col-span-2 space-y-6">
          <UserInterface 
            accountForm={AccountForm}
            preferenceForm={PreferenceForm}
            securityForm={SecurityForm}
          />
        </div>
        
        <div className="bg-white shadow-md rounded-lg p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Help & Support</h2>
          <p className="text-gray-600 mb-4">
            Having trouble with your account settings? Contact our support team for assistance.
          </p>
          <a 
            href="mailto:support@kevin.ai" 
            className="text-blue-600 hover:text-blue-800 font-medium"
          >
            Contact Support
          </a>
        </div>
      </div>
    </div>
  );
} 