import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/hosts/$hostId')({
  component: HostProfilePage,
})

function HostProfilePage() {
  const { hostId } = Route.useParams()

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: '60vh',
      padding: '1rem',
    }}>
      <h1 style={{
        fontSize: '2rem',
        fontWeight: 'bold',
        color: '#1f2937',
        marginBottom: '1rem',
      }}>
        Host Profile
      </h1>
      <p style={{ color: '#6b7280' }}>
        Host ID: {hostId}
      </p>
      <p style={{ color: '#9ca3af', marginTop: '0.5rem' }}>
        Full profile view coming in T033...
      </p>
    </div>
  )
}
