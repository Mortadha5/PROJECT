import { useState, useEffect } from 'react';
import { getAdminRoadmaps, deleteRoadmap } from '../../services/api';
import { FaRoad, FaUsers, FaCheckCircle, FaSpinner, FaTrash } from 'react-icons/fa';
import toast from 'react-hot-toast';

export default function AdminRoadmaps() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const res = await getAdminRoadmaps();
      setData(res.data);
    } catch {
      toast.error('Erreur de chargement');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id, username, formation) => {
    if (!confirm(`Supprimer la roadmap "${formation}" de ${username} ?`)) return;
    try {
      await deleteRoadmap(id);
      toast.success('Roadmap supprimée');
      loadData();
    } catch {
      toast.error('Erreur de suppression');
    }
  };

  if (loading) return <div className="loading-screen"><div className="spinner" /></div>;

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto', padding: '2rem' }}>
      <div className="page-header">
        <FaRoad className="page-icon" />
        <h1>Roadmaps des Utilisateurs</h1>
      </div>

      <div className="stats-grid" style={{ marginTop: '1.5rem' }}>
        <div className="stat-card">
          <div className="stat-value">{data?.total || 0}</div>
          <div className="stat-label">Total Roadmaps</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{data?.completed || 0}</div>
          <div className="stat-label">Complétés</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{data?.in_progress || 0}</div>
          <div className="stat-label">En cours</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{data?.avg_progress || 0}%</div>
          <div className="stat-label">Progression moy.</div>
        </div>
      </div>

      {data?.roadmaps?.length > 0 && (
        <div className="card" style={{ marginTop: '1.5rem' }}>
          <h3>Liste des Roadmaps</h3>
          <table className="data-table" style={{ marginTop: '1rem' }}>
            <thead>
              <tr>
                <th>Utilisateur</th>
                <th>Formation</th>
                <th>Progression</th>
                <th>Statut</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {data.roadmaps.map((r, i) => (
                <tr key={r._id || i}>
                  <td>{r.username}</td>
                  <td>{r.formation}</td>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <div style={{ flex: 1, height: 8, background: 'var(--bg-secondary)', borderRadius: 4, overflow: 'hidden' }}>
                        <div style={{ width: `${r.progress || 0}%`, height: '100%', background: r.progress === 100 ? '#28a745' : 'var(--primary)', borderRadius: 4 }} />
                      </div>
                      <span style={{ fontSize: '0.85rem' }}>{r.progress || 0}%</span>
                    </div>
                  </td>
                  <td>
                    {r.progress === 100 ? (
                      <span className="badge badge-active"><FaCheckCircle /> Complété</span>
                    ) : (
                      <span className="badge badge-user"><FaSpinner /> En cours</span>
                    )}
                  </td>
                  <td>
                    <button
                      className="btn-icon danger"
                      onClick={() => handleDelete(r._id, r.username, r.formation)}
                      title="Supprimer"
                      style={{ color: '#dc3545', background: 'rgba(220,53,69,0.08)', border: 'none', borderRadius: 8, padding: '6px 10px', cursor: 'pointer' }}
                    >
                      <FaTrash />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
