import React, { useState } from 'react';
import { useProfile } from '../lib/contexts/ProfileContext';
import { ProfileSection } from '../lib/services/types';

export function ProfileBuilder() {
  const { state, loading, error, sendAnswer, uploadDocument, submitReview } = useProfile();
  const [currentAnswer, setCurrentAnswer] = useState('');

  if (loading) {
    return <div>Loading profile builder...</div>;
  }

  if (error) {
    return <div>Error: {error.message}</div>;
  }

  if (!state) {
    return <div>No profile state available</div>;
  }

  const handleSubmitAnswer = (e: React.FormEvent) => {
    e.preventDefault();
    if (currentAnswer.trim()) {
      sendAnswer(currentAnswer);
      setCurrentAnswer('');
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const content = await file.text();
      await uploadDocument(content, state.current_section);
    }
  };

  const renderSection = (section: ProfileSection) => {
    const sectionData = state.sections[section];
    return (
      <div key={section} className="mb-8">
        <h2 className="text-2xl font-bold mb-4">{section}</h2>
        <div className="bg-gray-50 p-4 rounded">
          <p>Status: {sectionData.status}</p>
          {sectionData.recommendations && (
            <div className="mt-4">
              <h3 className="font-semibold">Recommendations:</h3>
              <ul className="list-disc pl-5">
                {sectionData.recommendations.map((rec, i) => (
                  <li key={i}>{rec.description}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-8">Student Profile Builder</h1>
      
      {/* Current Section */}
      <div className="mb-8">
        <h2 className="text-xl font-semibold mb-4">Current Section: {state.current_section}</h2>
        
        {/* Questions */}
        {state.current_questions.length > 0 && (
          <div className="mb-4">
            <h3 className="font-medium mb-2">Current Questions:</h3>
            <ul className="list-disc pl-5">
              {state.current_questions.map((q, i) => (
                <li key={i}>{q}</li>
              ))}
            </ul>
          </div>
        )}

        {/* Answer Form */}
        <form onSubmit={handleSubmitAnswer} className="mb-4">
          <textarea
            value={currentAnswer}
            onChange={(e) => setCurrentAnswer(e.target.value)}
            className="w-full p-2 border rounded"
            rows={4}
            placeholder="Enter your answer..."
          />
          <button
            type="submit"
            className="mt-2 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            Submit Answer
          </button>
        </form>

        {/* File Upload */}
        <div className="mb-4">
          <input
            type="file"
            onChange={handleFileUpload}
            className="block w-full text-sm text-gray-500
              file:mr-4 file:py-2 file:px-4
              file:rounded-full file:border-0
              file:text-sm file:font-semibold
              file:bg-blue-50 file:text-blue-700
              hover:file:bg-blue-100"
          />
        </div>
      </div>

      {/* Review Requests */}
      {state.review_requests.length > 0 && (
        <div className="mb-8">
          <h2 className="text-xl font-semibold mb-4">Review Requests</h2>
          {state.review_requests.map((request, i) => (
            <div key={i} className="bg-yellow-50 p-4 rounded mb-4">
              <h3 className="font-medium mb-2">Section: {request.section}</h3>
              <p>Quality Score: {request.quality_score}</p>
              <div className="mt-4">
                <button
                  onClick={() => submitReview(request.section, { approved: true })}
                  className="mr-2 px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600"
                >
                  Approve
                </button>
                <button
                  onClick={() => submitReview(request.section, { approved: false })}
                  className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600"
                >
                  Reject
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* All Sections */}
      <div className="mb-8">
        <h2 className="text-xl font-semibold mb-4">All Sections</h2>
        {Object.values(ProfileSection).map(renderSection)}
      </div>

      {/* Summary */}
      {state.summary && (
        <div className="bg-gray-50 p-6 rounded">
          <h2 className="text-xl font-semibold mb-4">Profile Summary</h2>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <h3 className="font-medium mb-2">Strengths</h3>
              <ul className="list-disc pl-5">
                {state.summary.strengths.map((s, i) => (
                  <li key={i}>{s}</li>
                ))}
              </ul>
            </div>
            <div>
              <h3 className="font-medium mb-2">Areas for Improvement</h3>
              <ul className="list-disc pl-5">
                {state.summary.areas_for_improvement.map((a, i) => (
                  <li key={i}>{a}</li>
                ))}
              </ul>
            </div>
            <div>
              <h3 className="font-medium mb-2">Unique Selling Points</h3>
              <ul className="list-disc pl-5">
                {state.summary.unique_selling_points.map((p, i) => (
                  <li key={i}>{p}</li>
                ))}
              </ul>
            </div>
            <div>
              <h3 className="font-medium mb-2">Overall Quality</h3>
              <p>{state.summary.overall_quality.toFixed(2)}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
} 