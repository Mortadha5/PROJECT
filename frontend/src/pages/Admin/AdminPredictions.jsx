import { useState, useEffect } from 'react';
import { getAdminPredictions, sendPredictionToUser, commentPrediction } from '../../services/api';
import { FaClipboardList, FaUser, FaCalendarAlt, FaBrain, FaPaperPlane, FaComment, FaEye, FaInbox } from 'react-icons/fa';
import toast from 'react-hot-toast';
import './AdminPredictions.css';

export default function AdminPredictions() {
  const [predictions, setPredictions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('pending');
  const [selectedPred, setSelectedPred] = useState(null);
  const [comment, setComment] = useState('');
  const [sending, setSending] = useState(false);

  useEffect(() => {
    loadData();
  }, [statusFilter]);

  const loadData = async () => {
    setLoading(true);
    try {
      const res = await getAdminPredictions(statusFilter);
      setPredictions(res.data.predictions || []);
    } catch {
      toast.error('Erreur de chargement');
    } finally {
      setLoading(false);
    }
  };

  const handleSend = async (pred) => {
    setSending(true);
    try {
      await sendPredictionToUser(pred._id, comment);
      toast.success('Résultat envoyé à l\'utilisateur !');
      setSelectedPred(null);
      setComment('');
      loadData();
    } catch {
      toast.error('Erreur lors de l\'envoi');
    } finally {
      setSending(false);
    }
  };

  const handleComment = async (pred) => {
    try {
      await commentPrediction(pred._id, comment);
      toast.success('Commentaire ajouté');
      setSelectedPred(null);
      setComment('');
      loadData();
    } catch {
      toast.error('Erreur');
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
    const map = { pending: 'En attente', reviewed: 'Examiné', sent_to_user: 'Envoyé' };
    return map[status] || status;
  };

  return (
    <div className="admin-predictions">
      <div className="page-header">
        <FaClipboardList className="page-icon" />
        <h1>Prédictions en Attente</h1>
        <p>Examinez et validez les demandes de prédiction des utilisateurs</p>
      </div>

      <div className="filter-tabs">
        {['pending', 'reviewed', 'sent_to_user', 'all'].map(s => (
          <button
            key={s}
            className={statusFilter === s ? 'active' : ''}
            onClick={() => setStatusFilter(s)}
          >
            {s === 'all' ? 'Toutes' : getStatusLabel(s)}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="loading-state">
          <div className="spinner-large" />
          <p>Chargement...</p>
        </div>
      ) : predictions.length === 0 ? (
        <div className="empty-state">
          <FaInbox className="empty-icon" />
          <p>Aucune prédiction {statusFilter !== 'all' ? getStatusLabel(statusFilter).toLowerCase() : ''}</p>
        </div>
      ) : (
        <div className="predictions-grid">
          {predictions.map(pred => (
            <div key={pred._id} className="prediction-card">
              <div className="prediction-card-header">
                <h3><FaUser /> {pred.username}</h3>
                <span className={`status-badge ${pred.status}`}>
                  {getStatusLabel(pred.status)}
                </span>
              </div>
              <div className="prediction-card-body">
                <div className="info-item">
                  <span className="label">Âge</span>
                  <span className="value">{pred.input_data?.age} ans</span>
                </div>
                <div className="info-item">
                  <span className="label">Expérience</span>
                  <span className="value">{pred.input_data?.experience} ans</span>
                </div>
                <div className="info-item">
                  <span className="label">Compétences</span>
                  <span className="value">{pred.input_data?.competences?.length || 0}</span>
                </div>
                <div className="info-item">
                  <span className="label">Formation suggérée</span>
                  <span className="value">{pred.prediction_result?.formation_suggeree || '—'}</span>
                </div>
                <div className="info-item">
                  <span className="label">Score</span>
                  <span className="value">{pred.prediction_result?.confidence_score || 0}%</span>
                </div>
                <div className="info-item">
                  <span className="label">Date</span>
                  <span className="value">{formatDate(pred.created_at)}</span>
                </div>
              </div>
              <div className="prediction-card-actions">
                <button className="btn-view" onClick={() => { setSelectedPred(pred); setComment(pred.admin_comment || ''); }}>
                  <FaEye /> Détails
                </button>
                {pred.status !== 'sent_to_user' && (
                  <button className="btn-send" onClick={() => { setSelectedPred(pred); setComment(pred.admin_comment || ''); }}>
                    <FaPaperPlane /> Envoyer au user
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Detail Modal */}
      {selectedPred && (
        <div className="detail-overlay" onClick={(e) => e.target === e.currentTarget && setSelectedPred(null)}>
          <div className="detail-modal">
            <h2><FaBrain /> Détail de la Prédiction</h2>
            
            <div className="detail-section">
              <h4><FaUser /> Utilisateur: {selectedPred.username}</h4>
              <div className="prediction-card-body">
                <div className="info-item">
                  <span className="label">Âge</span>
                  <span className="value">{selectedPred.input_data?.age} ans</span>
                </div>
                <div className="info-item">
                  <span className="label">Expérience</span>
                  <span className="value">{selectedPred.input_data?.experience} ans</span>
                </div>
                <div className="info-item">
                  <span className="label">Compétences</span>
                  <span className="value">{selectedPred.input_data?.competences?.join(', ')}</span>
                </div>
              </div>
            </div>

            <div className="detail-section">
              <h4><FaBrain /> Recommandations</h4>
              {selectedPred.prediction_result?.recommendations?.map((rec, i) => (
                <div key={i} className="recommendation-item">
                  <div className="recommendation-rank">{i + 1}</div>
                  <div className="recommendation-info">
                    <div className="recommendation-name">{rec.formation}</div>
                    <div className="recommendation-score">Score: {rec.confidence_score}%</div>
                  </div>
                </div>
              ))}
            </div>

            <div className="detail-section">
              <h4><FaComment /> Commentaire Admin</h4>
              <textarea
                className="comment-input"
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                placeholder="Ajouter un commentaire pour l'utilisateur..."
              />
            </div>

            <div className="modal-actions">
              <button className="btn-close-modal" onClick={() => setSelectedPred(null)}>
                Fermer
              </button>
              {selectedPred.status !== 'sent_to_user' && (
                <>
                  <button className="btn-view" onClick={() => handleComment(selectedPred)}>
                    <FaComment /> Sauvegarder commentaire
                  </button>
                  <button className="btn-send" onClick={() => handleSend(selectedPred)} disabled={sending}>
                    <FaPaperPlane /> {sending ? 'Envoi...' : 'Envoyer au user'}
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
