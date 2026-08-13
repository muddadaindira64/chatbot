import axios from './axios';

/**
 * Send a message and get a JSON response
 * @param {number} conversationId - Conversation ID
 * @param {string} message - User message
 * @returns {Promise<object>} - JSON chat response
 */
export const sendMessage = async (conversationId, message) => {
  try {
    const response = await axios.post('/chat', {
      conversation_id: conversationId,
      message,
    });
    return response.data;
  } catch (error) {
    console.error('Failed to send message:', error?.response?.data || error.message || error);
    throw error;
  }
};

/**
 * Stream a chat message using SSE (Server-Sent Events)
 * @param {number} conversationId - Conversation ID
 * @param {string} message - User message
 * @param {function} onEvent - Callback for each SSE event ({type, content, name, ...})
 * @returns {Promise<object>} - Final result with conversation_id and message_id
 */
export const streamMessage = async (conversationId, message, onEvent) => {
  const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';
  const ACCESS_TOKEN_KEY = 'access_token';
  const LEGACY_TOKEN_KEY = 'token';
  const token = localStorage.getItem(ACCESS_TOKEN_KEY) || localStorage.getItem(LEGACY_TOKEN_KEY);

  const response = await fetch(`${API_URL}/chat/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({
      conversation_id: conversationId,
      message,
    }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Stream request failed: ${response.status}`);
  }

  if (!response.body) {
    throw new Error('Streaming not supported in this browser');
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  let finalConversationId = conversationId;
  let finalMessageId = null;

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });

    // Parse SSE events (separated by double newlines)
    const events = buffer.split('\n\n');
    buffer = events.pop() || '';

    for (const event of events) {
      const lines = event.split('\n');
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6));
            if (data.type === 'done') {
              finalConversationId = data.conversation_id ?? finalConversationId;
              finalMessageId = data.message_id ?? null;
            }
            onEvent?.(data);
          } catch (e) {
            console.error('Failed to parse SSE event:', e);
          }
        }
      }
    }
  }

  return {
    conversation_id: finalConversationId,
    message_id: finalMessageId,
  };
};

/**
 * Create a new chat conversation
 * @returns {Promise<{id: number, conversation_id: number, title: string}>}
 */
