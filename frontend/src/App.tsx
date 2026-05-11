import React, { useEffect, useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import AuthPage from './pages/AuthPage';
import HomePage from './pages/HomePage';
import FileEditor from './pages/FileEditor';
import { ToastProvider } from './context/ToastContext';

interface AuthGuardProps {
  children: React.ReactElement;
}

const AuthGuard: React.FC<AuthGuardProps> = ({ children }) => {
  const [checking, setChecking] = useState<boolean>(true);
  const [authenticated, setAuthenticated] = useState<boolean>(false);

  useEffect(() => {
    fetch('/api/v1/users/me', { credentials: 'include' })
      .then((r) => {
        setAuthenticated(r.ok);
        setChecking(false);
      })
      .catch(() => {
        setAuthenticated(false);
        setChecking(false);
      });
  }, []);

  if (checking) return <div className="p-4">Loading…</div>;
  if (!authenticated) return <Navigate to="/login" replace />;
  return children;
};

const App: React.FC = () => (
  <ToastProvider>
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<AuthPage />} />
        <Route path="/" element={<HomePage />} />
        <Route
          path="/files/:id/edit"
          element={
            <AuthGuard>
              <FileEditor />
            </AuthGuard>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  </ToastProvider>
);

export default App;
