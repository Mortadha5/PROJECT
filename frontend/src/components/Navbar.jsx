import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useState, useEffect } from 'react';
import { getUnreadMessages, getUnreadNotifCount, getPendingPredictionsCount } from '../services/api';
import { FaBrain, FaSignOutAlt, FaBars, FaTimes, FaUser, FaComments, FaChartBar, FaUsers, FaHistory, FaShieldAlt, FaBell, FaRoad, FaMagic, FaEnvelope, FaClipboardList, FaGraduationCap } from 'react-icons/fa';

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [menuOpen, setMenuOpen] = useState(false);
  const [expanded, setExpanded] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const [notifCount, setNotifCount] = useState(0);
  const [pendingPredCount, setPendingPredCount] = useState(0);

  useEffect(() => {
    if (!user) return;
    const isAdmin = user.role === 'admin';
    const fetchBadges = async () => {
      try {
        const msgRes = await getUnreadMessages();
        setUnreadCount(msgRes.data.unread_count || 0);
        if (isAdmin) {
          const [notifRes, predRes] = await Promise.all([
            getUnreadNotifCount(),
            getPendingPredictionsCount()
          ]);
          setNotifCount(notifRes.data.count || 0);
          setPendingPredCount(predRes.data.count || 0);
        }
      } catch { /* silent */ }
    };
    fetchBadges();
    const interval = setInterval(fetchBadges, 10000);
    return () => clearInterval(interval);
  }, [user]);

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  if (!user) return null;

  const isAdmin = user.role === 'admin';
  const isActive = (path) => location.pathname === path ? 'active' : '';

  return (
    <>
      {/* Mobile hamburger */}
      <button className="navbar-toggle" onClick={() => setMenuOpen(!menuOpen)}>
        {menuOpen ? <FaTimes /> : <FaBars />}
      </button>

      {/* Hover trigger zone (desktop only) */}
      <div
        className="sidebar-trigger"
        onMouseEnter={() => setExpanded(true)}
      />

      {/* Mobile overlay */}
      {menuOpen && <div className="sidebar-overlay" onClick={() => setMenuOpen(false)} />}

      <nav
        className={`navbar ${expanded ? 'expanded' : ''} ${menuOpen ? 'mobile-open' : ''}`}
        onMouseEnter={() => setExpanded(true)}
        onMouseLeave={() => setExpanded(false)}
      >
        <div className="navbar-brand">
          <Link to="/">
            <FaBrain className="brand-icon" />
            <span className="brand-text">Formation IA</span>
          </Link>
        </div>

        <div className="navbar-links">
          <div className="navbar-user-badge">
            <FaUser className="nav-icon" />
            <span className="nav-label">{user.username}</span>
            <span className={`navbar-role ${isAdmin ? 'admin' : 'user'}`}>
              {isAdmin ? 'Admin' : 'User'}
            </span>
          </div>

          {isAdmin ? (
            <>
              <Link to="/admin/dashboard" className={isActive('/admin/dashboard')}>
                <FaChartBar className="nav-icon" />
                <span className="nav-label">Dashboard</span>
              </Link>
              <Link to="/admin/users" className={isActive('/admin/users')}>
                <FaUsers className="nav-icon" />
                <span className="nav-label">Utilisateurs</span>
              </Link>
              <Link to="/admin/historique" className={isActive('/admin/historique')}>
                <FaHistory className="nav-icon" />
                <span className="nav-label">Historique</span>
              </Link>
              <Link to="/admin/security" className={isActive('/admin/security')}>
                <FaShieldAlt className="nav-icon" />
                <span className="nav-label">Sécurité</span>
              </Link>
              <Link to="/admin/notifications" className={`${isActive('/admin/notifications')} nav-badge-link`}>
                <FaBell className="nav-icon" />
                <span className="nav-label">Notifs</span>
                {notifCount > 0 && <span className="nav-badge">{notifCount}</span>}
              </Link>
              <Link to="/admin/roadmaps" className={isActive('/admin/roadmaps')}>
                <FaRoad className="nav-icon" />
                <span className="nav-label">Roadmaps</span>
              </Link>
              <Link to="/admin/predictions" className={`${isActive('/admin/predictions')} nav-badge-link`}>
                <FaClipboardList className="nav-icon" />
                <span className="nav-label">Prédictions</span>
                {pendingPredCount > 0 && <span className="nav-badge">{pendingPredCount}</span>}
              </Link>
              <Link to="/advanced-prediction" className={isActive('/advanced-prediction')}>
                <FaMagic className="nav-icon" />
                <span className="nav-label">Prédiction</span>
              </Link>
              <Link to="/messages" className={`${isActive('/messages')} nav-badge-link`}>
                <FaEnvelope className="nav-icon" />
                <span className="nav-label">Messages</span>
                {unreadCount > 0 && <span className="nav-badge">{unreadCount}</span>}
              </Link>
            </>
          ) : (
            <>
              <Link to="/" className={isActive('/')}>
                <FaMagic className="nav-icon" />
                <span className="nav-label">Prédiction</span>
              </Link>
              <Link to="/profile" className={isActive('/profile')}>
                <FaUser className="nav-icon" />
                <span className="nav-label">Profil</span>
              </Link>
              <Link to="/roadmap" className={isActive('/roadmap')}>
                <FaRoad className="nav-icon" />
                <span className="nav-label">Roadmap</span>
              </Link>
              <Link to="/mes-resultats" className={isActive('/mes-resultats')}>
                <FaGraduationCap className="nav-icon" />
                <span className="nav-label">Mes Résultats</span>
              </Link>
              <Link to="/chatbot" className={isActive('/chatbot')}>
                <FaComments className="nav-icon" />
                <span className="nav-label">Chatbot</span>
              </Link>
              <Link to="/messages" className={`${isActive('/messages')} nav-badge-link`}>
                <FaEnvelope className="nav-icon" />
                <span className="nav-label">Messages</span>
                {unreadCount > 0 && <span className="nav-badge">{unreadCount}</span>}
              </Link>
            </>
          )}

          <button className="navbar-logout" onClick={handleLogout}>
            <FaSignOutAlt className="nav-icon" />
            <span className="nav-label">Déconnexion</span>
          </button>
        </div>
      </nav>
    </>
  );
}
