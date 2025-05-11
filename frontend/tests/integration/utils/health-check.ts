/**
 * Interface for health check endpoints
 */
export interface HealthCheckEndpoints {
  backend: {
    api: string;
  };
  ui: {
    ui: string;
  };
  frontend: {
    url: string;
  };
}

/**
 * Health check service with retry logic
 * 
 * @param url URL to check
 * @param maxRetries Maximum number of retries
 * @param retryInterval Interval between retries in milliseconds
 * @returns Promise that resolves when the endpoint is healthy
 */
export async function checkEndpoint(url: string, maxRetries = 5, retryInterval = 2000): Promise<boolean> {
  for (let i = 0; i < maxRetries; i++) {
    try {
      const response = await fetch(url);
      if (response.ok) {
        console.log(`Health check passed for ${url}`);
        return true;
      }
      console.log(`Health check failed for ${url}, status: ${response.status}, retrying (${i + 1}/${maxRetries})...`);
    } catch (error: any) {
      console.log(`Health check error for ${url}: ${error.message}, retrying (${i + 1}/${maxRetries})...`);
    }
    
    // Wait before retry
    if (i < maxRetries - 1) {
      await new Promise(resolve => setTimeout(resolve, retryInterval));
    }
  }
  
  throw new Error(`Health check failed for ${url} after ${maxRetries} attempts`);
}

/**
 * Check all services
 * 
 * @param endpoints Health check endpoints
 * @returns Promise that resolves when all services are healthy
 */
export async function healthCheck(endpoints: HealthCheckEndpoints): Promise<boolean> {
  console.log('Running health checks...');
  
  const checks = [
    checkEndpoint(`${endpoints.backend.api}/health`),
    checkEndpoint(`${endpoints.ui.ui}/health`),
    checkEndpoint(`${endpoints.frontend.url}/api/health`),
  ];
  
  try {
    await Promise.all(checks);
    console.log('All services are healthy');
    return true;
  } catch (error: any) {
    console.error('Health check failed:', error.message);
    throw error;
  }
} 