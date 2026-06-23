import { useState, useEffect } from 'react';
import { getSecurityData, blockUser, unblockUser, clearLogs } from '../../services/api';
import { FaShieldAlt, FaBan, FaCheck, FaTrash, FaExclamationTriangle, FaUserLock, FaLock, FaEye, FaSearch, FaSkullCrossbones } from 'react-icons/fa';
import toast from 'react-hot-toast';
import './Security.css';

export default function Security() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [logFilter, setLogFilter] = useState('');
  const [tab, setTab] = useState('logs');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const res = await getSecurityData();
      setData(res.data);
    } catch {
      toast.error('Erreur de chargement');
    } finally {
      setLoading(false);
    }
  };

  const handleBlock = async (username) => {
    try {
      await blockUser(username);
      toast.success(`${username} bloqué`);
      loadData();
    } catch {
      toast.error('Erreur');
    }
  };

  const handleUnblock = async (username) => {
    try {
      await unblockUser(username);
      toast.success(`${username} débloqué`);
      loadData();
    } catch {
      toast.error('Erreur');
    }
  };

  const handleClearLogs = async () => {
    if (!confirm('Supprimer tous les logs ?')) return;
    try {
      await clearLogs();
      toast.success('Logs supprimés');
      loadData();
    } catch {
      toast.error('Erreur');
    }
  };

  const filteredLogs = (data?.recent_logs || []).filter(log =>
    !logFilter ||
    log.username?.toLowerCase().includes(logFilter.toLowerCase()) ||
    log.action?.toLowerCase().includes(logFilter.toLowerCase()) ||
    log.details?.toLowerCase().includes(logFilter.toLowerCase())
  );

  const getActionIcon = (action) => {
    if (action?.includes('fail')) return <FaExclamationTriangle />;
    if (action?.includes('block')) return <FaUserLock />;
    if (action?.includes('login')) return <FaLock />;
    return <FaEye />;
  };

  const getActionColor = (action) => {
    if (action?.includes('fail')) return '#dc3545';
    if (action?.includes('block')) return '#fd7e14';
    if (action?.includes('login') && !action?.includes('fail')) return '#28a745';
    return '#667eea';
  };

  if (loading) return <div className="loading-screen"><div className="spinner" /></div>;

  return (
    <div className="security-page">
      {/* Header */}
      <div className="sec-header">
        <div className="sec-header-left">
          <h1><FaShieldAlt /> Centre de Sécurité</h1>
          <p>Surveillance et protection de la plateforme</p>
        </div>
      </div>

      {/* Stats */}
      <div className="sec-stats">
        <div className="sec-stat-card sec-stat-red">
          <div className="sec-stat-visual">
            <FaExclamationTriangle />
          </div>
          <div className="sec-stat-info">
            <span className="sec-stat-number">{data?.failed_logins || 0}</span>
            <span className="sec-stat-text">Tentatives échouées</span>
          </div>
          <div className="sec-stat-ring">
            <svg viewBox="0 0 36 36">
              <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                fill="none" stroke="rgba(220,53,69,0.15)" strokeWidth="3" />
              <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                fill="none" stroke="#dc3545" strokeWidth="3"
                strokeDasharray={`${Math.min((data?.failed_logins || 0) * 2, 100)}, 100`} />
            </svg>
          </div>
        </div>

        <div className="sec-stat-card sec-stat-orange">
          <div className="sec-stat-visual">
            <FaUserLock />
          </div>
          <div className="sec-stat-info">
            <span className="sec-stat-number">{data?.blocked_users || 0}</span>
            <span className="sec-stat-text">Utilisateurs bloqués</span>
          </div>
        </div>

        <div className="sec-stat-card sec-stat-green">
          <div className="sec-stat-visual">
            <FaEye />
          </div>
          <div className="sec-stat-info">
            <span className="sec-stat-number">{data?.active_sessions || 0}</span>
            <span className="sec-stat-text">Sessions actives</span>
          </div>
        </div>

        <div className="sec-stat-card sec-stat-purple">
          <div className="sec-stat-visual">
            <FaSkullCrossbones />
          </div>
          <div className="sec-stat-info">
            <span className="sec-stat-number">{data?.suspicious_users?.length || 0}</span>
            <span className="sec-stat-text">Suspects détectés</span>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="sec-tabs">
        <button className={`sec-tab ${tab === 'logs' ? 'active' : ''}`} onClick={() => setTab('logs')}>
          <FaEye /> Logs ({data?.recent_logs?.length || 0})
        </button>
        <button className={`sec-tab ${tab === 'suspects' ? 'active' : ''}`} onClick={() => setTab('suspects')}>
          <FaExclamationTriangle /> Suspects ({data?.suspicious_users?.length || 0})
        </button>
      </div>

      {/* Logs Tab */}
      {tab === 'logs' && (
        <div className="sec-card">
          <div className="sec-card-header">
            <div className="sec-search">
              <FaSearch className="sec-search-icon" />
              <input
                type="text"
                placeholder="Filtrer les logs..."
                value={logFilter}
                onChange={e => setLogFilter(e.target.value)}
              />
            </div>
            <button className="sec-clear-btn" onClick={handleClearLogs}>
              <FaTrash /> Vider
            </button>
          </div>

          {filteredLogs.length === 0 ? (
            <div className="sec-empty">
              <FaShieldAlt />
              <p>Aucun log de sécurité</p>
            </div>
          ) : (
            <div className="sec-logs-list">
              {filteredLogs.map((log, i) => (
                <div key={i} className={`sec-log-item ${log.action?.includes('fail') ? 'log-danger' : ''}`}>
                  <div className="sec-log-icon" style={{ color: getActionColor(log.action) }}>
                    {getActionIcon(log.action)}
                  </div>
                  <div className="sec-log-content">
                    <div className="sec-log-main">
                      <span className="sec-log-user">{log.username}</span>
                      <span className="sec-log-action" style={{ background: `${getActionColor(log.action)}15`, color: getActionColor(log.action) }}>
                        {log.action}
                      </span>
                    </div>
                    <p className="sec-log-details">{log.details}</p>
                  </div>
                  <span className="sec-log-time">
                    {log.timestamp ? new Date(log.timestamp).toLocaleString('fr-FR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' }) : '-'}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Suspects Tab */}
      {tab === 'suspects' && (
        <div className="sec-card">
          {(!data?.suspicious_users || data.suspicious_users.length === 0) ? (
            <div className="sec-empty">
              <FaCheck style={{ color: '#28a745' }} />
              <p>Aucun utilisateur suspect détecté</p>
            </div>
          ) : (
            <div className="sec-suspects-list">
              {data.suspicious_users.map((u, i) => (
                <div key={i} className="sec-suspect-card">
                  <div className="sec-suspect-avatar">
                    {u.username?.charAt(0).toUpperCase()}
                  </div>
                  <div className="sec-suspect-info">
                    <h4>{u.username}</h4>
                    <div className="sec-suspect-meta">
                      <span className="sec-suspect-attempts">
                        <FaExclamationTriangle /> {u.failed_attempts} tentatives échouées
                      </span>
                      <span className={`sec-suspect-status ${u.blocked ? 'blocked' : 'active'}`}>
                        {u.blocked ? '🔴 Bloqué' : '🟡 Non bloqué'}
                      </span>
                    </div>
                  </div>
                  <div className="sec-suspect-actions">
                    {u.blocked ? (
                      <button className="sec-action-btn unblock" onClick={() => handleUnblock(u.username)}>
                        <FaCheck /> Débloquer
                      </button>
                    ) : (
                      <button className="sec-action-btn block" onClick={() => handleBlock(u.username)}>
                        <FaBan /> Bloquer
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
