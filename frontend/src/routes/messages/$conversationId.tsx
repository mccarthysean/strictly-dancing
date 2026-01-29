import { createFileRoute, Link } from '@tanstack/react-router'
import { useAuth } from '@/contexts/AuthContext'
import { $api, getAccessToken } from '@/lib/api/$api'
import { useState, useEffect, useRef, useCallback } from 'react'
import type { components } from '@/types/api.gen'

type MessageWithSenderResponse = components['schemas']['MessageWithSenderResponse']
type MessageType = components['schemas']['MessageType']

// WebSocket message types
interface WSMessage {
  type: 'MESSAGE_RECEIVED' | 'MESSAGE_SENT' | 'MESSAGES_READ' | 'TYPING_START' | 'TYPING_STOP' | 'CONNECTED' | 'ERROR' | 'USER_ONLINE' | 'USER_OFFLINE'
  data?: unknown
  message?: MessageWithSenderResponse
  user_id?: string
  error?: string
}

export const Route = createFileRoute('/messages/$conversationId')({
  component: ChatPage,
})

function ChatPage() {
  const { conversationId } = Route.useParams()
  const { user, isAuthenticated, isLoading: authLoading } = useAuth()
  const [messageInput, setMessageInput] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const [partnerTyping, setPartnerTyping] = useState(false)
  const [wsConnected, setWsConnected] = useState(false)
  const [localMessages, setLocalMessages] = useState<MessageWithSenderResponse[]>([])
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const messagesContainerRef = useRef<HTMLDivElement>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const typingTimeoutRef = useRef<number | null>(null)
  const [cursor, setCursor] = useState<string | null>(null)
  const [hasMoreMessages, setHasMoreMessages] = useState(true)
  const [loadingMore, setLoadingMore] = useState(false)

  // Fetch conversation data
  const { data: conversationData, isLoading: conversationLoading, error: conversationError } = $api.useQuery(
    'get',
    '/api/v1/conversations/{conversation_id}',
    {
      params: { path: { conversation_id: conversationId } },
    },
    {
      enabled: isAuthenticated && !!conversationId,
    }
  )

  // Fetch more messages (for infinite scroll)
  const { data: moreMessagesData, refetch: fetchMoreMessages, isFetching: fetchingMore } = $api.useQuery(
    'get',
    '/api/v1/conversations/{conversation_id}/messages',
    {
      params: {
        path: { conversation_id: conversationId },
        query: cursor ? { cursor, limit: 20 } : { limit: 20 },
      },
    },
    {
      enabled: false, // Manual fetch only
    }
  )

  // Send message mutation
  const sendMessageMutation = $api.useMutation(
    'post',
    '/api/v1/conversations/{conversation_id}/messages',
  )

  // Mark as read mutation
  const markReadMutation = $api.useMutation(
    'post',
    '/api/v1/conversations/{conversation_id}/read',
  )

  // Initialize local messages from conversation data
  useEffect(() => {
    if (conversationData?.messages) {
      setLocalMessages(conversationData.messages)
      // Check if there might be more messages
      setHasMoreMessages((conversationData.messages.length ?? 0) >= 20)
    }
  }, [conversationData?.messages])

  // Process more messages when loaded
  useEffect(() => {
    if (moreMessagesData?.items) {
      setLocalMessages(prev => [...moreMessagesData.items, ...prev])
      setCursor(moreMessagesData.next_cursor ?? null)
      setHasMoreMessages(moreMessagesData.has_more)
      setLoadingMore(false)
    }
  }, [moreMessagesData])

  // WebSocket connection
  useEffect(() => {
    if (!isAuthenticated || !conversationId) return

    const token = getAccessToken()
    if (!token) return

    const wsUrl = (import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8001')
      .replace('http://', 'ws://')
      .replace('https://', 'wss://')

    const ws = new WebSocket(`${wsUrl}/ws/chat/${conversationId}?token=${token}`)
    wsRef.current = ws

    ws.onopen = () => {
      setWsConnected(true)
    }

    ws.onmessage = (event) => {
      try {
        const message: WSMessage = JSON.parse(event.data)

        switch (message.type) {
          case 'MESSAGE_RECEIVED':
          case 'MESSAGE_SENT':
            if (message.message) {
              setLocalMessages(prev => {
                // Avoid duplicates
                if (prev.some(m => m.id === message.message?.id)) {
                  return prev
                }
                return [...prev, message.message as MessageWithSenderResponse]
              })
            }
            break
          case 'TYPING_START':
            if (message.user_id !== user?.id) {
              setPartnerTyping(true)
            }
            break
          case 'TYPING_STOP':
            if (message.user_id !== user?.id) {
              setPartnerTyping(false)
            }
            break
          case 'MESSAGES_READ':
            // Could update read status of messages here
            break
          case 'ERROR':
            console.error('WebSocket error:', message.error)
            break
        }
      } catch (e) {
        console.error('Failed to parse WebSocket message:', e)
      }
    }

    ws.onclose = () => {
      setWsConnected(false)
    }

    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
      setWsConnected(false)
    }

    return () => {
      ws.close()
      wsRef.current = null
    }
  }, [isAuthenticated, conversationId, user?.id])

  // Scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [localMessages])

  // Mark messages as read when viewing
  useEffect(() => {
    if (isAuthenticated && conversationId && conversationData) {
      markReadMutation.mutate({
        params: { path: { conversation_id: conversationId } },
      })
    }
  }, [isAuthenticated, conversationId, conversationData, markReadMutation])

  // Handle sending typing indicator
  const handleTyping = useCallback(() => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return

    if (!isTyping) {
      setIsTyping(true)
      wsRef.current.send(JSON.stringify({ type: 'TYPING_START' }))
    }

    // Clear existing timeout
    if (typingTimeoutRef.current) {
      clearTimeout(typingTimeoutRef.current)
    }

    // Set new timeout to stop typing indicator
    typingTimeoutRef.current = window.setTimeout(() => {
      setIsTyping(false)
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'TYPING_STOP' }))
      }
    }, 2000)
  }, [isTyping])

  // Handle send message
  const handleSendMessage = async () => {
    if (!messageInput.trim() || sendMessageMutation.isPending) return

    const content = messageInput.trim()
    setMessageInput('')
    setIsTyping(false)

    // Clear typing timeout
    if (typingTimeoutRef.current) {
      clearTimeout(typingTimeoutRef.current)
    }

    // Send via WebSocket if connected, otherwise use HTTP
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'MESSAGE', content }))
    } else {
      // Fallback to HTTP
      sendMessageMutation.mutate({
        params: { path: { conversation_id: conversationId } },
        body: { content, message_type: 'text' as MessageType },
      }, {
        onSuccess: (newMessage) => {
          if (newMessage) {
            setLocalMessages(prev => {
              if (prev.some(m => m.id === newMessage.id)) return prev
              return [...prev, newMessage]
            })
          }
        },
      })
    }
  }

  // Handle key press in input
  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  // Handle scroll for infinite scroll
  const handleScroll = useCallback(() => {
    const container = messagesContainerRef.current
    if (!container || !hasMoreMessages || loadingMore || fetchingMore) return

    // Load more when scrolled near top
    if (container.scrollTop < 100) {
      setLoadingMore(true)
      // Set cursor to oldest message
      if (localMessages.length > 0) {
        const oldestMessage = localMessages[0]
        if (oldestMessage) {
          setCursor(oldestMessage.id)
          fetchMoreMessages()
        }
      }
    }
  }, [hasMoreMessages, loadingMore, fetchingMore, localMessages, fetchMoreMessages])

  // Get other participant info
  const getOtherParticipant = () => {
    if (!conversationData || !user) return null
    if (conversationData.participant_1?.id === user.id) {
      return conversationData.participant_2
    }
    return conversationData.participant_1
  }

  const otherParticipant = getOtherParticipant()

  // Loading state
  if (authLoading || conversationLoading) {
    return (
      <div style={styles.container}>
        <div style={styles.loadingContainer}>
          <div style={styles.spinner} />
          <p>Loading conversation...</p>
        </div>
      </div>
    )
  }

  // Not authenticated
  if (!isAuthenticated) {
    return (
      <div style={styles.container}>
        <div style={styles.authRequired}>
          <h2>Sign in required</h2>
          <p>Please log in to view your messages.</p>
          <Link to="/login" style={styles.loginLink}>
            Sign In
          </Link>
        </div>
      </div>
    )
  }

  // Error state
  if (conversationError) {
    return (
      <div style={styles.container}>
        <div style={styles.errorContainer}>
          <h2>Conversation not found</h2>
          <p>This conversation may not exist or you may not have access to it.</p>
          <Link to="/messages" style={styles.backLink}>
            Back to Messages
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div style={styles.container}>
      {/* Header */}
      <div style={styles.header}>
        <Link to="/messages" style={styles.backButton}>
          &larr;
        </Link>
        <div style={styles.headerInfo}>
          <div style={styles.avatar}>
            {otherParticipant?.first_name?.charAt(0) ?? '?'}
            {otherParticipant?.last_name?.charAt(0) ?? ''}
          </div>
          <div style={styles.headerText}>
            <h2 style={styles.headerName}>
              {otherParticipant?.first_name ?? 'Unknown'} {otherParticipant?.last_name ?? 'User'}
            </h2>
            <span style={styles.connectionStatus}>
              {wsConnected ? (
                <span style={styles.onlineIndicator}>Online</span>
              ) : (
                <span style={styles.offlineIndicator}>Connecting...</span>
              )}
            </span>
          </div>
        </div>
      </div>

      {/* Messages List */}
      <div
        ref={messagesContainerRef}
        style={styles.messagesContainer}
        onScroll={handleScroll}
      >
        {/* Loading more indicator */}
        {(loadingMore || fetchingMore) && (
          <div style={styles.loadingMore}>
            <div style={styles.smallSpinner} />
            <span>Loading older messages...</span>
          </div>
        )}

        {/* Messages */}
        {localMessages.map((message) => {
          const isOwnMessage = message.sender_id === user?.id
          return (
            <div
              key={message.id}
              style={{
                ...styles.messageWrapper,
                justifyContent: isOwnMessage ? 'flex-end' : 'flex-start',
              }}
            >
              <div
                style={{
                  ...styles.messageBubble,
                  ...(isOwnMessage ? styles.ownMessage : styles.otherMessage),
                }}
              >
                <p style={styles.messageContent}>{message.content}</p>
                <span style={styles.messageTime}>
                  {formatMessageTime(message.created_at)}
                  {isOwnMessage && message.read_at && (
                    <span style={styles.readIndicator}> ✓</span>
                  )}
                </span>
              </div>
            </div>
          )
        })}

        {/* Typing indicator */}
        {partnerTyping && (
          <div style={styles.typingIndicator}>
            <span style={styles.typingDots}>
              <span>.</span><span>.</span><span>.</span>
            </span>
            {otherParticipant?.first_name ?? 'User'} is typing
          </div>
        )}

        {/* Scroll anchor */}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div style={styles.inputArea}>
        <input
          type="text"
          value={messageInput}
          onChange={(e) => {
            setMessageInput(e.target.value)
            handleTyping()
          }}
          onKeyDown={handleKeyPress}
          placeholder="Type a message..."
          style={styles.textInput}
          disabled={sendMessageMutation.isPending}
        />
        <button
          onClick={handleSendMessage}
          disabled={!messageInput.trim() || sendMessageMutation.isPending}
          style={{
            ...styles.sendButton,
            ...((!messageInput.trim() || sendMessageMutation.isPending) ? styles.sendButtonDisabled : {}),
          }}
        >
          {sendMessageMutation.isPending ? '...' : 'Send'}
        </button>
      </div>
    </div>
  )
}

