'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useAuth } from '@/hooks/useAuth';

export function PasswordResetForm() {
  const { requestPasswordReset, isLoading, error } = useAuth();
  const [email, setEmail] = useState('');
  const [submitted, setSubmitted] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setEmail(e.target.value);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);
    
    if (!email.trim()) {
      setFormError('Email is required');
      return;
    }
    
    const success = await requestPasswordReset(email);
    if (success) {
      setSubmitted(true);
    }
  };

  if (submitted) {
    return (
      <div className="w-full max-w-md mx-auto bg-white p-8 rounded-lg shadow-md">
        <h2 className="text-2xl font-bold text-center mb-6">Reset Your Password</h2>
        
        <div className="p-4 bg-green-50 border border-green-200 text-green-800 rounded mb-6">
          <p>
            If an account exists for <strong>{email}</strong>, we've sent instructions
            for resetting your password. Please check your email.
          </p>
        </div>
        
        <div className="text-center">
          <Link href="/login" className="font-medium text-blue-600 hover:text-blue-500">
            Return to login
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full max-w-md mx-auto bg-white p-8 rounded-lg shadow-md">
      <h2 className="text-2xl font-bold text-center mb-6">Reset Your Password</h2>
      
      <p className="mb-6 text-gray-600">
        Enter your email address and we'll send you a link to reset your password.
      </p>
      
      {(error || formError) && (
        <div className="mb-4 p-3 bg-red-50 border border-red-300 text-red-900 rounded">
          {formError || error}
        </div>
      )}
      
      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label htmlFor="email" className="block text-sm font-medium text-gray-700">
            Email
          </label>
          <input
            id="email"
            name="email"
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={handleChange}
            disabled={isLoading}
            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
        
        <div>
          <button
            type="submit"
            disabled={isLoading}
            className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
          >
            {isLoading ? 'Sending...' : 'Send reset link'}
          </button>
        </div>
        
        <div className="text-center text-sm">
          <Link href="/login" className="font-medium text-blue-600 hover:text-blue-500">
            Return to login
          </Link>
        </div>
      </form>
    </div>
  );
} 