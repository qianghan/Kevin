'use client';

import React from 'react';
import { useUserContext } from '@/features/user/context/UserContext';

type ProfileSection = 'general' | 'picture' | 'preferences';

export function ProfileNavigation() {
  const { profile } = useUserContext();
  const [currentSection, setCurrentSection] = React.useState<ProfileSection>('general');

  const sections: ProfileSection[] = ['general', 'picture', 'preferences'];

  const getSectionTitle = (section: ProfileSection) => {
    switch (section) {
      case 'general':
        return 'General Information';
      case 'picture':
        return 'Profile Picture';
      case 'preferences':
        return 'Preferences';
      default:
        return section;
    }
  };

  const getSectionStatus = (section: ProfileSection) => {
    if (!profile) return 'not_started';

    switch (section) {
      case 'general':
        return profile.name && profile.email ? 'completed' : 'in_progress';
      case 'picture':
        return profile.image ? 'completed' : 'in_progress';
      case 'preferences':
        return 'in_progress';
      default:
        return 'not_started';
    }
  };

  return (
    <nav className="flex flex-col space-y-2">
      {sections.map((section) => {
        const status = getSectionStatus(section);
        const isActive = currentSection === section;

        return (
          <button
            key={section}
            onClick={() => setCurrentSection(section)}
            className={`
              flex justify-between items-center p-3 rounded-md border text-left
              ${isActive ? 'border-blue-500 bg-blue-50' : 'hover:bg-gray-50'}
              ${status === 'completed' ? 'border-green-500' : 'border-gray-300'}
            `}
          >
            <span className="capitalize font-medium">{getSectionTitle(section)}</span>
            {status === 'completed' && (
              <svg
                className="w-5 h-5 text-green-500"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                xmlns="http://www.w3.org/2000/svg"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  d="M5 13l4 4L19 7"
                />
              </svg>
            )}
          </button>
        );
      })}
    </nav>
  );
} 