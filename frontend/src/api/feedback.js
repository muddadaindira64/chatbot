/**
 * Submit feedback for a message
 * @param {number} messageId - Message ID to provide feedback for
 * @param {string} rating - "positive" or "negative"
 * @param {string} comment - Optional comment
 * @returns {Promise<{message: string, feedback_id: number}>}
 */
export const submitFeedback = async (messageId, rating, comment = '') => {
  try {
    const response = await fetch('/api/v1/feedback', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message_id: messageId,
        rating,
        comment,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to submit feedback');
    }

    return await response.json();
  } catch (error) {
    console.error('Failed to submit feedback:', error);
    throw error;
  }
};