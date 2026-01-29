import { Redirect } from 'expo-router';
import { useAuthStore } from '@/stores/auth';

export default function Index() {
  const { isAuthenticated } = useAuthStore();

  // Redirect based on authentication state
  if (isAuthenticated) {
    return <Redirect href="/(tabs)/discover" />;
  }

  return <Redirect href="/(auth)/login" />;
}
