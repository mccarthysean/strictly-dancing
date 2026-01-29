import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { useEffect } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import * as SplashScreen from 'expo-splash-screen';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { useAuthStore } from '@/stores/auth';
import { initSentry, SentryProvider } from '@/lib/sentry';

// Initialize Sentry for error tracking and performance monitoring
initSentry();

// Prevent the splash screen from auto-hiding
SplashScreen.preventAutoHideAsync();

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      retry: 3,
    },
  },
});

function RootLayout() {
  const { isLoading, initialize } = useAuthStore();

  useEffect(() => {
    async function prepare() {
      try {
        // Initialize auth state from secure storage
        await initialize();
      } catch (e) {
        console.warn('Error initializing auth:', e);
      } finally {
        // Hide splash screen after auth state is loaded
        await SplashScreen.hideAsync();
      }
    }

    prepare();
  }, [initialize]);

  // Show nothing while loading auth state (splash screen is visible)
  if (isLoading) {
    return null;
  }

  return (
    <SafeAreaProvider>
      <QueryClientProvider client={queryClient}>
        <StatusBar style="auto" />
        <Stack screenOptions={{ headerShown: false }}>
          <Stack.Screen name="(auth)" options={{ headerShown: false }} />
          <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
          <Stack.Screen name="+not-found" />
        </Stack>
      </QueryClientProvider>
    </SafeAreaProvider>
  );
}

// Wrap the app with Sentry's error boundary
export default SentryProvider(RootLayout);
