/**
 * Profile Service Interface
 * 
 * Defines the contract for profile-related operations.
 * This follows the Interface Segregation Principle by including
 * only methods related to user profiles.
 */

import { User } from './auth.service';

export interface ProfileExtended extends User {
  bio?: string;
  avatar?: string;
  phone?: string;
  address?: Address;
  education?: Education[];
  experience?: Experience[];
  skills?: string[];
  interests?: string[];
  socialLinks?: SocialLink[];
}

export interface Address {
  street: string;
  city: string;
  state: string;
  zipCode: string;
  country: string;
}

export interface Education {
  id: string;
  institution: string;
  degree: string;
  fieldOfStudy: string;
  startDate: string;
  endDate?: string;
  current: boolean;
  description?: string;
  gpa?: number;
}

export interface Experience {
  id: string;
  organization: string;
  position: string;
  startDate: string;
  endDate?: string;
  current: boolean;
  description?: string;
  location?: string;
}

export interface SocialLink {
  platform: 'linkedin' | 'twitter' | 'facebook' | 'instagram' | 'github' | 'other';
  url: string;
  name?: string;
}

export interface ProfileUpdate {
  firstName?: string;
  lastName?: string;
  bio?: string;
  avatar?: string;
  phone?: string;
  address?: Address;
  education?: Education[];
  experience?: Experience[];
  skills?: string[];
  interests?: string[];
  socialLinks?: SocialLink[];
}

export interface IProfileService {
  /**
   * Get the current user's extended profile
   * @returns Promise resolving to the user's profile
   */
  getProfile(): Promise<ProfileExtended>;
  
  /**
   * Update the current user's profile
   * @param updates Profile updates to apply
   * @returns Promise resolving to the updated profile
   */
  updateProfile(updates: ProfileUpdate): Promise<ProfileExtended>;
  
  /**
   * Upload a profile avatar image
   * @param file Image file to upload
   * @returns Promise resolving to the avatar URL
   */
  uploadAvatar(file: File): Promise<string>;
  
  /**
   * Add a new education item to the user's profile
   * @param education Education item to add
   * @returns Promise resolving to the added education item with generated ID
   */
  addEducation(education: Omit<Education, 'id'>): Promise<Education>;
  
  /**
   * Update an existing education item
   * @param id Education item ID
   * @param updates Updates to apply
   * @returns Promise resolving to the updated education item
   */
  updateEducation(id: string, updates: Partial<Omit<Education, 'id'>>): Promise<Education>;
  
  /**
   * Remove an education item
   * @param id Education item ID
   * @returns Promise that resolves when the item is removed
   */
  removeEducation(id: string): Promise<void>;
  
  /**
   * Add a new experience item to the user's profile
   * @param experience Experience item to add
   * @returns Promise resolving to the added experience item with generated ID
   */
  addExperience(experience: Omit<Experience, 'id'>): Promise<Experience>;
  
  /**
   * Update an existing experience item
   * @param id Experience item ID
   * @param updates Updates to apply
   * @returns Promise resolving to the updated experience item
   */
  updateExperience(id: string, updates: Partial<Omit<Experience, 'id'>>): Promise<Experience>;
  
  /**
   * Remove an experience item
   * @param id Experience item ID
   * @returns Promise that resolves when the item is removed
   */
  removeExperience(id: string): Promise<void>;
  
  /**
   * Get educational and professional recommendations
   * @returns Promise resolving to personalized recommendations
   */
  getRecommendations(): Promise<{
    education: string[];
    career: string[];
    skills: string[];
  }>;
} 