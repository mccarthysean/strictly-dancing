import { createFileRoute, Link } from '@tanstack/react-router'
import { useAuth } from '@/contexts/AuthContext'

export const Route = createFileRoute('/')({
  component: HomePage,
})

function HomePage() {
  const { isAuthenticated, user } = useAuth()

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: '60vh',
      textAlign: 'center',
      padding: '1rem',
    }}>
      <h1 style={{
        fontSize: 'clamp(2rem, 5vw, 3rem)',
        fontWeight: 'bold',
        color: '#1f2937',
        marginBottom: '1rem',
        lineHeight: '1.2',
      }}>
        Strictly Dancing
      </h1>
      <p style={{
        fontSize: 'clamp(1rem, 2.5vw, 1.25rem)',
        color: '#6b7280',
        maxWidth: '600px',
        marginBottom: '2rem',
        lineHeight: '1.6',
      }}>
        Connect with qualified dance hosts around the world.
        Whether you're traveling or looking for a dance partner locally,
        we've got you covered.
      </p>

      {isAuthenticated && user ? (
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: '1rem',
        }}>
          <p style={{ color: '#374151' }}>
            Welcome back, {user.first_name}!
          </p>
          <div style={{
            display: 'flex',
            flexWrap: 'wrap',
            justifyContent: 'center',
            gap: '1rem',
          }}>
            <Link
              to="/hosts"
              style={{
                padding: '0.75rem 1.5rem',
                backgroundColor: '#6366f1',
                color: '#ffffff',
                borderRadius: '0.5rem',
                textDecoration: 'none',
                fontWeight: '500',
              }}
            >
              Find a Host
            </Link>
          </div>
        </div>
      ) : (
        <div style={{
          display: 'flex',
          flexWrap: 'wrap',
          justifyContent: 'center',
          gap: '1rem',
        }}>
          <Link
            to="/hosts"
            style={{
              padding: '0.75rem 1.5rem',
              backgroundColor: '#6366f1',
              color: '#ffffff',
              borderRadius: '0.5rem',
              textDecoration: 'none',
              fontWeight: '500',
            }}
          >
            Find a Host
          </Link>
          <Link
            to="/register"
            style={{
              padding: '0.75rem 1.5rem',
              border: '1px solid #6366f1',
              color: '#6366f1',
              borderRadius: '0.5rem',
              textDecoration: 'none',
              fontWeight: '500',
            }}
          >
            Become a Host
          </Link>
        </div>
      )}
    </div>
  )
}
