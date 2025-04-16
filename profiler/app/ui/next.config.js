/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  // No need for appDir in Next.js 14+ as it's the default
  experimental: {
    // Remove the appDir option as it's deprecated
  }
}

module.exports = nextConfig 