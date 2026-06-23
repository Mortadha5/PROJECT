import { useState, useEffect } from 'react';
import { getMesResultats, getMesDemandes } from '../../services/api';
import { FaGraduationCap, FaClock, FaCheckCircle, FaComment, FaInbox, FaChevronDown, FaChevronUp } from 'react-icons/fa';
import toast from 'react-hot-toast';
import './MesResultats.css';

export default function MesResultats() {
  const [results, setResults] = useState([]);
  const [demandes, setDemandes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [resResults, resDemandes] = await Promise.all([
        getMesResultats(),
        getMesDemandes()
      ]);
      setResults(resResults.data.predictions || []);
      // Only show pending/reviewed demandes (not sent_to_user, those are in results)
      const pending = (resDemandes.data.predictions || []).filter(d => d.status !== 'sent_to_user');
      setDemandes(pending);
    } catch {
      toast.error('Erreur de chargement');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '—';
    return new Date(dateStr).toLocaleDateString('fr-FR', {
      day: '2-digit', month: '2-digit', year: 'numeric',
      hour: '2-digit', minute: '2-digit'
    });
  };

  const getStatusLabel = (status) => {
    const map = { pending: 'En attente', reviewed: 'En cours d\'examen', sent_to_user: 'Disponible' };
    return map[status] || status;
  };

  if (loading) {
    return (
      <div className="mes-resultats">
        <div className="loading-state">
          <div className="spinner-large" />
          <p>Chargement...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="mes-resultats">
      <div className="page-header">
        <FaGraduationCap className="page-icon" />
        <h1>Mes Résultats</h1>
        <p>Vos recommandations de formation validées par l'administrateur</p>
      </div>

      {/* Demandes en cours */}
      {demandes.length > 0 && (
        <>
          <h3 className="section-title"><FaClock /> Demandes en cours</h3>
          <div className="results-list">
            {demandes.map(d => (
              <div key={d._id} className="demande-card">
                <div className="demande-info">
                  <span><strong>Compétences:</strong> {d.input_data?.competences?.join(', ')}</span>
                  <span><strong>Soumis:</strong> {formatDate(d.created_at)}</span>
                </div>
                <span className={`status-badge ${d.status}`}>
                  {getStatusLabel(d.status)}
                </span>
              </div>
            ))}
          </div>
        </>
      )}

      {/* Résultats validés */}
      <h3 className="section-title"><FaCheckCircle /> Résultats Validés</h3>
      
      {results.length === 0 ? (
        <div className="empty-state">
          <FaInbox className="empty-icon" />
          <p>Aucun résultat disponible pour le moment</p>
          <p style={{ fontSize: '0.9rem', marginTop: '0.5rem' }}>
            Soumettez une prédiction et attendez la validation de l'administrateur
          </p>
        </div>
      ) : (
        <div className="results-list">
          {results.map((r, idx) => (
            <div key={r._id} className="result-card">
              <div className="result-card-header">
                <h3><FaGraduationCap /> Recommandation #{idx + 1}</h3>
                <span className="result-date">{formatDate(r.sent_at)}</span>
              </div>

              <div className="result-main-formation">
                <h4>{r.prediction_result?.formation_suggeree}</h4>
                <div className="score">
                  Score de confiance : {r.prediction_result?.confidence_score}%
                </div>
              </div>

              {/* Alternatives */}
              {r.prediction_result?.recommendations?.length > 1 && (
                <div className="result-alternatives">
                  <h5>Autres formations recommandées</h5>
                  <div className="alt-list">
                    {r.prediction_result.recommendations.slice(1).map((rec, i) => (
                      <span key={i} className="alt-chip">
                        {rec.formation} ({rec.confidence_score}%)
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Admin Comment */}
              {r.admin_comment && (
                <div className="admin-comment-section">
                  <h5><FaComment /> Commentaire de l'administrateur</h5>
                  <p>{r.admin_comment}</p>
                </div>
              )}

              {/* Expand for profile analysis */}
              {r.prediction_result?.profile_analysis && (
                <>
                  <button
                    className="result-expand-btn"
                    onClick={() => setExpanded(expanded === idx ? null : idx)}
                  >
                    {expanded === idx ? <><FaChevronUp /> Masquer l'analyse</> : <><FaChevronDown /> Voir l'analyse du profil</>}
                  </button>
                  {expanded === idx && (
                    <div className="profile-analysis">
                      <h5>Analyse de votre profil</h5>
                      <div className="profile-grid">
                        <div className="stat">
                          <span className="stat-label">Carrière</span>
                          <span className="stat-value">{r.prediction_result.profile_analysis.career_stage}</span>
                        </div>
                        <div className="stat">
                          <span className="stat-label">Apprentissage</span>
                          <span className="stat-value">{r.prediction_result.profile_analysis.learning_capacity}</span>
                        </div>
                        <div className="stat">
                          <span className="stat-label">Disponibilité</span>
                          <span className="stat-value">{r.prediction_result.profile_analysis.time_availability}</span>
                        </div>
                        <div className="stat">
                          <span className="stat-label">Risque</span>
                          <span className="stat-value">{r.prediction_result.profile_analysis.risk_tolerance}</span>
                        </div>
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
