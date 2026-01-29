import { createRootRoute, Link, Outlet } from '@tanstack/react-router'
import { TanStackRouterDevtools } from '@tanstack/router-devtools'

export const Route = createRootRoute({
  component: RootLayout,
})

function RootLayout() {
  return (
    <>
      <header style={{
        padding: '1rem',
        borderBottom: '1px solid #e5e7eb',
        backgroundColor: '#ffffff',
      }}>
        <nav style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          maxWidth: '1200px',
          margin: '0 auto',
        }}>
          <Link
            to="/"
            style={{
              fontSize: '1.25rem',
              fontWeight: 'bold',
              color: '#6366f1',
              textDecoration: 'none',
            }}
          >
            Strictly Dancing
          </Link>
          <div style={{ display: 'flex', gap: '1rem' }}>
            <Link
              to="/login"
              style={{
                padding: '0.5rem 1rem',
                color: '#374151',
                textDecoration: 'none',
              }}
            >
              Login
            </Link>
            <Link
              to="/register"
              style={{
                padding: '0.5rem 1rem',
                backgroundColor: '#6366f1',
                color: '#ffffff',
                borderRadius: '0.375rem',
                textDecoration: 'none',
              }}
            >
              Register
            </Link>
          </div>
        </nav>
      </header>
      <main style={{
        minHeight: 'calc(100vh - 80px)',
        maxWidth: '1200px',
        margin: '0 auto',
        padding: '1rem',
      }}>
        <Outlet />
      </main>
      {import.meta.env.DEV && <TanStackRouterDevtools />}
    </>
  )
}
