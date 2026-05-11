import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { createContext, useContext, useState, useCallback } from 'react';
const ToastContext = createContext(undefined);
let toastId = 0;
export const ToastProvider = ({ children }) => {
    const [toasts, setToasts] = useState([]);
    const removeToast = useCallback((id) => {
        setToasts((prev) => prev.filter((t) => t.id !== id));
    }, []);
    const showToast = useCallback((message) => {
        const id = ++toastId;
        setToasts((prev) => [...prev, { id, message }]);
        setTimeout(() => removeToast(id), 3000);
    }, [removeToast]);
    return (_jsxs(ToastContext.Provider, { value: { showToast }, children: [children, _jsx("div", { className: "fixed top-4 right-4 flex flex-col space-y-2 z-50 pointer-events-none", children: toasts.map((t) => (_jsx("div", { className: "bg-green-600 text-white px-4 py-2 rounded shadow-md pointer-events-auto", children: t.message }, t.id))) })] }));
};
export const useToast = () => {
    const ctx = useContext(ToastContext);
    if (!ctx) {
        throw new Error('useToast must be used within a ToastProvider');
    }
    return ctx;
};
