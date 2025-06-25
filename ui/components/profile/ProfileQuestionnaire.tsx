'use client';

import React, { useState } from 'react';
import { useUserContext } from '@/features/user/context/UserContext';

interface Question {
  id: string;
  text: string;
  answer?: string;
}

export function ProfileQuestionnaire() {
  const { profile, updateProfile } = useUserContext();
  const [questions] = useState<Question[]>([
    {
      id: '1',
      text: 'What are your main interests and hobbies?',
    },
    {
      id: '2',
      text: 'What are your career goals?',
    },
    {
      id: '3',
      text: 'What skills would you like to develop?',
    }
  ]);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);

  const handleAnswerChange = (questionId: string, answer: string) => {
    setAnswers(prev => ({
      ...prev,
      [questionId]: answer
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setSuccess(false);

    try {
      // In a real app, you would save the answers to your backend
      // For now, we'll just simulate a successful submission
      await new Promise(resolve => setTimeout(resolve, 1000));
      setSuccess(true);
    } catch (error) {
      console.error('Failed to submit answers:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!profile) {
    return <div className="p-4">Loading...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="border-b pb-4">
        <h2 className="text-2xl font-semibold text-gray-800">Profile Questionnaire</h2>
        <p className="text-gray-600 mt-1">
          Help us understand you better by answering these questions.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {questions.map((question) => (
          <div key={question.id} className="space-y-2">
            <label
              htmlFor={question.id}
              className="block text-sm font-medium text-gray-700"
            >
              {question.text}
            </label>
            <textarea
              id={question.id}
              value={answers[question.id] || ''}
              onChange={(e) => handleAnswerChange(question.id, e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              rows={3}
              placeholder="Type your answer here..."
            />
          </div>
        ))}

        {success && (
          <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded">
            Your answers have been saved successfully!
          </div>
        )}

        <div className="flex justify-end">
          <button
            type="submit"
            disabled={isSubmitting}
            className="bg-blue-600 text-white py-2 px-6 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:bg-blue-300"
          >
            {isSubmitting ? 'Saving...' : 'Save Answers'}
          </button>
        </div>
      </form>
    </div>
  );
} 