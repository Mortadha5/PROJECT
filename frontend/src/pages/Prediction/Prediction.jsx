import { useState } from 'react';
import { predictAdvanced } from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { FaMagic, FaBrain, FaCalendar, FaBriefcase, FaUser, FaIdCard, FaCheckCircle, FaClock } from 'react-icons/fa';
import toast from 'react-hot-toast';
import './Prediction.css';

const COMPETENCES = [
  'Python', 'Data Science', 'IA/ML', 'Cloud Computing', 'DevOps',
  'Développement Web', 'Développement Mobile', 'Cybersécurité',
  'Réseaux', 'Base de Données', 'Support Technique', 'Cloud',
  'Docker', 'Kubernetes', 'Linux'
];

export default function Prediction() {
  const { user } = useAuth();
  const isAdmin = user?.role === 'admin';
  const [nom, setNom] = useState('');
  const [prenom, setPrenom] = useState('');
  const [age, setAge] = useState('');
  const [experience, setExperience] = useState('');
  const [selectedComps, setSelectedComps] = useState([]);
  const [results, setResults] = useState(null);
  const [pending, setPending] = useState(false);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState('');

  const filteredComps = COMPETENCES.filter(c =>
    c.toLowerCase().includes(search.toLowerCase())
  );

  const toggleComp = (comp) => {
    setSelectedComps(prev =>
      prev.includes(comp) ? prev.filter(c => c !== comp) : [...prev, comp]
    );
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (selectedComps.length === 0) {
      toast.error('Sélectionnez au moins une compétence');
      return;
    }

    setLoading(true);
    try {
      const payload = {
        age: parseInt(age),
        experience: parseInt(experience),
        competences: selectedComps,
      };
      if (isAdmin) {
        payload.nom = nom;
        payload.prenom = prenom;
      }
      const res = await predictAdvanced(payload);

      if (res.data.success) {
        if (res.data.pending) {
          setPending(true);
          toast.success('Demande envoyée avec succès !');
        } else {
          setResults(res.data);
        }
      } else {
        toast.error(res.data.error || 'Erreur de prédiction');
      }
    } catch (err) {
      toast.error('Erreur de connexion au serveur');
    } finally {
      setLoading(false);
    }
  };

  const reset = () => {
    setResults(null);
    setPending(false);
    setNom('');
    setPrenom('');
    setAge('');
    setExperience('');
    setSelectedComps([]);
  };

  return (
    <div className="prediction-page">
      <div className="page-header">
        <FaBrain className="page-icon" />
        <h1>Prédiction de Formation</h1>
        <p>Analysez votre profil pour obtenir une recommandation personnalisée</p>
      </div>

      {pending ? (
        <div className="pending-section card">
          <div className="pending-icon">
            <FaClock />
          </div>
          <h2>Demande envoyée avec succès !</h2>
          <p className="pending-message">
            Votre demande a été envoyée à l'administrateur pour validation.
            Vous recevrez une notification dès que votre résultat sera disponible.
          </p>
          <p className="pending-hint">
            Consultez vos résultats dans la section <strong>Mes Résultats</strong> une fois validés.
          </p>
          <button className="btn-reset" onClick={reset}>
            Nouvelle Prédiction
          </button>
        </div>
      ) : !results ? (
        <form className="prediction-form card" onSubmit={handleSubmit}>
          {isAdmin && (
            <div className="form-row">
              <div className="form-group">
                <label><FaUser /> Nom</label>
                <input
                  type="text"
                  value={nom}
                  onChange={(e) => setNom(e.target.value)}
                  placeholder="Nom de l'employé"
                  required
                />
              </div>
              <div className="form-group">
                <label><FaIdCard /> Prénom</label>
                <input
                  type="text"
                  value={prenom}
                  onChange={(e) => setPrenom(e.target.value)}
                  placeholder="Prénom de l'employé"
                  required
                />
              </div>
            </div>
          )}
          <div className="form-row">
            <div className="form-group">
              <label><FaCalendar /> Âge</label>
              <input
                type="number"
                min="18"
                max="65"
                value={age}
                onChange={(e) => setAge(e.target.value)}
                placeholder="Ex: 28"
                required
              />
            </div>
            <div className="form-group">
              <label><FaBriefcase /> Expérience (années)</label>
              <input
                type="number"
                min="0"
                max="40"
                value={experience}
                onChange={(e) => setExperience(e.target.value)}
                placeholder="Ex: 5"
                required
              />
            </div>
          </div>

          <div className="competences-section">
            <label>Compétences ({selectedComps.length} sélectionnées)</label>
            <input
              type="text"
              className="search-input"
              placeholder="Rechercher une compétence..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
            <div className="competences-grid">
              {filteredComps.map(comp => (
                <button
                  key={comp}
                  type="button"
                  className={`comp-tag ${selectedComps.includes(comp) ? 'selected' : ''}`}
                  onClick={() => toggleComp(comp)}
                >
                  {comp}
                </button>
              ))}
            </div>
          </div>

          <button type="submit" className="btn-predict" disabled={loading}>
            {loading ? (
              <span className="spinner-small" />
            ) : (
              <>
                <FaMagic /> Prédire la Formation
              </>
            )}
          </button>
        </form>
      ) : (
        <div className="results-section">
          <ResultsDisplay results={results} />
          <button className="btn-reset" onClick={reset}>
            Nouvelle Prédiction
          </button>
        </div>
      )}
    </div>
  );
}

