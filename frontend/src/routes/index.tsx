import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/')({
  component: HomePage,
})

function HomePage() {
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: '60vh',
      textAlign: 'center',
    }}>
      <h1 style={{
        fontSize: '3rem',
        fontWeight: 'bold',
        color: '#1f2937',
        marginBottom: '1rem',
      }}>
        Welcome to Strictly Dancing
      </h1>
      <p style={{
        fontSize: '1.25rem',
        color: '#6b7280',
        maxWidth: '600px',
        marginBottom: '2rem',
      }}>
        Connect with qualified dance hosts around the world.
        Whether you're traveling or looking for a dance partner locally,
        we've got you covered.
      </p>
      <div style={{ display: 'flex', gap: '1rem' }}>
        <a
          href="/hosts"
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
        </a>
        <a
          href="/register"
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
        </a>
      </div>
    </div>
  )
}
