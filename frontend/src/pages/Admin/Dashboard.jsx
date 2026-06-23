import { useState, useEffect } from 'react';
import { getDashboardStats } from '../../services/api';
import { FaUsers, FaChartBar, FaBrain, FaClock, FaArrowUp, FaGraduationCap, FaCalendarAlt, FaRocket } from 'react-icons/fa';
import toast from 'react-hot-toast';
import './Dashboard.css';

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      const res = await getDashboardStats();
      setStats(res.data);
    } catch {
      toast.error('Erreur de chargement du dashboard');
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="loading-screen"><div className="spinner" /></div>;

  const topFormation = stats?.formation_distribution
    ? Object.entries(stats.formation_distribution).sort((a, b) => b[1] - a[1])[0]
    : null;

  const totalFormations = stats?.formation_distribution
    ? Object.keys(stats.formation_distribution).length
    : 0;

  return (
    <div className="dashboard-page">
      {/* Welcome banner */}
      <div className="dashboard-banner">
        <div className="banner-content">
          <h1><FaRocket /> Tableau de Bord</h1>
          <p>Vue d'ensemble de votre plateforme de formation IA</p>
        </div>
        <div className="banner-decoration">
          <div className="circle c1"></div>
          <div className="circle c2"></div>
          <div className="circle c3"></div>
        </div>
      </div>

      {/* Stats cards */}
      <div className="dashboard-stats">
        <div className="dash-stat-card stat-purple">
          <div className="dash-stat-icon">
            <FaUsers />
          </div>
          <div className="dash-stat-info">
            <span className="dash-stat-value">{stats?.total_users || 0}</span>
            <span className="dash-stat-label">Utilisateurs</span>
          </div>
          <div className="dash-stat-trend up">
            <FaArrowUp /> Actifs
          </div>
        </div>

        <div className="dash-stat-card stat-green">
          <div className="dash-stat-icon">
            <FaBrain />
          </div>
          <div className="dash-stat-info">
            <span className="dash-stat-value">{stats?.total_predictions || 0}</span>
            <span className="dash-stat-label">Prédictions</span>
          </div>
          <div className="dash-stat-trend up">
            <FaArrowUp /> Total
          </div>
        </div>

        <div className="dash-stat-card stat-orange">
          <div className="dash-stat-icon">
            <FaCalendarAlt />
          </div>
          <div className="dash-stat-info">
            <span className="dash-stat-value">{stats?.avg_age || 0} <small>ans</small></span>
            <span className="dash-stat-label">Âge moyen</span>
          </div>
        </div>

        <div className="dash-stat-card stat-blue">
          <div className="dash-stat-icon">
            <FaClock />
          </div>
          <div className="dash-stat-info">
            <span className="dash-stat-value">{stats?.avg_experience || 0} <small>ans</small></span>
            <span className="dash-stat-label">Expérience moy.</span>
          </div>
        </div>
      </div>

      {/* Content grid */}
      <div className="dashboard-grid">
        {/* Formation distribution chart */}
        {stats?.formation_distribution && (
          <div className="dashboard-card chart-card">
            <div className="card-header-dash">
              <h3><FaGraduationCap /> Distribution des Formations</h3>
              <span className="card-badge">{totalFormations} formations</span>
            </div>
            <div className="chart-list">
              {Object.entries(stats.formation_distribution)
                .sort((a, b) => b[1] - a[1])
                .map(([name, count], index) => {
                  const percentage = Math.round((count / stats.total_predictions) * 100);
                  const colors = ['#667eea', '#28a745', '#fd7e14', '#dc3545', '#17a2b8', '#6f42c1', '#e83e8c', '#20c997', '#ffc107', '#6610f2'];
                  const color = colors[index % colors.length];
                  return (
                    <div key={name} className="chart-item">
                      <div className="chart-item-header">
                        <div className="chart-item-color" style={{ background: color }}></div>
                        <span className="chart-item-name">{name}</span>
                        <span className="chart-item-count">{count}</span>
                        <span className="chart-item-percent">{percentage}%</span>
                      </div>
                      <div className="chart-bar-track">
                        <div
                          className="chart-bar-fill"
                          style={{ width: `${percentage}%`, background: color }}
                        ></div>
                      </div>
                    </div>
                  );
                })}
            </div>
          </div>
        )}

        {/* Quick insights */}
        <div className="dashboard-card insights-card">
          <div className="card-header-dash">
            <h3><FaChartBar /> Résumé</h3>
          </div>
          <div className="insights-list">
            <div className="insight-item">
              <div className="insight-icon" style={{ background: 'rgba(102,126,234,0.1)', color: '#667eea' }}>
                <FaGraduationCap />
              </div>
              <div className="insight-text">
                <strong>Formation la plus demandée</strong>
                <p>{topFormation ? topFormation[0] : 'Aucune donnée'}</p>
              </div>
              {topFormation && <span className="insight-badge">{topFormation[1]} fois</span>}
            </div>

            <div className="insight-item">
              <div className="insight-icon" style={{ background: 'rgba(40,167,69,0.1)', color: '#28a745' }}>
                <FaUsers />
              </div>
              <div className="insight-text">
                <strong>Ratio prédictions/utilisateur</strong>
                <p>{stats?.total_users ? (stats.total_predictions / stats.total_users).toFixed(1) : 0} prédictions/user</p>
              </div>
            </div>

            <div className="insight-item">
              <div className="insight-icon" style={{ background: 'rgba(253,126,20,0.1)', color: '#fd7e14' }}>
                <FaBrain />
              </div>
              <div className="insight-text">
                <strong>Formations disponibles</strong>
                <p>{totalFormations} programmes actifs</p>
              </div>
            </div>

            <div className="insight-item">
              <div className="insight-icon" style={{ background: 'rgba(23,162,184,0.1)', color: '#17a2b8' }}>
                <FaRocket />
              </div>
              <div className="insight-text">
                <strong>Profil moyen</strong>
                <p>{stats?.avg_age || 0} ans, {stats?.avg_experience || 0} ans d'expérience</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