function ResultsDisplay({ results }) {
  const [selected, setSelected] = useState(null);
  const top = results.recommendations[0];
  const alternatives = results.recommendations.slice(1);
  const profile = results.profile_analysis;
  const colors = ['#667eea', '#28a745', '#fd7e14', '#dc3545', '#17a2b8'];

  return (
    <>
      {/* Main result */}
      <div className="card result-main">
        <h2>{top.formation}</h2>
        <div className="confidence" style={{ color: top.confidence_level.color }}>
          Score de confiance : {top.confidence_score}%
        </div>
        {top.details && (
          <div className="details-grid">
            <div className="detail-box">
              <span className="detail-label">Durée</span>
              <span className="detail-value">{top.details.duration || 'Variable'}</span>
            </div>
            <div className="detail-box">
              <span className="detail-label">Difficulté</span>
              <span className="detail-value">{top.details.difficulty || 'Modérée'}</span>
            </div>
            <div className="detail-box">
              <span className="detail-label">Salaire</span>
              <span className="detail-value">{top.details.salary_range || 'Variable'}</span>
            </div>
            <div className="detail-box">
              <span className="detail-label">Opportunités</span>
              <span className="detail-value">{top.details.job_opportunities || 'Bonnes'}</span>
            </div>
          </div>
        )}
      </div>

      {/* Alternatives */}
      {alternatives.length > 0 && (
        <div className="card">
          <h3>Autres Formations Recommandées</h3>
          <p className="alt-hint">Cliquez sur une formation pour voir ses détails</p>
          <div className="alternatives-list">
            {alternatives.map((rec, i) => (
              <div key={i}>
                <div
                  className={`alt-item ${selected === i ? 'alt-selected' : ''}`}
                  onClick={() => setSelected(selected === i ? null : i)}
                  style={{ cursor: 'pointer' }}
                >
                  <div className="alt-rank" style={{ background: colors[i + 1] || colors[0] }}>
                    {i + 2}
                  </div>
                  <div className="alt-info">
                    <div className="alt-name">{rec.formation}</div>
                    <div className="alt-score">{rec.confidence_score}%</div>
                  </div>
                  <div className="alt-bar-container">
                    <div
                      className="alt-bar"
                      style={{ width: `${rec.confidence_score}%`, background: rec.confidence_level.color }}
                    />
                  </div>
                </div>
                {selected === i && (
                  <div className="alt-details-expanded">
                    {rec.details && (
                      <div className="details-grid">
                        <div className="detail-box">
                          <span className="detail-label">Durée</span>
                          <span className="detail-value">{rec.details.duration || 'Variable'}</span>
                        </div>
                        <div className="detail-box">
                          <span className="detail-label">Difficulté</span>
                          <span className="detail-value">{rec.details.difficulty || 'Modérée'}</span>
                        </div>
                        <div className="detail-box">
                          <span className="detail-label">Salaire</span>
                          <span className="detail-value">{rec.details.salary_range || 'Variable'}</span>
                        </div>
                        <div className="detail-box">
                          <span className="detail-label">Opportunités</span>
                          <span className="detail-value">{rec.details.job_opportunities || 'Bonnes'}</span>
                        </div>
                      </div>
                    )}
                    {rec.reasons?.length > 0 && (
                      <div className="alt-reasons">
                        <h4>Pourquoi cette formation ?</h4>
                        <ul>
                          {rec.reasons.map((r, j) => <li key={j}>{r}</li>)}
                        </ul>
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Profile Analysis */}
      {profile && (
        <div className="card">
          <h3>Analyse de Votre Profil</h3>
          <div className="profile-grid">
            <div className="profile-stat">
              <h4>Stade de Carrière</h4>
              <p>{profile.career_stage}</p>
            </div>
            <div className="profile-stat">
              <h4>Capacité d'Apprentissage</h4>
              <p>{profile.learning_capacity}</p>
            </div>
            <div className="profile-stat">
              <h4>Disponibilité</h4>
              <p>{profile.time_availability}</p>
            </div>
            <div className="profile-stat">
              <h4>Tolérance au Risque</h4>
              <p>{profile.risk_tolerance}</p>
            </div>
          </div>
          {profile.recommendations?.length > 0 && (
            <div className="profile-recommendations">
              <h4>Conseils</h4>
              <ul>
                {profile.recommendations.map((r, i) => (
                  <li key={i}>{r}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </>
  );
}
