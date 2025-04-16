'use client';

import React from 'react';

interface ProfileQuestionnaireProps {
  questions: string[];
  userAnswer: string;
  onAnswerChange: (answer: string) => void;
  onSubmit: (e: React.FormEvent) => void;
}

const ProfileQuestionnaire: React.FC<ProfileQuestionnaireProps> = ({
  questions,
  userAnswer,
  onAnswerChange,
  onSubmit
}) => {
  if (!questions || questions.length === 0) {
    return (
      <div className="bg-yellow-50 border border-yellow-100 p-4 rounded-md">
        <h3 className="font-medium text-yellow-700">No questions available</h3>
        <p className="text-yellow-600 mt-1">
          Select a different section or upload a document to generate questions.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="bg-white border rounded-md p-4">
        <h3 className="font-medium mb-3">Current Questions</h3>
        <ul className="list-disc pl-5 space-y-2">
          {questions.map((question, index) => (
            <li key={index} className="text-gray-700">
              {question}
            </li>
          ))}
        </ul>
      </div>

      <form onSubmit={onSubmit} className="mt-4">
        <h3 className="font-medium mb-2">Your Answer</h3>
        <textarea
          value={userAnswer}
          onChange={(e) => onAnswerChange(e.target.value)}
          className="w-full p-3 border rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          rows={5}
          placeholder="Type your answer here..."
        ></textarea>
        
        <div className="mt-3 flex justify-end">
          <button
            type="submit"
            disabled={!userAnswer.trim()}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Submit Answer
          </button>
        </div>
      </form>
    </div>
  );
};

export default ProfileQuestionnaire; 