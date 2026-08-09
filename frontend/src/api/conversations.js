import axios from './axios';

export const getConversations = async (options = {}) => {
  try {
    const response = await axios.get('/conversations', options);
    return response.data;
  } catch (error) {
    console.error('Failed to fetch conversations:', error);
    throw error;
  }
};

export const createConversation = async () => {
  try {
    const response = await axios.post('/conversations');
    return response.data;
  } catch (error) {
    console.error('Failed to create conversation:', error);
    throw error;
  }
};

export const getConversationMessages = async (conversationId) => {
  try {
    const response = await axios.get(`/conversations/${conversationId}/messages`);
    return response.data;
  } catch (error) {
    console.error('Failed to fetch messages:', error);
    throw error;
  }
};

export const renameConversation = async (conversationId, title) => {
  try {
    const response = await axios.patch(`/conversations/${conversationId}`, { title });
    return response.data;
  } catch (error) {
    console.error('Failed to rename conversation:', error);
    throw error;
  }
};

export const deleteConversation = async (conversationId) => {
  try {
    const response = await axios.delete(`/conversations/${conversationId}`);
    return response.data;
  } catch (error) {
    console.error('Failed to delete conversation:', error);
    throw error;
  }
};