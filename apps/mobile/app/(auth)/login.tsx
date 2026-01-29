import { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
  ActivityIndicator,
} from 'react-native';
import { Link, useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useAuthStore } from '@/stores/auth';

type LoginStep = 'email' | 'code';

export default function LoginScreen() {
  const router = useRouter();
  const { requestMagicLink, verifyMagicLink, isLoading } = useAuthStore();

  const [step, setStep] = useState<LoginStep>('email');
  const [email, setEmail] = useState('');
  const [code, setCode] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const handleRequestMagicLink = async () => {
    setError(null);
    setSuccessMessage(null);

    if (!email.trim()) {
      setError('Please enter your email');
      return;
    }

    if (!email.includes('@')) {
      setError('Please enter a valid email address');
      return;
    }

    try {
      await requestMagicLink(email.trim().toLowerCase());
      setSuccessMessage('Check your email for a 6-digit code');
      setStep('code');
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to send magic link';
      setError(message);
    }
  };

  const handleVerifyCode = async () => {
    setError(null);

    if (code.length !== 6) {
      setError('Please enter a 6-digit code');
      return;
    }

    try {
      await verifyMagicLink(email.trim().toLowerCase(), code);
      router.replace('/(tabs)/discover');
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Invalid or expired code';
      setError(message);
    }
  };

  const handleResendCode = async () => {
    setError(null);
    try {
      await requestMagicLink(email.trim().toLowerCase());
      setSuccessMessage('A new code has been sent to your email');
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to resend code';
      setError(message);
    }
  };

  const handleBackToEmail = () => {
    setStep('email');
    setCode('');
    setError(null);
    setSuccessMessage(null);
  };

  return (
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.content}
      >
        <View style={styles.header}>
          <Text style={styles.title}>Strictly Dancing</Text>
          <Text style={styles.subtitle}>
            {step === 'email'
              ? 'Enter your email to sign in'
              : `Enter the 6-digit code sent to ${email}`}
          </Text>
        </View>

        {error && (
          <View style={styles.errorContainer}>
            <Text style={styles.errorText}>{error}</Text>
          </View>
        )}

        {successMessage && (
          <View style={styles.successContainer}>
            <Text style={styles.successText}>{successMessage}</Text>
          </View>
        )}

        <View style={styles.form}>
          {step === 'email' ? (
            <>
              <View style={styles.inputContainer}>
                <Text style={styles.label}>Email</Text>
                <TextInput
                  style={styles.input}
                  placeholder="Enter your email"
                  placeholderTextColor="#9CA3AF"
                  value={email}
                  onChangeText={setEmail}
                  keyboardType="email-address"
                  autoCapitalize="none"
                  autoComplete="email"
                  editable={!isLoading}
                />
              </View>

              <TouchableOpacity
                style={[styles.button, isLoading && styles.buttonDisabled]}
                onPress={handleRequestMagicLink}
                disabled={isLoading}
              >
                {isLoading ? (
                  <ActivityIndicator color="#fff" />
                ) : (
                  <Text style={styles.buttonText}>Send Magic Link</Text>
                )}
              </TouchableOpacity>
            </>
          ) : (
            <>
              <View style={styles.inputContainer}>
                <Text style={styles.label}>6-Digit Code</Text>
                <TextInput
                  style={styles.codeInput}
                  placeholder="000000"
                  placeholderTextColor="#9CA3AF"
                  value={code}
                  onChangeText={(text) => setCode(text.replace(/\D/g, '').slice(0, 6))}
                  keyboardType="number-pad"
                  maxLength={6}
                  editable={!isLoading}
                  autoComplete="one-time-code"
                />
              </View>

              <TouchableOpacity
                style={[styles.button, isLoading && styles.buttonDisabled]}
                onPress={handleVerifyCode}
                disabled={isLoading || code.length !== 6}
              >
                {isLoading ? (
                  <ActivityIndicator color="#fff" />
                ) : (
                  <Text style={styles.buttonText}>Sign In</Text>
                )}
              </TouchableOpacity>

              <View style={styles.codeActions}>
                <TouchableOpacity onPress={handleBackToEmail} disabled={isLoading}>
                  <Text style={styles.linkText}>Use different email</Text>
                </TouchableOpacity>
                <TouchableOpacity onPress={handleResendCode} disabled={isLoading}>
                  <Text style={styles.linkText}>Resend code</Text>
                </TouchableOpacity>
              </View>
            </>
          )}
        </View>

        <View style={styles.footer}>
          <Text style={styles.footerText}>Don't have an account? </Text>
          <Link href="/(auth)/register" asChild>
            <TouchableOpacity disabled={isLoading}>
              <Text style={styles.linkText}>Sign Up</Text>
            </TouchableOpacity>
          </Link>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },
  content: {
    flex: 1,
    padding: 24,
    justifyContent: 'center',
  },
  header: {
    marginBottom: 32,
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#1a1a1a',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: '#666',
  },
  errorContainer: {
    backgroundColor: '#FEF2F2',
    borderWidth: 1,
    borderColor: '#FECACA',
    borderRadius: 8,
    padding: 12,
    marginBottom: 16,
  },
  errorText: {
    color: '#DC2626',
    fontSize: 14,
  },
  successContainer: {
    backgroundColor: '#F0FDF4',
    borderWidth: 1,
    borderColor: '#BBF7D0',
    borderRadius: 8,
    padding: 12,
    marginBottom: 16,
  },
  successText: {
    color: '#16A34A',
    fontSize: 14,
  },
  form: {
    gap: 16,
  },
  inputContainer: {
    marginBottom: 16,
  },
  label: {
    fontSize: 14,
    fontWeight: '600',
    color: '#374151',
    marginBottom: 8,
  },
  input: {
    borderWidth: 1,
    borderColor: '#D1D5DB',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    color: '#1a1a1a',
    backgroundColor: '#fff',
  },
  codeInput: {
    borderWidth: 1,
    borderColor: '#D1D5DB',
    borderRadius: 8,
    padding: 16,
    fontSize: 24,
    color: '#1a1a1a',
    backgroundColor: '#fff',
    textAlign: 'center',
    letterSpacing: 8,
  },
  button: {
    backgroundColor: '#8B5CF6',
    borderRadius: 8,
    padding: 16,
    alignItems: 'center',
    marginTop: 8,
  },
  buttonDisabled: {
    backgroundColor: '#C4B5FD',
  },
  buttonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  codeActions: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 16,
  },
  footer: {
    flexDirection: 'row',
    justifyContent: 'center',
    marginTop: 24,
  },
  footerText: {
    color: '#666',
    fontSize: 14,
  },
  linkText: {
    color: '#8B5CF6',
    fontSize: 14,
    fontWeight: '600',
  },
});
