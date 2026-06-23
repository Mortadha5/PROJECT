import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { FaBrain, FaUser, FaLock, FaSignInAlt } from 'react-icons/fa';
import './Login.css';

export default function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const result = await login(username, password);
      if (result.success) {
        navigate('/');
      } else {
        setError(result.error || 'Identifiants incorrects');
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Erreur de connexion au serveur');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-particles">
        {[...Array(9)].map((_, i) => (
          <div key={i} className="particle" style={{ left: `${(i + 1) * 10}%`, animationDelay: `${i}s` }} />
        ))}
      </div>

      <div className="login-container">
        <div className="login-logo">
          <FaBrain />
          <h1>Formation IA</h1>
          <p>Système intelligent de recommandation</p>
        </div>

        {error && (
          <div className="login-error">
            <span>⚠️ {error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <FaUser className="input-icon" />
            <input
              type="text"
              placeholder="Nom d'utilisateur"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
          </div>

          <div className="form-group">
            <FaLock className="input-icon" />
            <input
              type="password"
              placeholder="Mot de passe"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          <button type="submit" className="login-btn" disabled={loading}>
            {loading ? (
              <span className="spinner-small" />
            ) : (
              <>
                <FaSignInAlt /> Se connecter
              </>
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
