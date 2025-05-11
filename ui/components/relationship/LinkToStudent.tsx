'use client';

import { useState } from 'react';
import { useRelationships } from '@/hooks/useRelationships';
import { Button } from '@/components/ui/button';

/**
 * Component for parents to link to a student account
 */
export function LinkToStudent() {
  const { linkToStudent, hasParentRole } = useRelationships();
  
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!email) {
      setError('Email is required');
      return;
    }
    
    try {
      setIsSubmitting(true);
      setError(null);
      setSuccess(null);
      
      await linkToStudent(email, message);
      
      setSuccess(`Invitation sent to ${email}`);
      setEmail('');
      setMessage('');
    } catch (err: any) {
      setError(err.message || 'Failed to send invitation');
    } finally {
      setIsSubmitting(false);
    }
  };
  
  if (!hasParentRole) {
    return (
      <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-4">
        <p className="text-yellow-700">
          Only parents can link to student accounts.
        </p>
      </div>
    );
  }
  
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-xl font-semibold mb-4">Link to a Student Account</h2>
      
      {error && (
        <div className="bg-red-50 border-l-4 border-red-400 p-4 mb-4">
          <p className="text-red-700">{error}</p>
        </div>
      )}
      
      {success && (
        <div className="bg-green-50 border-l-4 border-green-400 p-4 mb-4">
          <p className="text-green-700">{success}</p>
        </div>
      )}
      
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
            Student Email
          </label>
          <input
            type="email"
            id="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            placeholder="student@example.com"
            disabled={isSubmitting}
          />
        </div>
        
        <div>
          <label htmlFor="message" className="block text-sm font-medium text-gray-700 mb-1">
            Message (Optional)
          </label>
          <textarea
            id="message"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            rows={3}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            placeholder="Include a personal message in the invitation"
            disabled={isSubmitting}
          />
        </div>
        
        <Button
          type="submit"
          disabled={isSubmitting || !email}
          className="w-full"
        >
          {isSubmitting ? 'Sending Invitation...' : 'Send Invitation'}
        </Button>
      </form>
      
      <div className="mt-4 text-sm text-gray-500">
        <p>
          The student will receive an invitation to connect. Once accepted,
          you will be able to view their academic information and progress.
        </p>
      </div>
    </div>
  );
} 