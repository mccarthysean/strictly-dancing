import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/hosts/')({
  component: HostsPage,
})

function HostsPage() {
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: '60vh',
    }}>
      <h1 style={{
        fontSize: '2rem',
        fontWeight: 'bold',
        color: '#1f2937',
        marginBottom: '1rem',
      }}>
        Find a Host
      </h1>
      <p style={{ color: '#6b7280' }}>
        Host discovery coming soon...
      </p>
    </div>
  )
}
