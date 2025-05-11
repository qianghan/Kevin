/**
 * SessionExporter
 * 
 * This service provides functionality to export chat sessions in various formats.
 */

import { ChatSession, ExportFormat, ExportResult } from '../../interfaces/services/chat.session';
import { ChatMessage } from '../../interfaces/services/chat.service';

/**
 * SessionExporter class provides methods to export sessions in different formats
 */
export class SessionExporter {
  /**
   * Export a session to the specified format
   */
  static exportSession(session: ChatSession, messages: ChatMessage[], format: ExportFormat): ExportResult {
    switch (format) {
      case 'json':
        return this.exportAsJSON(session, messages);
      case 'text':
        return this.exportAsText(session, messages);
      case 'markdown':
        return this.exportAsMarkdown(session, messages);
      case 'html':
        return this.exportAsHTML(session, messages);
      case 'pdf':
        return this.exportAsPDF(session, messages);
      default:
        throw new Error(`Unsupported export format: ${format}`);
    }
  }
  
  /**
   * Export a session as JSON
   */
  private static exportAsJSON(session: ChatSession, messages: ChatMessage[]): ExportResult {
    const exportData = {
      session: {
        id: session.id,
        name: session.name,
        createdAt: session.createdAt,
        updatedAt: session.updatedAt,
        messageCount: messages.length,
        tags: session.tags,
      },
      messages: messages.map(msg => ({
        id: msg.id,
        role: msg.role,
        content: msg.content,
        timestamp: msg.timestamp,
      }))
    };
    
    const data = JSON.stringify(exportData, null, 2);
    
    return {
      data,
      filename: `${this.sanitizeFilename(session.name)}_${this.getDateString()}.json`,
      mimeType: 'application/json'
    };
  }
  
  /**
   * Export a session as plain text
   */
  private static exportAsText(session: ChatSession, messages: ChatMessage[]): ExportResult {
    let content = `Chat Session: ${session.name}\n`;
    content += `Created: ${new Date(session.createdAt).toLocaleString()}\n`;
    content += `Last Updated: ${new Date(session.updatedAt).toLocaleString()}\n`;
    
    if (session.tags && session.tags.length > 0) {
      content += `Tags: ${session.tags.join(', ')}\n`;
    }
    
    content += '\n--- Conversation ---\n\n';
    
    for (const message of messages) {
      const sender = message.role === 'user' ? 'User' : 'AI';
      const timestamp = new Date(message.timestamp).toLocaleString();
      const messageContent = typeof message.content === 'string' 
        ? message.content 
        : JSON.stringify(message.content);
      
      content += `[${timestamp}] ${sender}:\n${messageContent}\n\n`;
    }
    
    return {
      data: content,
      filename: `${this.sanitizeFilename(session.name)}_${this.getDateString()}.txt`,
      mimeType: 'text/plain'
    };
  }
  
  /**
   * Export a session as Markdown
   */
  private static exportAsMarkdown(session: ChatSession, messages: ChatMessage[]): ExportResult {
    let content = `# Chat Session: ${session.name}\n\n`;
    content += `**Created:** ${new Date(session.createdAt).toLocaleString()}\n`;
    content += `**Last Updated:** ${new Date(session.updatedAt).toLocaleString()}\n`;
    
    if (session.tags && session.tags.length > 0) {
      content += `**Tags:** ${session.tags.join(', ')}\n`;
    }
    
    content += '\n## Conversation\n\n';
    
    for (const message of messages) {
      const sender = message.role === 'user' ? '**User**' : '**AI**';
      const timestamp = new Date(message.timestamp).toLocaleString();
      const messageContent = typeof message.content === 'string' 
        ? message.content 
        : JSON.stringify(message.content);
      
      content += `### ${sender} (${timestamp})\n\n${messageContent}\n\n`;
    }
    
    return {
      data: content,
      filename: `${this.sanitizeFilename(session.name)}_${this.getDateString()}.md`,
      mimeType: 'text/markdown'
    };
  }
  
  /**
   * Export a session as HTML
   */
  private static exportAsHTML(session: ChatSession, messages: ChatMessage[]): ExportResult {
    let content = `<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Chat Session: ${session.name}</title>
  <style>
    body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
    .header { margin-bottom: 20px; }
    .metadata { color: #666; margin-bottom: 5px; }
    .conversation { border-top: 1px solid #eee; padding-top: 20px; }
    .message { margin-bottom: 20px; padding: 10px; border-radius: 5px; }
    .user { background-color: #f0f7ff; border-left: 3px solid #3498db; }
    .ai { background-color: #f9f9f9; border-left: 3px solid #2ecc71; }
    .timestamp { color: #999; font-size: 12px; margin-top: 5px; }
    .tag { display: inline-block; background: #e0e0e0; border-radius: 3px; padding: 2px 6px; margin-right: 5px; font-size: 12px; }
  </style>
</head>
<body>
  <div class="header">
    <h1>Chat Session: ${session.name}</h1>
    <div class="metadata">Created: ${new Date(session.createdAt).toLocaleString()}</div>
    <div class="metadata">Last Updated: ${new Date(session.updatedAt).toLocaleString()}</div>`;
    
    if (session.tags && session.tags.length > 0) {
      content += `
    <div class="metadata">
      Tags: ${session.tags.map(tag => `<span class="tag">${tag}</span>`).join(' ')}
    </div>`;
    }
    
    content += `
  </div>
  
  <div class="conversation">
    <h2>Conversation</h2>`;
    
    for (const message of messages) {
      const messageClass = message.role === 'user' ? 'user' : 'ai';
      const sender = message.role === 'user' ? 'User' : 'AI';
      const timestamp = new Date(message.timestamp).toLocaleString();
      const messageContent = typeof message.content === 'string' 
        ? message.content.replace(/\n/g, '<br>') 
        : JSON.stringify(message.content);
      
      content += `
    <div class="message ${messageClass}">
      <strong>${sender}</strong>
      <div>${messageContent}</div>
      <div class="timestamp">${timestamp}</div>
    </div>`;
    }
    
    content += `
  </div>
</body>
</html>`;
    
    return {
      data: content,
      filename: `${this.sanitizeFilename(session.name)}_${this.getDateString()}.html`,
      mimeType: 'text/html'
    };
  }
  
  /**
   * Export a session as PDF (basic implementation)
   * Note: For a complete PDF implementation, we would need additional libraries
   */
  private static exportAsPDF(session: ChatSession, messages: ChatMessage[]): ExportResult {
    // For a real PDF export, we would use a library like jsPDF
    // This is a placeholder that returns HTML, which would need to be converted
    const htmlResult = this.exportAsHTML(session, messages);
    
    return {
      data: htmlResult.data,
      filename: `${this.sanitizeFilename(session.name)}_${this.getDateString()}.pdf`,
      mimeType: 'application/pdf'
    };
  }
  
  /**
   * Sanitize a filename to remove invalid characters
   */
  private static sanitizeFilename(name: string): string {
    return name
      .replace(/[/\\?%*:|"<>]/g, '-') // Replace invalid filename chars with dashes
      .replace(/\s+/g, '_') // Replace spaces with underscores
      .trim();
  }
  
  /**
   * Get a formatted date string for filenames
   */
  private static getDateString(): string {
    const date = new Date();
    return date.toISOString().split('T')[0]; // YYYY-MM-DD format
  }
} 