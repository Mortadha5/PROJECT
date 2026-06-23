import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ProtectedRoute } from './components/ProtectedRoute';
import Navbar from './components/Navbar';
import Login from './pages/Login/Login';
import Prediction from './pages/Prediction/Prediction';
import Profile from './pages/Profile/Profile';
import Chatbot from './pages/Chatbot/Chatbot';
import Messages from './pages/Messages/Messages';
import Roadmap from './pages/Roadmap/Roadmap';
import Dashboard from './pages/Admin/Dashboard';
import UsersManagement from './pages/Admin/UsersManagement';
import CreateUser from './pages/Admin/CreateUser';
import Historique from './pages/Admin/Historique';
import Security from './pages/Admin/Security';
import Notifications from './pages/Admin/Notifications';
import AdminRoadmaps from './pages/Admin/AdminRoadmaps';
import AdminPredictions from './pages/Admin/AdminPredictions';
import MesResultats from './pages/Prediction/MesResultats';
import './App.css';

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      
      {/* User routes */}
      <Route path="/" element={
        <ProtectedRoute><Prediction /></ProtectedRoute>
      } />
      <Route path="/profile" element={
        <ProtectedRoute><Profile /></ProtectedRoute>
      } />
      <Route path="/chatbot" element={
        <ProtectedRoute><Chatbot /></ProtectedRoute>
      } />
      <Route path="/messages" element={
        <ProtectedRoute><Messages /></ProtectedRoute>
      } />
      <Route path="/roadmap" element={
        <ProtectedRoute><Roadmap /></ProtectedRoute>
      } />
      <Route path="/mes-resultats" element={
        <ProtectedRoute><MesResultats /></ProtectedRoute>
      } />

      {/* Admin routes */}
      <Route path="/admin/dashboard" element={
        <ProtectedRoute adminOnly><Dashboard /></ProtectedRoute>
      } />
      <Route path="/admin/users" element={
        <ProtectedRoute adminOnly><UsersManagement /></ProtectedRoute>
      } />
      <Route path="/admin/users/create" element={
        <ProtectedRoute adminOnly><CreateUser /></ProtectedRoute>
      } />
      <Route path="/admin/historique" element={
        <ProtectedRoute adminOnly><Historique /></ProtectedRoute>
      } />
      <Route path="/admin/security" element={
        <ProtectedRoute adminOnly><Security /></ProtectedRoute>
      } />
      <Route path="/admin/notifications" element={
        <ProtectedRoute adminOnly><Notifications /></ProtectedRoute>
      } />
      <Route path="/admin/roadmaps" element={
        <ProtectedRoute adminOnly><AdminRoadmaps /></ProtectedRoute>
      } />
      <Route path="/admin/predictions" element={
        <ProtectedRoute adminOnly><AdminPredictions /></ProtectedRoute>
      } />
      <Route path="/advanced-prediction" element={
        <ProtectedRoute adminOnly><Prediction /></ProtectedRoute>
      } />

      {/* Fallback */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

function AppLayout() {
  const { user } = useAuth();
  const location = useLocation();
  const isAuthPage = ['/login', '/register', '/forgot_password'].includes(location.pathname);
  const showNavbar = user && !isAuthPage;

  return (
    <>
      {showNavbar && <Navbar />}
      <main className={showNavbar ? 'main-content' : ''}>
        <AppRoutes />
      </main>
      <Toaster position="top-right" toastOptions={{ duration: 3000 }} />
    </>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppLayout />
      </AuthProvider>
    </BrowserRouter>
  );
}
