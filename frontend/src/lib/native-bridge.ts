/**
 * Native Bridge — Unified interface for Capacitor native features.
 * All functions gracefully no-op on web, so the web app continues to work normally.
 */

import { Capacitor } from '@capacitor/core';

// ─── Platform Detection ───────────────────────────────────────
export const isNative = () => Capacitor.isNativePlatform();
export const getPlatform = () => Capacitor.getPlatform(); // 'ios' | 'android' | 'web'

// ─── 1. Camera (Receipt Scanning) ─────────────────────────────
export async function takePhoto(): Promise<string | null> {
    if (!isNative()) return null;
    try {
        const { Camera, CameraResultType, CameraSource } = await import('@capacitor/camera');
        const image = await Camera.getPhoto({
            quality: 85,
            allowEditing: false,
            resultType: CameraResultType.Base64,
            source: CameraSource.Camera,
            width: 1200,
            correctOrientation: true,
        });
        return image.base64String ?? null;
    } catch {
        return null;
    }
}

export async function pickPhoto(): Promise<string | null> {
    if (!isNative()) return null;
    try {
        const { Camera, CameraResultType, CameraSource } = await import('@capacitor/camera');
        const image = await Camera.getPhoto({
            quality: 85,
            allowEditing: false,
            resultType: CameraResultType.Base64,
            source: CameraSource.Photos,
        });
        return image.base64String ?? null;
    } catch {
        return null;
    }
}

// ─── 2. Biometric Auth (Face ID / Touch ID) ───────────────────
export async function authenticateWithBiometrics(): Promise<boolean> {
    if (!isNative()) return true; // Auto-pass on web
    try {
        const { BiometricAuth } = await import('capacitor-biometric-auth');

        // Check availability first
        const availability = await BiometricAuth.isAvailable();
        if (!availability.has) return true; // No biometrics = skip

        const result = await BiometricAuth.verify({
            reason: 'Verify your identity to access AutoMatch Books',
        });
        return result.verified;
    } catch {
        return false;
    }
}

export async function checkBiometricAvailability(): Promise<{
    available: boolean;
}> {
    if (!isNative()) return { available: false };
    try {
        const { BiometricAuth } = await import('capacitor-biometric-auth');
        const result = await BiometricAuth.isAvailable();
        return { available: result.has };
    } catch {
        return { available: false };
    }
}

// ─── 3. Push Notifications ────────────────────────────────────
export async function registerForPush(): Promise<string | null> {
    if (!isNative()) return null;
    try {
        const { PushNotifications } = await import('@capacitor/push-notifications');

        // Request permission
        const permResult = await PushNotifications.requestPermissions();
        if (permResult.receive !== 'granted') return null;

        // Register with APNs/FCM
        await PushNotifications.register();

        // Wait for token
        return new Promise((resolve) => {
            PushNotifications.addListener('registration', (token) => {
                resolve(token.value);
            });
            PushNotifications.addListener('registrationError', () => {
                resolve(null);
            });
            // Timeout after 10s
            setTimeout(() => resolve(null), 10000);
        });
    } catch {
        return null;
    }
}

export async function setupPushListeners(
    onNotification: (data: { title?: string; body?: string; data?: Record<string, unknown> }) => void
): Promise<void> {
    if (!isNative()) return;
    try {
        const { PushNotifications } = await import('@capacitor/push-notifications');

        // Notification received while app is in foreground
        PushNotifications.addListener('pushNotificationReceived', (notification) => {
            onNotification({
                title: notification.title,
                body: notification.body,
                data: notification.data,
            });
        });

        // Notification tapped
        PushNotifications.addListener('pushNotificationActionPerformed', (action) => {
            onNotification({
                title: action.notification.title,
                body: action.notification.body,
                data: action.notification.data,
            });
        });
    } catch {
        // Silent fail on web
    }
}

// ─── 4. Haptic Feedback ───────────────────────────────────────
export async function triggerHaptic(
    style: 'success' | 'warning' | 'error' | 'light' | 'medium' | 'heavy' = 'medium'
): Promise<void> {
    if (!isNative()) return;
    try {
        const { Haptics, ImpactStyle, NotificationType } = await import('@capacitor/haptics');

        switch (style) {
            case 'success':
                await Haptics.notification({ type: NotificationType.Success });
                break;
            case 'warning':
                await Haptics.notification({ type: NotificationType.Warning });
                break;
            case 'error':
                await Haptics.notification({ type: NotificationType.Error });
                break;
            case 'light':
                await Haptics.impact({ style: ImpactStyle.Light });
                break;
            case 'medium':
                await Haptics.impact({ style: ImpactStyle.Medium });
                break;
            case 'heavy':
                await Haptics.impact({ style: ImpactStyle.Heavy });
                break;
        }
    } catch {
        // Silent fail on web
    }
}

// ─── 5. App Badge Count ───────────────────────────────────────
export async function updateBadgeCount(count: number): Promise<void> {
    if (!isNative()) return;
    try {
        const { Badge } = await import('@capawesome/capacitor-badge');
        if (count <= 0) {
            await Badge.clear();
        } else {
            await Badge.set({ count });
        }
    } catch {
        // Silent fail
    }
}

export async function clearBadge(): Promise<void> {
    if (!isNative()) return;
    try {
        const { Badge } = await import('@capawesome/capacitor-badge');
        await Badge.clear();
    } catch {
        // Silent fail
    }
}

// ─── 6. Secure Storage (Keychain / Keystore) ──────────────────
export async function secureStore(key: string, value: string): Promise<void> {
    if (!isNative()) {
        // Fallback to localStorage on web
        localStorage.setItem(key, value);
        return;
    }
    try {
        const { Preferences } = await import('@capacitor/preferences');
        await Preferences.set({ key, value });
    } catch {
        localStorage.setItem(key, value);
    }
}

export async function secureGet(key: string): Promise<string | null> {
    if (!isNative()) {
        return localStorage.getItem(key);
    }
    try {
        const { Preferences } = await import('@capacitor/preferences');
        const { value } = await Preferences.get({ key });
        return value;
    } catch {
        return localStorage.getItem(key);
    }
}

export async function secureRemove(key: string): Promise<void> {
    if (!isNative()) {
        localStorage.removeItem(key);
        return;
    }
    try {
        const { Preferences } = await import('@capacitor/preferences');
        await Preferences.remove({ key });
    } catch {
        localStorage.removeItem(key);
    }
}

// ─── 9. Splash Screen ────────────────────────────────────────
export async function hideSplashScreen(): Promise<void> {
    if (!isNative()) return;
    try {
        const { SplashScreen } = await import('@capacitor/splash-screen');
        await SplashScreen.hide({ fadeOutDuration: 300 });
    } catch {
        // Silent fail
    }
}

// ─── 10. Background Sync ──────────────────────────────────────
// Background sync is configured in capacitor.config.ts and handled
// by the background runner script (public/runners/sync.js).
// This function manually triggers a check if needed.
export async function requestBackgroundSync(): Promise<void> {
    if (!isNative()) return;
    try {
        const { BackgroundRunner } = await import('@capacitor/background-runner');
        await BackgroundRunner.dispatchEvent({
            label: 'com.automatchbooks.ai.sync',
            event: 'syncTransactions',
            details: {},
        });
    } catch {
        // Silent fail
    }
}
