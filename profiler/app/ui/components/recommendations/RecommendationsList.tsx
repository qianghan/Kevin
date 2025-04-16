'use client';

import React from 'react';
import { Recommendation } from '../../lib/services/types';

interface RecommendationsListProps {
  recommendations: Recommendation[];
  onRefresh: () => void;
}

const RecommendationsList: React.FC<RecommendationsListProps> = ({ 
  recommendations,
  onRefresh
}) => {
  // Function to get badge color based on score
  const getScoreBadgeColor = (score: number) => {
    if (score >= 0.8) return 'bg-green-100 text-green-800';
    if (score >= 0.6) return 'bg-blue-100 text-blue-800';
    if (score >= 0.4) return 'bg-yellow-100 text-yellow-800';
    return 'bg-red-100 text-red-800';
  };

  return (
    <div className="bg-white rounded-lg shadow-sm p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-semibold text-gray-800">Recommendations</h2>
        <button 
          onClick={onRefresh}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
        >
          Refresh Recommendations
        </button>
      </div>

      {recommendations.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 rounded-lg border border-gray-200">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12 mx-auto text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <h3 className="mt-2 text-lg font-medium text-gray-900">No recommendations yet</h3>
          <p className="mt-1 text-gray-500">
            Complete more sections of your profile to get personalized recommendations.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-6">
          {recommendations.map((recommendation) => (
            <div 
              key={recommendation.id} 
              className="border rounded-lg p-5 hover:shadow-md transition-shadow"
            >
              <div className="flex justify-between mb-2">
                <h3 className="text-lg font-medium text-gray-900">{recommendation.title}</h3>
                <span className={`px-2 py-1 text-xs font-semibold rounded-full ${getScoreBadgeColor(recommendation.score)}`}>
                  Match: {Math.round(recommendation.score * 100)}%
                </span>
              </div>
              <p className="text-gray-600 mb-4">{recommendation.description}</p>
              
              {recommendation.match_reasons && recommendation.match_reasons.length > 0 && (
                <div className="mb-3">
                  <h4 className="text-sm font-medium text-gray-700 mb-1">Why this is a good fit:</h4>
                  <ul className="list-disc pl-5 text-sm text-gray-600 space-y-1">
                    {recommendation.match_reasons.map((reason, index) => (
                      <li key={index}>{reason}</li>
                    ))}
                  </ul>
                </div>
              )}
              
              {recommendation.requirements && recommendation.requirements.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-1">Requirements:</h4>
                  <ul className="list-disc pl-5 text-sm text-gray-600 space-y-1">
                    {recommendation.requirements.map((requirement, index) => (
                      <li key={index}>{requirement}</li>
                    ))}
                  </ul>
                </div>
              )}
              
              <div className="flex justify-end mt-4">
                <span className="px-2 py-1 text-xs inline-flex items-center rounded-full bg-gray-100 text-gray-800">
                  {recommendation.category}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default RecommendationsList; 