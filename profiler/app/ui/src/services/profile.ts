import { getProfileClient, IProfileClient, ProfileData } from './api';

export type ProfileState = ProfileData;

export class ProfileService {
    private profileClient: IProfileClient;
    private state: ProfileState;
    private stateHandlers: ((state: ProfileState) => void)[] = [];

    constructor(userId: string) {
        this.profileClient = getProfileClient(userId);
        this.state = {
            userId,
            status: 'idle',
            progress: 0
        };
        
        // Set up profile update handlers
        this.profileClient.onProfileUpdate((profile) => {
            this.updateState(profile);
        });
    }

    connect(): void {
        this.profileClient.connect();
    }

    disconnect(): void {
        this.profileClient.disconnect();
    }

    private updateState(newState: ProfileState): void {
        this.state = newState;
        this.notifyStateChange();
    }

    private notifyStateChange(): void {
        this.stateHandlers.forEach(handler => handler(this.state));
    }

    onStateChange(handler: (state: ProfileState) => void): void {
        this.stateHandlers.push(handler);
        // Immediately notify with current state
        handler(this.state);
    }

    getState(): ProfileState {
        return this.state;
    }

    async fetchProfile(): Promise<ProfileState> {
        const response = await this.profileClient.getProfile(this.state.userId);
        if (response.status === 'success' && response.data) {
            this.updateState(response.data);
            return this.state;
        }
        return this.state;
    }

    sendMessage(type: string, data: any): void {
        this.profileClient.sendMessage(type, data);
    }
} 