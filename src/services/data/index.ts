/**
 * Data modeling service with single source of truth.
 * 
 * This module provides a centralized service for managing application data models,
 * with repository patterns for CRUD operations and relationships between models.
 */

import { User, ChatConversation, ChatMessage, Document, ProfileItem, Profile } from '../../models/api_models';

/**
 * Base repository interface for all entity types.
 */
export interface Repository<T> {
  findAll(): Promise<T[]>;
  findById(id: string): Promise<T | null>;
  create(data: Omit<T, 'id' | 'createdAt' | 'updatedAt'>): Promise<T>;
  update(id: string, data: Partial<T>): Promise<T>;
  delete(id: string): Promise<boolean>;
}

/**
 * User repository interface extending the base repository.
 */
export interface UserRepository extends Repository<User> {
  findByEmail(email: string): Promise<User | null>;
  findByRole(role: string): Promise<User[]>;
  updatePreferences(id: string, preferences: Partial<User['preferences']>): Promise<User>;
}

/**
 * Chat conversation repository interface.
 */
export interface ChatConversationRepository extends Repository<ChatConversation> {
  findByUserId(userId: string): Promise<ChatConversation[]>;
  findMessages(conversationId: string): Promise<ChatMessage[]>;
  addMessage(conversationId: string, message: Omit<ChatMessage, 'id' | 'conversationId' | 'createdAt'>): Promise<ChatMessage>;
}

/**
 * Document repository interface.
 */
export interface DocumentRepository extends Repository<Document> {
  findByUserId(userId: string): Promise<Document[]>;
  findByTags(tags: string[]): Promise<Document[]>;
}

/**
 * Profile repository interface.
 */
export interface ProfileRepository extends Repository<Profile> {
  findByUserId(userId: string): Promise<Profile | null>;
  addProfileItem(userId: string, item: Omit<ProfileItem, 'id' | 'userId' | 'createdAt' | 'updatedAt'>): Promise<ProfileItem>;
  updateProfileItem(itemId: string, data: Partial<ProfileItem>): Promise<ProfileItem>;
  deleteProfileItem(itemId: string): Promise<boolean>;
}

/**
 * Base repository implementation with common CRUD operations.
 */
export abstract class BaseRepository<T extends { id: string }> implements Repository<T> {
  protected items: Map<string, T> = new Map();
  
  async findAll(): Promise<T[]> {
    return Array.from(this.items.values());
  }
  
  async findById(id: string): Promise<T | null> {
    return this.items.get(id) || null;
  }
  
  abstract create(data: Omit<T, 'id' | 'createdAt' | 'updatedAt'>): Promise<T>;
  
  abstract update(id: string, data: Partial<T>): Promise<T>;
  
  async delete(id: string): Promise<boolean> {
    if (!this.items.has(id)) {
      return false;
    }
    
    this.items.delete(id);
    return true;
  }
}

/**
 * Data store service that manages all repositories.
 */
export class DataStore {
  private static instance: DataStore;
  
  private userRepository: UserRepository;
  private chatConversationRepository: ChatConversationRepository;
  private documentRepository: DocumentRepository;
  private profileRepository: ProfileRepository;
  
  private constructor() {
    // Initialize repositories
    this.userRepository = new UserRepositoryImpl();
    this.chatConversationRepository = new ChatConversationRepositoryImpl();
    this.documentRepository = new DocumentRepositoryImpl();
    this.profileRepository = new ProfileRepositoryImpl();
  }
  
  public static getInstance(): DataStore {
    if (!DataStore.instance) {
      DataStore.instance = new DataStore();
    }
    return DataStore.instance;
  }
  
  public getUserRepository(): UserRepository {
    return this.userRepository;
  }
  
  public getChatConversationRepository(): ChatConversationRepository {
    return this.chatConversationRepository;
  }
  
  public getDocumentRepository(): DocumentRepository {
    return this.documentRepository;
  }
  
  public getProfileRepository(): ProfileRepository {
    return this.profileRepository;
  }
}

/**
 * User repository implementation.
 */
class UserRepositoryImpl extends BaseRepository<User> implements UserRepository {
  async findByEmail(email: string): Promise<User | null> {
    const users = Array.from(this.items.values());
    return users.find(user => user.email === email) || null;
  }
  
  async findByRole(role: string): Promise<User[]> {
    const users = Array.from(this.items.values());
    return users.filter(user => user.role === role);
  }
  
