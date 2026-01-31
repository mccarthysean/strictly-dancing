import { createFileRoute, Link } from '@tanstack/react-router'
import { useAuth } from '@/contexts/AuthContext'
import { $api } from '@/lib/api/$api'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { cn } from '@/lib/utils'
import { Loader2 } from 'lucide-react'

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
      <div className="mx-auto min-h-[calc(100vh-60px)] max-w-4xl p-4">
        <div className="flex h-[300px] items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return (
      <div className="mx-auto min-h-[calc(100vh-60px)] max-w-4xl p-4">
        <Card className="mx-auto max-w-md">
          <CardContent className="flex h-[300px] flex-col items-center justify-center gap-4 text-center">
            <h2 className="font-display text-2xl font-bold text-foreground">Sign in required</h2>
            <p className="text-muted-foreground">Please log in to view your messages.</p>
            <Button asChild>
              <Link to="/login" className="no-underline">
                Sign In
              </Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  const conversations = data?.items ?? []
  const totalUnread = unreadData?.total_unread ?? 0

  return (
    <div className="mx-auto min-h-[calc(100vh-60px)] max-w-4xl p-4">
      <div className="mb-6 flex items-center gap-2">
        <h1 className="font-display text-[clamp(1.5rem,4vw,2rem)] font-bold text-foreground">
          Messages
        </h1>
        {totalUnread > 0 && (
          <Badge variant="destructive" className="min-w-[1.5rem] text-center">
            {totalUnread}
          </Badge>
        )}
      </div>

      {isLoading && (
        <div className="flex h-[200px] flex-col items-center justify-center gap-4 text-muted-foreground">
          <Loader2 className="h-10 w-10 animate-spin" />
          <span>Loading conversations...</span>
        </div>
      )}

      {error && (
        <Card className="border-destructive bg-destructive/10">
          <CardContent className="flex flex-col items-center justify-center gap-4 p-8">
            <p className="text-destructive">Failed to load conversations</p>
            <Button onClick={() => refetch()} variant="outline">
              Try Again
            </Button>
          </CardContent>
        </Card>
      )}

      {!isLoading && !error && conversations.length === 0 && (
        <Card className="bg-muted/50">
          <CardContent className="flex flex-col items-center justify-center gap-3 p-12 text-center">
            <div className="text-5xl">💬</div>
            <h3 className="font-display text-xl font-semibold text-foreground">No conversations yet</h3>
            <p className="max-w-xs text-muted-foreground">
              Start a conversation by messaging a host from their profile page.
            </p>
            <Button asChild className="mt-2">
              <Link to="/hosts" className="no-underline">
                Find a Host
              </Link>
            </Button>
          </CardContent>
        </Card>
      )}

      {!isLoading && !error && conversations.length > 0 && (
        <Card className="overflow-hidden">
          <div className="divide-y divide-border">
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
                  className={cn(
                    "flex items-center gap-3 p-4 no-underline transition-colors hover:bg-muted/50",
                    hasUnread && "bg-amber-50 dark:bg-amber-900/10"
                  )}
                >
                  <Avatar>
                    <AvatarFallback className="bg-indigo-100 text-indigo-600 dark:bg-indigo-900/50 dark:text-indigo-400">
                      {getInitials(otherUser.first_name, otherUser.last_name)}
                    </AvatarFallback>
                  </Avatar>
                  <div className="flex min-w-0 flex-1 flex-col gap-1">
                    <div className="flex items-center justify-between gap-2">
                      <span
                        className={cn(
                          "text-foreground",
                          hasUnread ? "font-bold" : "font-medium"
                        )}
                      >
                        {otherUser.first_name} {otherUser.last_name}
                      </span>
                      <span className="shrink-0 text-xs text-muted-foreground">{lastMessageTime}</span>
                    </div>
                    <div className="flex items-center justify-between gap-2">
                      <p
                        className={cn(
                          "flex-1 truncate text-sm",
                          hasUnread ? "font-medium text-foreground" : "text-muted-foreground"
                        )}
                      >
                        {conversation.last_message_preview ?? 'No messages yet'}
                      </p>
                      {hasUnread && (
                        <Badge variant="default" className="min-w-[1.25rem] text-center text-xs">
                          {conversation.unread_count > 99
                            ? '99+'
                            : conversation.unread_count}
                        </Badge>
                      )}
                    </div>
                  </div>
                </Link>
              )
            })}
          </div>
        </Card>
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
