import { useState, useEffect, useRef } from 'react';
import { chatbotMessage } from '../../services/api';
import { FaRobot, FaPaperPlane } from 'react-icons/fa';
import './Chatbot.css';

export default function Chatbot() {
  const [messages, setMessages] = useState([
    { role: 'bot', content: 'Bonjour ! Je suis votre assistant formation. Comment puis-je vous aider ?' }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEnd = useRef(null);

  useEffect(() => {
    messagesEnd.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMsg = input.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
    setLoading(true);

    try {
      const res = await chatbotMessage({ message: userMsg });
      setMessages(prev => [...prev, { role: 'bot', content: res.data.response }]);
    } catch {
      setMessages(prev => [...prev, { role: 'bot', content: 'Désolé, une erreur est survenue.' }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chatbot-page">
      <div className="chatbot-container card">
        <div className="chatbot-header">
          <FaRobot />
          <h2>Assistant Formation</h2>
        </div>

        <div className="chatbot-messages">
          {messages.map((msg, i) => (
            <div key={i} className={`message ${msg.role}`}>
              <div className="message-bubble">
                {msg.content}
              </div>
            </div>
          ))}
          {loading && (
            <div className="message bot">
              <div className="message-bubble typing">
                <span></span><span></span><span></span>
              </div>
            </div>
          )}
          <div ref={messagesEnd} />
        </div>

        <form className="chatbot-input" onSubmit={handleSend}>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Posez votre question..."
            disabled={loading}
          />
          <button type="submit" disabled={loading || !input.trim()}>
            <FaPaperPlane />
          </button>
        </form>
      </div>
    </div>
  );
}
