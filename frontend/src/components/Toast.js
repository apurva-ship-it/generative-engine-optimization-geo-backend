import { jsx as _jsx } from "react/jsx-runtime";
import { useEffect } from 'react';
const Toast = ({ message, onClose }) => {
    useEffect(() => {
        const timer = setTimeout(onClose, 3000);
        return () => clearTimeout(timer);
    }, [onClose]);
    return (_jsx("div", { className: "fixed top-4 right-4 bg-green-600 text-white px-4 py-2 rounded shadow-md", role: "alert", children: message }));
};
export default Toast;
