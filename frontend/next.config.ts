import type { NextConfig } from "next";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
// Extract base URL (without /api/v1) for the proxy destination
const API_BASE = API_URL.replace(/\/api\/v1\/?$/, "");

const nextConfig: NextConfig = {
  images: {
    domains: ["avatars.githubusercontent.com", "github.com"],
  },
  typescript: { ignoreBuildErrors: true },
  eslint: { ignoreDuringBuilds: true },

  // Proxy /api/v1/* → backend so there are zero CORS issues in dev
  async rewrites() {
    return [
      {
        source: "/api/v1/:path*",
        destination: `${API_BASE}/api/v1/:path*`,
      },
    ];
  },
};

export default nextConfig;
