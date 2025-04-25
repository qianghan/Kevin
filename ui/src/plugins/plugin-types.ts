/**
 * Plugin System Types
 * 
 * This file defines the types for the plugin system in KAI UI.
 * It follows the Open/Closed Principle (OCP) by defining interfaces 
 * that can be implemented by plugins without modifying the core application.
 */

import { ReactNode } from 'react';

/**
 * Plugin metadata interface
 */
export interface PluginManifest {
  id: string;
  name: string;
  version: string;
  description: string;
  author: string;
  dependencies?: Record<string, string>;
  minAppVersion?: string;
  maxAppVersion?: string;
  tags?: string[];
  icon?: string;
}

/**
 * Extension points that plugins can hook into
 */
export type ExtensionPoint = 
  | 'navigation'       // Left navigation items
  | 'topbar-right'     // Top bar right side
  | 'topbar-left'      // Top bar left side
  | 'chat-sidebar'     // Chat sidebar panels
  | 'chat-message'     // Chat message renderers
  | 'dashboard-widget' // Dashboard widgets
  | 'settings-page'    // Settings pages
  | 'profile-section'  // Profile sections
  | 'theme'           // Theme extensions
  | 'service'         // Service extensions
  | 'route'           // Route extensions
  | 'api-middleware'  // API middleware
  | 'global-command'  // Global commands (keyboard shortcuts, etc.)
  | 'document-viewer' // Document viewer extensions
  | 'document-editor' // Document editor extensions
  | 'context-menu'    // Context menu items
  | 'export-format'   // Export format options
  | 'chat-tool';      // Chat tools

/**
 * Extension contribution interface
 */
export interface ExtensionContribution<T = any> {
  extensionPoint: ExtensionPoint;
  priority?: number;
  id: string;
  data: T;
}

/**
 * Required plugin interface that all plugins must implement
 */
export interface IPlugin {
  /**
   * Plugin manifest with metadata
   */
  manifest: PluginManifest;
  
  /**
   * Initialize the plugin
   * @param container Plugin container reference
   * @returns Promise that resolves when the plugin is initialized
   */
  initialize(container: IPluginContainer): Promise<void>;
  
  /**
   * Get extensions contributed by this plugin
   * @returns Array of extension contributions
   */
  getExtensions(): ExtensionContribution[];
  
  /**
   * Clean up plugin resources
   * @returns Promise that resolves when the plugin is deactivated
   */
  deactivate?(): Promise<void>;
}

/**
 * Plugin container interface that the core application implements
 */
export interface IPluginContainer {
  /**
   * Register an extension
   * @param extension Extension contribution
   */
  registerExtension(extension: ExtensionContribution): void;
  
  /**
   * Unregister an extension
   * @param extensionId Extension ID
   * @param extensionPoint Extension point
   */
  unregisterExtension(extensionId: string, extensionPoint: ExtensionPoint): void;
  
  /**
   * Get extensions for a specific extension point
   * @param extensionPoint Extension point
   * @returns Array of extensions
   */
  getExtensions<T = any>(extensionPoint: ExtensionPoint): ExtensionContribution<T>[];
  
  /**
   * Get service instances
   * @param serviceId Service ID
   * @returns Service instance
   */
  getService<T = any>(serviceId: string): T;
  
  /**
   * Register a service implementation
   * @param serviceId Service ID
   * @param implementation Service implementation
   */
  registerService<T = any>(serviceId: string, implementation: T): void;
  
  /**
   * Register a plugin
   * @param plugin Plugin to register
   */
  registerPlugin(plugin: IPlugin): Promise<void>;
  
  /**
   * Unregister a plugin
   * @param pluginId Plugin ID to unregister
   */
  unregisterPlugin(pluginId: string): Promise<void>;
  
  /**
   * Get all registered plugins
   * @returns Array of registered plugins
   */
  getPlugins(): IPlugin[];
  
  /**
   * Add event listener
   * @param event Event type
   * @param listener Event listener function
   */
  addEventListener(event: PluginEventType, listener: Function): void;
  
  /**
   * Remove event listener
   * @param event Event type
   * @param listener Event listener function to remove
   */
  removeEventListener(event: PluginEventType, listener: Function): void;
}

/**
 * Common extension data types
 */

// Navigation Item extension data
export interface NavigationItemData {
  label: string;
  path: string;
  icon?: string;
  children?: NavigationItemData[];
  requiredPermission?: string;
}

// Widget extension data
export interface WidgetData {
  title: string;
  component: ReactNode;
  width?: 'full' | 'half' | 'third';
  height?: 'small' | 'medium' | 'large';
  requiredPermission?: string;
}

// Route extension data
export interface RouteData {
  path: string;
  component: ReactNode;
  exact?: boolean;
  requiredPermission?: string;
}

// Service extension data
export interface ServiceExtensionData {
  serviceId: string;
  implementation: any;
  override?: boolean;
}

// Theme extension data
export interface ThemeExtensionData {
  colors?: Record<string, Record<string, string>>;
  components?: Record<string, any>;
  typography?: Record<string, any>;
}

/**
 * Plugin event types
 */
export type PluginEventType = 
  | 'plugin-loaded' 
  | 'plugin-error' 
  | 'plugin-unloaded' 
  | 'extension-registered' 
  | 'extension-unregistered';

/**
 * Plugin event data
 */
export interface PluginEvent {
  type: PluginEventType;
  pluginId?: string;
  data?: any;
} 