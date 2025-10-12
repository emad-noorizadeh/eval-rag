import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: true,
  },
  // Disable all telemetry and analytics
  experimental: {
    telemetry: false,
  },
  // Disable webpack telemetry
  webpack: (config: any) => {
    config.infrastructureLogging = {
      level: 'error',
    };
    return config;
  },
  // Disable build telemetry
  generateBuildId: async () => {
    return 'build-' + Date.now();
  },
};

export default nextConfig;
