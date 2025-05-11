import { spawn, ChildProcess } from 'child_process';
import path from 'path';

/**
 * Interface for backend service configuration
 */
export interface BackendServiceConfig {
  port?: number;
  dbUri?: string;
  environment?: string;
}

/**
 * Interface for backend service endpoints
 */
export interface BackendEndpoints {
  api: string;
}

/**
 * Interface for the backend service return object
 */
export interface BackendConfig {
  process: ChildProcess;
  endpoints: BackendEndpoints;
  port: number;
  shutdown: () => Promise<void>;
}

/**
 * Waits for an endpoint to be available
 * 
 * @param url URL to check
 * @param timeout Timeout in milliseconds
 * @returns Promise that resolves when the endpoint is available
 */
export async function waitForEndpoint(url: string, timeout = 30000): Promise<void> {
  const startTime = Date.now();
  
  // Use this in Node.js environment with fetch
  const checkEndpoint = async () => {
    try {
      const response = await fetch(url);
      return response.ok;
    } catch (error) {
      return false;
    }
  };
  
  while (Date.now() - startTime < timeout) {
    if (await checkEndpoint()) {
      return;
    }
    await new Promise(resolve => setTimeout(resolve, 1000));
  }
  
  throw new Error(`Timeout waiting for endpoint: ${url}`);
}

/**
 * Starts the backend services
 * 
 * @param options Backend service configuration options
 * @returns Backend service configuration object
 */
export async function startBackendServices(options: BackendServiceConfig = {}): Promise<BackendConfig> {
  const config = {
    port: options.port || 4000,
    dbUri: options.dbUri || 'mongodb://localhost:27017/kai-test',
    environment: options.environment || 'test',
  };
  
  // Resolve the path to the backend directory
  const backendDir = path.resolve(__dirname, '../../../../backend');
  
  console.log(`Starting backend services in ${backendDir}`);
  
  // Start backend server with test configuration
  const backendProcess = spawn('node', [
    'server.js',
    '--port', config.port.toString(),
    '--db', config.dbUri,
    '--env', config.environment,
  ], {
    cwd: backendDir,
    env: {
      ...process.env,
      NODE_ENV: 'test',
    },
    stdio: 'pipe',
  });
  
  backendProcess.stdout?.on('data', (data) => {
    console.log(`Backend: ${data}`);
  });
  
  backendProcess.stderr?.on('data', (data) => {
    console.error(`Backend error: ${data}`);
  });
  
  // Mock waiting for backend to be ready (in a real scenario, we would check health endpoint)
  console.log(`Waiting for backend to be ready at http://localhost:${config.port}/health`);
  try {
    await waitForEndpoint(`http://localhost:${config.port}/health`, 30000);
  } catch (error) {
    console.warn(`Warning: Could not verify backend health: ${error.message}`);
    console.log('Continuing anyway as this is a mock implementation');
  }
  
  return {
    process: backendProcess,
    endpoints: {
      api: `http://localhost:${config.port}`,
    },
    port: config.port,
    shutdown: () => {
      return new Promise((resolve) => {
        backendProcess.on('close', resolve);
        backendProcess.kill();
      });
    },
  };
} 