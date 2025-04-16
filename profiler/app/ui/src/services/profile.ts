import { WebSocketService } from './websocket';

export interface ProfileState {
    userId: string;
    status: 'idle' | 'processing' | 'completed' | 'error';
    progress: number;
    data?: any;
    error?: string;
}

export class ProfileService {
    private wsService: WebSocketService;
    private state: ProfileState;
    private stateHandlers: ((state: ProfileState) => void)[] = [];

    constructor(userId: string) {
        this.wsService = new WebSocketService(userId);
        this.state = {
            userId,
            status: 'idle',
            progress: 0
        };

        // Set up WebSocket message handlers
        this.wsService.onMessage('state_update', (data: ProfileState) => {
            this.updateState(data);
        });

        this.wsService.onMessage('error', (error: string) => {
            this.updateState({
                ...this.state,
                status: 'error',
                error
            });
        });
    }

    connect(): void {
        this.wsService.connect();
    }

    disconnect(): void {
        this.wsService.disconnect();
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

    sendMessage(type: string, data: any): void {
        this.wsService.sendMessage(type, data);
    }
} 