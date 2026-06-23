import { useState, useEffect } from 'react';
import { generateRoadmap, getUserRoadmapProgress, updateRoadmapProgress, getRoadmapFormations, startRoadmap } from '../../services/api';
import { FaRoad, FaCheck, FaSpinner, FaRocket, FaFlag, FaLightbulb, FaChevronRight, FaMapMarkerAlt, FaGraduationCap } from 'react-icons/fa';
import toast from 'react-hot-toast';
import './Roadmap.css';

export default function Roadmap() {
  const [roadmap, setRoadmap] = useState(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [formation, setFormation] = useState('');
  const [formations, setFormations] = useState([]);

  useEffect(() => {
    loadProgress();
    loadFormations();
  }, []);

  const loadFormations = async () => {
    try {
      const res = await getRoadmapFormations();
      setFormations(res.data.formations || []);
    } catch {
      // silent
    }
  };

  const loadProgress = async () => {
    try {
      const res = await getUserRoadmapProgress();
      // Backend returns {roadmaps: [...]} when no formation param
      const roadmaps = res.data.roadmaps || [];
      if (roadmaps.length > 0) {
        // Load the most recent roadmap's full data
        const latest = roadmaps[roadmaps.length - 1];
        setFormation(latest.formation || '');
        // Generate the roadmap structure to display
        const roadmapRes = await generateRoadmap({ formation: latest.formation });
        if (roadmapRes.data.success && roadmapRes.data.roadmap) {
          const rm = roadmapRes.data.roadmap;
          // Mark completed steps
          const completedSteps = latest.completed_steps || [];
          if (rm.phases) {
            rm.phases.forEach((phase, pi) => {
              const steps = phase.steps || phase.skills || [];
              steps.forEach((step, si) => {
                const key = `${pi}_${si}`;
                if (typeof step === 'string') {
                  // Convert string to object
                  steps[si] = { title: step, completed: completedSteps.includes(key) };
                } else {
                  step.completed = completedSteps.includes(key);
                }
              });
              phase.skills = steps;
            });
          }
          rm.formation = latest.formation;
          setRoadmap(rm);
        }
      } else if (res.data.roadmap) {
        setRoadmap(res.data.roadmap);
      }
    } catch {
      // No existing roadmap
    } finally {
      setLoading(false);
    }
  };

  const handleGenerate = async () => {
    if (!formation.trim()) {
      toast.error('Entrez le nom de la formation');
      return;
    }
    setGenerating(true);
    try {
      const res = await generateRoadmap({ formation: formation.trim() });
      if (res.data.success) {
        const rm = res.data.roadmap;
        rm.formation = formation.trim();
        setRoadmap(rm);
        // Start tracking in DB
        await startRoadmap({ formation: formation.trim() });
        toast.success('Roadmap générée !');
      }
    } catch {
      toast.error('Erreur de génération');
    } finally {
      setGenerating(false);
    }
  };

  const handleProgress = async (phaseIndex, stepIndex) => {
    try {
      await updateRoadmapProgress({
        formation: roadmap.formation || formation,
        phase_index: phaseIndex,
        skill_index: stepIndex
      });
      loadProgress();
    } catch {
      toast.error('Erreur de mise à jour');
    }
  };

  const getPhaseSteps = (phase) => {
    // Backend may return 'steps' or 'skills'
    return phase.steps || (phase.skills || []).map(s => ({
      title: s.name || s.title || s,
      completed: s.completed || false,
      type: s.type
    }));
  };

  const getPhaseProgress = (phase) => {
    const steps = getPhaseSteps(phase);
    if (!steps.length) return 0;
    const done = steps.filter(s => s.completed).length;
    return Math.round((done / steps.length) * 100);
  };

  const getTotalProgress = () => {
    if (!roadmap?.phases) return 0;
    const allSteps = roadmap.phases.flatMap(p => getPhaseSteps(p));
    if (!allSteps.length) return 0;
    return Math.round((allSteps.filter(s => s.completed).length / allSteps.length) * 100);
  };

  const phaseColors = ['#667eea', '#28a745', '#fd7e14', '#dc3545', '#17a2b8', '#764ba2'];

  if (loading) return <div className="loading-screen"><div className="spinner" /></div>;

  return (
    <div className="roadmap-page">
      {/* Header */}
      <div className="rm-header">
        <div className="rm-header-left">
          <h1><FaRoad /> Mon Roadmap</h1>
          <p>Votre plan d'apprentissage personnalisé</p>
        </div>
      </div>

      {!roadmap ? (
        /* Generate form */
        <div className="rm-generate-card">
          <div className="rm-generate-icon">
            <FaRocket />
          </div>
          <h2>Choisissez votre Formation</h2>
          <p>Sélectionnez une formation pour générer votre plan d'apprentissage personnalisé</p>

          <div className="rm-formations-grid">
            {formations.map((f) => (
              <div
                key={f}
                className={`rm-formation-item ${formation === f ? 'selected' : ''}`}
                onClick={() => setFormation(f)}
              >
                <div className="rm-formation-check">
                  {formation === f && <FaCheck />}
                </div>
                <FaGraduationCap className="rm-formation-icon" />
                <span>{f}</span>
              </div>
            ))}
          </div>

          <button className="rm-generate-btn" onClick={handleGenerate} disabled={generating || !formation}>
            {generating ? <FaSpinner className="spin" /> : <><FaRoad /> Générer le Roadmap</>}
          </button>
        </div>
      ) : (
        /* Roadmap display */
        <div className="rm-content">
          {/* Progress overview */}
          <div className="rm-overview">
            <div className="rm-overview-info">
              <h2>{roadmap.formation}</h2>
              <span className="rm-overview-stats">
                {roadmap.phases?.length || 0} phases · {getTotalProgress()}% complété
              </span>
            </div>
            <div className="rm-progress-ring">
              <svg viewBox="0 0 36 36">
                <path
                  d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                  fill="none" stroke="rgba(102,126,234,0.15)" strokeWidth="3"
                />
                <path
                  d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                  fill="none" stroke="#667eea" strokeWidth="3"
                  strokeDasharray={`${getTotalProgress()}, 100`}
                  strokeLinecap="round"
                />
              </svg>
              <span className="rm-progress-text">{getTotalProgress()}%</span>
            </div>
          </div>

          {/* Timeline */}
          <div className="rm-timeline">
            {roadmap.phases?.map((phase, pi) => {
              const progress = getPhaseProgress(phase);
              const color = phaseColors[pi % phaseColors.length];
              const isComplete = progress === 100;

              return (
                <div key={pi} className={`rm-phase ${isComplete ? 'complete' : ''}`}>
                  {/* Timeline connector */}
                  <div className="rm-phase-connector">
                    <div className="rm-phase-dot" style={{ background: isComplete ? '#28a745' : color }}>
                      {isComplete ? <FaCheck /> : <span>{pi + 1}</span>}
                    </div>
                    {pi < roadmap.phases.length - 1 && (
                      <div className="rm-phase-line" style={{ background: isComplete ? '#28a745' : 'var(--border)' }} />
                    )}
                  </div>

                  {/* Phase card */}
                  <div className="rm-phase-card">
                    <div className="rm-phase-header">
                      <div className="rm-phase-title">
                        <h3 style={{ color }}>Phase {pi + 1}: {phase.title}</h3>
                        <p>{phase.description || phase.duration || ''}</p>
                      </div>
                      <div className="rm-phase-progress">
                        <div className="rm-mini-bar">
                          <div className="rm-mini-bar-fill" style={{ width: `${progress}%`, background: color }} />
                        </div>
                        <span style={{ color }}>{progress}%</span>
                      </div>
                    </div>

                    <div className="rm-steps">
                      {getPhaseSteps(phase).map((step, si) => (
                        <div
                          key={si}
                          className={`rm-step ${step.completed ? 'done' : ''}`}
                          onClick={() => handleProgress(pi, si)}
                        >
                          <div className="rm-step-check" style={{ borderColor: step.completed ? '#28a745' : 'var(--border)', background: step.completed ? '#28a745' : 'transparent' }}>
                            {step.completed && <FaCheck />}
                          </div>
                          <span className="rm-step-title">{step.title}</span>
                          <FaChevronRight className="rm-step-arrow" />
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              );
            })}

            {/* End marker */}
            <div className="rm-end-marker">
              <FaFlag />
              <span>Objectif atteint !</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
