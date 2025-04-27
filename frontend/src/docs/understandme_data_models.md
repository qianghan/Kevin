# KAI Data Models Documentation

This document outlines the data models used throughout the KAI application, including their interfaces, validation schemas, and transformation utilities.

## Core Data Models

### User Model

```typescript
export interface User {
  id: string;
  username: string;
  email: string;
  displayName: string;
  profileImage?: string;
  role: UserRole;
  preferences: UserPreferences;
  createdAt: string;
  updatedAt: string;
}

export type UserRole = 'admin' | 'user' | 'guest';

export interface UserPreferences {
  theme: 'light' | 'dark' | 'system';
  notifications: NotificationPreferences;
  accessibility: AccessibilityPreferences;
}

export interface NotificationPreferences {
  email: boolean;
  push: boolean;
  desktop: boolean;
}

export interface AccessibilityPreferences {
  reducedMotion: boolean;
  highContrast: boolean;
  largeText: boolean;
}
```

### Chat Models

```typescript
export interface Conversation {
  id: string;
  title: string;
  participants: string[];
  messages: Message[];
  createdAt: string;
  updatedAt: string;
  metadata: ConversationMetadata;
}

export interface Message {
  id: string;
  conversationId: string;
  senderId: string;
  content: string;
  contentType: 'text' | 'markdown' | 'code' | 'image';
  timestamp: string;
  status: 'sending' | 'sent' | 'delivered' | 'read' | 'failed';
  reactions?: MessageReaction[];
  metadata?: Record<string, unknown>;
}

export interface MessageReaction {
  userId: string;
  emoji: string;
  timestamp: string;
}

export interface ConversationMetadata {
  isArchived: boolean;
  isPinned: boolean;
  lastReadMessageId: Record<string, string>;
  customData?: Record<string, unknown>;
}
```

### Profiler Models

```typescript
export interface Profile {
  id: string;
  userId: string;
  skills: Skill[];
  experience: Experience[];
  education: Education[];
  projects: Project[];
  bio: string;
  socialLinks: SocialLink[];
  createdAt: string;
  updatedAt: string;
}

export interface Skill {
  name: string;
  category: string;
  proficiency: 'beginner' | 'intermediate' | 'advanced' | 'expert';
  yearsOfExperience: number;
}

export interface Experience {
  company: string;
  title: string;
  location: string;
  startDate: string;
  endDate?: string;
  isCurrent: boolean;
  description: string;
  skills: string[];
}

export interface Education {
  institution: string;
  degree: string;
  field: string;
  startDate: string;
  endDate?: string;
  isCurrent: boolean;
  description?: string;
}

export interface Project {
  name: string;
  description: string;
  url?: string;
  startDate: string;
  endDate?: string;
  isCurrent: boolean;
  skills: string[];
  images?: string[];
}

export interface SocialLink {
  platform: 'github' | 'linkedin' | 'twitter' | 'website' | 'other';
  url: string;
  username?: string;
}
```

## Data Validation Schemas

Data validation is implemented using JSON Schema. Below are the schema definitions for our core models.

### User Schema

```typescript
export const userSchema = {
  type: 'object',
  required: ['id', 'username', 'email', 'displayName', 'role', 'preferences', 'createdAt', 'updatedAt'],
  properties: {
    id: { type: 'string', format: 'uuid' },
    username: { type: 'string', minLength: 3, maxLength: 50 },
    email: { type: 'string', format: 'email' },
    displayName: { type: 'string', minLength: 1, maxLength: 100 },
    profileImage: { type: 'string', format: 'uri', nullable: true },
    role: { type: 'string', enum: ['admin', 'user', 'guest'] },
    preferences: {
      type: 'object',
      required: ['theme', 'notifications', 'accessibility'],
      properties: {
        theme: { type: 'string', enum: ['light', 'dark', 'system'] },
        notifications: {
          type: 'object',
          required: ['email', 'push', 'desktop'],
          properties: {
            email: { type: 'boolean' },
            push: { type: 'boolean' },
            desktop: { type: 'boolean' }
          }
        },
        accessibility: {
          type: 'object',
          required: ['reducedMotion', 'highContrast', 'largeText'],
          properties: {
            reducedMotion: { type: 'boolean' },
            highContrast: { type: 'boolean' },
            largeText: { type: 'boolean' }
          }
        }
      }
    },
    createdAt: { type: 'string', format: 'date-time' },
    updatedAt: { type: 'string', format: 'date-time' }
  }
};
```

## Data Transformation Utilities

The application uses a set of utilities to transform data between backend and frontend representations:

### Entity Transformers

