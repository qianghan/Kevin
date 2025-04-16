'use client';

import React from 'react';
import { ProfileSection, ProfileStatus } from '../../lib/services/types';

interface ProfileNavigationProps {
  sections: {
    [key in ProfileSection]?: {
      status: ProfileStatus;
      [key: string]: any;
    };
  };
  currentSection: ProfileSection | null;
  onSectionClick: (section: ProfileSection) => void;
}

const ProfileNavigation: React.FC<ProfileNavigationProps> = ({
  sections,
  currentSection,
  onSectionClick
}) => {
  // Function to get status color
  const getStatusColor = (status: ProfileStatus) => {
    switch (status) {
      case 'completed':
        return 'text-green-500 border-green-500';
      case 'in_progress':
        return 'text-blue-500 border-blue-500';
      case 'needs_review':
        return 'text-yellow-500 border-yellow-500';
      default:
        return 'text-gray-400 border-gray-300';
    }
  };

  // Function to get status icon
  const getStatusIcon = (status: ProfileStatus) => {
    switch (status) {
      case 'completed':
        return '✓';
      case 'in_progress':
        return '⟳';
      case 'needs_review':
        return '!';
      default:
        return '';
    }
  };

  return (
    <nav className="flex flex-col space-y-2">
      {Object.entries(sections || {}).map(([section, data]) => (
        <button
          key={section}
          onClick={() => onSectionClick(section as ProfileSection)}
          className={`
            flex justify-between items-center p-3 rounded-md border text-left
            ${currentSection === section ? 'border-blue-500 bg-blue-50' : 'hover:bg-gray-50'}
            ${data && getStatusColor(data.status)}
          `}
        >
          <span className="capitalize font-medium">{section}</span>
          {data && data.status !== 'not_started' && (
            <span className="text-sm font-bold">{getStatusIcon(data.status)}</span>
          )}
        </button>
      ))}
    </nav>
  );
};

export default ProfileNavigation; 