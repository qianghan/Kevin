/**
 * SessionSearchIndex
 * 
 * This file implements a search index for chat sessions using the Lunr.js library
 * to provide fast, client-side full-text search capabilities.
 */

import * as lunr from 'lunr';
import { ChatSession, ChatSessionIndex } from '../../interfaces/services/chat.session';

/**
 * SessionSearchIndex implementation using Lunr.js
 */
export class SessionSearchIndex implements ChatSessionIndex {
  private index: lunr.Index | null = null;
  private sessionStore: Map<string, ChatSession> = new Map();
  
  constructor() {
    this.buildIndex();
  }
  
  /**
   * Build or rebuild the search index
   */
  private buildIndex(): void {
    this.index = lunr(function() {
      this.field('name', { boost: 10 });
      this.field('preview', { boost: 5 });
      this.field('tags', { boost: 7 });
      this.field('content');
      this.ref('id');
      
      // Add existing sessions to the index
      for (const session of this.sessionStore.values()) {
        this.add(session);
      }
    }.bind(this));
  }
  
  /**
   * Convert a session to an indexable document
   */
  private sessionToDocument(session: ChatSession): any {
    return {
      id: session.id,
      name: session.name,
      preview: session.preview || '',
      tags: session.tags ? session.tags.join(' ') : '',
      content: this.extractSessionContent(session)
    };
  }
  
  /**
   * Extract searchable content from a session
   */
  private extractSessionContent(session: ChatSession): string {
    const contentParts = [];
    
    if (session.firstMessage?.content) {
      contentParts.push(typeof session.firstMessage.content === 'string' 
        ? session.firstMessage.content 
        : JSON.stringify(session.firstMessage.content));
    }
    
    if (session.lastMessage?.content) {
      contentParts.push(typeof session.lastMessage.content === 'string' 
        ? session.lastMessage.content 
        : JSON.stringify(session.lastMessage.content));
    }
    
    return contentParts.join(' ');
  }
  
  /**
   * Add a session to the index
   */
  addSession(session: ChatSession): void {
    this.sessionStore.set(session.id, session);
    
    // If index exists, add document to it
    if (this.index) {
      const document = this.sessionToDocument(session);
      this.index.builder.add(document);
      this.index.builder.build();
    } else {
      // Otherwise rebuild the entire index
      this.buildIndex();
    }
  }
  
  /**
   * Update a session in the index
   */
  updateSession(sessionId: string, sessionUpdates: Partial<ChatSession>): void {
    const existingSession = this.sessionStore.get(sessionId);
    
    if (existingSession) {
      // Create updated session
      const updatedSession = {
        ...existingSession,
        ...sessionUpdates
      };
      
      // Store updated session
      this.sessionStore.set(sessionId, updatedSession);
      
      // Rebuild index (simpler than trying to update in place)
      this.buildIndex();
    }
  }
  
  /**
   * Remove a session from the index
   */
  removeSession(sessionId: string): void {
    if (this.sessionStore.has(sessionId)) {
      this.sessionStore.delete(sessionId);
      this.buildIndex();
    }
  }
  
  /**
   * Search sessions by query
   */
  search(query: string): ChatSession[] {
    if (!this.index || !query.trim()) {
      // If no query or no index, return all sessions
      return Array.from(this.sessionStore.values());
    }
    
    try {
      // Perform search and get results
      const results = this.index.search(query);
      
      // Map results to sessions
      return results
        .map(result => this.sessionStore.get(result.ref))
        .filter((session): session is ChatSession => !!session);
    } catch (err) {
      console.error('Search error:', err);
      
      // Fall back to simple contains search on error
      const lowerQuery = query.toLowerCase();
      return Array.from(this.sessionStore.values()).filter(session => 
        session.name.toLowerCase().includes(lowerQuery) ||
        (session.preview && session.preview.toLowerCase().includes(lowerQuery)) ||
        (session.tags && session.tags.some(tag => tag.toLowerCase().includes(lowerQuery)))
      );
    }
  }
  
  /**
   * Clear the index
   */
  clear(): void {
    this.sessionStore.clear();
    this.buildIndex();
  }
  
  /**
   * Bulk add sessions to the index
   */
  addSessions(sessions: ChatSession[]): void {
    for (const session of sessions) {
      this.sessionStore.set(session.id, session);
    }
    
    this.buildIndex();
  }
  
  /**
   * Get the number of indexed sessions
   */
  get size(): number {
    return this.sessionStore.size;
  }
} 