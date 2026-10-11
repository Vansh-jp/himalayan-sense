import type { ReactNode } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import LandingPage from './pages/LandingPage';
import MapPage from './pages/MapPage';
import ReportPage from './pages/ReportPage';
import IncidentsPage from './pages/IncidentsPage';
import AlertsPage from './pages/AlertsPage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import DashboardOverview from './pages/admin/DashboardOverview';
import ManageIncidents from './pages/admin/ManageIncidents';
import AnalyticsPage from './pages/admin/AnalyticsPage';

function ProtectedAdminRoute({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="p-8 text-center">Loading session...</div>;
  if (!user || user.role !== 'admin') return <Navigate replace to="/login" />;
  return <>{children}</>;
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public Routes */}
          <Route path="/" element={<LandingPage />} />
          <Route path="/map" element={<MapPage />} />
          <Route path="/incidents" element={<IncidentsPage />} />
          <Route path="/alerts" element={<AlertsPage />} />
          <Route path="/report" element={<ReportPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />

          {/* Protected Admin Routes */}
          <Route
            path="/dashboard"
            element={
              <ProtectedAdminRoute>
                <DashboardOverview />
              </ProtectedAdminRoute>
            }
          />
          <Route
            path="/dashboard/incidents"
            element={
              <ProtectedAdminRoute>
                <ManageIncidents />
              </ProtectedAdminRoute>
            }
          />
          <Route
            path="/dashboard/analytics"
            element={
              <ProtectedAdminRoute>
                <AnalyticsPage />
              </ProtectedAdminRoute>
            }
          />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}