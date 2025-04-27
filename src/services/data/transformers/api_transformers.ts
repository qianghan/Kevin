/**
 * Data transformation layer for normalizing API responses to frontend models.
 * 
 * This module provides transformation functions between API and frontend models.
 */

import { 
  User, 
  ChatConversation, 
  ChatMessage,
  Document,
  ProfileItem,
  Profile,
  UserPreferences,
  NotificationPreferences,
  NotificationPreference,
  ProfileSection
} from '../../../models/api_models';

// API response types (snake_case)
export interface ApiUser {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
  role: string;
  preferences: ApiUserPreferences;
  created_at: string;
  updated_at: string;
}

export interface ApiUserPreferences {
  theme: string;
  language: string;
  notifications: ApiNotificationPreferences;
}

export interface ApiNotificationPreferences {
  chat: ApiNotificationPreference;
  system: ApiNotificationPreference;
  updates: ApiNotificationPreference;
}

export interface ApiNotificationPreference {
  email: boolean;
  push: boolean;
  in_app: boolean;
}

export interface ApiChatMessage {
  id: string;
  conversation_id: string;
  content: string;
  role: string;
  created_at: string;
  metadata: Record<string, any>;
}

export interface ApiChatConversation {
  id: string;
  user_id: string;
  title: string;
  messages: ApiChatMessage[];
  created_at: string;
  updated_at: string;
}

export interface ApiDocument {
  id: string;
  user_id: string;
  title: string;
  content: string;
  mime_type: string;
  tags: string[];
  created_at: string;
  updated_at: string;
}

