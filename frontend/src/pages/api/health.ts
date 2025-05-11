import type { NextApiRequest, NextApiResponse } from 'next';
import { serviceDiscovery, ServiceRegistry, ServiceEndpoint } from '@/services/discovery/service-discovery';

type HealthResponse = {
  status: string;
  timestamp: number;
  version: string;
  environment: string;
  services: ServiceRegistry;
};

/**
 * Health check endpoint for the frontend service
 */
export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse<HealthResponse>
) {
  // Start service discovery if not already running
  await serviceDiscovery.startHealthChecks();

  // Get current service status
  const services = serviceDiscovery.getServiceStatus();

  // Calculate overall status
  const isHealthy = Object.values(services).every((service: ServiceEndpoint) => service.isHealthy);

  res.status(200).json({
    status: isHealthy ? 'ok' : 'degraded',
    timestamp: Date.now(),
    version: process.env.NEXT_PUBLIC_VERSION || '1.0.0',
    environment: process.env.NODE_ENV || 'development',
    services,
  });
} 