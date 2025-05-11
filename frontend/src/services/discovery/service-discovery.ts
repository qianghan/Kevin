export interface ServiceEndpoint {
  url: string;
  isHealthy: boolean;
  lastCheck: number;
}

export interface ServiceRegistry {
  chat: ServiceEndpoint;
  mongodb: ServiceEndpoint;
  auth: ServiceEndpoint;
}

class ServiceDiscovery {
  private static instance: ServiceDiscovery;
  private registry: ServiceRegistry;
  private checkInterval: NodeJS.Timeout | null = null;

  private constructor() {
    this.registry = {
      chat: {
        url: process.env.NEXT_PUBLIC_CHAT_API_URL || 'http://localhost:8000',
        isHealthy: false,
        lastCheck: 0,
      },
      mongodb: {
        url: process.env.MONGODB_URI || 'mongodb://localhost:27018/kevin',
        isHealthy: false,
        lastCheck: 0,
      },
      auth: {
        url: process.env.NEXT_PUBLIC_AUTH_URL || 'http://localhost:8000/auth',
        isHealthy: false,
        lastCheck: 0,
      },
    };
  }

  public static getInstance(): ServiceDiscovery {
    if (!ServiceDiscovery.instance) {
      ServiceDiscovery.instance = new ServiceDiscovery();
    }
    return ServiceDiscovery.instance;
  }

  public async startHealthChecks(interval: number = 30000): Promise<void> {
    if (this.checkInterval) {
      clearInterval(this.checkInterval);
    }

    // Initial check
    await this.checkAllServices();

    // Set up periodic checks
    this.checkInterval = setInterval(() => {
      this.checkAllServices();
    }, interval);
  }

  public stopHealthChecks(): void {
    if (this.checkInterval) {
      clearInterval(this.checkInterval);
      this.checkInterval = null;
    }
  }

  public getServiceStatus(): ServiceRegistry {
    return { ...this.registry };
  }

  private async checkAllServices(): Promise<void> {
    const checks = [
      this.checkChatService(),
      this.checkMongoDBService(),
      this.checkAuthService(),
    ];

    await Promise.all(checks);
  }

  private async checkChatService(): Promise<void> {
    try {
      const response = await fetch(`${this.registry.chat.url}/health`);
      this.registry.chat.isHealthy = response.ok;
    } catch {
      this.registry.chat.isHealthy = false;
    }
    this.registry.chat.lastCheck = Date.now();
  }

  private async checkMongoDBService(): Promise<void> {
    try {
      const response = await fetch('http://localhost:27018');
      this.registry.mongodb.isHealthy = response.ok;
    } catch {
      this.registry.mongodb.isHealthy = false;
    }
    this.registry.mongodb.lastCheck = Date.now();
  }

  private async checkAuthService(): Promise<void> {
    try {
      const response = await fetch(`${this.registry.auth.url}/health`);
      this.registry.auth.isHealthy = response.ok;
    } catch {
      this.registry.auth.isHealthy = false;
    }
    this.registry.auth.lastCheck = Date.now();
  }
}

export const serviceDiscovery = ServiceDiscovery.getInstance();
export default serviceDiscovery; 