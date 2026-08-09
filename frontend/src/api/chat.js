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
 * Create a new chat conversation
 * @returns {Promise<{id: number, conversation_id: number, title: string}>}
 */
