import * as dotenv from 'dotenv';
import * as path from 'path';
import * as fs from 'fs';

/**
 * Loads test environment variables from .env files
 * 
 * @returns Loaded environment variables
 */
export function loadTestEnvironment(): NodeJS.ProcessEnv {
  // Load environment-specific variables
  const envFiles = [
    '.env.test.local', // Local overrides
    '.env.test',       // Test environment defaults
    '.env',            // Global defaults
  ];
  
  for (const file of envFiles) {
    const filePath = path.resolve(process.cwd(), file);
    if (fs.existsSync(filePath)) {
      const result = dotenv.config({ path: filePath });
      if (result.error) {
        console.error(`Error loading environment from ${file}:`, result.error);
      } else {
        console.log(`Loaded environment variables from ${file}`);
      }
    }
  }
  
  // Set default values for required variables if not present
  const defaults: Record<string, string> = {
    'API_URL': 'http://localhost:4000',
    'UI_URL': 'http://localhost:3001',
    'FRONTEND_URL': 'http://localhost:3000',
    'MONGODB_URI': 'mongodb://localhost:27017/kai-test',
  };
  
  for (const [key, value] of Object.entries(defaults)) {
    if (!process.env[key]) {
      process.env[key] = value;
      console.log(`Using default value for ${key}: ${value}`);
    }
  }
  
  return process.env;
}

/**
 * Gets the integration test configuration from environment variables
 * 
 * @returns Integration test configuration
 */
export function getIntegrationConfig() {
  const env = loadTestEnvironment();
  
  return {
    backend: {
      port: parseInt(env.API_PORT || '4000', 10),
      dbUri: env.MONGODB_URI || 'mongodb://localhost:27017/kai-test',
    },
    ui: {
      port: parseInt(env.UI_PORT || '3001', 10),
    },
    frontend: {
      port: parseInt(env.FRONTEND_PORT || '3000', 10),
    },
  };
} 