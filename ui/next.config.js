/** @type {import('next').NextConfig} */
const nextConfig = {
  // Disable React strict mode in production for better performance
  reactStrictMode: process.env.NODE_ENV === 'development',
  
  // Output standalone build for better performance on Vercel
  output: 'standalone',
  
  // Increase Lambda function timeout
  serverRuntimeConfig: {
    vercelTimeout: 60, // 60 seconds
  },
  
  // Optimize production builds
  compiler: {
    removeConsole: process.env.NODE_ENV === 'production' 
      ? { exclude: ['error', 'warn', 'info'] } 
      : false,
  },
  
  // Configure header to enable CORS for API routes
  async headers() {
    return [
      {
        source: '/api/:path*',
        headers: [
          { key: 'Access-Control-Allow-Credentials', value: 'true' },
          { key: 'Access-Control-Allow-Origin', value: '*' },
          { key: 'Access-Control-Allow-Methods', value: 'GET,OPTIONS,PATCH,DELETE,POST,PUT' },
          { key: 'Access-Control-Allow-Headers', value: 'X-CSRF-Token, X-Requested-With, Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, X-Api-Version, Authorization' },
        ],
      },
    ];
  },
  
  // External packages for server components
  serverExternalPackages: ['mongoose'],
  
  // Experimental features
  experimental: {
    largePageDataBytes: 512 * 1000, // 512KB
  },
};

module.exports = nextConfig; 