  async create(data: Omit<User, 'id' | 'createdAt' | 'updatedAt'>): Promise<User> {
    const id = crypto.randomUUID();
    const now = new Date();
    
    const user: User = {
      ...data as any,
      id,
      createdAt: now,
      updatedAt: now,
    };
    
    this.items.set(id, user);
    return user;
  }
  
  async update(id: string, data: Partial<User>): Promise<User> {
    const user = await this.findById(id);
    if (!user) {
      throw new Error(`User with ID ${id} not found`);
    }
    
    const updatedUser: User = {
      ...user,
      ...data,
      updatedAt: new Date(),
    };
    
    this.items.set(id, updatedUser);
    return updatedUser;
  }
  
  async updatePreferences(id: string, preferences: Partial<User['preferences']>): Promise<User> {
    const user = await this.findById(id);
    if (!user) {
      throw new Error(`User with ID ${id} not found`);
    }
    
    const updatedUser: User = {
      ...user,
      preferences: {
        ...user.preferences,
        ...preferences,
      },
      updatedAt: new Date(),
    };
    
    this.items.set(id, updatedUser);
    return updatedUser;
  }
}

/**
 * Chat conversation repository implementation.
 */
class ChatConversationRepositoryImpl extends BaseRepository<ChatConversation> implements ChatConversationRepository {
  private messages: Map<string, ChatMessage[]> = new Map();
  
  async findByUserId(userId: string): Promise<ChatConversation[]> {
    const conversations = Array.from(this.items.values());
    return conversations.filter(conversation => conversation.userId === userId);
  }
  
  async findMessages(conversationId: string): Promise<ChatMessage[]> {
    return this.messages.get(conversationId) || [];
  }
  
  async addMessage(conversationId: string, message: Omit<ChatMessage, 'id' | 'conversationId' | 'createdAt'>): Promise<ChatMessage> {
    const conversation = await this.findById(conversationId);
    if (!conversation) {
      throw new Error(`Conversation with ID ${conversationId} not found`);
    }
    
    const id = crypto.randomUUID();
    const now = new Date();
    
    const newMessage: ChatMessage = {
      ...message as any,
      id,
      conversationId,
      createdAt: now,
    };
    
    const messages = this.messages.get(conversationId) || [];
    messages.push(newMessage);
    this.messages.set(conversationId, messages);
    
    // Update conversation's messages and updatedAt
    const updatedConversation: ChatConversation = {
      ...conversation,
      messages: [...messages],
      updatedAt: now,
    };
    
    this.items.set(conversationId, updatedConversation);
    return newMessage;
  }
  
  async create(data: Omit<ChatConversation, 'id' | 'createdAt' | 'updatedAt'>): Promise<ChatConversation> {
    const id = crypto.randomUUID();
    const now = new Date();
    
    const conversation: ChatConversation = {
      ...data as any,
      id,
      messages: [],
      createdAt: now,
      updatedAt: now,
    };
    
    this.items.set(id, conversation);
    this.messages.set(id, []);
    return conversation;
  }
  
  async update(id: string, data: Partial<ChatConversation>): Promise<ChatConversation> {
    const conversation = await this.findById(id);
    if (!conversation) {
      throw new Error(`Conversation with ID ${id} not found`);
    }
    
    const updatedConversation: ChatConversation = {
      ...conversation,
      ...data,
      updatedAt: new Date(),
    };
    
    this.items.set(id, updatedConversation);
    return updatedConversation;
  }
  
  async delete(id: string): Promise<boolean> {
    const result = await super.delete(id);
    if (result) {
      this.messages.delete(id);
    }
    return result;
  }
}

/**
 * Document repository implementation.
 */
class DocumentRepositoryImpl extends BaseRepository<Document> implements DocumentRepository {
  async findByUserId(userId: string): Promise<Document[]> {
    const documents = Array.from(this.items.values());
    return documents.filter(document => document.userId === userId);
  }
  
  async findByTags(tags: string[]): Promise<Document[]> {
    const documents = Array.from(this.items.values());
    return documents.filter(document => 
      tags.some(tag => document.tags.includes(tag))
    );
  }
  
  async create(data: Omit<Document, 'id' | 'createdAt' | 'updatedAt'>): Promise<Document> {
    const id = crypto.randomUUID();
    const now = new Date();
    
    const document: Document = {
      ...data as any,
      id,
      createdAt: now,
      updatedAt: now,
    };
    
    this.items.set(id, document);
    return document;
  }
  
