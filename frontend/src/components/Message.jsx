import Feedback from './Feedback';

const TOOL_LABELS = {
  live_search: '🔎 Tool: live_search',
  calculator: '🧮 Tool: calculator',
  get_weather: '🌤️ Tool: get_weather',
  get_datetime: '📅 Tool: get_datetime',
};

const Message = ({ role, content, tool, messageId }) => {
  const toolLabel = tool && TOOL_LABELS[tool] ? TOOL_LABELS[tool] : null;

  return (
    <div className={`mb-6 ${role === 'user' ? 'text-right' : 'text-left'}`}>
      {toolLabel && (
        <div className="text-xs text-gray-500 mb-2">
          {toolLabel}
        </div>
      )}

      <div
        className={`inline-block rounded-xl px-4 py-3 max-w-3xl whitespace-pre-wrap ${role === 'user'
            ? 'bg-blue-600 text-white'
            : 'bg-gray-100 text-gray-900'
          }`}
      >
        {content}
      </div>

      {role === 'assistant' && messageId && (
        <div className="mt-1">
          <Feedback messageId={messageId} />
        </div>
      )}
    </div>
  );
};

export default Message;
