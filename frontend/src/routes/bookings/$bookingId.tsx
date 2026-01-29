import { createFileRoute, Link } from '@tanstack/react-router'

export const Route = createFileRoute('/bookings/$bookingId')({
  component: BookingDetailPage,
})

function BookingDetailPage() {
  const { bookingId } = Route.useParams()

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <Link to="/bookings" style={styles.backButton}>
          &larr; Back to bookings
        </Link>
      </div>

      <div style={styles.card}>
        <h1 style={styles.title}>Booking Details</h1>
        <p style={styles.placeholder}>
          Booking detail page for ID: {bookingId}
        </p>
        <p style={styles.note}>
          This page will be fully implemented in task T067.
        </p>
      </div>
    </div>
  )
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    maxWidth: '800px',
    margin: '0 auto',
    padding: '1rem',
  },
  header: {
    marginBottom: '1rem',
  },
  backButton: {
    color: '#6b7280',
    textDecoration: 'none',
    fontSize: '0.875rem',
  },
  card: {
    backgroundColor: 'white',
    borderRadius: '12px',
    boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
    padding: '2rem',
    textAlign: 'center',
  },
  title: {
    fontSize: '1.5rem',
    fontWeight: 'bold',
    color: '#1f2937',
    marginBottom: '1rem',
  },
  placeholder: {
    color: '#6b7280',
    marginBottom: '0.5rem',
  },
  note: {
    color: '#9ca3af',
    fontSize: '0.875rem',
    fontStyle: 'italic',
  },
}
