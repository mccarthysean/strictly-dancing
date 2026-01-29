import { useEffect } from 'react';
import { Linking } from 'react-native';
import { useRouter } from 'expo-router';
import * as ExpoLinking from 'expo-linking';
import { useAuthStore } from '@/stores/auth';

/**
 * Hook to handle deep links for magic link authentication.
 *
 * Supported deep link formats:
 * - strictlydancing://auth/verify?email=...&code=... (login verification)
 * - strictlydancing://auth/register/verify?email=...&code=... (registration verification)
 * - https://strictlydancing.com/auth/verify?email=...&code=... (universal links)
 */
export function useDeepLinking() {
  const router = useRouter();
  const { verifyMagicLink, verifyRegistration, isAuthenticated } = useAuthStore();

  useEffect(() => {
    // Handle deep links when app is opened from a link
    const handleDeepLink = async (event: { url: string }) => {
      const { url } = event;
      await processDeepLink(url);
    };

    // Process the deep link URL
    const processDeepLink = async (url: string) => {
      try {
        const parsed = ExpoLinking.parse(url);
        const { path, queryParams } = parsed;

        if (!path || !queryParams) {
          return;
        }

        const email = queryParams.email as string | undefined;
        const code = queryParams.code as string | undefined;

        if (!email || !code) {
          console.warn('Deep link missing email or code parameters');
          return;
        }

        // Handle login verification
        if (path === 'auth/verify' || path === '/auth/verify') {
          try {
            await verifyMagicLink(email, code);
            router.replace('/(tabs)/discover');
          } catch (err) {
            // Navigate to login with error state
            router.push({
              pathname: '/(auth)/login',
              params: { error: 'Invalid or expired code. Please try again.' },
            });
          }
          return;
        }

        // Handle registration verification
        if (path === 'auth/register/verify' || path === '/auth/register/verify') {
          try {
            await verifyRegistration(email, code);
            router.replace('/(tabs)/discover');
          } catch (err) {
            // Navigate to register with error state
            router.push({
              pathname: '/(auth)/register',
              params: { error: 'Invalid or expired code. Please try again.' },
            });
          }
          return;
        }
      } catch (error) {
        console.error('Error processing deep link:', error);
      }
    };

    // Check for initial URL (app opened from a link)
    const checkInitialUrl = async () => {
      const initialUrl = await Linking.getInitialURL();
      if (initialUrl) {
        await processDeepLink(initialUrl);
      }
    };

    // Only process deep links if not already authenticated
    if (!isAuthenticated) {
      checkInitialUrl();
    }

    // Subscribe to deep link events
    const subscription = Linking.addEventListener('url', handleDeepLink);

    return () => {
      subscription.remove();
    };
  }, [router, verifyMagicLink, verifyRegistration, isAuthenticated]);
}
