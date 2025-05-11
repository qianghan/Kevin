/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  experimental: {
    forceSwcTransforms: true,
  },
  async headers() {
    return [
      {
        // Allow CORS for all routes
        source: '/:path*',
        headers: [
          { key: 'Access-Control-Allow-Origin', value: '*' },
          { key: 'Access-Control-Allow-Methods', value: 'GET,POST,PUT,DELETE,OPTIONS' },
          { key: 'Access-Control-Allow-Headers', value: 'Content-Type, Authorization' },
        ],
      },
    ];
  },
  // Configure rewrites for development
  async rewrites() {
    return [
      {
        source: '/api/chat/:path*',
        destination: 'http://localhost:8000/api/chat/:path*',
      },
      {
        source: '/api/auth/:path*',
        destination: 'http://localhost:8000/api/auth/:path*',
      },
    ];
  },
  // Configure webpack for development
  webpack: (config, { dev, isServer }) => {
    if (dev && !isServer) {
      // Enable hot module replacement
      config.watchOptions = {
        poll: 1000,
        aggregateTimeout: 300,
      };
    }
    
    // Optimize webpack cache to reduce serialization warnings
    config.infrastructureLogging = config.infrastructureLogging || {};
    config.infrastructureLogging.level = 'error';
    
    if (config.optimization && config.optimization.splitChunks) {
      config.optimization.splitChunks.cacheGroups = {
        ...(config.optimization.splitChunks.cacheGroups || {}),
        // Create a separate chunk for large modules
        largePackages: {
          test: /[\\/]node_modules[\\/](lodash|rxjs|@chakra-ui)[\\/]/,
          name: 'large-packages',
          priority: 10,
          chunks: 'all',
        },
      };
    }
    
    return config;
  },
}

module.exports = nextConfig 