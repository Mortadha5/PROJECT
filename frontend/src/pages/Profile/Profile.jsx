import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { getProfile, uploadAvatar } from '../../services/api';
import { FaUser, FaEnvelope, FaCalendar, FaEdit, FaShieldAlt, FaCameraRetro, FaBriefcase, FaLock, FaCheckCircle } from 'react-icons/fa';
import { Link } from 'react-router-dom';
import toast from 'react-hot-toast';
import './Profile.css';

export default function Profile() {
  const { user } = useAuth();
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadProfile();
  }, []);

  const loadProfile = async () => {
    try {
      const res = await getProfile();
      setProfile(res.data);
    } catch {
      toast.error('Erreur de chargement du profil');
    } finally {
      setLoading(false);
    }
  };

  const handleAvatarUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('avatar', file);

    try {
      const res = await uploadAvatar(formData);
      if (res.data.success) {
        toast.success('Avatar mis à jour');
        loadProfile();
      }
    } catch {
      toast.error("Erreur lors de l'upload");
    }
  };

  if (loading) return <div className="loading-screen"><div className="spinner" /></div>;

  const initials = (profile?.full_name || user?.username || '?')
    .split(' ')
    .map(n => n.charAt(0).toUpperCase())
    .slice(0, 2)
    .join('');

  return (
    <div className="profile-page">
      {/* Banner */}
      <div className="profile-banner">
        <div className="profile-banner-overlay" />
      </div>

      {/* Profile card */}
      <div className="profile-main-card">
        <div className="profile-avatar-wrapper">
          <div className="profile-avatar-circle">
            {profile?.avatar ? (
              <img src={profile.avatar} alt="Avatar" />
            ) : (
              <span className="profile-initials">{initials}</span>
            )}
          </div>
          <label className="profile-avatar-edit">
            <FaCameraRetro />
            <input type="file" accept="image/*" onChange={handleAvatarUpload} hidden />
          </label>
        </div>

        <div className="profile-identity">
          <h1>{profile?.full_name || user?.username}</h1>
          <span className="profile-role-badge">
            <FaShieldAlt /> {profile?.role || user?.role || 'Utilisateur'}
          </span>
          {profile?.bio && <p className="profile-bio">{profile.bio}</p>}
        </div>
      </div>

      {/* Info cards */}
      <div className="profile-details-grid">
        <div className="profile-detail-card">
          <div className="profile-detail-icon"><FaUser /></div>
          <div className="profile-detail-content">
            <span className="profile-detail-label">Nom d'utilisateur</span>
            <span className="profile-detail-value">{user?.username}</span>
          </div>
        </div>

        {profile?.email && (
          <div className="profile-detail-card">
            <div className="profile-detail-icon email"><FaEnvelope /></div>
            <div className="profile-detail-content">
              <span className="profile-detail-label">Email</span>
              <span className="profile-detail-value">{profile.email}</span>
            </div>
          </div>
        )}

        {profile?.full_name && (
          <div className="profile-detail-card">
            <div className="profile-detail-icon name"><FaBriefcase /></div>
            <div className="profile-detail-content">
              <span className="profile-detail-label">Nom complet</span>
              <span className="profile-detail-value">{profile.full_name}</span>
            </div>
          </div>
        )}

        <div className="profile-detail-card">
          <div className="profile-detail-icon date"><FaCalendar /></div>
          <div className="profile-detail-content">
            <span className="profile-detail-label">Membre depuis</span>
            <span className="profile-detail-value">
              {profile?.created_at ? new Date(profile.created_at).toLocaleDateString('fr-FR', { day: '2-digit', month: 'long', year: 'numeric' }) : 'N/A'}
            </span>
          </div>
        </div>

        <div className="profile-detail-card">
          <div className="profile-detail-icon role"><FaShieldAlt /></div>
          <div className="profile-detail-content">
            <span className="profile-detail-label">Rôle</span>
            <span className="profile-detail-value">{profile?.role || 'user'}</span>
          </div>
        </div>

        <div className="profile-detail-card">
          <div className="profile-detail-icon status"><FaCheckCircle /></div>
          <div className="profile-detail-content">
            <span className="profile-detail-label">Statut</span>
            <span className="profile-detail-value profile-status-active">Actif</span>
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="profile-actions-section">
        <Link to="/edit-profile" className="profile-action-btn primary">
          <FaEdit /> Modifier le profil
        </Link>
        <Link to="/change-password" className="profile-action-btn secondary">
          <FaLock /> Changer le mot de passe
        </Link>
      </div>
    </div>
  );
}
