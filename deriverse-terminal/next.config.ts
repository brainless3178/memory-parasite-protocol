import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  // Output standalone for Docker deployments
  output: 'standalone',
  
  // Disable strict mode for framer-motion compatibility
  reactStrictMode: false,
  
  // Image optimization
  images: {
    unoptimized: true,
  },
  
  // Environment variables available to browser
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'https://memory-parasite-protocol-brainless3178.koyeb.app',
  },
  
  // Typescript config
  typescript: {
    // Don't fail build on type errors in production
    ignoreBuildErrors: false,
  },
};

export default nextConfig;
