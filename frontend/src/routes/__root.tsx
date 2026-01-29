import { createRootRoute, Link, Outlet, useRouter } from '@tanstack/react-router'
import { TanStackRouterDevtools } from '@tanstack/router-devtools'
import { useAuth } from '@/contexts/AuthContext'

export const Route = createRootRoute({
  component: RootLayout,
  notFoundComponent: NotFoundComponent,
  errorComponent: ErrorComponent,
})

function RootLayout() {
  const { isAuthenticated, user, isLoading } = useAuth()

  return (
    <>
      <header style={styles.header}>
        <nav style={styles.nav}>
          <Link to="/" style={styles.logo}>
            Strictly Dancing
          </Link>
          <div style={styles.navLinks}>
            {isLoading ? (
              <span style={styles.loadingText}>...</span>
            ) : isAuthenticated ? (
              <>
                <Link to="/hosts" style={styles.navLink}>
                  Find Hosts
                </Link>
                <Link to="/bookings" style={styles.navLink}>
                  Bookings
                </Link>
                <Link to="/messages" style={styles.navLink}>
                  Messages
                </Link>
                {(user?.user_type === 'host' || user?.user_type === 'both') && (
                  <Link to="/host/dashboard" style={styles.navLink}>
                    Dashboard
                  </Link>
                )}
                <Link to="/settings" style={styles.settingsLink}>
                  <span style={styles.userInitials}>
                    {user?.first_name?.charAt(0) ?? '?'}
                  </span>
                </Link>
              </>
            ) : (
              <>
                <Link to="/hosts" style={styles.navLink}>
                  Browse
                </Link>
                <Link to="/login" style={styles.navLink}>
                  Login
                </Link>
                <Link to="/register" style={styles.registerButton}>
                  Register
                </Link>
              </>
            )}
          </div>
        </nav>
      </header>
      <main style={styles.main}>
        <Outlet />
      </main>
      {import.meta.env.DEV && <TanStackRouterDevtools />}
    </>
  )
}

function NotFoundComponent() {
  return (
    <div style={errorStyles.container}>
      <div style={errorStyles.content}>
        <div style={errorStyles.errorCode}>404</div>
        <h1 style={errorStyles.title}>Page Not Found</h1>
        <p style={errorStyles.message}>
          Sorry, we couldn't find the page you're looking for.
          It might have been moved or doesn't exist.
        </p>
        <div style={errorStyles.actions}>
          <Link to="/" style={errorStyles.homeButton}>
            Go to Home
          </Link>
          <Link to="/hosts" style={errorStyles.secondaryLink}>
            Browse Hosts
          </Link>
        </div>
      </div>
    </div>
  )
}

function ErrorComponent() {
  const router = useRouter()
  const matches = router.state.matches
  const lastMatch = matches[matches.length - 1]
  const error = lastMatch?.error as Error | undefined

  return (
    <div style={errorStyles.container}>
      <div style={errorStyles.errorContent}>
        <div style={errorStyles.iconContainer}>
          <span style={errorStyles.icon}>&#9888;</span>
        </div>
        <h1 style={errorStyles.title}>Something went wrong</h1>
        <p style={errorStyles.message}>
          We encountered an error while loading this page. Please try again.
        </p>
        {error && (
          <p style={errorStyles.errorMessage}>{error.message}</p>
        )}
        <div style={errorStyles.actions}>
          <button
            type="button"
            onClick={() => window.location.reload()}
            style={errorStyles.homeButton}
          >
            Refresh Page
          </button>
          <Link to="/" style={errorStyles.secondaryLink}>
            Go to Home
          </Link>
        </div>
      </div>
    </div>
  )
}

const styles: Record<string, React.CSSProperties> = {
  header: {
    padding: '0.75rem 1rem',
    borderBottom: '1px solid #e5e7eb',
    backgroundColor: '#ffffff',
    position: 'sticky',
    top: 0,
    zIndex: 100,
  },
  nav: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    maxWidth: '1200px',
    margin: '0 auto',
    flexWrap: 'wrap',
    gap: '0.5rem',
  },
  logo: {
    fontSize: '1.125rem',
    fontWeight: 'bold',
    color: '#e11d48',
    textDecoration: 'none',
  },
  navLinks: {
    display: 'flex',
    gap: '0.5rem',
    alignItems: 'center',
    flexWrap: 'wrap',
  },
  navLink: {
    padding: '0.5rem 0.75rem',
    color: '#374151',
    textDecoration: 'none',
    fontSize: '0.9375rem',
    fontWeight: 500,
    borderRadius: '6px',
  },
  registerButton: {
    padding: '0.5rem 1rem',
    backgroundColor: '#e11d48',
    color: '#ffffff',
    borderRadius: '6px',
    textDecoration: 'none',
    fontSize: '0.9375rem',
    fontWeight: 500,
  },
  settingsLink: {
    padding: '0.25rem',
    textDecoration: 'none',
  },
  userInitials: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    width: '32px',
    height: '32px',
    borderRadius: '50%',
    backgroundColor: '#e11d48',
    color: 'white',
    fontSize: '0.875rem',
    fontWeight: 600,
  },
  loadingText: {
    color: '#9ca3af',
    padding: '0.5rem',
  },
  main: {
    minHeight: 'calc(100vh - 60px)',
    backgroundColor: '#fafafa',
  },
}

const errorStyles: Record<string, React.CSSProperties> = {
  container: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: '80vh',
    padding: '1rem',
  },
  content: {
    maxWidth: '450px',
    width: '100%',
    textAlign: 'center',
  },
  errorContent: {
    maxWidth: '500px',
    width: '100%',
    textAlign: 'center',
    backgroundColor: 'white',
    borderRadius: '16px',
    boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
    padding: '2.5rem',
  },
  iconContainer: {
    width: '80px',
    height: '80px',
    margin: '0 auto 1.5rem',
    backgroundColor: '#fef2f2',
    borderRadius: '50%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  icon: {
    fontSize: '2.5rem',
    color: '#dc2626',
  },
  errorCode: {
    fontSize: 'clamp(5rem, 15vw, 8rem)',
    fontWeight: 800,
    color: '#e5e7eb',
    lineHeight: 1,
    marginBottom: '0.5rem',
  },
  title: {
    fontSize: '1.5rem',
    fontWeight: 700,
    color: '#1f2937',
    margin: 0,
    marginBottom: '0.75rem',
  },
  message: {
    fontSize: '1rem',
    color: '#6b7280',
    margin: 0,
    marginBottom: '1.5rem',
    lineHeight: 1.6,
  },
  errorMessage: {
    fontSize: '0.875rem',
    color: '#dc2626',
    backgroundColor: '#fef2f2',
    padding: '0.75rem 1rem',
    borderRadius: '8px',
    marginBottom: '1.5rem',
    fontFamily: 'monospace',
  },
  actions: {
    display: 'flex',
    flexDirection: 'column',
    gap: '0.75rem',
  },
  homeButton: {
    display: 'block',
    width: '100%',
    padding: '0.875rem',
    backgroundColor: '#e11d48',
    color: 'white',
    border: 'none',
    borderRadius: '8px',
    fontSize: '1rem',
    fontWeight: 600,
    textDecoration: 'none',
    textAlign: 'center',
    cursor: 'pointer',
  },
  secondaryLink: {
    display: 'block',
    padding: '0.875rem',
    backgroundColor: 'white',
    color: '#374151',
    border: '1px solid #e5e7eb',
    borderRadius: '8px',
    fontSize: '1rem',
    fontWeight: 500,
    textDecoration: 'none',
    textAlign: 'center',
  },
}
