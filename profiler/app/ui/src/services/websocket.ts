interface WebSocketMessage {
    type: string;
    data?: any;
    error?: string;
    timestamp?: string;
}

export class WebSocketService {
    private ws: WebSocket | null = null;
    private reconnectAttempts = 0;
    private maxReconnectAttempts = 5;
    private reconnectDelay = 1000;
    private messageHandlers: Map<string, ((data: any) => void)[]> = new Map();
    private userId: string;
    private apiKey: string = process.env.NEXT_PUBLIC_API_KEY || 'test-key-123';
    private baseUrl: string;

    constructor(userId: string) {
        this.userId = userId;
        this.baseUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';
    }

    connect(): void {
        if (this.ws) {
            console.warn('WebSocket already connected');
            return;
        }

        const encodedApiKey = encodeURIComponent(this.apiKey);
        const wsUrl = `${this.baseUrl}/ws/${this.userId}?x-api-key=${encodedApiKey}`;
        console.log('Connecting to WebSocket:', wsUrl);
        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
            console.log('WebSocket connected');
            this.reconnectAttempts = 0;
            // Send initial connection message
            this.sendMessage('connection_init', { userId: this.userId });
        };

        this.ws.onmessage = (event: MessageEvent) => {
            try {
                const message: WebSocketMessage = JSON.parse(event.data);
                console.log('Received WebSocket message:', message);
                this.handleMessage(message);
            } catch (error) {
                console.error('Error parsing WebSocket message:', error);
            }
        };

        this.ws.onclose = (event: CloseEvent) => {
            console.log('WebSocket disconnected:', event.code, event.reason);
            this.ws = null;
            this.reconnect();
        };

        this.ws.onerror = (error: Event) => {
            console.error('WebSocket error:', error);
            // Attempt to reconnect on error
            this.reconnect();
        };
    }

    private reconnect(): void {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error('Max reconnection attempts reached');
            return;
        }

        this.reconnectAttempts++;
        setTimeout(() => {
            console.log(`Reconnecting... Attempt ${this.reconnectAttempts}`);
            this.connect();
        }, this.reconnectDelay * this.reconnectAttempts);
    }

    private handleMessage(message: WebSocketMessage): void {
        const handlers = this.messageHandlers.get(message.type);
        if (handlers) {
            handlers.forEach(handler => handler(message.data));
        }
    }

    sendMessage(type: string, data: any): void {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
            console.error('WebSocket is not connected');
            return;
        }

        const message: WebSocketMessage = {
            type,
            data,
            timestamp: new Date().toISOString()
        };

        this.ws.send(JSON.stringify(message));
    }

    onMessage(type: string, handler: (data: any) => void): void {
        if (!this.messageHandlers.has(type)) {
            this.messageHandlers.set(type, []);
        }
        this.messageHandlers.get(type)?.push(handler);
    }

    disconnect(): void {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }
} 