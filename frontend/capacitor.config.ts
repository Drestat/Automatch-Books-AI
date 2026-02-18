import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.automatchbooks.ai',
  appName: 'AutoMatch Books AI',
  webDir: 'out',
  server: {
    // Production URL
    url: 'https://automatchbooksai.com/dashboard',
    cleartext: false,
    allowNavigation: [
      'automatchbooksai.com',
      '*.automatchbooksai.com',
      'accounts.google.com',
      '*.google.com',
      '*.clerk.com',
      '*.clerk.accounts.dev'
    ],
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
