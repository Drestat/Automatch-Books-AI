import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Image optimization enabled for web (Vercel).
  // Capacitor native pages use <Image unoptimized> prop individually.
  // Exclude Capacitor native packages from server-side bundling.
  // These are client-only modules that use dynamic imports at runtime.
  serverExternalPackages: [
    '@capacitor/core',
    '@capacitor/camera',
    '@capacitor/haptics',
    '@capacitor/push-notifications',
    '@capacitor/splash-screen',
    '@capacitor/preferences',
    '@capacitor/background-runner',
    '@capawesome/capacitor-badge',
    'capacitor-biometric-auth',
  ],
};

export default nextConfig;