```typescript
// Example of a transformer for User entity
export const transformUserFromAPI = (apiUser: APIUser): User => {
  return {
    id: apiUser.id,
    username: apiUser.username,
    email: apiUser.email,
    displayName: apiUser.display_name,
    profileImage: apiUser.profile_image,
    role: apiUser.role,
    preferences: {
      theme: apiUser.preferences.theme,
      notifications: {
        email: apiUser.preferences.notifications.email,
        push: apiUser.preferences.notifications.push,
        desktop: apiUser.preferences.notifications.desktop
      },
      accessibility: {
        reducedMotion: apiUser.preferences.accessibility.reduced_motion,
        highContrast: apiUser.preferences.accessibility.high_contrast,
        largeText: apiUser.preferences.accessibility.large_text
      }
    },
    createdAt: apiUser.created_at,
    updatedAt: apiUser.updated_at
  };
};

export const transformUserToAPI = (user: User): APIUser => {
  return {
    id: user.id,
    username: user.username,
    email: user.email,
    display_name: user.displayName,
    profile_image: user.profileImage,
    role: user.role,
    preferences: {
      theme: user.preferences.theme,
      notifications: {
        email: user.preferences.notifications.email,
        push: user.preferences.notifications.push,
        desktop: user.preferences.notifications.desktop
      },
      accessibility: {
        reduced_motion: user.preferences.accessibility.reducedMotion,
        high_contrast: user.preferences.accessibility.highContrast,
        large_text: user.preferences.accessibility.largeText
      }
    },
    created_at: user.createdAt,
    updated_at: user.updatedAt
  };
};
```

## Immutable Data Patterns

The application follows immutable data patterns to ensure data integrity and prevent unintended side effects.

### Immutable Updates

```typescript
// Example of immutable update for User
export const updateUser = (user: User, updates: Partial<User>): User => {
  return {
    ...user,
    ...updates,
    updatedAt: new Date().toISOString(),
    preferences: updates.preferences 
      ? { ...user.preferences, ...updates.preferences }
      : user.preferences
  };
};
```

### Immutable Collections

```typescript
// Example of immutable collection updates
export const addMessage = (conversation: Conversation, message: Message): Conversation => {
  return {
    ...conversation,
    messages: [...conversation.messages, message],
    updatedAt: new Date().toISOString()
  };
};

export const updateMessage = (conversation: Conversation, messageId: string, updates: Partial<Message>): Conversation => {
  return {
    ...conversation,
    messages: conversation.messages.map(msg => 
      msg.id === messageId ? { ...msg, ...updates } : msg
    ),
    updatedAt: new Date().toISOString()
  };
};
```

## Factory Functions

Factory functions are used to create consistent model instances for testing and development:

```typescript
export const createUser = (overrides: Partial<User> = {}): User => {
  const id = overrides.id || generateUUID();
  const timestamp = new Date().toISOString();
  
  return {
    id,
    username: overrides.username || `user_${id.substring(0, 8)}`,
    email: overrides.email || `${id.substring(0, 8)}@example.com`,
    displayName: overrides.displayName || `User ${id.substring(0, 8)}`,
    profileImage: overrides.profileImage,
    role: overrides.role || 'user',
    preferences: overrides.preferences || {
      theme: 'system',
      notifications: {
        email: true,
        push: true,
        desktop: true
      },
      accessibility: {
        reducedMotion: false,
        highContrast: false,
        largeText: false
      }
    },
    createdAt: overrides.createdAt || timestamp,
    updatedAt: overrides.updatedAt || timestamp
  };
};
```

## Model Compatibility Testing

The application includes tests to verify model compatibility across different services:

```typescript
// Example test pseudocode
describe('User Model Compatibility', () => {
  it('should be compatible with the profile service', () => {
    const user = createUser();
    const profileUser = ProfileService.transformUserToProfileUser(user);
    const backToUser = ProfileService.transformProfileUserToUser(profileUser);
    
    // Assert key properties are maintained through transformations
    expect(backToUser.id).toEqual(user.id);
    expect(backToUser.username).toEqual(user.username);
    expect(backToUser.email).toEqual(user.email);
  });
  
  it('should be compatible with the chat service', () => {
    const user = createUser();
    const chatUser = ChatService.transformUserToChatUser(user);
    const backToUser = ChatService.transformChatUserToUser(chatUser);
    
    // Assert key properties are maintained through transformations
    expect(backToUser.id).toEqual(user.id);
    expect(backToUser.username).toEqual(user.username);
    expect(backToUser.displayName).toEqual(user.displayName);
  });
});
```

## Conclusion

This document provides an overview of the core data models used in the KAI application. These models are designed to be consistent, immutable, and easily validated. The transformation utilities ensure compatibility with backend APIs, while factory functions simplify testing and development. 