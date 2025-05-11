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
  
  // Configure headers for API routes and locales
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
      {
        source: '/locales/:path*',
        headers: [
          {
            key: 'Cache-Control',
            value: 'no-store, must-revalidate'
          }
        ]
      }
    ];
  },
  
  // External packages that should be transpiled
  transpilePackages: ['@userman/core'],

  // Packages that should be treated as external in server components
  serverExternalPackages: [
    'bcrypt',
    '@mapbox/node-pre-gyp',
    'aws-sdk',
    'mongoose',
    'child_process',
    'fs',
    'net',
    'tls',
    'crypto',
    'os',
    'path',
    'stream',
    'util',
    'zlib',
    'nock',
    '@mswjs/interceptors'
  ],
  
  // Experimental features
  experimental: {
    largePageDataBytes: 512 * 1000, // 512KB
  },

  // Webpack configuration to handle native modules
  webpack: (config, { isServer }) => {
    if (!isServer) {
      // Don't attempt to load native modules in the browser
      config.resolve.fallback = {
        ...config.resolve.fallback,
        bcrypt: false,
        fs: false,
        net: false,
        tls: false,
        crypto: false,
        'aws-sdk': false,
        child_process: false,
        os: false,
        path: false,
        stream: false,
        util: false,
        zlib: false,
        nock: false,
        '@mswjs/interceptors': false,
        '@mswjs/interceptors/presets/node': false
      };
    }
    return config;
  },

  // Configure rewrites for locales
  async rewrites() {
    return [
      // Handle locale paths for i18n resources
      {
        source: '/locales/:path*',
        destination: '/locales/:path*'
      },
      {
        source: '/:locale/locales/:path*',
        destination: '/locales/:path*'
      },
      {
        source: '/:locale/:path*/locales/:file*',
        destination: '/locales/:file*'
      },
      // Handle all dynamic routes that need locales
      {
        source: '/en/:path*',
        destination: '/en/:path*'
      },
      {
        source: '/zh/:path*',
        destination: '/zh/:path*'
      },
      {
        source: '/fr/:path*',
        destination: '/fr/:path*'
      },
      {
        source: '/es/:path*',
        destination: '/es/:path*'
      }
    ];
  }
};

module.exports = nextConfig; 