import { ServiceRegistry, ServiceStatus, ServiceDefinition } from '../services/service_registry';

/**
 * Initialize core services in the registry
 */
export const initializeServices = async () => {
  const registry = new ServiceRegistry();

  // Register auth service
  const authService: ServiceDefinition = {
    id: 'auth-service',
    name: 'Authentication Service',
    description: 'Handles user authentication and registration',
    baseUrl: 'http://localhost:8001/api/auth',
    status: ServiceStatus.ACTIVE,
    allowedRoles: ['any'], // Allow registration for anyone
    configOptions: {
      registrationEnabled: true,
      emailVerificationRequired: true
    }
  };

  await registry.registerService(authService);

  return registry;
}; 