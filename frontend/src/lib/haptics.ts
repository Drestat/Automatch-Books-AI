import { Haptics, ImpactStyle } from '@capacitor/haptics';
import { Capacitor } from '@capacitor/core';

export const triggerHapticFeedback = async () => {
    if (Capacitor.isNativePlatform()) {
        try {
            await Haptics.impact({ style: ImpactStyle.Medium });
        } catch (e) {
            console.warn('Haptic feedback failed:', e);
        }
    }
};
