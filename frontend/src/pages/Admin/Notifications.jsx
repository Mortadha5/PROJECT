import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getNotifications, markNotifRead, markAllNotifsRead, deleteNotification } from '../../services/api';
import { FaBell, FaCheck, FaTrash, FaCheckDouble, FaInfoCircle, FaExclamationTriangle, FaEnvelope, FaEnvelopeOpen, FaFilter, FaRocket, FaBrain, FaShieldAlt, FaRoad, FaComments, FaExternalLinkAlt } from 'react-icons/fa';
import toast from 'react-hot-toast';
import './Notifications.css';

const TYPE_CONFIG = {
  prediction: { icon: FaBrain, color: '#667eea', bg: 'rgba(102, 126, 234, 0.1)', label: 'Prédiction' },
  info: { icon: FaInfoCircle, color: '#17a2b8', bg: 'rgba(23, 162, 184, 0.1)', label: 'Info' },
  success: { icon: FaRocket, color: '#28a745', bg: 'rgba(40, 167, 69, 0.1)', label: 'Succès' },
  warning: { icon: FaExclamationTriangle, color: '#fd7e14', bg: 'rgba(253, 126, 20, 0.1)', label: 'Attention' },
  error: { icon: FaExclamationTriangle, color: '#dc3545', bg: 'rgba(220, 53, 69, 0.1)', label: 'Erreur' },
  security: { icon: FaShieldAlt, color: '#6f42c1', bg: 'rgba(111, 66, 193, 0.1)', label: 'Sécurité' },
  admin_message: { icon: FaComments, color: '#20c997', bg: 'rgba(32, 201, 151, 0.1)', label: 'Message' },
  broadcast: { icon: FaEnvelope, color: '#fd7e14', bg: 'rgba(253, 126, 20, 0.1)', label: 'Diffusion' },
  roadmap: { icon: FaRoad, color: '#e83e8c', bg: 'rgba(232, 62, 140, 0.1)', label: 'Roadmap' },
};

function getConfig(type) {
  return TYPE_CONFIG[type] || TYPE_CONFIG.info;
}

