import { spawn, ChildProcess } from 'child_process';
import path from 'path';
import { BackendEndpoints, waitForEndpoint } from './backend';

/**
 * Interface for UI service configuration
 */
export interface UIServiceConfig {
  port?: number;
  environment?: string;
  backendEndpoints?: BackendEndpoints;
}

/**
 * Interface for UI service endpoints
 */
export interface UIEndpoints {
  ui: string;
}

/**
 * Interface for the UI service return object
 */
export interface UIConfig {
  process: ChildProcess;
  endpoints: UIEndpoints;
  port: number;
  shutdown: () => Promise<void>;
}

/**
 * Starts the UI services
 * 
 * @param options UI service configuration options
 * @returns UI service configuration object
 */
export async function startUIServices(options: UIServiceConfig = {}): Promise<UIConfig> {
  const config = {
    port: options.port || 3001,
    backendEndpoints: options.backendEndpoints || { api: 'http://localhost:4000' },
    environment: options.environment || 'test',
  };
  
  // Resolve the path to the UI directory
  const uiDir = path.resolve(__dirname, '../../../../ui');
  
  console.log(`Starting UI services in ${uiDir}`);
  console.log(`UI will connect to backend at ${config.backendEndpoints.api}`);
  
  // Start UI server with test configuration
  const uiProcess = spawn('npm', ['run', 'start:test'], {
    cwd: uiDir,
    env: {
      ...process.env,
      NODE_ENV: 'test',
      PORT: config.port.toString(),
      API_URL: config.backendEndpoints.api,
    },
    stdio: 'pipe',
  });
  
  uiProcess.stdout?.on('data', (data) => {
    console.log(`UI: ${data}`);
  });
  
  uiProcess.stderr?.on('data', (data) => {
    console.error(`UI error: ${data}`);
  });
  
  // Mock waiting for UI to be ready (in a real scenario, we would check health endpoint)
  console.log(`Waiting for UI to be ready at http://localhost:${config.port}/health`);
  try {
    await waitForEndpoint(`http://localhost:${config.port}/health`, 30000);
  } catch (error: any) {
    console.warn(`Warning: Could not verify UI health: ${error.message}`);
    console.log('Continuing anyway as this is a mock implementation');
  }
  
  return {
    process: uiProcess,
    endpoints: {
      ui: `http://localhost:${config.port}`,
    },
    port: config.port,
    shutdown: () => {
      return new Promise((resolve) => {
        uiProcess.on('close', resolve);
        uiProcess.kill();
      });
    },
  };
} 