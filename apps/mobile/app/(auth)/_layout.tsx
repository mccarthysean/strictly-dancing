import { Redirect, Stack } from 'expo-router';
import { useAuthStore } from '@/stores/auth';

export default function AuthLayout() {
  const { isAuthenticated } = useAuthStore();

  // If user is authenticated, redirect to main app
  if (isAuthenticated) {
    return <Redirect href="/(tabs)/discover" />;
  }

  return (
    <Stack
      screenOptions={{
        headerShown: false,
        animation: 'slide_from_right',
      }}
    >
      <Stack.Screen name="login" />
      <Stack.Screen name="register" />
    </Stack>
  );
}
