import React, { useState } from 'react';
import { useProfile } from '../lib/contexts/ProfileContext';
import { ProfileSection, ProfileState } from '../lib/services/types';

// Define valid profile sections
const PROFILE_SECTIONS = ['education', 'skills', 'experience', 'projects'];

export default function ProfileBuilder() {
  const { state, loading, error, sendAnswer, uploadDocument, submitReview } = useProfile();
  const [userAnswer, setUserAnswer] = useState('');
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'uploading' | 'success' | 'error'>('idle');
  const [file, setFile] = useState<File | null>(null);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center p-8">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
        <p className="mt-4">Loading your profile...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center p-8">
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative" role="alert">
          <strong className="font-bold">Error!</strong>
          <span className="block sm:inline"> {error.toString()}</span>
        </div>
        <button 
          onClick={() => window.location.reload()} 
          className="mt-4 bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
        >
          Try Again
        </button>
      </div>
    );
  }

  if (!state) {
    return (
      <div className="flex flex-col items-center justify-center p-8">
        <p>No profile data loaded. Please refresh the page.</p>
      </div>
    );
  }

  const handleSubmitAnswer = (e: React.FormEvent) => {
    e.preventDefault();
    if (userAnswer.trim()) {
      sendAnswer(userAnswer);
      setUserAnswer('');
    }
  };

  const handleUploadDocument = () => {
    if (file) {
      setUploadStatus('uploading');
      uploadDocument(file)
        .then(() => setUploadStatus('success'))
        .catch(() => setUploadStatus('error'))
        .finally(() => setFile(null));
    }
  };

  const renderSection = (section: string) => {
    const isActive = state.current_section === section;
    const completed = state.sections?.[section as keyof typeof state.sections]?.status === 'completed';
    
    return (
      <div 
        key={section}
        className={`p-4 border rounded mb-2 ${isActive ? 'border-blue-500' : completed ? 'border-green-500' : 'border-gray-300'}`}
      >
        <div className="flex justify-between items-center">
          <h3 className="font-medium">
            {section.charAt(0).toUpperCase() + section.slice(1)}
          </h3>
          {completed && (
            <span className="text-green-500">✓ Completed</span>
          )}
        </div>
      </div>
    );
  };

  const renderSectionStatus = () => {
    return (
      <div className="mb-6">
        <h3 className="font-semibold mb-2">Section Status</h3>
        {PROFILE_SECTIONS.map(renderSection)}
      </div>
    );
  };

  const renderCurrentQuestions = () => {
    if (!state.current_questions || state.current_questions.length === 0) {
      return (
        <div className="p-4 bg-yellow-100 rounded">
          <p>No questions available at the moment.</p>
        </div>
      );
    }

    return (
      <div className="bg-white border rounded p-4 mb-4">
        <h3 className="font-semibold mb-2">Current Questions:</h3>
        <ul className="list-disc pl-5">
          {state.current_questions.map((question: any, index: number) => (
            <li key={index} className="mb-2">{typeof question === 'string' ? question : question.text}</li>
          ))}
        </ul>
      </div>
    );
  };

  return (
    <div className="max-w-4xl mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">Profile Builder</h1>
      
      {/* Profile Navigation */}
      <div className="flex mb-4 border-b overflow-x-auto">
        {PROFILE_SECTIONS.map((section) => (
          <button
            key={section}
            className={`px-4 py-2 ${state.current_section === section ? 'border-b-2 border-blue-500 text-blue-500' : 'text-gray-500'}`}
            onClick={() => submitReview({ action: 'switch_section', data: { section } })}
          >
            {section.charAt(0).toUpperCase() + section.slice(1)}
          </button>
        ))}
      </div>

      {/* Section Status */}
      {renderSectionStatus()}
      
      {/* Current Questions */}
      {renderCurrentQuestions()}
      
      {/* Document Upload */}
      <div className="mb-6">
        <h3 className="font-semibold mb-2">Upload Document</h3>
        <input 
          type="file" 
          onChange={(e) => setFile(e.target.files?.[0] || null)} 
          className="mb-2"
        />
        <button
          onClick={handleUploadDocument}
          className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-1 px-4 rounded mr-2"
          disabled={uploadStatus === 'uploading' || !file}
        >
          {uploadStatus === 'uploading' ? 'Uploading...' : 'Upload'}
        </button>
        {uploadStatus === 'success' && <span className="text-green-500">Upload successful!</span>}
        {uploadStatus === 'error' && <span className="text-red-500">Upload failed!</span>}
      </div>
      
      {/* Answer Form */}
      <div className="mb-6">
        <h3 className="font-semibold mb-2">Your Answer</h3>
        <form onSubmit={handleSubmitAnswer} className="mb-4">
          <textarea
            value={userAnswer}
            onChange={(e) => setUserAnswer(e.target.value)}
            className="w-full p-2 border rounded"
            rows={4}
            placeholder="Type your answer here..."
          ></textarea>
          <button
            type="submit"
            className="mt-2 bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
            disabled={!userAnswer.trim()}
          >
            Submit Answer
          </button>
        </form>
      </div>
    </div>
  );
} 