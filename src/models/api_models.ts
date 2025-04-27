/**
 * TypeScript interfaces for the API models.
 * 
 * These interfaces define the shared data contracts between frontend and backend.
 */

export type UserRole = 'student' | 'parent' | 'counselor' | 'admin';

export interface NotificationPreference {
  email: boolean;
  push: boolean;
  in_app: boolean;
}

export interface NotificationPreferences {
  chat: NotificationPreference;
  system: NotificationPreference;
  updates: NotificationPreference;
}

export interface UserPreferences {
  theme: 'light' | 'dark' | 'system';
  language: 'en' | 'zh' | 'fr';
  notifications: NotificationPreferences;
}

export interface User {
  id: string;
  firstName: string;
  lastName: string;
  email: string;
  role: UserRole;
  preferences: UserPreferences;
  createdAt: Date;
  updatedAt: Date;
}

export interface ChatMessage {
  id: string;
  conversationId: string;
  content: string;
  role: 'user' | 'assistant';
  createdAt: Date;
  metadata: Record<string, any>;
}

export interface ChatConversation {
  id: string;
  userId: string;
  title: string;
  messages: ChatMessage[];
  createdAt: Date;
  updatedAt: Date;
}

export interface Document {
  id: string;
  userId: string;
  title: string;
  content: string;
  mimeType: string;
  tags: string[];
  createdAt: Date;
  updatedAt: Date;
}

export type ProfileSection = 'education' | 'experience' | 'skills' | 'achievements' | 'interests';

export interface ProfileItem {
  id: string;
  userId: string;
  section: ProfileSection;
  title: string;
  description: string;
  startDate?: Date;
  endDate?: Date;
  metadata: Record<string, any>;
  createdAt: Date;
  updatedAt: Date;
}

export interface Profile {
  userId: string;
  items: Record<ProfileSection, ProfileItem[]>;
  lastUpdated: Date;
}

export type ErrorCode = 'unauthorized' | 'forbidden' | 'not_found' | 'validation_error' | 
  'internal_server_error' | 'service_unavailable';

export interface ErrorResponse {
  code: ErrorCode;
  message: string;
  details?: Record<string, any>;
}

export interface PaginationParams {
  page: number;
  limit: number;
}

export type SortDirection = 'asc' | 'desc';

export interface SortParams {
  field: string;
  direction: SortDirection;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  limit: number;
  pages: number;
} 