  async update(id: string, data: Partial<Document>): Promise<Document> {
    const document = await this.findById(id);
    if (!document) {
      throw new Error(`Document with ID ${id} not found`);
    }
    
    const updatedDocument: Document = {
      ...document,
      ...data,
      updatedAt: new Date(),
    };
    
    this.items.set(id, updatedDocument);
    return updatedDocument;
  }
}

/**
 * Profile repository implementation.
 */
class ProfileRepositoryImpl extends BaseRepository<Profile> implements ProfileRepository {
  private profileItems: Map<string, ProfileItem> = new Map();
  
  async findByUserId(userId: string): Promise<Profile | null> {
    const profiles = Array.from(this.items.values());
    return profiles.find(profile => profile.userId === userId) || null;
  }
  
  async addProfileItem(userId: string, item: Omit<ProfileItem, 'id' | 'userId' | 'createdAt' | 'updatedAt'>): Promise<ProfileItem> {
    const profile = await this.findByUserId(userId);
    if (!profile) {
      throw new Error(`Profile for user ${userId} not found`);
    }
    
    const id = crypto.randomUUID();
    const now = new Date();
    
    const newItem: ProfileItem = {
      ...item as any,
      id,
      userId,
      createdAt: now,
      updatedAt: now,
    };
    
    this.profileItems.set(id, newItem);
    
    // Update profile's items
    const section = newItem.section;
    const items = profile.items[section] || [];
    items.push(newItem);
    
    const updatedProfile: Profile = {
      ...profile,
      items: {
        ...profile.items,
        [section]: items,
      },
      lastUpdated: now,
    };
    
    this.items.set(profile.userId, updatedProfile);
    return newItem;
  }
  
  async updateProfileItem(itemId: string, data: Partial<ProfileItem>): Promise<ProfileItem> {
    const item = this.profileItems.get(itemId);
    if (!item) {
      throw new Error(`Profile item with ID ${itemId} not found`);
    }
    
    const now = new Date();
    const updatedItem: ProfileItem = {
      ...item,
      ...data,
      updatedAt: now,
    };
    
    this.profileItems.set(itemId, updatedItem);
    
    // Update the profile that contains this item
    const profile = await this.findByUserId(item.userId);
    if (profile) {
      const section = item.section;
      const items = profile.items[section] || [];
      const updatedItems = items.map(i => i.id === itemId ? updatedItem : i);
      
      const updatedProfile: Profile = {
        ...profile,
        items: {
          ...profile.items,
          [section]: updatedItems,
        },
        lastUpdated: now,
      };
      
      this.items.set(profile.userId, updatedProfile);
    }
    
    return updatedItem;
  }
  
  async deleteProfileItem(itemId: string): Promise<boolean> {
    const item = this.profileItems.get(itemId);
    if (!item) {
      return false;
    }
    
    this.profileItems.delete(itemId);
    
    // Update the profile that contains this item
    const profile = await this.findByUserId(item.userId);
    if (profile) {
      const section = item.section;
      const items = profile.items[section] || [];
      const updatedItems = items.filter(i => i.id !== itemId);
      
      const updatedProfile: Profile = {
        ...profile,
        items: {
          ...profile.items,
          [section]: updatedItems,
        },
        lastUpdated: new Date(),
      };
      
      this.items.set(profile.userId, updatedProfile);
    }
    
    return true;
  }
  
  async create(data: Omit<Profile, 'id' | 'createdAt' | 'updatedAt'>): Promise<Profile> {
    const userId = data.userId;
    const now = new Date();
    
    const profile: Profile = {
      ...data as any,
      items: data.items || {},
      lastUpdated: now,
    };
    
    this.items.set(userId, profile);
    return profile;
  }
  
  async update(id: string, data: Partial<Profile>): Promise<Profile> {
    const profile = await this.findById(id);
    if (!profile) {
      throw new Error(`Profile with ID ${id} not found`);
    }
    
    const updatedProfile: Profile = {
      ...profile,
      ...data,
      lastUpdated: new Date(),
    };
    
    this.items.set(id, updatedProfile);
    return updatedProfile;
  }
}

// Export singleton instance for easy access
export const dataStore = DataStore.getInstance(); 