import { createFileRoute, Link } from '@tanstack/react-router'
import { useAuth } from '@/contexts/AuthContext'
import { $api } from '@/lib/api/$api'

export const Route = createFileRoute('/messages/')({
  component: MessagesIndexPage,
})

function MessagesIndexPage() {
  const { isAuthenticated, isLoading: authLoading } = useAuth()

  const { data, isLoading, error, refetch } = $api.useQuery(
    'get',
    '/api/v1/conversations',
    {
      params: {
        query: { limit: 50 },
      },
    },
    {
      enabled: isAuthenticated,
      refetchInterval: 30000, // Refresh every 30 seconds
    }
  )

  // Also fetch unread count for header badge
  const { data: unreadData } = $api.useQuery(
    'get',
    '/api/v1/conversations/unread',
    {},
    {
      enabled: isAuthenticated,
      refetchInterval: 30000,
    }
  )

  if (authLoading) {
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

  const conversations = data?.items ?? []
  const totalUnread = unreadData?.total_unread ?? 0

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h1 style={styles.pageTitle}>
          Messages
          {totalUnread > 0 && (
            <span style={styles.headerBadge}>{totalUnread}</span>
          )}
        </h1>
      </div>

      {isLoading && (
        <div style={styles.loadingContainer}>
          <div style={styles.spinner} />
          <span>Loading conversations...</span>
        </div>
      )}

      {error && (
        <div style={styles.errorContainer}>
          <p style={styles.errorText}>Failed to load conversations</p>
          <button onClick={() => refetch()} style={styles.retryButton}>
            Try Again
          </button>
        </div>
      )}

      {!isLoading && !error && conversations.length === 0 && (
        <div style={styles.emptyState}>
          <div style={styles.emptyIcon}>💬</div>
          <h3 style={styles.emptyTitle}>No conversations yet</h3>
          <p style={styles.emptySubtitle}>
            Start a conversation by messaging a host from their profile page.
          </p>
          <Link to="/hosts" style={styles.discoverButton}>
            Find a Host
          </Link>
        </div>
      )}

      {!isLoading && !error && conversations.length > 0 && (
        <div style={styles.conversationList}>
          {conversations.map((conversation) => {
            const otherUser = conversation.other_participant
            const hasUnread = conversation.unread_count > 0
            const lastMessageTime = conversation.last_message_at
              ? formatTime(new Date(conversation.last_message_at))
              : ''

            return (
              <Link
                key={conversation.id}
                to="/messages/$conversationId"
                params={{ conversationId: conversation.id }}
                style={{
                  ...styles.conversationItem,
                  ...(hasUnread ? styles.conversationItemUnread : {}),
                }}
              >
                <div style={styles.avatar}>
                  {getInitials(otherUser.first_name, otherUser.last_name)}
                </div>
                <div style={styles.conversationContent}>
                  <div style={styles.conversationHeader}>
                    <span
                      style={{
                        ...styles.participantName,
                        ...(hasUnread ? styles.participantNameUnread : {}),
                      }}
                    >
                      {otherUser.first_name} {otherUser.last_name}
                    </span>
                    <span style={styles.timestamp}>{lastMessageTime}</span>
                  </div>
                  <div style={styles.messagePreviewRow}>
                    <p
                      style={{
                        ...styles.messagePreview,
                        ...(hasUnread ? styles.messagePreviewUnread : {}),
                      }}
                    >
                      {conversation.last_message_preview ?? 'No messages yet'}
                    </p>
                    {hasUnread && (
                      <span style={styles.unreadBadge}>
                        {conversation.unread_count > 99
                          ? '99+'
                          : conversation.unread_count}
                      </span>
                    )}
                  </div>
                </div>
              </Link>
            )
          })}
        </div>
      )}
    </div>
  )
}

function getInitials(firstName: string, lastName: string): string {
  return `${firstName.charAt(0)}${lastName.charAt(0)}`.toUpperCase()
}

