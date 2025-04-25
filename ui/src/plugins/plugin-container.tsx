/**
 * Plugin Container Implementation
 * 
 * This file implements the plugin container for the KAI UI.
 * It follows the Open/Closed Principle (OCP) by allowing plugins
 * to extend the application without modifying its core.
 */

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { 
  IPluginContainer, 
  IPlugin, 
  ExtensionContribution, 
  ExtensionPoint,
  PluginEvent,
  PluginEventType
} from './plugin-types';

/**
 * Plugin container implementation
 */
class PluginContainer implements IPluginContainer {
  private extensions: Map<ExtensionPoint, ExtensionContribution[]> = new Map();
  private services: Map<string, any> = new Map();
  private plugins: Map<string, IPlugin> = new Map();
  private eventListeners: Map<PluginEventType, Function[]> = new Map();
  
  /**
   * Register an extension
   */
  public registerExtension(extension: ExtensionContribution): void {
    const existingExtensions = this.extensions.get(extension.extensionPoint) || [];
    
    // Remove any existing extension with the same ID
    const filteredExtensions = existingExtensions.filter(
      ext => ext.id !== extension.id
    );
    
    // Add the new extension
    const newExtensions = [...filteredExtensions, extension];
    
    // Sort by priority (higher numbers come first)
    newExtensions.sort((a, b) => (b.priority || 0) - (a.priority || 0));
    
    // Update the extensions map
    this.extensions.set(extension.extensionPoint, newExtensions);
    
    // Emit event
    this.emitEvent('extension-registered', {
      extensionPoint: extension.extensionPoint,
      extensionId: extension.id
    });
  }
  
  /**
   * Unregister an extension
   */
  public unregisterExtension(extensionId: string, extensionPoint: ExtensionPoint): void {
    const existingExtensions = this.extensions.get(extensionPoint) || [];
    
    const filteredExtensions = existingExtensions.filter(
      ext => ext.id !== extensionId
    );
    
    if (filteredExtensions.length === existingExtensions.length) {
      // No extension was removed
      return;
    }
    
    this.extensions.set(extensionPoint, filteredExtensions);
    
    // Emit event
    this.emitEvent('extension-unregistered', {
      extensionPoint,
      extensionId
    });
  }
  
  /**
   * Get extensions for a specific extension point
   */
  public getExtensions<T = any>(extensionPoint: ExtensionPoint): ExtensionContribution<T>[] {
    return (this.extensions.get(extensionPoint) || []) as ExtensionContribution<T>[];
  }
  
  /**
   * Get a service instance
   */
  public getService<T = any>(serviceId: string): T {
    const service = this.services.get(serviceId);
    if (!service) {
      throw new Error(`Service '${serviceId}' not found`);
    }
    return service as T;
  }
  
  /**
   * Register a service implementation
   */
  public registerService<T = any>(serviceId: string, implementation: T): void {
    this.services.set(serviceId, implementation);
  }
  
  /**
   * Register a plugin
   */
  public async registerPlugin(plugin: IPlugin): Promise<void> {
    const { id } = plugin.manifest;
    
    if (this.plugins.has(id)) {
      throw new Error(`Plugin with ID '${id}' is already registered`);
    }
    
    this.plugins.set(id, plugin);
    
    try {
      // Initialize the plugin
      await plugin.initialize(this);
      
      // Register all extensions from the plugin
      const extensions = plugin.getExtensions();
      extensions.forEach(extension => {
        this.registerExtension(extension);
      });
      
      // Emit plugin loaded event
      this.emitEvent('plugin-loaded', { pluginId: id });
    } catch (error) {
      // If initialization fails, unregister the plugin
      this.plugins.delete(id);
      
      // Emit plugin error event
      this.emitEvent('plugin-error', { 
        pluginId: id, 
        error 
      });
      
      throw error;
    }
  }
  
  /**
   * Unregister a plugin
   */
  public async unregisterPlugin(pluginId: string): Promise<void> {
    const plugin = this.plugins.get(pluginId);
    
    if (!plugin) {
      throw new Error(`Plugin with ID '${pluginId}' not found`);
    }
    
    // Call deactivate if implemented
    if (plugin.deactivate) {
      await plugin.deactivate();
    }
    
    // Unregister all extensions from the plugin
    const extensions = plugin.getExtensions();
    extensions.forEach(extension => {
      this.unregisterExtension(extension.id, extension.extensionPoint);
    });
    
    // Remove the plugin from the registry
    this.plugins.delete(pluginId);
    
    // Emit plugin unloaded event
    this.emitEvent('plugin-unloaded', { pluginId });
  }
  
