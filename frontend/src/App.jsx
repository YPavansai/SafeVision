import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ThemeProvider } from './context/ThemeContext';
import { DemoProvider } from './context/DemoContext';
import Sidebar from './components/Layout/Sidebar';
import Navbar from './components/Layout/Navbar';

import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import WorkersPage from './pages/WorkersPage';
import AttendancePage from './pages/AttendancePage';
import LiveMonitoringPage from './pages/LiveMonitoringPage';
import ImageAnalysisPage from './pages/ImageAnalysisPage';
import AlertsPage from './pages/AlertsPage';
import MediaLibraryPage from './pages/MediaLibraryPage';
import ReportsPage from './pages/ReportsPage';

const ProtectedLayout = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh', color: 'var(--cyan-primary)' }}>Initializing Session...</div>;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return (
    <div className="app-container">
      <Sidebar />
      <div className="main-content">
        <Navbar />
        {children}
      </div>
    </div>
  );
};

export default function App() {
  return (
    <AuthProvider>
      <ThemeProvider>
        <DemoProvider>
          <Router>
            <Routes>
              <Route path="/login" element={<Login />} />
              <Route
                path="/dashboard"
                element={
                  <ProtectedLayout>
                    <Dashboard />
                  </ProtectedLayout>
                }
              />
              <Route
                path="/workers"
                element={
                  <ProtectedLayout>
                    <WorkersPage />
                  </ProtectedLayout>
                }
              />
              <Route
                path="/attendance"
                element={
                  <ProtectedLayout>
                    <AttendancePage />
                  </ProtectedLayout>
                }
              />
              <Route
                path="/monitoring"
                element={
                  <ProtectedLayout>
                    <LiveMonitoringPage />
                  </ProtectedLayout>
                }
              />
              <Route
                path="/image-analysis"
                element={
                  <ProtectedLayout>
                    <ImageAnalysisPage />
                  </ProtectedLayout>
                }
              />
              <Route
                path="/alerts"
                element={
                  <ProtectedLayout>
                    <AlertsPage />
                  </ProtectedLayout>
                }
              />
              <Route
                path="/media-library"
                element={
                  <ProtectedLayout>
                    <MediaLibraryPage />
                  </ProtectedLayout>
                }
              />
              <Route
                path="/reports"
                element={
                  <ProtectedLayout>
                    <ReportsPage />
                  </ProtectedLayout>
                }
              />
              <Route path="*" element={<Navigate to="/dashboard" replace />} />
            </Routes>
          </Router>
        </DemoProvider>
      </ThemeProvider>
    </AuthProvider>
  );
}