// Format message time
function formatMessageTime(dateString: string): string {
  const date = new Date(dateString)
  const now = new Date()
  const diffDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24))

  if (diffDays === 0) {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  } else if (diffDays === 1) {
    return `Yesterday ${date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`
  } else if (diffDays < 7) {
    return date.toLocaleDateString([], { weekday: 'short' }) + ' ' +
           date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }
  return date.toLocaleDateString([], { month: 'short', day: 'numeric' }) + ' ' +
         date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    height: 'calc(100vh - 60px)',
    maxWidth: '800px',
    margin: '0 auto',
    backgroundColor: '#f9fafb',
  },
  loadingContainer: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    height: '100%',
    gap: '1rem',
    color: '#6b7280',
  },
  spinner: {
    width: '40px',
    height: '40px',
    border: '4px solid #e5e7eb',
    borderTop: '4px solid #3b82f6',
    borderRadius: '50%',
    animation: 'spin 1s linear infinite',
  },
  smallSpinner: {
    width: '16px',
    height: '16px',
    border: '2px solid #e5e7eb',
    borderTop: '2px solid #3b82f6',
    borderRadius: '50%',
    animation: 'spin 1s linear infinite',
  },
  authRequired: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    height: '100%',
    gap: '1rem',
    textAlign: 'center',
    padding: '2rem',
  },
  loginLink: {
    backgroundColor: '#3b82f6',
    color: 'white',
    padding: '0.75rem 1.5rem',
    borderRadius: '8px',
    textDecoration: 'none',
    fontWeight: '500',
  },
  errorContainer: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    height: '100%',
    gap: '1rem',
    textAlign: 'center',
    padding: '2rem',
    color: '#6b7280',
  },
  backLink: {
    color: '#3b82f6',
    textDecoration: 'none',
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.75rem',
    padding: '1rem',
    backgroundColor: 'white',
    borderBottom: '1px solid #e5e7eb',
  },
  backButton: {
    color: '#6b7280',
    textDecoration: 'none',
    fontSize: '1.25rem',
    padding: '0.5rem',
  },
  headerInfo: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.75rem',
    flex: 1,
  },
  avatar: {
    width: '40px',
    height: '40px',
    borderRadius: '50%',
    backgroundColor: '#3b82f6',
    color: 'white',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontWeight: '600',
    fontSize: '0.875rem',
  },
  headerText: {
    display: 'flex',
    flexDirection: 'column',
  },
  headerName: {
    fontSize: '1rem',
    fontWeight: '600',
    color: '#1f2937',
    margin: 0,
  },
  connectionStatus: {
    fontSize: '0.75rem',
  },
  onlineIndicator: {
    color: '#10b981',
  },
  offlineIndicator: {
    color: '#9ca3af',
  },
  messagesContainer: {
    flex: 1,
    overflowY: 'auto',
    padding: '1rem',
    display: 'flex',
    flexDirection: 'column',
    gap: '0.5rem',
  },
  loadingMore: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '0.5rem',
    padding: '0.5rem',
    color: '#9ca3af',
    fontSize: '0.875rem',
  },
  messageWrapper: {
    display: 'flex',
    width: '100%',
  },
  messageBubble: {
    maxWidth: '70%',
    padding: '0.75rem 1rem',
    borderRadius: '16px',
    wordBreak: 'break-word',
  },
  ownMessage: {
    backgroundColor: '#3b82f6',
    color: 'white',
    borderBottomRightRadius: '4px',
  },
  otherMessage: {
    backgroundColor: 'white',
    color: '#1f2937',
    borderBottomLeftRadius: '4px',
    boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
  },
  messageContent: {
    margin: 0,
    lineHeight: 1.4,
  },
  messageTime: {
    fontSize: '0.7rem',
    opacity: 0.7,
    display: 'block',
    marginTop: '0.25rem',
    textAlign: 'right',
  },
  readIndicator: {
    marginLeft: '0.25rem',
  },
  typingIndicator: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
    padding: '0.5rem 1rem',
    color: '#9ca3af',
    fontSize: '0.875rem',
    fontStyle: 'italic',
  },
  typingDots: {
    display: 'inline-flex',
    gap: '2px',
  },
  inputArea: {
    display: 'flex',
    gap: '0.75rem',
    padding: '1rem',
    backgroundColor: 'white',
    borderTop: '1px solid #e5e7eb',
  },
  textInput: {
    flex: 1,
    padding: '0.75rem 1rem',
    borderRadius: '24px',
    border: '1px solid #e5e7eb',
    fontSize: '1rem',
    outline: 'none',
  },
  sendButton: {
    padding: '0.75rem 1.5rem',
    borderRadius: '24px',
    backgroundColor: '#3b82f6',
    color: 'white',
    border: 'none',
    fontWeight: '600',
    cursor: 'pointer',
    transition: 'background-color 0.2s',
  },
  sendButtonDisabled: {
    backgroundColor: '#9ca3af',
    cursor: 'not-allowed',
  },
}

// Add CSS animation for spinner
const styleSheet = document.createElement('style')
styleSheet.textContent = `
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
`
document.head.appendChild(styleSheet)