  /**
   * Get all registered plugins
   */
  public getPlugins(): IPlugin[] {
    return Array.from(this.plugins.values());
  }
  
  /**
   * Add event listener
   */
  public addEventListener(event: PluginEventType, listener: Function): void {
    const listeners = this.eventListeners.get(event) || [];
    this.eventListeners.set(event, [...listeners, listener]);
  }
  
  /**
   * Remove event listener
   */
  public removeEventListener(event: PluginEventType, listener: Function): void {
    const listeners = this.eventListeners.get(event) || [];
    this.eventListeners.set(
      event,
      listeners.filter(l => l !== listener)
    );
  }
  
  /**
   * Emit event
   */
  private emitEvent(type: PluginEventType, data: any): void {
    const event: PluginEvent = { type, ...data };
    const listeners = this.eventListeners.get(type) || [];
    
    listeners.forEach(listener => {
      try {
        listener(event);
      } catch (error) {
        console.error(`Error in plugin event listener for event '${type}':`, error);
      }
    });
  }
}

// Create the plugin container instance
const pluginContainer = new PluginContainer();

// Create React context
const PluginContext = createContext<IPluginContainer>(pluginContainer);

/**
 * Props for PluginProvider component
 */
interface PluginProviderProps {
  children: ReactNode;
  initialPlugins?: IPlugin[];
}

/**
 * Plugin Provider component
 */
export const PluginProvider: React.FC<PluginProviderProps> = ({ 
  children,
  initialPlugins = []
}) => {
  const [isInitialized, setIsInitialized] = useState(false);
  
  useEffect(() => {
    // Initialize plugins
    const initPlugins = async (): Promise<void> => {
      for (const plugin of initialPlugins) {
        try {
          await pluginContainer.registerPlugin(plugin);
        } catch (error) {
          console.error(`Failed to initialize plugin '${plugin.manifest.id}':`, error);
        }
      }
      
      setIsInitialized(true);
    };
    
    initPlugins();
    
    return () => {
      // Cleanup plugins when the provider is unmounted
      pluginContainer.getPlugins().forEach(plugin => {
        pluginContainer.unregisterPlugin(plugin.manifest.id).catch(error => {
          console.error(`Failed to unregister plugin '${plugin.manifest.id}':`, error);
        });
      });
    };
  }, [initialPlugins]);
  
  if (!isInitialized && initialPlugins.length > 0) {
    // Show loading indicator while plugins are initializing
    return <div>Loading plugins...</div>;
  }
  
  return (
    <PluginContext.Provider value={pluginContainer}>
      {children}
    </PluginContext.Provider>
  );
};

/**
 * Hook for accessing the plugin container
 */
export const usePluginContainer = (): IPluginContainer => {
  const context = useContext(PluginContext);
  
  if (!context) {
    throw new Error('usePluginContainer must be used within a PluginProvider');
  }
  
  return context;
};

/**
 * Hook for accessing extensions for a specific extension point
 */
export const useExtensions = <T = any>(
  extensionPoint: ExtensionPoint
): ExtensionContribution<T>[] => {
  const container = usePluginContainer();
  const [extensions, setExtensions] = useState<ExtensionContribution<T>[]>(
    container.getExtensions<T>(extensionPoint)
  );
  
  useEffect(() => {
    // Update extensions when they change
    const handleExtensionChange = (event: PluginEvent) => {
      if (
        event.type === 'extension-registered' || 
        event.type === 'extension-unregistered'
      ) {
        if (event.data.extensionPoint === extensionPoint) {
          setExtensions(container.getExtensions<T>(extensionPoint));
        }
      }
    };
    
    // Add event listeners
    container.addEventListener('extension-registered', handleExtensionChange);
    container.addEventListener('extension-unregistered', handleExtensionChange);
    
    return () => {
      // Remove event listeners
      container.removeEventListener('extension-registered', handleExtensionChange);
      container.removeEventListener('extension-unregistered', handleExtensionChange);
    };
  }, [container, extensionPoint]);
  
  return extensions;
};

export default pluginContainer; 