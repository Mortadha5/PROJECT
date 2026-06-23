import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getUsers, editUser } from '../../services/api';
import { FaUserEdit, FaArrowLeft, FaSave } from 'react-icons/fa';
import toast from 'react-hot-toast';

export default function EditUser() {
  const { username } = useParams();
  const navigate = useNavigate();
  const [form, setForm] = useState({ full_name: '', email: '', role: 'user' });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadUser();
  }, [username]);

  const loadUser = async () => {
    try {
      const res = await getUsers();
      const user = (res.data.users || []).find(u => u.username === username);
      if (user) {
        setForm({
          full_name: user.full_name || '',
          email: user.email || '',
          role: user.role || 'user',
        });
      } else {
        toast.error('Utilisateur non trouvé');
        navigate('/admin/users');
      }
    } catch {
      toast.error('Erreur de chargement');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      const res = await editUser(username, form);
      if (res.data.success) {
        toast.success('Utilisateur modifié avec succès');
        navigate('/admin/users');
      } else {
        toast.error(res.data.error || 'Erreur');
      }
    } catch (err) {
      toast.error(err.response?.data?.error || 'Erreur de modification');
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div className="loading-screen"><div className="spinner" /></div>;

  return (
    <div style={{ maxWidth: 600, margin: '0 auto', padding: '2rem' }}>
      <button
        onClick={() => navigate('/admin/users')}
        style={{
          background: 'none', border: 'none', color: '#a78bfa', cursor: 'pointer',
          display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.9rem', marginBottom: '1.5rem'
        }}
      >
        <FaArrowLeft /> Retour aux utilisateurs
      </button>

      <div className="page-header">
        <FaUserEdit className="page-icon" />
        <h1>Modifier : {username}</h1>
      </div>

      <form className="card" onSubmit={handleSubmit} style={{ padding: '2rem' }}>
        <div className="form-group" style={{ marginBottom: '1.5rem' }}>
          <label>Nom complet</label>
          <input
            type="text"
            value={form.full_name}
            onChange={e => setForm({ ...form, full_name: e.target.value })}
          />
        </div>
        <div className="form-group" style={{ marginBottom: '1.5rem' }}>
          <label>Email</label>
          <input
            type="email"
            value={form.email}
            onChange={e => setForm({ ...form, email: e.target.value })}
          />
        </div>
        <div className="form-group" style={{ marginBottom: '1.5rem' }}>
          <label>Rôle</label>
          <select value={form.role} onChange={e => setForm({ ...form, role: e.target.value })}>
            <option value="user">Utilisateur</option>
            <option value="admin">Administrateur</option>
          </select>
        </div>

        <button
          type="submit"
          disabled={saving}
          style={{
            width: '100%', padding: '14px', border: 'none', borderRadius: 12,
            background: 'linear-gradient(135deg, #667eea, #764ba2)', color: 'white',
            fontSize: '1rem', fontWeight: 600, cursor: 'pointer',
            display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
            opacity: saving ? 0.7 : 1
          }}
        >
          <FaSave /> {saving ? 'Enregistrement...' : 'Enregistrer les modifications'}
        </button>
      </form>
    </div>
  );
}
