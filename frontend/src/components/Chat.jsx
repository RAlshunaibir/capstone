import React, { useEffect, useRef, useState } from 'react';
import { API_ENDPOINTS } from '../config';

export default function Chat({ onAuthError }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [conversations, setConversations] = useState([]);
  const [selectedSession, setSelectedSession] = useState(null);
  const chatBoxRef = useRef(null);

  // Get token from localStorage
  const getAuthHeaders = () => {
    const token = localStorage.getItem('token');
    return {
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Bearer ${token}` })
    };
  };

  // Function to fetch chat history
  const fetchHistory = async () => {
    setError('');
    setLoading(true);
          try {
        const res = await fetch(API_ENDPOINTS.CHAT_HISTORY, {
        headers: getAuthHeaders()
      });
      const data = await res.json();
      if (!res.ok) {
        if (res.status === 401 || res.status === 403) {
          if (onAuthError) onAuthError();
          return;
        }
        setError(data.detail || 'No chat history found');
        setMessages([
          { role: 'bot', content: 'Hello! Ask me anything.' }
        ]);
        return;
      }
      // If data is an array of chat sessions, use the latest session's messages
      if (Array.isArray(data) && data.length > 0) {
        setConversations(data);
        // Use the latest session's messages
        const latestSession = data[0];
        setSelectedSession(latestSession.session_id);
        setMessages(latestSession.messages || [
          { role: 'bot', content: 'Hello! Ask me anything.' }
        ]);
      } else {
        setMessages([
          { role: 'bot', content: 'Hello! Ask me anything.' }
        ]);
      }
    } catch (err) {
      setError('No chat history found');
      setMessages([
        { role: 'bot', content: 'Hello! Ask me anything.' }
      ]);
    } finally {
      setLoading(false);
    }
  };

  // Fetch chat history after login
  useEffect(() => {
    fetchHistory();
    // eslint-disable-next-line
  }, []);

  // Scroll to bottom on new message
  useEffect(() => {
    if (chatBoxRef.current) {
      chatBoxRef.current.scrollTop = chatBoxRef.current.scrollHeight;
    }
  }, [messages]);

  async function sendMessage(e) {
    e.preventDefault();
    if (!input.trim()) return;
    setError('');
    const userMsg = { role: 'user', content: input };
    setMessages(msgs => [...msgs, userMsg]);
    setInput('');
    setLoading(true);
    try {
      const res = await fetch(API_ENDPOINTS.CHAT, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({ message: userMsg.content })
      });
      const data = await res.json();
      if (!res.ok) {
        if (res.status === 401 || res.status === 403) {
          if (onAuthError) onAuthError();
          return;
        }
        setError(data.error || 'Error from server');
        return;
      }
      setMessages(msgs => [...msgs, { role: 'bot', content: data.response }]);
      // Only refresh sidebar if this is a new conversation (no selected session)
      if (!selectedSession) {
        await fetchHistory();
      }
    } catch (err) {
      setError('Network error');
    } finally {
      setLoading(false);
    }
  }

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now - date);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays === 1) return 'Today';
    if (diffDays === 2) return 'Yesterday';
    if (diffDays <= 7) return `${diffDays - 1} days ago`;
    return date.toLocaleDateString();
  };

  const getConversationTitle = (conversation) => {
    if (conversation.messages && conversation.messages.length > 0) {
      const firstUserMessage = conversation.messages.find(msg => msg.role === 'user');
      if (firstUserMessage) {
        return firstUserMessage.content.slice(0, 30) + (firstUserMessage.content.length > 30 ? '...' : '');
      }
    }
    return 'New conversation';
  };

  const deleteConversation = async (sessionId, e) => {
    e.stopPropagation(); // Prevent selecting the conversation
    if (!confirm('Are you sure you want to delete this conversation?')) {
      return;
    }
    
    try {
      const res = await fetch(API_ENDPOINTS.DELETE_CHAT_HISTORY(sessionId), {
        method: 'DELETE',
        headers: getAuthHeaders()
      });
      
      if (!res.ok) {
        if (res.status === 401 || res.status === 403) {
          if (onAuthError) onAuthError();
          return;
        }
        setError('Failed to delete conversation');
        return;
      }
      
      // Remove from local state
      setConversations(prev => prev.filter(conv => conv.session_id !== sessionId));
      
      // If this was the selected conversation, clear it
      if (selectedSession === sessionId) {
        setSelectedSession(null);
        setMessages([{ role: 'bot', content: 'Hello! Ask me anything.' }]);
      }
    } catch (err) {
      setError('Failed to delete conversation');
    }
  };

  return (
    <div className="chat-layout">
      {/* Sidebar */}
      <div className="chat-sidebar">
        <div className="sidebar-header">
          <h3>Chat History</h3>
          <button 
            className="new-chat-btn"
            onClick={() => {
              setMessages([{ role: 'bot', content: 'Hello! Ask me anything.' }]);
              setSelectedSession(null);
            }}
          >
            + New Chat
          </button>
        </div>
        <div className="conversations-list">
          {conversations.map((conversation) => (
            <div
              key={conversation.session_id}
              className={`conversation-item ${selectedSession === conversation.session_id ? 'active' : ''}`}
              onClick={() => {
                setSelectedSession(conversation.session_id);
                setMessages(conversation.messages || [
                  { role: 'bot', content: 'Hello! Ask me anything.' }
                ]);
              }}
            >
              <div className="conversation-content">
                <div className="conversation-title">
                  {getConversationTitle(conversation)}
                </div>
                <div className="conversation-date">
                  {formatDate(conversation.last_activity)}
                </div>
              </div>
              <button
                className="delete-conversation-btn"
                onClick={(e) => deleteConversation(conversation.session_id, e)}
                title="Delete conversation"
              >
                🗑️
              </button>
            </div>
          ))}
          {conversations.length === 0 && (
            <div className="no-conversations">
              No previous conversations
            </div>
          )}
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="chat-main">
        <div className="chat-header">Rakan's Chatbot</div>
        <div className="chat-box" ref={chatBoxRef}>
          {messages.map((msg, idx) => (
            <div
              key={idx}
              className={`message ${msg.role}`}
            >
              <div className={`avatar ${msg.role}`}>{(msg.role === 'bot' || msg.role === 'assistant') ? 'AI' : ''}</div>
              <div className="bubble">{msg.content}</div>
            </div>
          ))}
          {loading && (
            <div className="message bot typing-indicator">
              <span></span><span></span><span></span>
            </div>
          )}
        </div>
        <form className="chat-input-container" onSubmit={sendMessage}>
          <div className="chat-input">
            <input
              type="text"
              value={input}
              onChange={e => setInput(e.target.value)}
              placeholder="Type a message..."
              disabled={loading}
            />
            <button type="submit" disabled={loading || !input.trim()}>
              ➤
            </button>
          </div>
        </form>
        {error && <div className="chat-error">{error}</div>}
      </div>
    </div>
  );
} 