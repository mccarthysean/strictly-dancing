import { useState, type FormEvent } from 'react'
import { createFileRoute, useNavigate, Link } from '@tanstack/react-router'
import { useAuth } from '@/contexts/AuthContext'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { cn } from '@/lib/utils'

export const Route = createFileRoute('/register')({
  component: RegisterPage,
})

type RegisterStep = 'info' | 'code'

function RegisterPage() {
  const navigate = useNavigate()
  const { registerWithMagicLink, verifyRegistration, isAuthenticated } = useAuth()
  const [step, setStep] = useState<RegisterStep>('info')
  const [email, setEmail] = useState('')
  const [firstName, setFirstName] = useState('')
  const [lastName, setLastName] = useState('')
  const [code, setCode] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)

  // Redirect if already authenticated
  if (isAuthenticated) {
    void navigate({ to: '/' })
    return null
  }

  const isEmailValid = email.includes('@') && email.length > 5
  const isFormValid = isEmailValid && firstName.length > 0 && lastName.length > 0
  const isCodeValid = code.length === 6 && /^\d{6}$/.test(code)

  const handleRequestRegistration = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)
    setSuccessMessage(null)
    setIsLoading(true)

    try {
      await registerWithMagicLink({
        email,
        first_name: firstName,
        last_name: lastName,
      })
      setSuccessMessage('Check your email for a 6-digit verification code')
      setStep('code')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Registration failed')
    } finally {
      setIsLoading(false)
    }
  }

  const handleVerifyCode = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)
    setIsLoading(true)

    try {
      await verifyRegistration(email, code)
      void navigate({ to: '/' })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Invalid or expired code')
    } finally {
      setIsLoading(false)
    }
  }

  const handleResendCode = async () => {
    setError(null)
    setIsLoading(true)

    try {
      await registerWithMagicLink({
        email,
        first_name: firstName,
        last_name: lastName,
      })
      setSuccessMessage('A new verification code has been sent to your email')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to resend code')
    } finally {
      setIsLoading(false)
    }
  }

  const handleBackToInfo = () => {
    setStep('info')
    setCode('')
    setError(null)
    setSuccessMessage(null)
  }

  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <CardTitle className="font-display text-2xl">Create Account</CardTitle>
          <CardDescription>
            {step === 'info'
              ? 'Enter your details to get started'
              : `Enter the 6-digit code sent to ${email}`}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {error && (
            <div className="mb-4 rounded-md border border-destructive/50 bg-destructive/10 px-3 py-2 text-sm text-destructive">
              {error}
            </div>
          )}

          {successMessage && (
            <div className="mb-4 rounded-md border border-green-500/50 bg-green-500/10 px-3 py-2 text-sm text-green-600 dark:text-green-400">
              {successMessage}
            </div>
          )}

          {step === 'info' ? (
            <form onSubmit={handleRequestRegistration} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="firstName">First Name</Label>
                  <Input
                    id="firstName"
                    type="text"
                    value={firstName}
                    onChange={(e) => setFirstName(e.target.value)}
                    placeholder="John"
                    required
                    disabled={isLoading}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="lastName">Last Name</Label>
                  <Input
                    id="lastName"
                    type="text"
                    value={lastName}
                    onChange={(e) => setLastName(e.target.value)}
                    placeholder="Doe"
                    required
                    disabled={isLoading}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  required
                  disabled={isLoading}
                />
                <p className="text-xs text-muted-foreground">
                  We'll send a verification code to this email
                </p>
              </div>

              <Button
                type="submit"
                disabled={isLoading || !isFormValid}
                className="w-full"
              >
                {isLoading ? 'Creating account...' : 'Create Account'}
              </Button>
            </form>
          ) : (
            <form onSubmit={handleVerifyCode} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="code">6-Digit Verification Code</Label>
                <Input
                  id="code"
                  type="text"
                  inputMode="numeric"
                  pattern="[0-9]*"
                  maxLength={6}
                  value={code}
                  onChange={(e) => setCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                  placeholder="000000"
                  required
                  disabled={isLoading}
                  autoComplete="one-time-code"
                  className="text-center text-2xl tracking-[0.5rem]"
                />
              </div>

              <Button
                type="submit"
                disabled={isLoading || !isCodeValid}
                className="w-full"
              >
                {isLoading ? 'Verifying...' : 'Complete Registration'}
              </Button>

              <div className="flex justify-between text-sm">
                <button
                  type="button"
                  onClick={handleBackToInfo}
                  disabled={isLoading}
                  className={cn(
                    "bg-transparent p-0 text-primary hover:underline",
                    "disabled:cursor-not-allowed disabled:opacity-50"
                  )}
                >
                  Edit info
                </button>
                <button
                  type="button"
                  onClick={handleResendCode}
                  disabled={isLoading}
                  className={cn(
                    "bg-transparent p-0 text-primary hover:underline",
                    "disabled:cursor-not-allowed disabled:opacity-50"
                  )}
                >
                  Resend code
                </button>
              </div>
            </form>
          )}

          <p className="mt-6 text-center text-sm text-muted-foreground">
            Already have an account?{' '}
            <Link
              to="/login"
              className="font-medium text-primary no-underline hover:underline"
            >
              Sign In
            </Link>
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
