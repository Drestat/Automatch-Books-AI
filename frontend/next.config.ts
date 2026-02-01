import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    unoptimized: true,
  },
  distDir: '../.next',
};

export default nextConfig;
