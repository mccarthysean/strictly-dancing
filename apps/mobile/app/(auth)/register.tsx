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
  ScrollView,
} from 'react-native';
import { Link, useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useAuthStore } from '@/stores/auth';

type RegisterStep = 'details' | 'code';

export default function RegisterScreen() {
  const router = useRouter();
  const { registerWithMagicLink, verifyRegistration, isLoading } = useAuthStore();

  const [step, setStep] = useState<RegisterStep>('details');
  const [email, setEmail] = useState('');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [userType, setUserType] = useState<'client' | 'host' | 'both'>('client');
  const [acceptedTerms, setAcceptedTerms] = useState(false);
  const [code, setCode] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const validateForm = (): string | null => {
    if (!firstName.trim()) return 'Please enter your first name';
    if (!lastName.trim()) return 'Please enter your last name';
    if (!email.trim()) return 'Please enter your email';
    if (!email.includes('@')) return 'Please enter a valid email address';
    if (!acceptedTerms) return 'Please accept the terms and conditions';
    return null;
  };

  const handleRegister = async () => {
    setError(null);
    setSuccessMessage(null);

    const validationError = validateForm();
    if (validationError) {
      setError(validationError);
      return;
    }

    try {
      await registerWithMagicLink({
        email: email.trim().toLowerCase(),
        first_name: firstName.trim(),
        last_name: lastName.trim(),
        user_type: userType,
      });
      setSuccessMessage('Check your email for a 6-digit code');
      setStep('code');
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Registration failed';
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
      await verifyRegistration(email.trim().toLowerCase(), code);
      router.replace('/(tabs)/discover');
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Invalid or expired code';
      setError(message);
    }
  };

  const handleResendCode = async () => {
    setError(null);
    try {
      await registerWithMagicLink({
        email: email.trim().toLowerCase(),
        first_name: firstName.trim(),
        last_name: lastName.trim(),
        user_type: userType,
      });
      setSuccessMessage('A new code has been sent to your email');
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to resend code';
      setError(message);
    }
  };

  const handleBackToDetails = () => {
    setStep('details');
    setCode('');
    setError(null);
    setSuccessMessage(null);
  };

  return (
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.flex}
      >
        <ScrollView contentContainerStyle={styles.content}>
          <View style={styles.header}>
            <Text style={styles.title}>Create Account</Text>
            <Text style={styles.subtitle}>
              {step === 'details'
                ? 'Join Strictly Dancing today'
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
            {step === 'details' ? (
              <>
                <View style={styles.row}>
                  <View style={[styles.inputContainer, styles.halfWidth]}>
                    <Text style={styles.label}>First Name</Text>
                    <TextInput
                      style={styles.input}
                      placeholder="First name"
                      placeholderTextColor="#9CA3AF"
                      value={firstName}
                      onChangeText={setFirstName}
                      autoCapitalize="words"
                      autoComplete="given-name"
                      editable={!isLoading}
                    />
                  </View>
                  <View style={[styles.inputContainer, styles.halfWidth]}>
                    <Text style={styles.label}>Last Name</Text>
                    <TextInput
                      style={styles.input}
                      placeholder="Last name"
                      placeholderTextColor="#9CA3AF"
                      value={lastName}
                      onChangeText={setLastName}
                      autoCapitalize="words"
                      autoComplete="family-name"
                      editable={!isLoading}
                    />
                  </View>
                </View>

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

                <View style={styles.inputContainer}>
                  <Text style={styles.label}>I am a...</Text>
                  <View style={styles.userTypeContainer}>
                    {(['client', 'host', 'both'] as const).map((type) => (
                      <TouchableOpacity
                        key={type}
                        style={[
                          styles.userTypeButton,
                          userType === type && styles.userTypeButtonActive,
                        ]}
                        onPress={() => setUserType(type)}
                        disabled={isLoading}
                      >
                        <Text
                          style={[
                            styles.userTypeText,
                            userType === type && styles.userTypeTextActive,
                          ]}
                        >
                          {type === 'client'
                            ? 'Client'
                            : type === 'host'
                              ? 'Host'
                              : 'Both'}
                        </Text>
                      </TouchableOpacity>
                    ))}
                  </View>
                </View>

                <TouchableOpacity
                  style={styles.checkboxContainer}
                  onPress={() => setAcceptedTerms(!acceptedTerms)}
                  disabled={isLoading}
                >
                  <View
                    style={[
                      styles.checkbox,
                      acceptedTerms && styles.checkboxChecked,
                    ]}
                  >
                    {acceptedTerms && <Text style={styles.checkmark}>✓</Text>}
                  </View>
                  <Text style={styles.checkboxLabel}>
                    I agree to the{' '}
                    <Text style={styles.linkText}>Terms of Service</Text> and{' '}
                    <Text style={styles.linkText}>Privacy Policy</Text>
                  </Text>
                </TouchableOpacity>

                <TouchableOpacity
                  style={[styles.button, isLoading && styles.buttonDisabled]}
                  onPress={handleRegister}
                  disabled={isLoading}
                >
                  {isLoading ? (
                    <ActivityIndicator color="#fff" />
                  ) : (
                    <Text style={styles.buttonText}>Create Account</Text>
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
                    <Text style={styles.buttonText}>Complete Registration</Text>
                  )}
                </TouchableOpacity>

                <View style={styles.codeActions}>
                  <TouchableOpacity onPress={handleBackToDetails} disabled={isLoading}>
                    <Text style={styles.linkText}>Back to details</Text>
                  </TouchableOpacity>
                  <TouchableOpacity onPress={handleResendCode} disabled={isLoading}>
                    <Text style={styles.linkText}>Resend code</Text>
                  </TouchableOpacity>
                </View>
              </>
            )}
          </View>

          <View style={styles.footer}>
            <Text style={styles.footerText}>Already have an account? </Text>
            <Link href="/(auth)/login" asChild>
              <TouchableOpacity disabled={isLoading}>
                <Text style={styles.linkText}>Sign In</Text>
              </TouchableOpacity>
            </Link>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },
  flex: {
    flex: 1,
  },
  content: {
    padding: 24,
    paddingTop: 48,
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
  row: {
    flexDirection: 'row',
    gap: 12,
  },
  inputContainer: {
    marginBottom: 16,
  },
  halfWidth: {
    flex: 1,
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
  userTypeContainer: {
    flexDirection: 'row',
    gap: 8,
  },
  userTypeButton: {
    flex: 1,
    borderWidth: 1,
    borderColor: '#D1D5DB',
    borderRadius: 8,
    padding: 12,
    alignItems: 'center',
  },
  userTypeButtonActive: {
    borderColor: '#8B5CF6',
    backgroundColor: '#F5F3FF',
  },
  userTypeText: {
    fontSize: 14,
    fontWeight: '500',
    color: '#6B7280',
  },
  userTypeTextActive: {
    color: '#8B5CF6',
  },
  checkboxContainer: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 12,
    marginBottom: 8,
  },
  checkbox: {
    width: 24,
    height: 24,
    borderWidth: 2,
    borderColor: '#D1D5DB',
    borderRadius: 4,
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: 2,
  },
  checkboxChecked: {
    borderColor: '#8B5CF6',
    backgroundColor: '#8B5CF6',
  },
  checkmark: {
    color: '#fff',
    fontSize: 14,
    fontWeight: 'bold',
  },
  checkboxLabel: {
    flex: 1,
    fontSize: 14,
    color: '#4B5563',
    lineHeight: 20,
  },
});
