import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { FaBrain, FaUser, FaLock, FaSignInAlt, FaEye, FaEyeSlash, FaRocket, FaShieldAlt, FaChartLine } from 'react-icons/fa';
import './Login.css';

export default function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
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
      {/* Animated background */}
      <div className="login-bg-shapes">
        <div className="shape shape-1"></div>
        <div className="shape shape-2"></div>
        <div className="shape shape-3"></div>
        <div className="shape shape-4"></div>
      </div>

      <div className="login-grid-overlay"></div>

      <div className="login-wrapper">
        {/* Left panel - branding */}
        <div className="login-left">
          <div className="login-left-content">
            <div className="login-brand-icon">
              <FaBrain />
            </div>
            <h1>Formation IA</h1>
            <p className="login-tagline">
              Plateforme intelligente de recommandation de formations professionnelles
            </p>

            <div className="login-features">
              <div className="login-feature">
                <FaRocket className="feature-icon" />
                <div>
                  <h4>Prédiction IA</h4>
                  <span>Recommandations personnalisées par Machine Learning</span>
                </div>
              </div>
              <div className="login-feature">
                <FaShieldAlt className="feature-icon" />
                <div>
                  <h4>Sécurisé</h4>
                  <span>Authentification biométrique & chiffrement</span>
                </div>
              </div>
              <div className="login-feature">
                <FaChartLine className="feature-icon" />
                <div>
                  <h4>Suivi en temps réel</h4>
                  <span>Roadmaps & progression personnalisées</span>
                </div>
              </div>
            </div>
          </div>

          <div className="login-left-footer">
            <span>© 2026 Formation IA — PFE</span>
          </div>
        </div>

        {/* Right panel - form */}
        <div className="login-right">
          <div className="login-form-container">
            <div className="login-form-header">
              <h2>Connexion</h2>
              <p>Accédez à votre espace personnel</p>
            </div>

            {error && (
              <div className="login-error">
                <span>⚠️ {error}</span>
              </div>
            )}

            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label htmlFor="username">Nom d'utilisateur</label>
                <div className="input-wrapper">
                  <FaUser className="input-icon" />
                  <input
                    id="username"
                    type="text"
                    placeholder="Entrez votre identifiant"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    required
                    autoComplete="username"
                  />
                </div>
              </div>

              <div className="form-group">
                <label htmlFor="password">Mot de passe</label>
                <div className="input-wrapper">
                  <FaLock className="input-icon" />
                  <input
                    id="password"
                    type={showPassword ? 'text' : 'password'}
                    placeholder="Entrez votre mot de passe"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    autoComplete="current-password"
                  />
                  <button
                    type="button"
                    className="password-toggle"
                    onClick={() => setShowPassword(!showPassword)}
                    tabIndex={-1}
                  >
                    {showPassword ? <FaEyeSlash /> : <FaEye />}
                  </button>
                </div>
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

            <div className="login-footer-text">
              <span>Plateforme réservée aux employés autorisés</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
