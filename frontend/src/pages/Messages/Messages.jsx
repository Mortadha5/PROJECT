import { useState, useEffect, useRef, useCallback } from 'react';
import { getMessages, sendMessage, getUsers, getUnreadMessages } from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { FaComments, FaPaperPlane, FaUsers, FaUser } from 'react-icons/fa';
import toast from 'react-hot-toast';
import './Messages.css';

// Notification sound using Web Audio API
function playNotifSound() {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.type = 'sine';
    osc.frequency.setValueAtTime(880, ctx.currentTime);
    osc.frequency.setValueAtTime(1100, ctx.currentTime + 0.1);
    gain.gain.setValueAtTime(0.3, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.4);
    osc.start(ctx.currentTime);
    osc.stop(ctx.currentTime + 0.4);
  } catch {
    // Audio not available
  }
}

// Browser notification
function showBrowserNotif(from, message) {
  if (Notification.permission === 'granted') {
    new Notification(`Nouveau message de ${from}`, {
      body: message.length > 60 ? message.slice(0, 60) + '...' : message,
      icon: '💬',
    });
  }
}

export default function Messages() {
  const { user } = useAuth();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(true);
  const [conversations, setConversations] = useState([]);
  const [selectedUser, setSelectedUser] = useState(null);
  const [newMsgFlash, setNewMsgFlash] = useState(false);
  const [unreadPerUser, setUnreadPerUser] = useState({});
  const prevMsgCount = useRef(0);
  const isFirstLoad = useRef(true);

  // Request notification permission on mount
  useEffect(() => {
    if ('Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission();
    }
  }, []);

  const checkNewMessages = useCallback((newMessages) => {
    if (isFirstLoad.current) {
      isFirstLoad.current = false;
      prevMsgCount.current = newMessages.length;
      return;
    }
    if (newMessages.length > prevMsgCount.current) {
      const lastMsg = newMessages[newMessages.length - 1];
      if (lastMsg) {
        playNotifSound();
        showBrowserNotif(lastMsg.from_user, lastMsg.message);
        setNewMsgFlash(true);
        setTimeout(() => setNewMsgFlash(false), 2000);
      }
    }
    prevMsgCount.current = newMessages.length;
  }, [user?.username]);

  useEffect(() => {
    if (user?.role === 'admin') {
      loadConversations();
    } else {
      loadMessages();
    }
    const interval = setInterval(() => {
      if (user?.role === 'admin' && selectedUser) {
        loadAdminMessages(selectedUser);
      } else if (user?.role !== 'admin') {
        loadMessages();
      }
    }, 5000);
    return () => clearInterval(interval);
  }, [selectedUser]);

  const loadConversations = async () => {
    try {
      const [usersRes, unreadRes] = await Promise.all([getUsers(), getUnreadMessages()]);
      const users = (usersRes.data.users || []).filter(u => u.username !== 'admin');
      setConversations(users);
      setUnreadPerUser(unreadRes.data.per_user || {});
    } catch {
      // fallback empty
    } finally {
      setLoading(false);
    }
  };

  const loadAdminMessages = async (username) => {
    try {
      const res = await getMessages(username);
      const msgs = res.data.messages || [];
      setMessages(msgs);
      checkNewMessages(msgs);
    } catch {
      // silent
    }
  };

  const selectConversation = (username) => {
    setSelectedUser(username);
    setMessages([]);
    isFirstLoad.current = true;
    prevMsgCount.current = 0;
    loadAdminMessages(username);
    // Clear unread for this user locally
    setUnreadPerUser(prev => ({ ...prev, [username]: 0 }));
  };

  const loadMessages = async () => {
    try {
      const res = await getMessages();
      const msgs = res.data.messages || [];
      setMessages(msgs);
      checkNewMessages(msgs);
    } catch {
      // silent
    } finally {
      setLoading(false);
    }
  };

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const payload = { message: input.trim() };
    if (user?.role === 'admin') {
      if (!selectedUser) {
        toast.error('Sélectionnez un utilisateur');
        return;
      }
      payload.to_user = selectedUser;
    }

    try {
      await sendMessage(payload);
      setInput('');
      if (user?.role === 'admin') {
        loadAdminMessages(selectedUser);
      } else {
        loadMessages();
      }
    } catch {
      toast.error("Erreur d'envoi");
    }
  };

  if (loading) return <div className="loading-screen"><div className="spinner" /></div>;

  // Admin layout with conversation list
  if (user?.role === 'admin') {
    return (
      <div className="messages-page">
        <div className="messages-layout">
          <div className="conversations-panel">
            <div className="conversations-header">
              <FaUsers />
              <h3>Conversations</h3>
            </div>
            <div className="conversations-list">
              {conversations.length === 0 ? (
                <p className="no-convos">Aucun utilisateur</p>
              ) : (
                conversations.map(u => (
                  <div
                    key={u.username}
                    className={`convo-item ${selectedUser === u.username ? 'active' : ''}`}
                    onClick={() => selectConversation(u.username)}
                  >
                    <div className="convo-avatar">{u.username.charAt(0).toUpperCase()}</div>
                    <span className="convo-name">{u.username}</span>
                    {unreadPerUser[u.username] > 0 && (
                      <span className="convo-badge">{unreadPerUser[u.username]}</span>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>

          <div className="messages-container card">
            {!selectedUser ? (
              <div className="no-selection">
                <FaComments />
                <p>Sélectionnez une conversation</p>
              </div>
            ) : (
              <>
                <div className="messages-header">
                  <FaUser />
                  <h2>{selectedUser}</h2>
                </div>
                <div className={`messages-list ${newMsgFlash ? 'msg-flash' : ''}`}>
                  {messages.length === 0 ? (
                    <p className="no-messages">Aucun message</p>
                  ) : (
                    messages.map((msg, i) => (
                      <div key={msg._id || i} className={`msg ${msg.from_user === user?.username ? 'sent' : 'received'}`}>
                        <div className="msg-bubble">
                          <p>{msg.message}</p>
                          <span className="msg-time">
                            {msg.created_at ? new Date(msg.created_at).toLocaleString('fr-FR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' }) : ''}
                          </span>
                        </div>
                      </div>
                    ))
                  )}
                </div>
                <form className="messages-input" onSubmit={handleSend}>
                  <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder={`Message à ${selectedUser}...`}
                  />
                  <button type="submit" disabled={!input.trim()}>
                    <FaPaperPlane />
                  </button>
                </form>
              </>
            )}
          </div>
        </div>
      </div>
    );
  }

  // Regular user layout
  return (
    <div className="messages-page">
      <div className="messages-container card">
        <div className="messages-header">
          <FaComments />
          <h2>Messages</h2>
        </div>

        <div className={`messages-list ${newMsgFlash ? 'msg-flash' : ''}`}>
          {messages.length === 0 ? (
            <p className="no-messages">Aucun message pour l'instant</p>
          ) : (
            messages.map((msg, i) => (
              <div key={msg._id || i} className={`msg ${msg.from_user === user?.username ? 'sent' : 'received'}`}>
                <div className="msg-bubble">
                  <p>{msg.message}</p>
                  <span className="msg-time">
                    {msg.created_at ? new Date(msg.created_at).toLocaleString('fr-FR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' }) : ''}
                  </span>
                </div>
              </div>
            ))
          )}
        </div>

        <form className="messages-input" onSubmit={handleSend}>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Écrire un message..."
          />
          <button type="submit" disabled={!input.trim()}>
            <FaPaperPlane />
          </button>
        </form>
      </div>
    </div>
  );
}
