import { useState } from 'react';
import { submitFeedback } from '../api/feedback';

const Feedback = ({ messageId, onFeedbackSubmitted }) => {
  const [rating, setRating] = useState(null);
  const [comment, setComment] = useState('');
  const [showCommentInput, setShowCommentInput] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleFeedback = async (selectedRating) => {
    if (submitted) return;

    setLoading(true);
    try {
      await submitFeedback(messageId, selectedRating, comment);
      setRating(selectedRating);
      setSubmitted(true);
      if (onFeedbackSubmitted) {
        onFeedbackSubmitted();
      }
    } catch (error) {
      console.error('Failed to submit feedback:', error);
      alert('Failed to submit feedback. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  if (submitted) {
    return (
      <div className="text-xs text-gray-500 mt-1">
        Thanks for your feedback!
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2 mt-1">
      <button
        onClick={() => handleFeedback('positive')}
        disabled={loading}
        className="text-gray-400 hover:text-green-600 transition-colors disabled:opacity-50"
        title="Good response"
      >
        👍
      </button>
      <button
        onClick={() => {
          setShowCommentInput(true);
          handleFeedback('negative');
        }}
        disabled={loading}
        className="text-gray-400 hover:text-red-600 transition-colors disabled:opacity-50"
        title="Bad response"
      >
        👎
      </button>

      {showCommentInput && (
        <div className="ml-2">
          <input
            type="text"
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            placeholder="Optional comment..."
            className="text-xs border border-gray-300 rounded px-2 py-1 w-48"
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                handleFeedback('negative');
              }
            }}
          />
        </div>
      )}
    </div>
  );
};

export default Feedback;