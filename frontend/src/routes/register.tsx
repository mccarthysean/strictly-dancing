import { useState, useMemo, type FormEvent } from 'react'
import { createFileRoute, useNavigate, Link } from '@tanstack/react-router'
import { useAuth } from '@/contexts/AuthContext'

export const Route = createFileRoute('/register')({
  component: RegisterPage,
})

interface PasswordStrength {
  score: number
  label: string
  color: string
}

function getPasswordStrength(password: string): PasswordStrength {
  let score = 0

  if (password.length >= 8) score += 1
  if (password.length >= 12) score += 1
  if (/[A-Z]/.test(password)) score += 1
  if (/[a-z]/.test(password)) score += 1
  if (/[0-9]/.test(password)) score += 1
  if (/[^A-Za-z0-9]/.test(password)) score += 1

  if (score <= 2) return { score, label: 'Weak', color: '#ef4444' }
  if (score <= 4) return { score, label: 'Medium', color: '#f59e0b' }
  return { score, label: 'Strong', color: '#22c55e' }
}

function RegisterPage() {
  const navigate = useNavigate()
  const { register, isAuthenticated } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [firstName, setFirstName] = useState('')
  const [lastName, setLastName] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  // Redirect if already authenticated
  if (isAuthenticated) {
    void navigate({ to: '/' })
    return null
  }

  const passwordStrength = useMemo(() => getPasswordStrength(password), [password])

  const passwordsMatch = password === confirmPassword
  const hasUppercase = /[A-Z]/.test(password)
  const hasLowercase = /[a-z]/.test(password)
  const hasNumber = /[0-9]/.test(password)
  const isPasswordValid = password.length >= 8 && hasUppercase && hasLowercase && hasNumber

  const isFormValid =
    email.length > 0 &&
    firstName.length > 0 &&
    lastName.length > 0 &&
    isPasswordValid &&
    passwordsMatch

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)

    if (!passwordsMatch) {
      setError('Passwords do not match')
      return
    }

    if (!isPasswordValid) {
      setError('Password must be at least 8 characters with uppercase, lowercase, and number')
      return
    }

    setIsLoading(true)

    try {
      await register({
        email,
        password,
        first_name: firstName,
        last_name: lastName,
      })
      void navigate({ to: '/login' })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Registration failed')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: '60vh',
      padding: '1rem',
    }}>
      <div style={{
        width: '100%',
        maxWidth: '400px',
        padding: '2rem',
        backgroundColor: '#ffffff',
        borderRadius: '0.5rem',
        boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)',
      }}>
        <h1 style={{
          fontSize: '1.5rem',
          fontWeight: 'bold',
          color: '#1f2937',
          marginBottom: '1.5rem',
          textAlign: 'center',
        }}>
          Create Account
        </h1>

        {error && (
          <div style={{
            padding: '0.75rem',
            marginBottom: '1rem',
            backgroundColor: '#fef2f2',
            border: '1px solid #fecaca',
            borderRadius: '0.375rem',
            color: '#dc2626',
            fontSize: '0.875rem',
          }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem' }}>
            <div style={{ flex: 1 }}>
              <label
                htmlFor="firstName"
                style={{
                  display: 'block',
                  marginBottom: '0.5rem',
                  fontSize: '0.875rem',
                  fontWeight: '500',
                  color: '#374151',
                }}
              >
                First Name
              </label>
              <input
                id="firstName"
                type="text"
                value={firstName}
                onChange={(e) => setFirstName(e.target.value)}
                placeholder="John"
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
            <div style={{ flex: 1 }}>
              <label
                htmlFor="lastName"
                style={{
                  display: 'block',
                  marginBottom: '0.5rem',
                  fontSize: '0.875rem',
                  fontWeight: '500',
                  color: '#374151',
                }}
              >
                Last Name
              </label>
              <input
                id="lastName"
                type="text"
                value={lastName}
                onChange={(e) => setLastName(e.target.value)}
                placeholder="Doe"
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
          </div>

          <div style={{ marginBottom: '1rem' }}>
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

          <div style={{ marginBottom: '1rem' }}>
            <label
              htmlFor="password"
              style={{
                display: 'block',
                marginBottom: '0.5rem',
                fontSize: '0.875rem',
                fontWeight: '500',
                color: '#374151',
              }}
            >
              Password
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Create a password"
              required
              minLength={8}
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
            {password.length > 0 && (
              <>
                <div style={{
                  marginTop: '0.5rem',
                  height: '4px',
                  backgroundColor: '#e5e7eb',
                  borderRadius: '2px',
                  overflow: 'hidden',
                }}>
                  <div style={{
                    height: '100%',
                    width: `${(passwordStrength.score / 6) * 100}%`,
                    backgroundColor: passwordStrength.color,
                    transition: 'width 0.3s, background-color 0.3s',
                  }} />
                </div>
                <p style={{
                  marginTop: '0.25rem',
                  fontSize: '0.75rem',
                  color: passwordStrength.color,
                }}>
                  Password strength: {passwordStrength.label}
                </p>
                <ul style={{
                  marginTop: '0.5rem',
                  fontSize: '0.75rem',
                  color: '#6b7280',
                  paddingLeft: '1rem',
                }}>
                  <li style={{ color: password.length >= 8 ? '#22c55e' : '#6b7280' }}>
                    At least 8 characters
                  </li>
                  <li style={{ color: hasUppercase ? '#22c55e' : '#6b7280' }}>
                    One uppercase letter
                  </li>
                  <li style={{ color: hasLowercase ? '#22c55e' : '#6b7280' }}>
                    One lowercase letter
                  </li>
                  <li style={{ color: hasNumber ? '#22c55e' : '#6b7280' }}>
                    One number
                  </li>
                </ul>
              </>
            )}
          </div>

          <div style={{ marginBottom: '1.5rem' }}>
            <label
              htmlFor="confirmPassword"
              style={{
                display: 'block',
                marginBottom: '0.5rem',
                fontSize: '0.875rem',
                fontWeight: '500',
                color: '#374151',
              }}
            >
              Confirm Password
            </label>
            <input
              id="confirmPassword"
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="Confirm your password"
              required
              minLength={8}
              disabled={isLoading}
              style={{
                width: '100%',
                padding: '0.75rem',
                border: confirmPassword.length > 0 && !passwordsMatch ? '1px solid #ef4444' : '1px solid #d1d5db',
                borderRadius: '0.375rem',
                fontSize: '1rem',
                boxSizing: 'border-box',
              }}
            />
            {confirmPassword.length > 0 && !passwordsMatch && (
              <p style={{
                marginTop: '0.25rem',
                fontSize: '0.75rem',
                color: '#ef4444',
              }}>
                Passwords do not match
              </p>
            )}
          </div>

          <button
            type="submit"
            disabled={isLoading || !isFormValid}
            style={{
              width: '100%',
              padding: '0.75rem',
              backgroundColor: isLoading || !isFormValid ? '#9ca3af' : '#6366f1',
              color: '#ffffff',
              border: 'none',
              borderRadius: '0.375rem',
              fontSize: '1rem',
              fontWeight: '500',
              cursor: isLoading || !isFormValid ? 'not-allowed' : 'pointer',
            }}
          >
            {isLoading ? 'Creating account...' : 'Create Account'}
          </button>
        </form>

        <p style={{
          marginTop: '1.5rem',
          textAlign: 'center',
          fontSize: '0.875rem',
          color: '#6b7280',
        }}>
          Already have an account?{' '}
          <Link
            to="/login"
            style={{
              color: '#6366f1',
              textDecoration: 'none',
              fontWeight: '500',
            }}
          >
            Sign In
          </Link>
        </p>
      </div>
    </div>
  )
}
