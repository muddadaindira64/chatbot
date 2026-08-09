import { useEffect, useRef } from 'react';
import Message from './Message';

const ChatWindow = ({ messages, loading }) => {
  const messagesContainerRef = useRef(null);

  useEffect(() => {
    if (messagesContainerRef.current) {
      messagesContainerRef.current.scrollTop = messagesContainerRef.current.scrollHeight;
    }
  }, [messages, loading]);

  return (
    <div
      ref={messagesContainerRef}
      className="flex-1 overflow-y-auto p-4 bg-white"
    >
      {messages.length === 0 ? (
        <div className="flex items-center justify-center h-full text-gray-400">
          <div className="text-center">
            <div className="text-4xl mb-4">ChatGPT Clone</div>
            <div className="text-xl mb-2">Start a new conversation</div>
            <div className="text-sm">Type a message below</div>
          </div>
        </div>
      ) : (
        <div className="max-w-4xl mx-auto">
          {messages.map((message, index) => (
            <Message
              key={message.localId || message.id || index}
              role={message.role}
              content={message.content}
              tool={message.tool}
            />
          ))}
          {loading && (
            <div className="flex justify-start mb-4">
              <div className="bg-gray-200 text-gray-900 rounded-lg p-3">
                <div className="text-sm flex items-center gap-2">
                  <span>Assistant is typing...</span>
                  <span className="inline-flex gap-1">
                    <span className="animate-bounce">.</span>
                    <span className="animate-bounce" style={{ animationDelay: '0.2s' }}>.</span>
                    <span className="animate-bounce" style={{ animationDelay: '0.4s' }}>.</span>
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ChatWindow;
