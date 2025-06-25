'use client';

import React, { useState, useEffect } from 'react';
import { useUserContext } from '@/features/user/context/UserContext';

export function ProfileForm() {
  const { profile, updateProfile, isLoading, error } = useUserContext();
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    image: ''
  });
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    if (profile) {
      setFormData({
        name: profile.name || '',
        email: profile.email || '',
        image: profile.image || ''
      });
    }
  }, [profile]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSuccess(false);
    
    const result = await updateProfile(formData);
    if (result) {
      setSuccess(true);
      // Hide success message after 3 seconds
      setTimeout(() => setSuccess(false), 3000);
    }
  };

  if (!profile) {
    return <div className="p-4">Loading...</div>;
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4 p-4 max-w-lg mx-auto">
      <h2 className="text-2xl font-bold mb-6">Edit Profile</h2>
      
      {success && (
        <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded">
          Profile updated successfully!
        </div>
      )}
      
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}
      
      <div>
        <label htmlFor="name" className="block text-sm font-medium mb-1">
          Name
        </label>
        <input
          type="text"
          id="name"
          name="name"
          value={formData.name}
          onChange={handleChange}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          required
        />
      </div>
      
      <div>
        <label htmlFor="email" className="block text-sm font-medium mb-1">
          Email
        </label>
        <input
          type="email"
          id="email"
          name="email"
          value={formData.email}
          onChange={handleChange}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          required
        />
      </div>
      
      <div>
        <label htmlFor="image" className="block text-sm font-medium mb-1">
          Profile Image URL
        </label>
        <input
          type="url"
          id="image"
          name="image"
          value={formData.image}
          onChange={handleChange}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>
      
      <div className="mt-6">
        <button
          type="submit"
          disabled={isLoading}
          className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:bg-blue-300"
        >
          {isLoading ? 'Saving...' : 'Save Changes'}
        </button>
      </div>
    </form>
  );
} 