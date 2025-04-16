import { 
  IProfileClient, 
  ApiResponse, 
  WebSocketConfig, 
  WebSocketError 
} from './interfaces';
import { WebSocketClient } from './websocket-client';

export interface ProfileData {
  userId: string;
  status: 'idle' | 'processing' | 'completed' | 'error';
  progress: number;
  sections?: Record<string, any>;
  current_section?: string;
  current_questions?: any[];
  data?: any;
  error?: string;
}

/**
 * ProfileClient - Handles all profile-related API communication
 */
export class ProfileClient implements IProfileClient {
  private wsClient: WebSocketClient;
  private profileUpdateHandlers: ((profile: ProfileData) => void)[] = [];
  private lastKnownProfile: ProfileData | null = null;
  
  constructor(config: WebSocketConfig) {
    this.wsClient = new WebSocketClient(config);
    
    // Set up handlers for profile updates
    this.wsClient.onMessage('state_update', (data: ProfileData) => {
      this.lastKnownProfile = data;
      this.notifyProfileUpdateHandlers(data);
    });
    
    this.wsClient.onMessage('error', (error: string) => {
      if (this.lastKnownProfile) {
        const updatedProfile = {
          ...this.lastKnownProfile,
          status: 'error' as const,
          error
        };
        this.lastKnownProfile = updatedProfile;
        this.notifyProfileUpdateHandlers(updatedProfile);
      }
    });
  }
  
  async initialize(): Promise<void> {
    await this.wsClient.initialize();
  }
  
  shutdown(): void {
    this.wsClient.shutdown();
    this.profileUpdateHandlers = [];
  }
  
  async getProfile(userId: string): Promise<ApiResponse<ProfileData>> {
    // If we already have the profile in memory, return it immediately
    if (this.lastKnownProfile && this.lastKnownProfile.userId === userId) {
      return {
        status: 'success',
        data: this.lastKnownProfile
      };
    }
    
    // Otherwise, we need to request it via WebSocket - we'll create a promise that will be resolved when we get a response
    return new Promise((resolve) => {
      const onceHandler = (data: ProfileData) => {
        if (data.userId === userId) {
          // Remove this one-time handler
          this.profileUpdateHandlers = this.profileUpdateHandlers.filter(h => h !== onceHandler);
          resolve({
            status: 'success',
            data
          });
        }
      };
      
      // Add a one-time handler for this specific user ID
      this.profileUpdateHandlers.push(onceHandler);
      
      // Request the profile via WebSocket
      this.wsClient.sendMessage('get_profile', { userId });
      
      // Set a timeout to avoid hanging promises
      setTimeout(() => {
        // If we haven't resolved yet, do so now with an error
        // First, remove the handler
        this.profileUpdateHandlers = this.profileUpdateHandlers.filter(h => h !== onceHandler);
        
        // If we got a profile in the meantime, return it
        if (this.lastKnownProfile && this.lastKnownProfile.userId === userId) {
          resolve({
            status: 'success',
            data: this.lastKnownProfile
          });
        } else {
          resolve({
            status: 'error',
            error: 'Timeout waiting for profile data'
          });
        }
      }, 5000);
    });
  }
  
  async updateProfile(userId: string, data: any): Promise<ApiResponse<ProfileData>> {
    return new Promise((resolve) => {
      const onceHandler = (updatedProfile: ProfileData) => {
        if (updatedProfile.userId === userId) {
          // Remove this one-time handler
          this.profileUpdateHandlers = this.profileUpdateHandlers.filter(h => h !== onceHandler);
          resolve({
            status: 'success',
            data: updatedProfile
          });
        }
      };
      
      // Add a one-time handler for this specific user ID
      this.profileUpdateHandlers.push(onceHandler);
      
      // Send the update via WebSocket
      this.wsClient.sendMessage('update_profile', { userId, data });
      
      // Set a timeout to avoid hanging promises
      setTimeout(() => {
        // If we haven't resolved yet, do so now with an error
        // First, remove the handler
        this.profileUpdateHandlers = this.profileUpdateHandlers.filter(h => h !== onceHandler);
        
        // If we got a profile update in the meantime, return it
        if (this.lastKnownProfile && this.lastKnownProfile.userId === userId) {
          resolve({
            status: 'success',
            data: this.lastKnownProfile
          });
        } else {
          resolve({
            status: 'error',
            error: 'Timeout waiting for profile update'
          });
        }
      }, 5000);
    });
  }
  
  onProfileUpdate(handler: (profile: ProfileData) => void): void {
    this.profileUpdateHandlers.push(handler);
    
    // If we already have profile data, notify the handler immediately
    if (this.lastKnownProfile) {
      try {
        handler(this.lastKnownProfile);
      } catch (error) {
        console.error('Error in profile update handler:', error);
      }
    }
  }
  
  connect(): void {
    this.wsClient.connect();
  }
  
  disconnect(): void {
    this.wsClient.disconnect();
  }
  
  sendMessage(type: string, data: any): void {
    this.wsClient.sendMessage(type, data);
  }
  
  private notifyProfileUpdateHandlers(profile: ProfileData): void {
    this.profileUpdateHandlers.forEach(handler => {
      try {
        handler(profile);
      } catch (error) {
        console.error('Error in profile update handler:', error);
      }
    });
  }
} 