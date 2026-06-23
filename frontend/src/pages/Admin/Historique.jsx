import { useState, useEffect } from 'react';
import { getHistorique } from '../../services/api';
import { FaHistory, FaSearch, FaBrain, FaCalendarAlt, FaUser, FaGraduationCap, FaClock, FaChartLine, FaFilter, FaSortAmountDown, FaTh, FaList, FaPercentage } from 'react-icons/fa';
import toast from 'react-hot-toast';
import './Historique.css';

export default function Historique() {
  const [predictions, setPredictions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('');
  const [formationFilter, setFormationFilter] = useState('all');
  const [sortBy, setSortBy] = useState('date');
  const [view, setView] = useState('cards');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const res = await getHistorique();
      setPredictions(res.data.predictions || []);
    } catch {
      toast.error('Erreur de chargement');
    } finally {
      setLoading(false);
    }
  };

  const filtered = predictions.filter(p => {
    if (formationFilter !== 'all' && p.formation !== formationFilter) return false;
    if (!filter) return true;
    const q = filter.toLowerCase();
    return (
      p.formation?.toLowerCase().includes(q) ||
      p.created_by?.toLowerCase().includes(q) ||
      p.nom?.toLowerCase().includes(q) ||
      p.prenom?.toLowerCase().includes(q) ||
      (Array.isArray(p.competences) && p.competences.some(c => c.toLowerCase().includes(q)))
    );
  });

  const sorted = [...filtered].sort((a, b) => {
    if (sortBy === 'date') return (b.created_at || '').localeCompare(a.created_at || '');
    if (sortBy === 'user') return (a.created_by || '').localeCompare(b.created_by || '');
    if (sortBy === 'formation') return (a.formation || '').localeCompare(b.formation || '');
    if (sortBy === 'score') return (b.confidence_score || 0) - (a.confidence_score || 0);
    return 0;
  });

  const uniqueFormations = [...new Set(predictions.map(p => p.formation).filter(Boolean))];
  const uniqueUsers = [...new Set(predictions.map(p => p.created_by).filter(Boolean))];
  const avgScore = predictions.length > 0 
    ? Math.round(predictions.reduce((sum, p) => sum + (p.confidence_score || 0), 0) / predictions.length) 
    : 0;

  const getScoreColor = (score) => {
    if (score >= 80) return '#28a745';
    if (score >= 60) return '#fd7e14';
    if (score >= 40) return '#ffc107';
    return '#dc3545';
  };

  if (loading) return <div className="loading-screen"><div className="spinner" /></div>;

  return (
    <div className="historique-page">
      {/* Header */}
      <div className="hist-header">
        <div className="hist-header-left">
          <div className="hist-header-icon"><FaHistory /></div>
          <div>
            <h1>Historique des Prédictions</h1>
            <p>{predictions.length} prédictions enregistrées</p>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="hist-stats">
        <div className="hist-stat-item">
          <div className="hist-stat-icon-box" style={{ background: 'rgba(102, 126, 234, 0.1)', color: '#667eea' }}>
            <FaChartLine />
          </div>
          <div className="hist-stat-text">
            <span className="hist-stat-value">{predictions.length}</span>
            <span className="hist-stat-label">Total Prédictions</span>
          </div>
        </div>
        <div className="hist-stat-item">
          <div className="hist-stat-icon-box" style={{ background: 'rgba(40, 167, 69, 0.1)', color: '#28a745' }}>
            <FaUser />
          </div>
          <div className="hist-stat-text">
            <span className="hist-stat-value">{uniqueUsers.length}</span>
            <span className="hist-stat-label">Utilisateurs</span>
          </div>
        </div>
        <div className="hist-stat-item">
          <div className="hist-stat-icon-box" style={{ background: 'rgba(253, 126, 20, 0.1)', color: '#fd7e14' }}>
            <FaGraduationCap />
          </div>
          <div className="hist-stat-text">
            <span className="hist-stat-value">{uniqueFormations.length}</span>
            <span className="hist-stat-label">Formations</span>
          </div>
        </div>
        <div className="hist-stat-item">
          <div className="hist-stat-icon-box" style={{ background: 'rgba(111, 66, 193, 0.1)', color: '#6f42c1' }}>
            <FaPercentage />
          </div>
          <div className="hist-stat-text">
            <span className="hist-stat-value">{avgScore}%</span>
            <span className="hist-stat-label">Score Moyen</span>
          </div>
        </div>
      </div>

      {/* Toolbar */}
      <div className="hist-toolbar">
        <div className="hist-search">
          <FaSearch className="hist-search-icon" />
          <input
            type="text"
            placeholder="Rechercher par formation, utilisateur, compétence..."
            value={filter}
            onChange={e => setFilter(e.target.value)}
          />
        </div>
        <div className="hist-controls">
          <div className="hist-filter-group">
            <FaFilter className="control-icon" />
            <select value={formationFilter} onChange={e => setFormationFilter(e.target.value)} className="hist-select">
              <option value="all">Toutes les formations</option>
              {uniqueFormations.map(f => <option key={f} value={f}>{f}</option>)}
            </select>
          </div>
          <div className="hist-filter-group">
            <FaSortAmountDown className="control-icon" />
            <select value={sortBy} onChange={e => setSortBy(e.target.value)} className="hist-select">
              <option value="date">Plus récent</option>
              <option value="score">Par score</option>
              <option value="user">Par utilisateur</option>
              <option value="formation">Par formation</option>
            </select>
          </div>
          <div className="view-toggle">
            <button className={view === 'cards' ? 'active' : ''} onClick={() => setView('cards')} title="Vue cartes"><FaTh /></button>
            <button className={view === 'table' ? 'active' : ''} onClick={() => setView('table')} title="Vue tableau"><FaList /></button>
          </div>
        </div>
      </div>

      {/* Results count */}
      {filter || formationFilter !== 'all' ? (
        <div className="hist-results-count">
          {sorted.length} résultat{sorted.length !== 1 ? 's' : ''} trouvé{sorted.length !== 1 ? 's' : ''}
          {(filter || formationFilter !== 'all') && (
            <button className="hist-clear-btn" onClick={() => { setFilter(''); setFormationFilter('all'); }}>
              Effacer filtres
            </button>
          )}
        </div>
      ) : null}

      {/* Content */}
      {sorted.length === 0 ? (
        <div className="hist-empty">
          <div className="hist-empty-icon"><FaBrain /></div>
          <h3>Aucune prédiction trouvée</h3>
          <p>Modifiez vos filtres ou attendez de nouvelles prédictions</p>
        </div>
      ) : view === 'cards' ? (
        <div className="hist-grid">
          {sorted.map((p, i) => (
            <div key={i} className="hist-card">
              <div className="hist-card-top">
                <div className="hist-card-formation">
                  <FaGraduationCap />
                  <span>{p.formation || 'N/A'}</span>
                </div>
                {p.confidence_score && (
                  <div className="hist-card-score" style={{ color: getScoreColor(p.confidence_score), background: `${getScoreColor(p.confidence_score)}15` }}>
                    {p.confidence_score}%
                  </div>
                )}
              </div>

              <div className="hist-card-body">
                <div className="hist-card-row">
                  <FaUser className="hist-row-icon" />
                  <span className="hist-row-label">Par</span>
                  <span className="hist-row-value">{p.created_by || 'Anonyme'}</span>
                </div>
                {(p.nom || p.prenom) && (
                  <div className="hist-card-row">
                    <FaUser className="hist-row-icon" />
                    <span className="hist-row-label">Pour</span>
                    <span className="hist-row-value">{p.prenom} {p.nom}</span>
                  </div>
                )}
                <div className="hist-card-row">
                  <FaCalendarAlt className="hist-row-icon" />
                  <span className="hist-row-label">Âge</span>
                  <span className="hist-row-value">{p.age} ans</span>
                </div>
                <div className="hist-card-row">
                  <FaClock className="hist-row-icon" />
                  <span className="hist-row-label">Expérience</span>
                  <span className="hist-row-value">{p.experience} ans</span>
                </div>
              </div>

              {(p.competences || p.competence) && (
                <div className="hist-card-comps">
                  {(Array.isArray(p.competences) ? p.competences : [p.competence]).map((c, j) => (
                    <span key={j} className="hist-comp-tag">{c}</span>
                  ))}
                </div>
              )}

              <div className="hist-card-footer">
                <span className="hist-card-date">
                  <FaCalendarAlt /> {p.created_at ? new Date(p.created_at).toLocaleDateString('fr-FR', { day: '2-digit', month: 'short', year: 'numeric' }) : '—'}
                </span>
                {p.prediction_type && (
                  <span className="hist-card-type">{p.prediction_type === 'advanced_multi' ? 'Avancée' : 'Simple'}</span>
                )}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="hist-table-wrapper">
          <table className="hist-table">
            <thead>
              <tr>
                <th>Utilisateur</th>
                <th>Âge</th>
                <th>Exp.</th>
                <th>Compétences</th>
                <th>Formation</th>
                <th>Score</th>
                <th>Date</th>
              </tr>
            </thead>
            <tbody>
              {sorted.map((p, i) => (
                <tr key={i}>
                  <td>
                    <div className="hist-user-cell">
                      <div className="hist-user-avatar">{(p.created_by || '?').charAt(0).toUpperCase()}</div>
                      <div className="hist-user-info">
                        <span className="hist-user-name">{p.created_by || '-'}</span>
                        {(p.nom || p.prenom) && <span className="hist-user-target">{p.prenom} {p.nom}</span>}
                      </div>
                    </div>
                  </td>
                  <td>{p.age}</td>
                  <td>{p.experience} ans</td>
                  <td>
                    <div className="hist-comps-cell">
                      {(Array.isArray(p.competences) ? p.competences : [p.competence]).filter(Boolean).slice(0, 3).map((c, j) => (
                        <span key={j} className="hist-comp-mini">{c}</span>
                      ))}
                      {(p.competences?.length || 0) > 3 && (
                        <span className="hist-comp-more">+{p.competences.length - 3}</span>
                      )}
                    </div>
                  </td>
                  <td><strong className="hist-formation-cell">{p.formation}</strong></td>
                  <td>
                    {p.confidence_score ? (
                      <span className="hist-score-cell" style={{ color: getScoreColor(p.confidence_score) }}>
                        {p.confidence_score}%
                      </span>
                    ) : '—'}
                  </td>
                  <td className="hist-date-cell">{p.created_at ? new Date(p.created_at).toLocaleDateString('fr-FR') : '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
