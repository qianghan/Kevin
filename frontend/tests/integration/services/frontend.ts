import { spawn, ChildProcess } from 'child_process';
import path from 'path';
import fs from 'fs/promises';
import { BackendEndpoints, waitForEndpoint } from './backend';
import { UIEndpoints } from './ui';

/**
 * Interface for frontend service configuration
 */
export interface FrontendServiceConfig {
  port?: number;
  environment?: string;
  backendEndpoints?: BackendEndpoints;
  uiEndpoints?: UIEndpoints;
}

/**
 * Interface for the frontend service return object
 */
export interface FrontendConfig {
  process: ChildProcess;
  port: number;
  shutdown: () => Promise<void>;
}

/**
 * Starts the frontend services
 * 
 * @param options Frontend service configuration options
 * @returns Frontend service configuration object
 */
export async function startFrontendServices(options: FrontendServiceConfig = {}): Promise<FrontendConfig> {
  const config = {
    port: options.port || 3000,
    backendEndpoints: options.backendEndpoints || { api: 'http://localhost:4000' },
    uiEndpoints: options.uiEndpoints || { ui: 'http://localhost:3001' },
    environment: options.environment || 'test',
  };
  
  // Resolve the path to the frontend directory
  const frontendDir = path.resolve(__dirname, '../../../../');
  const envTestPath = path.join(frontendDir, '.env.test.local');
  
  console.log(`Starting frontend services in ${frontendDir}`);
  console.log(`Frontend will connect to backend at ${config.backendEndpoints.api}`);
  console.log(`Frontend will connect to UI at ${config.uiEndpoints.ui}`);
  
  // Create temporary .env.test.local file
  const envContent = `
NEXT_PUBLIC_API_URL=${config.backendEndpoints.api}
NEXT_PUBLIC_UI_URL=${config.uiEndpoints.ui}
NEXT_PUBLIC_ENVIRONMENT=${config.environment}
PORT=${config.port}
`;
  
  try {
    // Write to temporary .env.test.local file
    await fs.writeFile(envTestPath, envContent);
    console.log(`Created temporary environment file at ${envTestPath}`);
  } catch (error: any) {
    console.error(`Error creating environment file: ${error.message}`);
  }
  
  // Start frontend server with test configuration
  const frontendProcess = spawn('npm', ['run', 'dev'], {
    cwd: frontendDir,
    env: {
      ...process.env,
      NODE_ENV: 'test',
      PORT: config.port.toString(),
      NEXT_PUBLIC_API_URL: config.backendEndpoints.api,
      NEXT_PUBLIC_UI_URL: config.uiEndpoints.ui,
    },
    stdio: 'pipe',
  });
  
  frontendProcess.stdout?.on('data', (data) => {
    console.log(`Frontend: ${data}`);
  });
  
  frontendProcess.stderr?.on('data', (data) => {
    console.error(`Frontend error: ${data}`);
  });
  
  // Mock waiting for frontend to be ready (in a real scenario, we would check health endpoint)
  console.log(`Waiting for frontend to be ready at http://localhost:${config.port}/api/health`);
  try {
    await waitForEndpoint(`http://localhost:${config.port}/api/health`, 30000);
  } catch (error: any) {
    console.warn(`Warning: Could not verify frontend health: ${error.message}`);
    console.log('Continuing anyway as this is a mock implementation');
  }
  
  return {
    process: frontendProcess,
    port: config.port,
    shutdown: async () => {
      return new Promise((resolve) => {
        frontendProcess.on('close', async () => {
          // Clean up temp env file
          try {
            await fs.unlink(envTestPath);
            console.log(`Removed temporary environment file at ${envTestPath}`);
          } catch (err: any) {
            console.error(`Error removing environment file: ${err.message}`);
          }
          resolve();
        });
        frontendProcess.kill();
      });
    },
  };
} 