export interface ApiProfileItem {
  id: string;
  user_id: string;
  section: string;
  title: string;
  description: string;
  start_date?: string;
  end_date?: string;
  metadata: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface ApiProfile {
  user_id: string;
  items: Record<string, ApiProfileItem[]>;
  last_updated: string;
}

/**
 * Transforms an API user to a frontend user model.
 */
export function mapApiUserToModel(apiUser: ApiUser): User {
  return {
    id: apiUser.id,
    firstName: apiUser.first_name,
    lastName: apiUser.last_name,
    email: apiUser.email,
    role: apiUser.role as any,
    preferences: mapApiUserPreferencesToModel(apiUser.preferences),
    createdAt: new Date(apiUser.created_at),
    updatedAt: new Date(apiUser.updated_at)
  };
}

/**
 * Transforms a frontend user model to an API user.
 */
export function mapModelToApiUser(user: User): ApiUser {
  return {
    id: user.id,
    first_name: user.firstName,
    last_name: user.lastName,
    email: user.email,
    role: user.role,
    preferences: mapModelToApiUserPreferences(user.preferences),
    created_at: user.createdAt.toISOString(),
    updated_at: user.updatedAt.toISOString()
  };
}

/**
 * Transforms API user preferences to frontend user preferences.
 */
function mapApiUserPreferencesToModel(apiPreferences: ApiUserPreferences): UserPreferences {
  return {
    theme: apiPreferences.theme as any,
    language: apiPreferences.language as any,
    notifications: {
      chat: mapApiNotificationPreferenceToModel(apiPreferences.notifications.chat),
      system: mapApiNotificationPreferenceToModel(apiPreferences.notifications.system),
      updates: mapApiNotificationPreferenceToModel(apiPreferences.notifications.updates)
    }
  };
}

/**
 * Transforms frontend user preferences to API user preferences.
 */
function mapModelToApiUserPreferences(preferences: UserPreferences): ApiUserPreferences {
  return {
    theme: preferences.theme,
    language: preferences.language,
    notifications: {
      chat: mapModelToApiNotificationPreference(preferences.notifications.chat),
      system: mapModelToApiNotificationPreference(preferences.notifications.system),
      updates: mapModelToApiNotificationPreference(preferences.notifications.updates)
    }
  };
}

/**
 * Transforms API notification preference to frontend notification preference.
 */
function mapApiNotificationPreferenceToModel(apiPreference: ApiNotificationPreference): NotificationPreference {
  return {
    email: apiPreference.email,
    push: apiPreference.push,
    in_app: apiPreference.in_app
  };
}

/**
 * Transforms frontend notification preference to API notification preference.
 */
function mapModelToApiNotificationPreference(preference: NotificationPreference): ApiNotificationPreference {
  return {
    email: preference.email,
    push: preference.push,
    in_app: preference.in_app
  };
}

/**
 * Transforms an API chat message to a frontend chat message model.
 */
export function mapApiChatMessageToModel(apiMessage: ApiChatMessage): ChatMessage {
  return {
    id: apiMessage.id,
    conversationId: apiMessage.conversation_id,
    content: apiMessage.content,
    role: apiMessage.role as any,
    createdAt: new Date(apiMessage.created_at),
    metadata: apiMessage.metadata
  };
}

/**
 * Transforms a frontend chat message model to an API chat message.
 */
export function mapModelToApiChatMessage(message: ChatMessage): ApiChatMessage {
  return {
    id: message.id,
    conversation_id: message.conversationId,
    content: message.content,
    role: message.role,
    created_at: message.createdAt.toISOString(),
    metadata: message.metadata
  };
}

/**
 * Transforms an API chat conversation to a frontend chat conversation model.
 */
export function mapApiChatConversationToModel(apiConversation: ApiChatConversation): ChatConversation {
  return {
    id: apiConversation.id,
    userId: apiConversation.user_id,
    title: apiConversation.title,
    messages: apiConversation.messages.map(mapApiChatMessageToModel),
    createdAt: new Date(apiConversation.created_at),
    updatedAt: new Date(apiConversation.updated_at)
  };
}

/**
 * Transforms a frontend chat conversation model to an API chat conversation.
 */
export function mapModelToApiChatConversation(conversation: ChatConversation): ApiChatConversation {
  return {
    id: conversation.id,
    user_id: conversation.userId,
    title: conversation.title,
    messages: conversation.messages.map(mapModelToApiChatMessage),
    created_at: conversation.createdAt.toISOString(),
    updated_at: conversation.updatedAt.toISOString()
  };
}

/**
 * Transforms an API document to a frontend document model.
 */
export function mapApiDocumentToModel(apiDocument: ApiDocument): Document {
  return {
    id: apiDocument.id,
    userId: apiDocument.user_id,
    title: apiDocument.title,
    content: apiDocument.content,
    mimeType: apiDocument.mime_type,
    tags: apiDocument.tags,
    createdAt: new Date(apiDocument.created_at),
    updatedAt: new Date(apiDocument.updated_at)
  };
}

/**
 * Transforms a frontend document model to an API document.
 */
export function mapModelToApiDocument(document: Document): ApiDocument {
  return {
    id: document.id,
    user_id: document.userId,
    title: document.title,
    content: document.content,
    mime_type: document.mimeType,
    tags: document.tags,
    created_at: document.createdAt.toISOString(),
    updated_at: document.updatedAt.toISOString()
  };
}

/**
 * Transforms an API profile item to a frontend profile item model.
 */
export function mapApiProfileItemToModel(apiItem: ApiProfileItem): ProfileItem {
  return {
    id: apiItem.id,
    userId: apiItem.user_id,
    section: apiItem.section as ProfileSection,
    title: apiItem.title,
    description: apiItem.description,
    startDate: apiItem.start_date ? new Date(apiItem.start_date) : undefined,
    endDate: apiItem.end_date ? new Date(apiItem.end_date) : undefined,
    metadata: apiItem.metadata,
    createdAt: new Date(apiItem.created_at),
    updatedAt: new Date(apiItem.updated_at)
  };
}

/**
 * Transforms a frontend profile item model to an API profile item.
 */
export function mapModelToApiProfileItem(item: ProfileItem): ApiProfileItem {
  return {
    id: item.id,
    user_id: item.userId,
    section: item.section,
    title: item.title,
    description: item.description,
    start_date: item.startDate?.toISOString(),
    end_date: item.endDate?.toISOString(),
    metadata: item.metadata,
    created_at: item.createdAt.toISOString(),
    updated_at: item.updatedAt.toISOString()
  };
}

/**
 * Transforms an API profile to a frontend profile model.
 */
export function mapApiProfileToModel(apiProfile: ApiProfile): Profile {
  const items: Record<ProfileSection, ProfileItem[]> = {} as any;
  
  // Convert each section's items
  Object.entries(apiProfile.items).forEach(([section, apiItems]) => {
    items[section as ProfileSection] = apiItems.map(mapApiProfileItemToModel);
  });
  
  return {
    userId: apiProfile.user_id,
    items,
    lastUpdated: new Date(apiProfile.last_updated)
  };
}

/**
 * Transforms a frontend profile model to an API profile.
 */
export function mapModelToApiProfile(profile: Profile): ApiProfile {
  const items: Record<string, ApiProfileItem[]> = {};
  
  // Convert each section's items
  Object.entries(profile.items).forEach(([section, modelItems]) => {
    items[section] = modelItems.map(mapModelToApiProfileItem);
  });
  
  return {
    user_id: profile.userId,
    items,
    last_updated: profile.lastUpdated.toISOString()
  };
} 