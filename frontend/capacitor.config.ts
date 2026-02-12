import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.automatchbooks.ai',
  appName: 'AutoMatch Books AI',
  webDir: 'out',
  server: {
    // Use the live URL so Clerk, API calls, etc. work correctly
    url: 'https://www.automatchbooksai.com',
    cleartext: false,
  },
  plugins: {
    SplashScreen: {
      launchShowDuration: 2000,
      launchAutoHide: true,
      backgroundColor: '#000000',
      androidSplashResourceName: 'splash',
      androidScaleType: 'CENTER_CROP',
      showSpinner: false,
      splashFullScreen: true,
      splashImmersive: true,
    },
    PushNotifications: {
      presentationOptions: ['badge', 'sound', 'alert'],
    },
    Camera: {
      // iOS permissions are handled in Info.plist
    },
    BackgroundRunner: {
      label: 'com.automatchbooks.ai.sync',
      src: 'runners/sync.js',
      event: 'syncTransactions',
      repeat: true,
      interval: 15, // minutes
      autoStart: true,
    },
  },
};

export default config;
