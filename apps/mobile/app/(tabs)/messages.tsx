import { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  ActivityIndicator,
  RefreshControl,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { router } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { apiClient } from '@/lib/api/client';
import { useAuthStore } from '@/stores/auth';
import type { components } from '@/types/api.gen';

type ConversationListResponse = components['schemas']['ConversationListResponse'];
type ConversationSummaryResponse = components['schemas']['ConversationSummaryResponse'];

export default function MessagesScreen() {
  const { isAuthenticated } = useAuthStore();

  // State
  const [conversations, setConversations] = useState<ConversationSummaryResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);

  // Fetch conversations
  const fetchConversations = useCallback(
    async (cursor?: string | null) => {
      if (!isAuthenticated) return;

      if (!cursor) {
        setIsLoading(true);
      } else {
        setLoadingMore(true);
      }

      try {
        const params = new URLSearchParams();
        params.set('limit', '20');
        if (cursor) {
          params.set('cursor', cursor);
        }

        const data = await apiClient.get<ConversationListResponse>(
          `/api/v1/conversations?${params.toString()}`
        );

        // API returns items sorted by last_message_at descending
        if (cursor) {
          setConversations((prev) => [...prev, ...data.items]);
        } else {
          setConversations(data.items);
        }

        setNextCursor(data.next_cursor ?? null);
        setHasMore(data.has_more);
      } catch (err) {
        console.error('Failed to fetch conversations:', err);
      } finally {
        setIsLoading(false);
        setRefreshing(false);
        setLoadingMore(false);
      }
    },
    [isAuthenticated]
  );

  // Initial load
  useEffect(() => {
    fetchConversations();
  }, [fetchConversations]);

  // Handle refresh
  const onRefresh = useCallback(() => {
    setRefreshing(true);
    setConversations([]);
    setNextCursor(null);
    fetchConversations();
  }, [fetchConversations]);

  // Load more
  const loadMore = useCallback(() => {
    if (!loadingMore && hasMore && nextCursor) {
      fetchConversations(nextCursor);
    }
  }, [loadingMore, hasMore, nextCursor, fetchConversations]);

  // Format time ago
  const formatTimeAgo = (dateString: string | null | undefined) => {
    if (!dateString) return '';

    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m`;
    if (diffHours < 24) return `${diffHours}h`;
    if (diffDays < 7) return `${diffDays}d`;

    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
    });
  };

  // Navigate to conversation
  const handleConversationPress = (conversation: ConversationSummaryResponse) => {
    router.push(`/messages/${conversation.id}` as any);
  };

  // Render conversation item
  const renderConversation = ({ item }: { item: ConversationSummaryResponse }) => {
    const participant = item.other_participant;
    const hasUnread = item.unread_count > 0;

    return (
      <TouchableOpacity
        style={[styles.conversationItem, hasUnread && styles.conversationUnread]}
        onPress={() => handleConversationPress(item)}
      >
        {/* Avatar */}
        <View style={styles.avatar}>
          <Text style={styles.avatarText}>
            {participant.first_name.charAt(0)}
            {participant.last_name.charAt(0)}
          </Text>
        </View>

        {/* Content */}
        <View style={styles.conversationContent}>
          <View style={styles.conversationHeader}>
            <Text
              style={[
                styles.participantName,
                hasUnread && styles.participantNameUnread,
              ]}
            >
              {participant.first_name} {participant.last_name}
            </Text>
            <Text style={styles.timeAgo}>
              {formatTimeAgo(item.last_message_at)}
            </Text>
          </View>

          <View style={styles.conversationPreview}>
            <Text
              style={[
                styles.messagePreview,
                hasUnread && styles.messagePreviewUnread,
              ]}
              numberOfLines={1}
            >
              {item.last_message_preview ?? 'No messages yet'}
            </Text>

            {/* Unread badge */}
            {hasUnread && (
              <View style={styles.unreadBadge}>
                <Text style={styles.unreadBadgeText}>
                  {item.unread_count > 99 ? '99+' : item.unread_count}
                </Text>
              </View>
            )}
          </View>
        </View>

        {/* Chevron */}
        <Ionicons name="chevron-forward" size={20} color="#9ca3af" />
      </TouchableOpacity>
    );
  };

  // Render empty state
  const renderEmptyState = () => {
    if (isLoading) return null;

    return (
      <View style={styles.emptyState}>
        <Ionicons name="chatbubbles-outline" size={64} color="#9ca3af" />
        <Text style={styles.emptyTitle}>No Conversations</Text>
        <Text style={styles.emptySubtitle}>
          Start a conversation with a host or client!
        </Text>
        <TouchableOpacity
          style={styles.findHostButton}
          onPress={() => router.push('/(tabs)/discover')}
        >
          <Text style={styles.findHostButtonText}>Find a Host</Text>
        </TouchableOpacity>
      </View>
    );
  };

  // Render footer (loading more)
  const renderFooter = () => {
    if (!loadingMore) return null;
    return (
      <View style={styles.footerLoader}>
        <ActivityIndicator size="small" color="#e11d48" />
      </View>
    );
  };

  // Auth required state
  if (!isAuthenticated) {
    return (
      <SafeAreaView style={styles.container} edges={['top']}>
        <View style={styles.header}>
          <Text style={styles.title}>Messages</Text>
        </View>
        <View style={styles.authRequired}>
          <Ionicons name="lock-closed-outline" size={64} color="#9ca3af" />
          <Text style={styles.authTitle}>Login Required</Text>
          <Text style={styles.authText}>
            Please log in to view your messages.
          </Text>
          <TouchableOpacity
            style={styles.loginButton}
            onPress={() => router.push('/(auth)/login')}
          >
            <Text style={styles.loginButtonText}>Log In</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.title}>Messages</Text>
      </View>

      {/* Conversations List */}
      {isLoading ? (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#e11d48" />
          <Text style={styles.loadingText}>Loading conversations...</Text>
        </View>
      ) : (
        <FlatList
          data={conversations}
          keyExtractor={(item) => item.id}
          renderItem={renderConversation}
          contentContainerStyle={styles.listContent}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
          }
          onEndReached={loadMore}
          onEndReachedThreshold={0.5}
          ListEmptyComponent={renderEmptyState}
          ListFooterComponent={renderFooter}
          ItemSeparatorComponent={() => <View style={styles.separator} />}
        />
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f3f4f6',
  },
  header: {
    backgroundColor: '#fff',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#e5e7eb',
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#1a1a1a',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 12,
    fontSize: 14,
    color: '#6b7280',
  },
  listContent: {
    flexGrow: 1,
    backgroundColor: '#fff',
  },
  conversationItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 14,
    backgroundColor: '#fff',
  },
  conversationUnread: {
    backgroundColor: '#fdf2f4',
  },
  avatar: {
    width: 52,
    height: 52,
    borderRadius: 26,
    backgroundColor: '#e11d48',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  avatarText: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
  },
  conversationContent: {
    flex: 1,
    marginRight: 8,
  },
  conversationHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  participantName: {
    fontSize: 16,
    fontWeight: '500',
    color: '#1f2937',
  },
  participantNameUnread: {
    fontWeight: '700',
  },
  timeAgo: {
    fontSize: 12,
    color: '#9ca3af',
  },
  conversationPreview: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  messagePreview: {
    flex: 1,
    fontSize: 14,
    color: '#6b7280',
    marginRight: 8,
  },
  messagePreviewUnread: {
    color: '#1f2937',
    fontWeight: '500',
  },
  unreadBadge: {
    minWidth: 22,
    height: 22,
    borderRadius: 11,
    backgroundColor: '#e11d48',
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 6,
  },
  unreadBadgeText: {
    fontSize: 12,
    fontWeight: 'bold',
    color: '#fff',
  },
  separator: {
    height: 1,
    backgroundColor: '#f3f4f6',
    marginLeft: 80,
  },
  emptyState: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 64,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1f2937',
    marginTop: 16,
  },
  emptySubtitle: {
    fontSize: 14,
    color: '#6b7280',
    marginTop: 8,
    textAlign: 'center',
  },
  findHostButton: {
    marginTop: 24,
    paddingVertical: 12,
    paddingHorizontal: 24,
    backgroundColor: '#e11d48',
    borderRadius: 8,
  },
  findHostButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
  },
  footerLoader: {
    paddingVertical: 16,
    alignItems: 'center',
  },
  authRequired: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  authTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#1f2937',
    marginTop: 16,
    marginBottom: 8,
  },
  authText: {
    fontSize: 14,
    color: '#6b7280',
    textAlign: 'center',
    marginBottom: 24,
  },
  loginButton: {
    paddingVertical: 14,
    paddingHorizontal: 32,
    backgroundColor: '#e11d48',
    borderRadius: 8,
  },
  loginButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
  },
});