export default function Notifications() {
  const navigate = useNavigate();
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');
  const [typeFilter, setTypeFilter] = useState('all');

  useEffect(() => {
    loadNotifs();
  }, []);

  const loadNotifs = async () => {
    try {
      const res = await getNotifications();
      setNotifications(res.data.notifications || []);
    } catch {
      toast.error('Erreur de chargement');
    } finally {
      setLoading(false);
    }
  };

  const handleMarkRead = async (id) => {
    try {
      await markNotifRead(id);
      setNotifications(prev => prev.map(n => n._id === id ? { ...n, read: true } : n));
    } catch {
      toast.error('Erreur');
    }
  };

  const handleMarkAll = async () => {
    try {
      await markAllNotifsRead();
      setNotifications(prev => prev.map(n => ({ ...n, read: true })));
      toast.success('Tout marqué comme lu');
    } catch {
      toast.error('Erreur');
    }
  };

  const handleDelete = async (id) => {
    try {
      await deleteNotification(id);
      setNotifications(prev => prev.filter(n => n._id !== id));
      toast.success('Supprimée');
    } catch {
      toast.error('Erreur');
    }
  };

  const handleClick = (notif) => {
    if (!notif.read) handleMarkRead(notif._id);
    if (notif.link) navigate(notif.link);
  };

  const unreadCount = notifications.filter(n => !n.read).length;
  const readCount = notifications.filter(n => n.read).length;

  const types = [...new Set(notifications.map(n => n.type).filter(Boolean))];

  const filtered = notifications.filter(n => {
    if (filter === 'unread' && n.read) return false;
    if (filter === 'read' && !n.read) return false;
    if (typeFilter !== 'all' && n.type !== typeFilter) return false;
    return true;
  });

  // Group by date
  const groupByDate = (notifs) => {
    const groups = {};
    notifs.forEach(n => {
      const date = n.created_at?.split(' ')[0] || 'Inconnu';
      if (!groups[date]) groups[date] = [];
      groups[date].push(n);
    });
    return groups;
  };

  const grouped = groupByDate(filtered);

  if (loading) return <div className="loading-screen"><div className="spinner" /></div>;

  return (
    <div className="notif-page">
      {/* Header */}
      <div className="notif-header">
        <div className="notif-header-left">
          <div className="notif-header-icon"><FaBell /></div>
          <div>
            <h1>Notifications</h1>
            <p>Centre de notifications et alertes système</p>
          </div>
        </div>
        {unreadCount > 0 && (
          <button className="notif-mark-all-btn" onClick={handleMarkAll}>
            <FaCheckDouble /> Tout marquer lu
          </button>
        )}
      </div>

      {/* Stats */}
      <div className="notif-stats">
        <div className={`notif-stat-card ${filter === 'all' ? 'stat-active' : ''}`} onClick={() => setFilter('all')}>
          <div className="notif-stat-icon total"><FaBell /></div>
          <div className="notif-stat-info">
            <span className="notif-stat-number">{notifications.length}</span>
            <span className="notif-stat-label">Total</span>
          </div>
        </div>
        <div className={`notif-stat-card ${filter === 'unread' ? 'stat-active' : ''}`} onClick={() => setFilter('unread')}>
          <div className="notif-stat-icon unread"><FaEnvelope /></div>
          <div className="notif-stat-info">
            <span className="notif-stat-number">{unreadCount}</span>
            <span className="notif-stat-label">Non lues</span>
          </div>
          {unreadCount > 0 && <div className="stat-pulse" />}
        </div>
        <div className={`notif-stat-card ${filter === 'read' ? 'stat-active' : ''}`} onClick={() => setFilter('read')}>
          <div className="notif-stat-icon read"><FaEnvelopeOpen /></div>
          <div className="notif-stat-info">
            <span className="notif-stat-number">{readCount}</span>
            <span className="notif-stat-label">Lues</span>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="notif-toolbar">
        <div className="notif-filters">
          <FaFilter className="notif-filter-icon" />
          {['all', 'unread', 'read'].map(f => (
            <button
              key={f}
              className={`notif-filter-btn ${filter === f ? 'active' : ''}`}
              onClick={() => setFilter(f)}
            >
              {f === 'all' ? 'Toutes' : f === 'unread' ? 'Non lues' : 'Lues'}
            </button>
          ))}
        </div>
        {types.length > 1 && (
          <div className="notif-type-filters">
            <button
              className={`notif-type-btn ${typeFilter === 'all' ? 'active' : ''}`}
              onClick={() => setTypeFilter('all')}
            >
              Tous types
            </button>
            {types.map(t => {
              const cfg = getConfig(t);
              return (
                <button
                  key={t}
                  className={`notif-type-btn ${typeFilter === t ? 'active' : ''}`}
                  onClick={() => setTypeFilter(t)}
                  style={typeFilter === t ? { background: cfg.bg, color: cfg.color, borderColor: cfg.color } : {}}
                >
                  <cfg.icon /> {cfg.label}
                </button>
              );
            })}
          </div>
        )}
      </div>

      {/* Notifications List */}
      <div className="notif-list">
        {filtered.length === 0 ? (
          <div className="notif-empty">
            <div className="notif-empty-icon"><FaBell /></div>
            <h3>Aucune notification</h3>
            <p>{filter !== 'all' ? 'Essayez un autre filtre' : 'Vous êtes à jour !'}</p>
          </div>
        ) : (
          Object.entries(grouped).map(([date, notifs]) => (
            <div key={date} className="notif-group">
              <div className="notif-group-header">
                <span className="notif-group-date">{date}</span>
                <span className="notif-group-count">{notifs.length}</span>
              </div>
              {notifs.map((n) => {
                const cfg = getConfig(n.type);
                const Icon = cfg.icon;
                return (
                  <div
                    key={n._id}
                    className={`notif-item ${n.read ? 'read' : 'unread'} ${n.link ? 'clickable' : ''}`}
                    onClick={() => n.link && handleClick(n)}
                  >
                    <div className="notif-item-indicator" style={{ background: n.read ? 'transparent' : cfg.color }} />
                    <div className="notif-item-icon" style={{ color: cfg.color, background: cfg.bg }}>
                      <Icon />
                    </div>
                    <div className="notif-item-content">
                      {n.title && <h4 className="notif-item-title">{n.title}</h4>}
                      <p className="notif-item-message">{n.message}</p>
                      <div className="notif-item-meta">
                        <span className="notif-item-time">{n.created_at}</span>
                        <span className="notif-item-type" style={{ color: cfg.color, background: cfg.bg }}>
                          {cfg.label}
                        </span>
                        {n.link && <FaExternalLinkAlt className="notif-link-icon" />}
                      </div>
                    </div>
                    <div className="notif-item-actions">
                      {!n.read && (
                        <button
                          className="notif-action-btn check"
                          onClick={(e) => { e.stopPropagation(); handleMarkRead(n._id); }}
                          title="Marquer lu"
                        >
                          <FaCheck />
                        </button>
                      )}
                      <button
                        className="notif-action-btn delete"
                        onClick={(e) => { e.stopPropagation(); handleDelete(n._id); }}
                        title="Supprimer"
                      >
                        <FaTrash />
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
