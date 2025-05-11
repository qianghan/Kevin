import { startBackendServices } from './services/backend.js';
import { startUIServices } from './services/ui.js';
import { startFrontendServices } from './services/frontend.js';
import { healthCheck } from './utils/health-check.js';
import { loadTestEnvironment } from './utils/env.js';

/**
 * Options for configuring the integrated test environment
 */
export interface TestEnvironmentOptions {
  backend?: {
    port?: number;
    dbUri?: string;
    environment?: string;
  };
  ui?: {
    port?: number;
    environment?: string;
  };
  frontend?: {
    port?: number;
    environment?: string;
  };
}

/**
 * Starts all services required for the integrated test environment
 * 
 * @param options Configuration options for the test environment
 * @returns Configuration object with service endpoints and teardown function
 */
export async function startIntegratedTestEnvironment(options: TestEnvironmentOptions = {}) {
  // Load environment variables
  loadTestEnvironment();
  
  console.log('Starting backend services...');
  const backendConfig = await startBackendServices(options.backend);
  
  console.log('Starting UI services...');
  const uiConfig = await startUIServices({
    ...options.ui,
    backendEndpoints: backendConfig.endpoints,
  });
  
  console.log('Starting frontend services...');
  const frontendConfig = await startFrontendServices({
    ...options.frontend,
    backendEndpoints: backendConfig.endpoints,
    uiEndpoints: uiConfig.endpoints,
  });
  
  console.log('Running health checks...');
  await healthCheck({
    backend: backendConfig.endpoints,
    ui: uiConfig.endpoints,
    frontend: { url: `http://localhost:${frontendConfig.port}` },
  });
  
  return {
    backend: backendConfig,
    ui: uiConfig,
    frontend: frontendConfig,
    teardown: async () => {
      console.log('Shutting down all services...');
      await Promise.all([
        backendConfig.shutdown(),
        uiConfig.shutdown(),
        frontendConfig.shutdown(),
      ]);
      console.log('All services shut down successfully');
    }
  };
}

// Command line interface for running the environment
if (require.main === module) {
  (async () => {
    try {
      const env = await startIntegratedTestEnvironment();
      console.log('Integrated test environment started successfully');
      console.log('Press Ctrl+C to stop all services');
      
      // Handle graceful shutdown
      process.on('SIGINT', async () => {
        console.log('Received SIGINT, shutting down...');
        await env.teardown();
        process.exit(0);
      });
    } catch (error) {
      console.error('Failed to start integrated test environment:', error);
      process.exit(1);
    }
  })();
} 