import { useState, useEffect, useRef, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import Sidebar from '../components/Sidebar';
import ChatWindow from '../components/ChatWindow';
import InputBox from '../components/InputBox';
import { getConversations, getConversationMessages } from '../api/conversations';
import { sendMessage } from '../api/chat';

const normalizeAssistantPayload = (payload) => {
  if (!payload || typeof payload !== 'object') {
    return { content: '', conversationId: null };
  }

  return {
    content: typeof payload.message === 'string' ? payload.message : '',
    conversationId: payload.conversation_id ?? null,
    tool: payload.tool?.name || null,
  };
};

const transformConversationMessages = (data = []) => {
  return data.map((msg) => ({
    id: msg.id,
    role: msg.role,
    content: msg.content || '',
  }));
};

const Chat = () => {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState(null);
  const [loadingMessages, setLoadingMessages] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [historyRefreshKey, setHistoryRefreshKey] = useState(0);
  const [conversations, setConversations] = useState([]);
  const [sidebarLoading, setSidebarLoading] = useState(false);
  const [sidebarError, setSidebarError] = useState(null);
  const { user, logout } = useAuth();
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const fetchConversations = useCallback(async () => {
    setSidebarLoading(true);
    setSidebarError(null);

    try {
      const data = await getConversations();
      setConversations(data);
    } catch (error) {
      console.error('Failed to fetch conversations:', error);
      setSidebarError(error);
    } finally {
      setSidebarLoading(false);
    }
  }, []);


  useEffect(() => {
    fetchConversations();
  }, [fetchConversations, historyRefreshKey]);

  const refreshConversationMessages = useCallback(async (activeConversationId) => {
    const data = await getConversationMessages(activeConversationId);
    setMessages(transformConversationMessages(data));
  }, []);


  const handleNewChat = useCallback(() => {
    setConversationId(null);
    setMessages([]);
    setHistoryRefreshKey((key) => key + 1);
  }, []);

  const handleSelectConversation = useCallback(async (selectedConversationId) => {
    setConversationId(selectedConversationId);
    setLoadingMessages(true);

    try {
      await refreshConversationMessages(selectedConversationId);
    } catch (error) {
      console.error('Failed to load messages:', error);
      setMessages([]);
    } finally {
      setLoadingMessages(false);
    }
  }, [refreshConversationMessages]);

  const updateAssistantMessage = useCallback((content, tool = null, localId = null) => {
    setMessages((prev) => {
      const updated = [...prev];
      const index = localId
        ? updated.findIndex((m) => m.localId === localId)
        : updated.findLastIndex((m) => m.role === 'assistant');

      if (index >= 0) {
        updated[index] = {
          ...updated[index],
          content,
          tool,
        };
      }

      return updated;
    });
  }, []);

  const handleSendMessage = async (content) => {
    const trimmedContent = content.trim();

    if (!trimmedContent || loading) {
      return;
    }

    let currentConversationId = conversationId;

    const now = Date.now();
    const userMessage = { role: 'user', content: trimmedContent, localId: `user-${now}` };
    const assistantMessage = { role: 'assistant', content: '', tool: null, localId: `assistant-${now}` };

    setMessages((prev) => [...prev, userMessage, assistantMessage]);
    setLoading(true);

    try {
      const response = await sendMessage(currentConversationId, trimmedContent);
      console.log('CHAT RESPONSE:', response);
      const normalized = normalizeAssistantPayload(response);

      if (normalized.conversationId) {
        currentConversationId = normalized.conversationId;
        setConversationId(normalized.conversationId);
      }

      updateAssistantMessage(normalized.content || '', normalized.tool, assistantMessage.localId);
      setLoading(false);
      setHistoryRefreshKey((key) => key + 1);
    } catch (error) {
      console.error('Failed to send message:', error);
      updateAssistantMessage('Sorry, I encountered an error. Please try again.', null, assistantMessage.localId);
      setLoading(false);
    }
  };

  return (
    <div className="flex h-screen bg-gray-100">
      <Sidebar
        onNewChat={handleNewChat}
        activeConversationId={conversationId}
        onSelectConversation={handleSelectConversation}
        onConversationDeleted={(deletedId) => {
          if (deletedId === conversationId) {
            setConversationId(null);
            setMessages([]);
          }
          setConversations((prev) => prev.filter((conv) => conv.id !== deletedId));
        }}
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        conversations={conversations}
        loading={sidebarLoading}
        error={sidebarError}
      />

      <div className="flex-1 flex flex-col">
        <div className="bg-white border-b border-gray-200 p-4 flex justify-between items-center">
          <div className="flex items-center gap-4">
            <button
              onClick={() => setSidebarOpen(true)}
              className="lg:hidden text-gray-600 hover:text-gray-900"
              aria-label="Open sidebar"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
            <h2 className="text-xl font-semibold">Chat</h2>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-gray-600 hidden sm:inline">{user?.username}</span>
            <button
              onClick={logout}
              className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition-colors"
            >
              Logout
            </button>
          </div>
        </div>

        {loadingMessages ? (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-gray-500">Loading messages...</div>
          </div>
        ) : (
          <ChatWindow messages={messages} loading={loading} />
        )}

        <InputBox onSend={handleSendMessage} loading={loading} />

        <div ref={messagesEndRef} />
      </div>
    </div>
  );
};

export default Chat;
