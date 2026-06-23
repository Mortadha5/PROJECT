import { useState, useEffect } from 'react';
import { getUsers, deleteUser, blockUser, unblockUser, resetUserPassword } from '../../services/api';
import { FaUsers, FaPlus, FaEdit, FaTrash, FaBan, FaCheck, FaKey, FaSearch, FaUserShield, FaUserCheck, FaUserLock } from 'react-icons/fa';
import { Link } from 'react-router-dom';
import toast from 'react-hot-toast';
import './UsersManagement.css';

export default function UsersManagement() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [filterRole, setFilterRole] = useState('all');

  useEffect(() => {
    loadUsers();
  }, []);

  const loadUsers = async () => {
    try {
      const res = await getUsers();
      setUsers(res.data.users || []);
    } catch {
      toast.error('Erreur de chargement');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (username) => {
    if (!confirm(`Supprimer l'utilisateur ${username} ?`)) return;
    try {
      await deleteUser(username);
      toast.success('Utilisateur supprimé');
      loadUsers();
    } catch {
      toast.error('Erreur de suppression');
    }
  };

  const handleBlock = async (username, blocked) => {
    try {
      if (blocked) {
        await unblockUser(username);
        toast.success('Utilisateur débloqué');
      } else {
        await blockUser(username);
        toast.success('Utilisateur bloqué');
      }
      loadUsers();
    } catch {
      toast.error('Erreur');
    }
  };

  const handleResetPwd = async (username) => {
    try {
      const res = await resetUserPassword(username);
      toast.success(`Mot de passe réinitialisé: ${res.data.temp_password}`);
    } catch {
      toast.error('Erreur de réinitialisation');
    }
  };

  const filtered = users.filter(u => {
    const matchSearch = u.username?.toLowerCase().includes(search.toLowerCase()) ||
      u.email?.toLowerCase().includes(search.toLowerCase()) ||
      u.full_name?.toLowerCase().includes(search.toLowerCase());
    const matchRole = filterRole === 'all' || u.role === filterRole;
    return matchSearch && matchRole;
  });

  const totalAdmins = users.filter(u => u.role === 'admin').length;
  const totalUsers = users.filter(u => u.role === 'user').length;
  const totalBlocked = users.filter(u => u.blocked).length;

  if (loading) return <div className="loading-screen"><div className="spinner" /></div>;

  return (
    <div className="users-page">
      {/* Header */}
      <div className="users-header">
        <div>
          <h1><FaUsers /> Gestion des Utilisateurs</h1>
          <p className="users-subtitle">{users.length} utilisateurs enregistrés</p>
        </div>
        <Link to="/admin/users/create" className="btn-add-user">
          <FaPlus /> Nouvel utilisateur
        </Link>
      </div>

      {/* Stats mini */}
      <div className="users-mini-stats">
        <div className="mini-stat">
          <FaUserShield className="mini-stat-icon purple" />
          <div>
            <span className="mini-stat-value">{totalAdmins}</span>
            <span className="mini-stat-label">Admins</span>
          </div>
        </div>
        <div className="mini-stat">
          <FaUserCheck className="mini-stat-icon green" />
          <div>
            <span className="mini-stat-value">{totalUsers}</span>
            <span className="mini-stat-label">Utilisateurs</span>
          </div>
        </div>
        <div className="mini-stat">
          <FaUserLock className="mini-stat-icon red" />
          <div>
            <span className="mini-stat-value">{totalBlocked}</span>
            <span className="mini-stat-label">Bloqués</span>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="users-filters">
        <div className="search-box">
          <FaSearch className="search-icon" />
          <input
            type="text"
            placeholder="Rechercher par nom, email..."
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
        </div>
        <div className="filter-tabs">
          <button className={`filter-tab ${filterRole === 'all' ? 'active' : ''}`} onClick={() => setFilterRole('all')}>
            Tous ({users.length})
          </button>
          <button className={`filter-tab ${filterRole === 'admin' ? 'active' : ''}`} onClick={() => setFilterRole('admin')}>
            Admins ({totalAdmins})
          </button>
          <button className={`filter-tab ${filterRole === 'user' ? 'active' : ''}`} onClick={() => setFilterRole('user')}>
            Users ({totalUsers})
          </button>
        </div>
      </div>

      {/* User cards */}
      <div className="users-grid">
        {filtered.map(u => (
          <div key={u.username} className={`user-card ${u.blocked ? 'blocked' : ''}`}>
            <div className="user-card-header">
              <div className="user-avatar-circle">
                {u.username?.charAt(0).toUpperCase()}
              </div>
              <div className="user-card-info">
                <h4>{u.full_name || u.username}</h4>
                <span className="user-card-username">@{u.username}</span>
              </div>
              <span className={`role-badge ${u.role === 'admin' ? 'role-admin' : 'role-user'}`}>
                {u.role === 'admin' ? '👑 Admin' : '👤 User'}
              </span>
            </div>

            <div className="user-card-details">
              {u.email && (
                <div className="user-detail">
                  <span className="detail-label">Email</span>
                  <span className="detail-val">{u.email}</span>
                </div>
              )}
              <div className="user-detail">
                <span className="detail-label">Statut</span>
                <span className={`status-dot ${u.blocked ? 'status-blocked' : 'status-active'}`}>
                  {u.blocked ? '🔴 Bloqué' : '🟢 Actif'}
                </span>
              </div>
              {u.last_login && u.last_login !== 'None' && (
                <div className="user-detail">
                  <span className="detail-label">Dernière connexion</span>
                  <span className="detail-val">{new Date(u.last_login).toLocaleDateString('fr-FR')}</span>
                </div>
              )}
            </div>

            <div className="user-card-actions">
              <Link to={`/admin/users/edit/${u.username}`} className="action-btn edit" title="Modifier">
                <FaEdit />
              </Link>
              <button className="action-btn key" title="Réinitialiser MDP" onClick={() => handleResetPwd(u.username)}>
                <FaKey />
              </button>
              <button
                className={`action-btn ${u.blocked ? 'unblock' : 'block'}`}
                title={u.blocked ? 'Débloquer' : 'Bloquer'}
                onClick={() => handleBlock(u.username, u.blocked)}
              >
                {u.blocked ? <FaCheck /> : <FaBan />}
              </button>
              {u.role !== 'admin' && (
                <button className="action-btn delete" title="Supprimer" onClick={() => handleDelete(u.username)}>
                  <FaTrash />
                </button>
              )}
            </div>
          </div>
        ))}

        {filtered.length === 0 && (
          <div className="no-results">
            <FaSearch />
            <p>Aucun utilisateur trouvé</p>
          </div>
        )}
      </div>
    </div>
  );
}
