import { useState, useEffect, useCallback, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  TextInput,
  KeyboardAvoidingView,
  Platform,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useLocalSearchParams, Stack, router } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { apiClient, ApiError } from '@/lib/api/client';
import { useAuthStore } from '@/stores/auth';
import type { components } from '@/types/api.gen';

type ConversationWithMessagesResponse = components['schemas']['ConversationWithMessagesResponse'];
type MessageWithSenderResponse = components['schemas']['MessageWithSenderResponse'];
type MessageListResponse = components['schemas']['MessageListResponse'];
type CreateMessageRequest = components['schemas']['CreateMessageRequest'];

// WebSocket state type
type WSStatus = 'connecting' | 'connected' | 'disconnected' | 'error';

export default function ChatScreen() {
  const { id: conversationId } = useLocalSearchParams<{ id: string }>();
  const { user, accessToken, isAuthenticated } = useAuthStore();

  // Refs
  const flatListRef = useRef<FlatList>(null);
  const wsRef = useRef<WebSocket | null>(null);

  // State
  const [conversation, setConversation] = useState<ConversationWithMessagesResponse | null>(null);
  const [messages, setMessages] = useState<MessageWithSenderResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [newMessage, setNewMessage] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [wsStatus, setWsStatus] = useState<WSStatus>('disconnected');
  const [loadingMore, setLoadingMore] = useState(false);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(false);

  // Get other participant
  const otherParticipant = conversation
    ? conversation.participant_1_id === user?.id
      ? conversation.participant_2
      : conversation.participant_1
    : null;

  // Fetch conversation and initial messages
  const fetchConversation = useCallback(async () => {
    if (!conversationId || !isAuthenticated) return;

    setIsLoading(true);
    try {
      // Fetch conversation with messages
      const data = await apiClient.get<ConversationWithMessagesResponse>(
        `/api/v1/conversations/${conversationId}`
      );
      setConversation(data);
      setMessages(data.messages ?? []);
      setError(null);

      // Mark as read
      await apiClient.post(`/api/v1/conversations/${conversationId}/read`);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.detail);
      } else {
        setError('Failed to load conversation');
      }
    } finally {
      setIsLoading(false);
    }
  }, [conversationId, isAuthenticated]);

  // Load more messages
  const loadMoreMessages = useCallback(async () => {
    if (!conversationId || !hasMore || loadingMore || !nextCursor) return;

    setLoadingMore(true);
    try {
      const data = await apiClient.get<MessageListResponse>(
        `/api/v1/conversations/${conversationId}/messages?cursor=${nextCursor}&limit=50`
      );

      setMessages((prev) => [...prev, ...data.items]);
      setNextCursor(data.next_cursor ?? null);
      setHasMore(data.has_more);
    } catch (err) {
      console.error('Failed to load more messages:', err);
    } finally {
      setLoadingMore(false);
    }
  }, [conversationId, hasMore, loadingMore, nextCursor]);

  // Setup WebSocket connection
  const connectWebSocket = useCallback(() => {
    if (!conversationId || !accessToken) return;

    // Get WebSocket URL (replace http with ws)
    const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL ?? 'http://localhost:8001';
    const wsUrl = API_BASE_URL.replace('http', 'ws');

    setWsStatus('connecting');

    const ws = new WebSocket(`${wsUrl}/ws/chat/${conversationId}?token=${accessToken}`);

    ws.onopen = () => {
      console.log('WebSocket connected');
      setWsStatus('connected');
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        if (data.type === 'message') {
          // New message received
          const newMsg: MessageWithSenderResponse = data.message;
          setMessages((prev) => {
            // Avoid duplicates
            if (prev.some((m) => m.id === newMsg.id)) {
              return prev;
            }
            return [newMsg, ...prev];
          });
        } else if (data.type === 'typing') {
          // Handle typing indicator (optional)
          console.log('Typing:', data);
        }
      } catch (err) {
        console.error('Failed to parse WebSocket message:', err);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setWsStatus('error');
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      setWsStatus('disconnected');
    };

    wsRef.current = ws;
  }, [conversationId, accessToken]);

  // Disconnect WebSocket
  const disconnectWebSocket = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  }, []);

  // Initial load
  useEffect(() => {
    fetchConversation();
  }, [fetchConversation]);

  // WebSocket lifecycle
  useEffect(() => {
    if (conversation) {
      connectWebSocket();
    }

    return () => {
      disconnectWebSocket();
    };
  }, [conversation, connectWebSocket, disconnectWebSocket]);

  // Send message
  const handleSend = useCallback(async () => {
    if (!newMessage.trim() || !conversationId || isSending) return;

    const messageContent = newMessage.trim();
    setNewMessage('');
    setIsSending(true);

    try {
      const request: CreateMessageRequest = {
        content: messageContent,
        message_type: 'text',
      };

      const sentMessage = await apiClient.post<MessageWithSenderResponse>(
        `/api/v1/conversations/${conversationId}/messages`,
        request
      );

      // Add to messages (WebSocket will also deliver it, so check for duplicates)
      setMessages((prev) => {
        if (prev.some((m) => m.id === sentMessage.id)) {
          return prev;
        }
        return [sentMessage, ...prev];
      });

      // Scroll to bottom
      flatListRef.current?.scrollToOffset({ offset: 0, animated: true });
    } catch (err) {
      // Restore message on error
      setNewMessage(messageContent);
      console.error('Failed to send message:', err);
    } finally {
      setIsSending(false);
    }
  }, [newMessage, conversationId, isSending]);

  // Format time
  const formatTime = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
    });
  };

  // Format date for separator
  const formatDateSeparator = (dateString: string) => {
    const date = new Date(dateString);
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);

    if (date.toDateString() === today.toDateString()) {
      return 'Today';
    } else if (date.toDateString() === yesterday.toDateString()) {
      return 'Yesterday';
    } else {
      return date.toLocaleDateString('en-US', {
        weekday: 'long',
        month: 'short',
        day: 'numeric',
      });
    }
  };

  // Render message item
  const renderMessage = ({ item, index }: { item: MessageWithSenderResponse; index: number }) => {
    const isOwnMessage = item.sender_id === user?.id;
    const showDateSeparator =
      index === messages.length - 1 ||
      formatDateSeparator(item.created_at) !==
        formatDateSeparator(messages[index + 1]?.created_at ?? '');

    return (
      <>
        <View
          style={[
            styles.messageContainer,
            isOwnMessage ? styles.ownMessage : styles.otherMessage,
          ]}
        >
          <View
            style={[
              styles.messageBubble,
              isOwnMessage ? styles.ownBubble : styles.otherBubble,
            ]}
          >
            <Text
              style={[
                styles.messageText,
                isOwnMessage ? styles.ownMessageText : styles.otherMessageText,
              ]}
            >
              {item.content}
            </Text>
            <Text
              style={[
                styles.messageTime,
                isOwnMessage ? styles.ownMessageTime : styles.otherMessageTime,
              ]}
            >
              {formatTime(item.created_at)}
            </Text>
          </View>
        </View>
        {showDateSeparator && (
          <View style={styles.dateSeparator}>
            <Text style={styles.dateSeparatorText}>
              {formatDateSeparator(item.created_at)}
            </Text>
          </View>
        )}
      </>
    );
  };

  // Loading state
  if (isLoading) {
    return (
      <>
        <Stack.Screen
          options={{
            headerShown: true,
            title: 'Chat',
            headerBackTitle: 'Back',
          }}
        />
        <SafeAreaView style={styles.container} edges={['bottom']}>
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color="#e11d48" />
            <Text style={styles.loadingText}>Loading conversation...</Text>
          </View>
        </SafeAreaView>
      </>
    );
  }

  // Error state
  if (error || !conversation) {
    return (
      <>
        <Stack.Screen
          options={{
            headerShown: true,
            title: 'Chat',
            headerBackTitle: 'Back',
          }}
        />
        <SafeAreaView style={styles.container} edges={['bottom']}>
          <View style={styles.errorContainer}>
            <Ionicons name="alert-circle-outline" size={64} color="#9ca3af" />
            <Text style={styles.errorTitle}>Conversation Not Found</Text>
            <Text style={styles.errorText}>
              {error ?? "This conversation doesn't exist."}
            </Text>
            <TouchableOpacity
              style={styles.retryButton}
              onPress={() => router.back()}
            >
              <Text style={styles.retryButtonText}>Go Back</Text>
            </TouchableOpacity>
          </View>
        </SafeAreaView>
      </>
    );
  }

  // Auth required state
  if (!isAuthenticated) {
    return (
      <>
        <Stack.Screen
          options={{
            headerShown: true,
            title: 'Chat',
            headerBackTitle: 'Back',
          }}
        />
        <SafeAreaView style={styles.container} edges={['bottom']}>
          <View style={styles.authRequired}>
            <Ionicons name="lock-closed-outline" size={64} color="#9ca3af" />
            <Text style={styles.authTitle}>Login Required</Text>
            <Text style={styles.authText}>Please log in to view messages.</Text>
            <TouchableOpacity
              style={styles.loginButton}
              onPress={() => router.push('/(auth)/login')}
            >
              <Text style={styles.loginButtonText}>Log In</Text>
            </TouchableOpacity>
          </View>
        </SafeAreaView>
      </>
    );
  }

  return (
    <>
      <Stack.Screen
        options={{
          headerShown: true,
          title: otherParticipant
            ? `${otherParticipant.first_name} ${otherParticipant.last_name}`
            : 'Chat',
          headerBackTitle: 'Back',
        }}
      />
      <SafeAreaView style={styles.container} edges={['bottom']}>
        <KeyboardAvoidingView
          style={styles.keyboardAvoid}
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
          keyboardVerticalOffset={90}
        >
          {/* Connection status */}
          {wsStatus !== 'connected' && (
            <View style={styles.connectionStatus}>
              {wsStatus === 'connecting' && (
                <>
                  <ActivityIndicator size="small" color="#fff" />
                  <Text style={styles.connectionStatusText}>Connecting...</Text>
                </>
              )}
              {wsStatus === 'disconnected' && (
                <Text style={styles.connectionStatusText}>Disconnected</Text>
              )}
              {wsStatus === 'error' && (
                <Text style={styles.connectionStatusText}>
                  Connection error
                </Text>
              )}
            </View>
          )}

          {/* Messages list */}
          <FlatList
            ref={flatListRef}
            data={messages}
            keyExtractor={(item) => item.id}
            renderItem={renderMessage}
            contentContainerStyle={styles.messagesList}
            inverted
            onEndReached={loadMoreMessages}
            onEndReachedThreshold={0.5}
            ListFooterComponent={
              loadingMore ? (
                <View style={styles.loadingMore}>
                  <ActivityIndicator size="small" color="#e11d48" />
                </View>
              ) : null
            }
            ListEmptyComponent={
              <View style={styles.emptyMessages}>
                <Ionicons name="chatbubbles-outline" size={48} color="#9ca3af" />
                <Text style={styles.emptyMessagesText}>No messages yet</Text>
                <Text style={styles.emptyMessagesSubtext}>
                  Start the conversation!
                </Text>
              </View>
            }
          />

          {/* Input area */}
          <View style={styles.inputContainer}>
            <TextInput
              style={styles.textInput}
              placeholder="Type a message..."
              placeholderTextColor="#9ca3af"
              value={newMessage}
              onChangeText={setNewMessage}
              multiline
              maxLength={2000}
            />
            <TouchableOpacity
              style={[
                styles.sendButton,
                (!newMessage.trim() || isSending) && styles.sendButtonDisabled,
              ]}
              onPress={handleSend}
              disabled={!newMessage.trim() || isSending}
            >
              {isSending ? (
                <ActivityIndicator size="small" color="#fff" />
              ) : (
                <Ionicons name="send" size={20} color="#fff" />
              )}
            </TouchableOpacity>
          </View>
        </KeyboardAvoidingView>
      </SafeAreaView>
    </>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f3f4f6',
  },
  keyboardAvoid: {
    flex: 1,
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
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  errorTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#1f2937',
    marginTop: 16,
    marginBottom: 8,
  },
  errorText: {
    fontSize: 14,
    color: '#6b7280',
    textAlign: 'center',
    marginBottom: 24,
  },
  retryButton: {
    paddingVertical: 12,
    paddingHorizontal: 24,
    backgroundColor: '#e11d48',
    borderRadius: 8,
  },
  retryButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
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
  connectionStatus: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#f59e0b',
    paddingVertical: 6,
    paddingHorizontal: 12,
    gap: 8,
  },
  connectionStatusText: {
    fontSize: 12,
    color: '#fff',
    fontWeight: '500',
  },
  messagesList: {
    paddingHorizontal: 16,
    paddingVertical: 8,
  },
  messageContainer: {
    marginVertical: 2,
    flexDirection: 'row',
  },
  ownMessage: {
    justifyContent: 'flex-end',
  },
  otherMessage: {
    justifyContent: 'flex-start',
  },
  messageBubble: {
    maxWidth: '75%',
    padding: 12,
    borderRadius: 16,
  },
  ownBubble: {
    backgroundColor: '#e11d48',
    borderBottomRightRadius: 4,
  },
  otherBubble: {
    backgroundColor: '#fff',
    borderBottomLeftRadius: 4,
  },
  messageText: {
    fontSize: 15,
    lineHeight: 20,
  },
  ownMessageText: {
    color: '#fff',
  },
  otherMessageText: {
    color: '#1f2937',
  },
  messageTime: {
    fontSize: 11,
    marginTop: 4,
  },
  ownMessageTime: {
    color: 'rgba(255, 255, 255, 0.7)',
    textAlign: 'right',
  },
  otherMessageTime: {
    color: '#9ca3af',
  },
  dateSeparator: {
    alignItems: 'center',
    marginVertical: 16,
  },
  dateSeparatorText: {
    fontSize: 12,
    color: '#9ca3af',
    backgroundColor: '#f3f4f6',
    paddingHorizontal: 12,
    paddingVertical: 4,
  },
  loadingMore: {
    paddingVertical: 16,
    alignItems: 'center',
  },
  emptyMessages: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 64,
  },
  emptyMessagesText: {
    fontSize: 16,
    fontWeight: '500',
    color: '#6b7280',
    marginTop: 12,
  },
  emptyMessagesSubtext: {
    fontSize: 14,
    color: '#9ca3af',
    marginTop: 4,
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    paddingHorizontal: 12,
    paddingVertical: 8,
    backgroundColor: '#fff',
    borderTopWidth: 1,
    borderTopColor: '#e5e7eb',
  },
  textInput: {
    flex: 1,
    backgroundColor: '#f3f4f6',
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 10,
    paddingRight: 48,
    fontSize: 15,
    maxHeight: 100,
    color: '#1f2937',
  },
  sendButton: {
    position: 'absolute',
    right: 20,
    bottom: 14,
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: '#e11d48',
    alignItems: 'center',
    justifyContent: 'center',
  },
  sendButtonDisabled: {
    backgroundColor: '#d1d5db',
  },
});
