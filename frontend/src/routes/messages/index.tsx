import { createFileRoute, Link } from '@tanstack/react-router'
import { useAuth } from '@/contexts/AuthContext'

export const Route = createFileRoute('/messages/')({
  component: MessagesIndexPage,
})

function MessagesIndexPage() {
  const { isAuthenticated, isLoading } = useAuth()

  if (isLoading) {
    return (
      <div style={styles.container}>
        <div style={styles.loading}>Loading...</div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return (
      <div style={styles.container}>
        <div style={styles.authRequired}>
          <h2 style={styles.title}>Sign in required</h2>
          <p style={styles.subtitle}>Please log in to view your messages.</p>
          <Link to="/login" style={styles.loginLink}>
            Sign In
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h1 style={styles.pageTitle}>Messages</h1>
      </div>

      <div style={styles.placeholder}>
        <p style={styles.placeholderText}>
          Your conversations will appear here.
        </p>
        <p style={styles.note}>
          This page will be fully implemented in task T054.
        </p>
        <Link to="/hosts" style={styles.discoverLink}>
          Find a Host to Message
        </Link>
      </div>
    </div>
  )
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    maxWidth: '800px',
    margin: '0 auto',
    padding: '1rem',
    minHeight: 'calc(100vh - 60px)',
  },
  loading: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    height: '300px',
    color: '#6b7280',
  },
  authRequired: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    height: '300px',
    textAlign: 'center',
    gap: '1rem',
  },
  title: {
    fontSize: '1.5rem',
    fontWeight: 'bold',
    color: '#1f2937',
    margin: 0,
  },
  subtitle: {
    color: '#6b7280',
    margin: 0,
  },
  loginLink: {
    backgroundColor: '#3b82f6',
    color: 'white',
    padding: '0.75rem 1.5rem',
    borderRadius: '8px',
    textDecoration: 'none',
    fontWeight: '500',
  },
  header: {
    marginBottom: '1.5rem',
  },
  pageTitle: {
    fontSize: 'clamp(1.5rem, 4vw, 2rem)',
    fontWeight: 'bold',
    color: '#1f2937',
    margin: 0,
  },
  placeholder: {
    backgroundColor: 'white',
    borderRadius: '12px',
    boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
    padding: '3rem',
    textAlign: 'center',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: '1rem',
  },
  placeholderText: {
    color: '#6b7280',
    margin: 0,
    fontSize: '1rem',
  },
  note: {
    color: '#9ca3af',
    fontSize: '0.875rem',
    fontStyle: 'italic',
    margin: 0,
  },
  discoverLink: {
    color: '#3b82f6',
    textDecoration: 'none',
    fontWeight: '500',
    marginTop: '0.5rem',
  },
}
