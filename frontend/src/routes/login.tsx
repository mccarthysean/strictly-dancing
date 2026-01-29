import { useState, type FormEvent } from 'react'
import { createFileRoute, useNavigate, Link } from '@tanstack/react-router'
import { useAuth } from '@/contexts/AuthContext'

export const Route = createFileRoute('/login')({
  component: LoginPage,
})

type LoginStep = 'email' | 'code'

function LoginPage() {
  const navigate = useNavigate()
  const { requestMagicLink, verifyMagicLink, isAuthenticated } = useAuth()
  const [step, setStep] = useState<LoginStep>('email')
  const [email, setEmail] = useState('')
  const [code, setCode] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)

  // Redirect if already authenticated
  if (isAuthenticated) {
    void navigate({ to: '/' })
    return null
  }

  const handleRequestMagicLink = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)
    setSuccessMessage(null)
    setIsLoading(true)

    try {
      await requestMagicLink(email)
      setSuccessMessage('Check your email for a 6-digit code')
      setStep('code')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send magic link')
    } finally {
      setIsLoading(false)
    }
  }

  const handleVerifyCode = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)
    setIsLoading(true)

    try {
      await verifyMagicLink(email, code)
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
      await requestMagicLink(email)
      setSuccessMessage('A new code has been sent to your email')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to resend code')
    } finally {
      setIsLoading(false)
    }
  }

  const handleBackToEmail = () => {
    setStep('email')
    setCode('')
    setError(null)
    setSuccessMessage(null)
  }

  const isEmailValid = email.includes('@') && email.length > 5
  const isCodeValid = code.length === 6 && /^\d{6}$/.test(code)

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '60vh',
        padding: '1rem',
      }}
    >
      <div
        style={{
          width: '100%',
          maxWidth: '400px',
          padding: '2rem',
          backgroundColor: '#ffffff',
          borderRadius: '0.5rem',
          boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)',
        }}
      >
        <h1
          style={{
            fontSize: '1.5rem',
            fontWeight: 'bold',
            color: '#1f2937',
            marginBottom: '0.5rem',
            textAlign: 'center',
          }}
        >
          Welcome Back
        </h1>
        <p
          style={{
            fontSize: '0.875rem',
            color: '#6b7280',
            marginBottom: '1.5rem',
            textAlign: 'center',
          }}
        >
          {step === 'email'
            ? "Enter your email to receive a sign-in code"
            : `Enter the 6-digit code sent to ${email}`}
        </p>

        {error && (
          <div
            style={{
              padding: '0.75rem',
              marginBottom: '1rem',
              backgroundColor: '#fef2f2',
              border: '1px solid #fecaca',
              borderRadius: '0.375rem',
              color: '#dc2626',
              fontSize: '0.875rem',
            }}
          >
            {error}
          </div>
        )}

        {successMessage && (
          <div
            style={{
              padding: '0.75rem',
              marginBottom: '1rem',
              backgroundColor: '#f0fdf4',
              border: '1px solid #bbf7d0',
              borderRadius: '0.375rem',
              color: '#16a34a',
              fontSize: '0.875rem',
            }}
          >
            {successMessage}
          </div>
        )}

        {step === 'email' ? (
          <form onSubmit={handleRequestMagicLink}>
            <div style={{ marginBottom: '1.5rem' }}>
              <label
                htmlFor="email"
                style={{
                  display: 'block',
                  marginBottom: '0.5rem',
                  fontSize: '0.875rem',
                  fontWeight: '500',
                  color: '#374151',
                }}
              >
                Email
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                required
                disabled={isLoading}
                style={{
                  width: '100%',
                  padding: '0.75rem',
                  border: '1px solid #d1d5db',
                  borderRadius: '0.375rem',
                  fontSize: '1rem',
                  boxSizing: 'border-box',
                }}
              />
            </div>

            <button
              type="submit"
              disabled={isLoading || !isEmailValid}
              style={{
                width: '100%',
                padding: '0.75rem',
                backgroundColor: isLoading || !isEmailValid ? '#9ca3af' : '#6366f1',
                color: '#ffffff',
                border: 'none',
                borderRadius: '0.375rem',
                fontSize: '1rem',
                fontWeight: '500',
                cursor: isLoading || !isEmailValid ? 'not-allowed' : 'pointer',
              }}
            >
              {isLoading ? 'Sending...' : 'Send Magic Link'}
            </button>
          </form>
        ) : (
          <form onSubmit={handleVerifyCode}>
            <div style={{ marginBottom: '1rem' }}>
              <label
                htmlFor="code"
                style={{
                  display: 'block',
                  marginBottom: '0.5rem',
                  fontSize: '0.875rem',
                  fontWeight: '500',
                  color: '#374151',
                }}
              >
                6-Digit Code
              </label>
              <input
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
                style={{
                  width: '100%',
                  padding: '0.75rem',
                  border: '1px solid #d1d5db',
                  borderRadius: '0.375rem',
                  fontSize: '1.5rem',
                  textAlign: 'center',
                  letterSpacing: '0.5rem',
                  boxSizing: 'border-box',
                }}
              />
            </div>

            <button
              type="submit"
              disabled={isLoading || !isCodeValid}
              style={{
                width: '100%',
                padding: '0.75rem',
                backgroundColor: isLoading || !isCodeValid ? '#9ca3af' : '#6366f1',
                color: '#ffffff',
                border: 'none',
                borderRadius: '0.375rem',
                fontSize: '1rem',
                fontWeight: '500',
                cursor: isLoading || !isCodeValid ? 'not-allowed' : 'pointer',
                marginBottom: '1rem',
              }}
            >
              {isLoading ? 'Verifying...' : 'Sign In'}
            </button>

            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                fontSize: '0.875rem',
              }}
            >
              <button
                type="button"
                onClick={handleBackToEmail}
                disabled={isLoading}
                style={{
                  background: 'none',
                  border: 'none',
                  color: '#6366f1',
                  cursor: 'pointer',
                  padding: 0,
                }}
              >
                Use different email
              </button>
              <button
                type="button"
                onClick={handleResendCode}
                disabled={isLoading}
                style={{
                  background: 'none',
                  border: 'none',
                  color: '#6366f1',
                  cursor: 'pointer',
                  padding: 0,
                }}
              >
                Resend code
              </button>
            </div>
          </form>
        )}

        <p
          style={{
            marginTop: '1.5rem',
            textAlign: 'center',
            fontSize: '0.875rem',
            color: '#6b7280',
          }}
        >
          Don't have an account?{' '}
          <Link
            to="/register"
            style={{
              color: '#6366f1',
              textDecoration: 'none',
              fontWeight: '500',
            }}
          >
            Register
          </Link>
        </p>
      </div>
    </div>
  )
}
