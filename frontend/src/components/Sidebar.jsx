import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import { deleteConversation, renameConversation } from '../api/conversations';

const Sidebar = ({
  onNewChat,
  activeConversationId,
  onSelectConversation,
  onConversationDeleted,
  isOpen,
  onClose,
  conversations: initialConversations = [],
  loading = false,
  error = null,
}) => {
  const [conversations, setConversations] = useState(initialConversations);
  const [contextMenu, setContextMenu] = useState(null);
  const [editingConversation, setEditingConversation] = useState({ id: null, title: '' });
  const { user, logout } = useAuth();

  useEffect(() => {
    setConversations(initialConversations);
  }, [initialConversations]);

  const handleNewChat = useCallback(async () => {
    try {
      await onNewChat();
      onClose();
    } catch (error) {
      console.error('Failed to create new chat:', error);
    }
  }, [onClose, onNewChat]);

  const closeContextMenu = useCallback(() => {
    setContextMenu(null);
  }, []);

  const handleContextMenu = useCallback((event, conversation) => {
    event.preventDefault();
    setContextMenu({
      x: event.pageX,
      y: event.pageY,
      conversation,
    });
  }, []);

  const handleSelectConversation = (conversation) => {
    onSelectConversation(conversation.id);
    onClose();
  };

  const handleRename = useCallback(() => {
    if (contextMenu?.conversation) {
      setEditingConversation({
        id: contextMenu.conversation.id,
        title: contextMenu.conversation.title || '',
      });
    }
    closeContextMenu();
  }, [contextMenu, closeContextMenu]);

  const handleDelete = useCallback(async () => {
    if (!contextMenu?.conversation) {
      closeContextMenu();
      return;
    }

    const confirmed = window.confirm('Delete this conversation and all associated messages?');
    if (!confirmed) {
      closeContextMenu();
      return;
    }

    const conversationId = contextMenu.conversation.id;
    closeContextMenu();

    try {
      await deleteConversation(conversationId);
      setConversations((prev) => prev.filter((conv) => conv.id !== conversationId));
      if (onConversationDeleted) {
        onConversationDeleted(conversationId);
      }
    } catch (error) {
      console.error('Failed to delete conversation:', error);
    }
  }, [contextMenu, onConversationDeleted, closeContextMenu]);

  const handleRenameSubmit = useCallback(async () => {
    if (!editingConversation.id) {
      return;
    }

    const title = editingConversation.title.trim();
    if (!title) {
      return;
    }

    try {
      const updated = await renameConversation(editingConversation.id, title);
      setConversations((prev) => prev.map((conv) => (
        conv.id === updated.id ? { ...conv, title: updated.title } : conv
      )));
      setEditingConversation({ id: null, title: '' });
    } catch (error) {
      console.error('Failed to rename conversation:', error);
    }
  }, [editingConversation.id, editingConversation.title]);

  const handleRenameCancel = useCallback(() => {
    setEditingConversation({ id: null, title: '' });
  }, []);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (contextMenu) {
        closeContextMenu();
      }
    };

    window.addEventListener('click', handleClickOutside);
    return () => window.removeEventListener('click', handleClickOutside);
  }, [contextMenu, closeContextMenu]);

  const groupConversationsByDate = (conversationList) => {
    const today = [];
    const yesterday = [];
    const older = [];

    const todayDate = new Date().toDateString();
    const yesterdayDate = new Date(Date.now() - 86400000).toDateString();

    conversationList.forEach((conv) => {
      const convDate = new Date(conv.created_at).toDateString();
      if (convDate === todayDate) {
        today.push(conv);
      } else if (convDate === yesterdayDate) {
        yesterday.push(conv);
      } else {
        older.push(conv);
      }
    });

    return { today, yesterday, older };
  };

  const { today, yesterday, older } = useMemo(
    () => groupConversationsByDate(conversations),
    [conversations]
  );

  const renderConversation = useCallback((conv) => {
    const isEditing = editingConversation.id === conv.id;

    return (
      <div
        key={conv.id}
        onClick={() => handleSelectConversation(conv)}
        onContextMenu={(event) => handleContextMenu(event, conv)}
        className={`text-sm p-2 rounded cursor-pointer truncate ${
          activeConversationId === conv.id
            ? 'bg-gray-700 text-white'
            : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
        }`}
      >
        {isEditing ? (
          <input
            autoFocus
            className="w-full rounded border border-gray-600 bg-gray-900 text-white px-2 py-1"
            value={editingConversation.title}
            onChange={(event) => setEditingConversation((prev) => ({ ...prev, title: event.target.value }))}
            onBlur={handleRenameSubmit}
            onKeyDown={(event) => {
              if (event.key === 'Enter') {
                handleRenameSubmit();
              } else if (event.key === 'Escape') {
                handleRenameCancel();
              }
            }}
          />
        ) : (
          conv.title || 'New Chat'
        )}
      </div>
    );
  }, [activeConversationId, editingConversation.id, editingConversation.title, handleContextMenu, handleRenameCancel, handleRenameSubmit, handleSelectConversation]);

  return (
    <>
      {isOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-20 lg:hidden"
          onClick={onClose}
        />
      )}

      <div className={`
        fixed lg:static inset-y-0 left-0 z-30
        bg-gray-900 text-white
        w-64 lg:w-64
        transform transition-transform duration-300 ease-in-out
        ${isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
        flex flex-col
      `}>
        <div className="p-4 border-b border-gray-700 flex items-center justify-between">
          <h1 className="text-xl font-bold">ChatGPT Clone</h1>
          <button
            onClick={onClose}
            className="lg:hidden text-gray-400 hover:text-white"
            aria-label="Close sidebar"
          >
            X
          </button>
        </div>

        <div className="p-4">
          <button
            onClick={handleNewChat}
            className="w-full bg-gray-800 hover:bg-gray-700 text-white py-2 px-4 rounded-lg flex items-center justify-center gap-2 transition-colors"
          >
            <span>+</span>
            <span>New Chat</span>
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-4">
          <div className="text-gray-400 text-sm mb-2">History</div>

          {loading ? (
            <div className="text-gray-500 text-sm p-2">Loading...</div>
          ) : error ? (
            <div className="text-red-400 text-sm p-2">Failed to load conversations.</div>
          ) : conversations.length === 0 ? (
            <div className="text-gray-500 text-sm p-2">No chats yet</div>
          ) : (
            <div className="space-y-2">
              {today.length > 0 && (
                <>
                  <div className="text-gray-500 text-xs uppercase mb-1">Today</div>
                  {today.map(renderConversation)}
                </>
              )}

              {yesterday.length > 0 && (
                <>
                  <div className="text-gray-500 text-xs uppercase mb-1 mt-4">Yesterday</div>
                  {yesterday.map(renderConversation)}
                </>
              )}

              {older.length > 0 && (
                <>
                  <div className="text-gray-500 text-xs uppercase mb-1 mt-4">Previous</div>
                  {older.map(renderConversation)}
                </>
              )}
            </div>
          )}
        </div>

        <div className="p-4 border-t border-gray-700">
          <div className="flex items-center justify-between gap-3">
            <div className="min-w-0 text-sm">
              <div className="truncate text-gray-300 font-medium">{user?.username}</div>
              <div className="truncate text-gray-500 text-xs">{user?.email}</div>
            </div>
            <button
              onClick={logout}
              className="text-gray-400 hover:text-white text-sm"
              title="Logout"
            >
              Logout
            </button>
          </div>
        </div>
      </div>
      {contextMenu && (
        <div
          className="fixed z-50 rounded-lg bg-gray-800 border border-gray-700 shadow-lg"
          style={{ top: contextMenu.y, left: contextMenu.x, minWidth: 160 }}
        >
          <button
            type="button"
            onClick={handleRename}
            className="w-full text-left px-4 py-2 hover:bg-gray-700"
          >
            Rename
          </button>
          <button
            type="button"
            onClick={handleDelete}
            className="w-full text-left px-4 py-2 hover:bg-gray-700"
          >
            Delete
          </button>
        </div>
      )}
    </>
  );
};

export default React.memo(Sidebar);
