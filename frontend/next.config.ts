import type { NextConfig } from "next";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

// Strip /api/v1 suffix to get the base URL for the proxy
const API_BASE = API_URL.replace(/\/api\/v1\/?$/, "");

const nextConfig: NextConfig = {
  images: {
    domains: ["avatars.githubusercontent.com", "github.com"],
  },
  typescript: { ignoreBuildErrors: true },
  eslint: { ignoreDuringBuilds: true },

  // Proxy /api/v1/* → backend so CORS is never an issue
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
