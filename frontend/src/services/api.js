import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5555';

const api = axios.create({
  baseURL: API_BASE,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Auth
export const login = (username, password) =>
  api.post('/api/auth/login', { username, password });

export const logout = () => api.post('/api/auth/logout');

export const getSession = () => api.get('/api/auth/session');

// Predictions
export const predict = (data) => api.post('/api/predict', data);

export const predictAdvanced = (data) => api.post('/api/predict_advanced', data);

// User Profile
export const getProfile = () => api.get('/api/profile');

export const updateProfile = (data) => api.put('/api/profile', data);

export const uploadAvatar = (formData) =>
  api.post('/api/upload_avatar', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });

export const changePassword = (data) => api.post('/api/change_password', data);

// Messages
export const getUnreadMessages = () => api.get('/api/unread_messages');

export const getMessages = (username) => 
  api.get('/api/get_messages', { params: username ? { username } : {} });

export const sendMessage = (data) => api.post('/send_message', data);

// Chatbot
export const chatbotMessage = (data) => api.post('/api/chatbot', data);

export const chatbotFeedback = (data) => api.post('/api/chatbot_feedback', data);

// Roadmap
export const generateRoadmap = (data) => api.post('/api/roadmap', data);

export const getRoadmapFormations = () => api.get('/api/roadmap/formations');

export const startRoadmap = (data) => api.post('/api/roadmap/start', data);

export const updateRoadmapProgress = (data) => api.post('/api/roadmap/progress', data);

export const getUserRoadmapProgress = () => api.get('/api/roadmap/user_progress');

// Notifications (Admin)
export const getNotifications = () => api.get('/api/notifications');

export const getUnreadNotifCount = () => api.get('/api/notifications/unread_count');

export const markNotifRead = (id) => api.post('/api/notifications/mark_read', { id });

export const markAllNotifsRead = () => api.post('/api/notifications/mark_all_read');

export const sendNotification = (data) => api.post('/api/notifications/send', data);

export const broadcastNotification = (data) => api.post('/api/notifications/broadcast', data);

export const deleteNotification = (id) => api.post('/api/notifications/delete', { id });

// Admin - Users
export const getUsers = () => api.get('/api/admin/users');

export const createUser = (data) => api.post('/api/admin/users/create', data);

export const editUser = (username, data) => api.put(`/api/admin/users/${username}`, data);

export const deleteUser = (username) => api.delete(`/api/admin/users/${username}`);

export const resetUserPassword = (username) =>
  api.post(`/api/admin/users/reset_password/${username}`);

export const blockUser = (username) =>
  api.post('/api/admin/security/block_user', { username });

export const unblockUser = (username) =>
  api.post('/api/admin/security/unblock_user', { username });

// Admin - Dashboard
export const getDashboardStats = () => api.get('/api/admin/dashboard');

// Admin - History
export const getHistorique = () => api.get('/api/admin/historique');

// Admin - Security
export const getSecurityData = () => api.get('/api/admin/security');

export const clearLogs = () => api.post('/api/admin/security/clear_logs');

// Admin - Roadmaps
export const getAdminRoadmaps = () => api.get('/api/admin/roadmaps');

export const deleteRoadmap = (id) => api.delete(`/api/admin/roadmaps/${id}`);

// Admin - Predictions Review
export const getAdminPredictions = (status = 'pending') =>
  api.get('/api/admin/predictions/pending', { params: { status } });

export const getPendingPredictionsCount = () =>
  api.get('/api/admin/predictions/pending_count');

export const getAdminPredictionDetail = (id) =>
  api.get(`/api/admin/predictions/${id}`);

export const sendPredictionToUser = (id, comment) =>
  api.post(`/api/admin/predictions/${id}/send`, { comment });

export const commentPrediction = (id, comment) =>
  api.post(`/api/admin/predictions/${id}/comment`, { comment });

// User - Mes Résultats
export const getMesResultats = () => api.get('/api/mes_resultats');

export const getMesDemandes = () => api.get('/api/mes_demandes');

export default api;
