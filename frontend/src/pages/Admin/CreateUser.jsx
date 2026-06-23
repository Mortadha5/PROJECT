import { useState } from 'react';
import { createUser } from '../../services/api';
import { useNavigate } from 'react-router-dom';
import { FaUserPlus } from 'react-icons/fa';
import toast from 'react-hot-toast';

export default function CreateUser() {
  const [form, setForm] = useState({ full_name: '', username: '', email: '', password: '', role: 'user' });
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await createUser(form);
      if (res.data.success) {
        toast.success('Utilisateur créé');
        navigate('/admin/users');
      } else {
        toast.error(res.data.error || 'Erreur');
      }
    } catch (err) {
      toast.error(err.response?.data?.error || 'Erreur');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: 600, margin: '0 auto', padding: '2rem' }}>
      <div className="page-header">
        <FaUserPlus className="page-icon" />
        <h1>Créer un utilisateur</h1>
      </div>

      <form className="card" onSubmit={handleSubmit} style={{ padding: '2rem' }}>
        <div className="form-group" style={{ marginBottom: '1.5rem' }}>
          <label>Nom complet</label>
          <input type="text" value={form.full_name} onChange={e => setForm({ ...form, full_name: e.target.value })} required />
        </div>
        <div className="form-group" style={{ marginBottom: '1.5rem' }}>
          <label>Nom d'utilisateur</label>
          <input type="text" value={form.username} onChange={e => setForm({ ...form, username: e.target.value })} required />
        </div>
        <div className="form-group" style={{ marginBottom: '1.5rem' }}>
          <label>Email</label>
          <input type="email" value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} required />
        </div>
        <div className="form-group" style={{ marginBottom: '1.5rem' }}>
          <label>Mot de passe temporaire</label>
          <input type="password" value={form.password} onChange={e => setForm({ ...form, password: e.target.value })} required minLength={6} />
        </div>
        <div className="form-group" style={{ marginBottom: '1.5rem' }}>
          <label>Rôle</label>
          <select value={form.role} onChange={e => setForm({ ...form, role: e.target.value })}>
            <option value="user">Utilisateur</option>
            <option value="admin">Administrateur</option>
          </select>
        </div>
        <button type="submit" className="btn-predict" disabled={loading}>
          {loading ? 'Création...' : 'Créer l\'utilisateur'}
        </button>
      </form>
    </div>
  );
}
