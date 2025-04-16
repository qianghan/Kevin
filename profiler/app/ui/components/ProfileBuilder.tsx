'use client';

import React, { useState, useEffect } from 'react';
import { useProfile } from '../lib/contexts/ProfileContext';
import { ProfileSection, ProfileStatus } from '../lib/services/types';

// Components
import ProfileNavigation from './profile/ProfileNavigation';
import ProfileQuestionnaire from './profile/ProfileQuestionnaire';
import DocumentsSection from './profile/DocumentsSection';
import ConnectionStatus from './shared/ConnectionStatus';
import RecommendationsList from './recommendations/RecommendationsList';

// Define valid profile sections
const PROFILE_SECTIONS: ProfileSection[] = ['academic', 'extracurricular', 'personal', 'essays'];

export default function ProfileBuilder() {
  const { 
    state, 
    loading, 
    error, 
    connectionStatus,
    recommendations,
    sendAnswer, 
    submitReview,
    navigateToSection,
    refreshRecommendations 
  } = useProfile();
  
  const [activeView, setActiveView] = useState<'profile' | 'documents' | 'recommendations'>('profile');
  const [userAnswer, setUserAnswer] = useState('');
  
  // Update effect to check for state and sections before calling refreshRecommendations
  useEffect(() => {
    if (state && state.sections && Object.keys(state.sections).length > 0) {
      refreshRecommendations();
    }
  }, [state, refreshRecommendations]);

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

  const handleSectionClick = (section: ProfileSection) => {
    navigateToSection(section);
  };
  
  const handleSwitchView = (view: 'profile' | 'documents' | 'recommendations') => {
    setActiveView(view);
  };

  // Add null/undefined checks for state.sections
  const completedSectionsCount = state?.sections 
    ? Object.values(state.sections).filter(section => section.status === 'completed').length 
    : 0;
  
  const totalSections = PROFILE_SECTIONS.length;
  const progress = Math.round((completedSectionsCount / totalSections) * 100);

  return (
    <div className="max-w-6xl mx-auto p-4">
      {/* Header with connection status */}
      <div className="flex justify-between items-center mb-6 border-b pb-4">
        <h1 className="text-2xl font-bold">Profile Builder</h1>
        <ConnectionStatus status={connectionStatus} />
      </div>
      
      {/* Progress bar */}
      <div className="w-full bg-gray-200 rounded-full h-4 mb-6">
        <div 
          className="bg-blue-600 h-4 rounded-full transition-all duration-500 ease-in-out"
          style={{ width: `${progress}%` }}
        />
        <p className="text-sm text-gray-600 mt-1">
          {completedSectionsCount} of {totalSections} sections completed ({progress}%)
        </p>
      </div>
      
      {/* View selector tabs */}
      <div className="flex border-b mb-6">
        <button
          className={`px-4 py-2 ${activeView === 'profile' ? 'border-b-2 border-blue-500 text-blue-500' : 'text-gray-500'}`}
          onClick={() => handleSwitchView('profile')}
        >
          Build Profile
        </button>
        <button
          className={`px-4 py-2 ${activeView === 'documents' ? 'border-b-2 border-blue-500 text-blue-500' : 'text-gray-500'}`}
          onClick={() => handleSwitchView('documents')}
        >
          Documents
        </button>
        <button
          className={`px-4 py-2 ${activeView === 'recommendations' ? 'border-b-2 border-blue-500 text-blue-500' : 'text-gray-500'}`}
          onClick={() => handleSwitchView('recommendations')}
        >
          View Recommendations {recommendations.length > 0 && `(${recommendations.length})`}
        </button>
      </div>
      
      {activeView === 'profile' && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          {/* Left sidebar with section navigation */}
          <div className="md:col-span-1">
            <h2 className="font-semibold mb-3 text-lg">Profile Sections</h2>
            <ProfileNavigation 
              sections={state?.sections || {}}
              currentSection={state?.current_section || null}
              onSectionClick={handleSectionClick}
            />
          </div>
          
          {/* Main content area */}
          <div className="md:col-span-3">
            <div className="bg-white shadow-sm rounded-lg p-6">
              <h2 className="text-xl font-semibold mb-4 capitalize">
                {state.current_section || 'Select a section'}
              </h2>
              
              {/* Questions and answers */}
              <div className="mb-6">
                <ProfileQuestionnaire
                  questions={state.current_questions}
                  userAnswer={userAnswer}
                  onAnswerChange={setUserAnswer}
                  onSubmit={handleSubmitAnswer}
                />
              </div>
            </div>
          </div>
        </div>
      )}
      
      {activeView === 'documents' && (
        <div className="bg-white shadow-sm rounded-lg p-6">
          <DocumentsSection />
        </div>
      )}
      
      {activeView === 'recommendations' && (
        <RecommendationsList 
          recommendations={recommendations}
          onRefresh={refreshRecommendations}
        />
      )}
    </div>
  );
} 