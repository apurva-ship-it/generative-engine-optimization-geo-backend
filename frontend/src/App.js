import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useEffect, useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import AuthPage from './pages/AuthPage';
import HomePage from './pages/HomePage';
import FileEditor from './pages/FileEditor';
import { ToastProvider } from './context/ToastContext';
const AuthGuard = ({ children }) => {
    const [checking, setChecking] = useState(true);
    const [authenticated, setAuthenticated] = useState(false);
    useEffect(() => {
        fetch('/api/v1/auth/me', { credentials: 'include' })
            .then((r) => {
            setAuthenticated(r.ok);
            setChecking(false);
        })
            .catch(() => {
            setAuthenticated(false);
            setChecking(false);
        });
    }, []);
    if (checking)
        return _jsx("div", { className: "p-4", children: "Loading\u2026" });
    if (!authenticated)
        return _jsx(Navigate, { to: "/login", replace: true });
    return children;
};
const App = () => (_jsx(ToastProvider, { children: _jsx(BrowserRouter, { children: _jsxs(Routes, { children: [_jsx(Route, { path: "/login", element: _jsx(AuthPage, {}) }), _jsx(Route, { path: "/", element: _jsx(HomePage, {}) }), _jsx(Route, { path: "/files/:id/edit", element: _jsx(AuthGuard, { children: _jsx(FileEditor, {}) }) }), _jsx(Route, { path: "*", element: _jsx(Navigate, { to: "/", replace: true }) })] }) }) }));
export default App;