function formatTime(date: Date): string {
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

  if (diffDays === 0) {
    // Today - show time
    return date.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })
  } else if (diffDays === 1) {
    return 'Yesterday'
  } else if (diffDays < 7) {
    // Within a week - show day name
    return date.toLocaleDateString([], { weekday: 'short' })
  } else {
    // Older - show date
    return date.toLocaleDateString([], { month: 'short', day: 'numeric' })
  }
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
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  pageTitle: {
    fontSize: 'clamp(1.5rem, 4vw, 2rem)',
    fontWeight: 'bold',
    color: '#1f2937',
    margin: 0,
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
  },
  headerBadge: {
    backgroundColor: '#ef4444',
    color: 'white',
    fontSize: '0.875rem',
    fontWeight: '600',
    padding: '0.25rem 0.5rem',
    borderRadius: '9999px',
    minWidth: '1.5rem',
    textAlign: 'center',
  },
  loadingContainer: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    height: '200px',
    gap: '1rem',
    color: '#6b7280',
  },
  spinner: {
    width: '40px',
    height: '40px',
    border: '3px solid #e5e7eb',
    borderTopColor: '#3b82f6',
    borderRadius: '50%',
    animation: 'spin 1s linear infinite',
  },
  errorContainer: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    height: '200px',
    gap: '1rem',
  },
  errorText: {
    color: '#dc2626',
    margin: 0,
  },
  retryButton: {
    backgroundColor: '#3b82f6',
    color: 'white',
    padding: '0.5rem 1rem',
    borderRadius: '8px',
    border: 'none',
    cursor: 'pointer',
    fontWeight: '500',
  },
  emptyState: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'white',
    borderRadius: '12px',
    boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
    padding: '3rem',
    textAlign: 'center',
    gap: '0.75rem',
  },
  emptyIcon: {
    fontSize: '3rem',
    marginBottom: '0.5rem',
  },
  emptyTitle: {
    fontSize: '1.25rem',
    fontWeight: '600',
    color: '#1f2937',
    margin: 0,
  },
  emptySubtitle: {
    color: '#6b7280',
    margin: 0,
    maxWidth: '300px',
  },
  discoverButton: {
    backgroundColor: '#3b82f6',
    color: 'white',
    padding: '0.75rem 1.5rem',
    borderRadius: '8px',
    textDecoration: 'none',
    fontWeight: '500',
    marginTop: '0.5rem',
  },
  conversationList: {
    display: 'flex',
    flexDirection: 'column',
    backgroundColor: 'white',
    borderRadius: '12px',
    boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
    overflow: 'hidden',
  },
  conversationItem: {
    display: 'flex',
    alignItems: 'center',
    padding: '1rem',
    gap: '0.75rem',
    textDecoration: 'none',
    color: 'inherit',
    borderBottom: '1px solid #f3f4f6',
    transition: 'background-color 0.15s ease',
    cursor: 'pointer',
  },
  conversationItemUnread: {
    backgroundColor: '#fefce8',
  },
  avatar: {
    width: '48px',
    height: '48px',
    borderRadius: '50%',
    backgroundColor: '#e0e7ff',
    color: '#4f46e5',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontWeight: '600',
    fontSize: '1rem',
    flexShrink: 0,
  },
  conversationContent: {
    flex: 1,
    minWidth: 0,
    display: 'flex',
    flexDirection: 'column',
    gap: '0.25rem',
  },
  conversationHeader: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: '0.5rem',
  },
  participantName: {
    fontWeight: '500',
    color: '#1f2937',
    fontSize: '1rem',
  },
  participantNameUnread: {
    fontWeight: '700',
  },
  timestamp: {
    fontSize: '0.75rem',
    color: '#9ca3af',
    flexShrink: 0,
  },
  messagePreviewRow: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: '0.5rem',
  },
  messagePreview: {
    color: '#6b7280',
    fontSize: '0.875rem',
    margin: 0,
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap',
    flex: 1,
  },
  messagePreviewUnread: {
    color: '#374151',
    fontWeight: '500',
  },
  unreadBadge: {
    backgroundColor: '#3b82f6',
    color: 'white',
    fontSize: '0.75rem',
    fontWeight: '600',
    padding: '0.125rem 0.5rem',
    borderRadius: '9999px',
    minWidth: '1.25rem',
    textAlign: 'center',
    flexShrink: 0,
  },
}
