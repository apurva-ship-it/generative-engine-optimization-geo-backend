import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import ProgressBar from '../components/ProgressBar';
import Toast from '../components/Toast';
const MAX_SIZE = 1 * 1024 * 1024; // 1 MB
const HomePage = () => {
    const navigate = useNavigate();
    const [preview, setPreview] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const [fileName, setFileName] = useState('');
    const [progress, setProgress] = useState(0);
    const [showToast, setShowToast] = useState(false);
    const inputRef = useRef(null);
    // Redirect to /login if no auth cookie is present
    useEffect(() => {
        fetch('/api/v1/auth/me', { credentials: 'include' })
            .then(r => { if (!r.ok)
            navigate('/login'); })
            .catch(() => navigate('/login'));
    }, [navigate]);
    const handleFileChange = (e) => {
        setPreview('');
        setError('');
        const file = e.target.files?.[0];
        if (!file)
            return;
        const ext = file.name.split('.').pop()?.toLowerCase();
        if (ext !== 'txt') {
            setError('Only .txt files are supported.');
            if (inputRef.current)
                inputRef.current.value = '';
            return;
        }
        if (file.size > MAX_SIZE) {
            setError(`File is too large (${(file.size / 1024).toFixed(0)} KB). Maximum size is 1 MB.`);
            if (inputRef.current)
                inputRef.current.value = '';
            return;
        }
        setFileName(file.name);
        // Immediate local preview using FileReader
        const reader = new FileReader();
        reader.onload = () => setPreview(reader.result);
        reader.readAsText(file);
    };
    const handleUpload = async () => {
        const file = inputRef.current?.files?.[0];
        if (!file)
            return;
        setLoading(true);
        setError('');
        setProgress(0);
        try {
            const formData = new FormData();
            formData.append('file', file);
            // Use XMLHttpRequest to track progress
            await new Promise((resolve, reject) => {
                const xhr = new XMLHttpRequest();
                xhr.open('POST', '/api/v1/files/upload');
                xhr.withCredentials = true;
                xhr.upload.onprogress = (e) => {
                    if (e.lengthComputable) {
                        const percent = Math.round((e.loaded / e.total) * 100);
                        setProgress(percent);
                    }
                };
                xhr.onload = () => {
                    if (xhr.status >= 200 && xhr.status < 300) {
                        resolve();
                    }
                    else {
                        reject(new Error('Upload failed'));
                    }
                };
                xhr.onerror = () => reject(new Error('Network error'));
                xhr.send(formData);
            });
            // After successful upload, fetch preview content
            const res = await fetch('/api/v1/files/upload', {
                method: 'POST',
                credentials: 'include',
                body: formData,
            });
            const data = await res.json().catch(() => ({}));
            if (!res.ok) {
                setError(data.error || 'Upload failed');
                setPreview('');
            }
            else {
                setPreview(data.content);
                setShowToast(true);
            }
        }
        catch (err) {
            setError(err.message || 'Network error — is the backend running?');
        }
        finally {
            setLoading(false);
            setProgress(0);
        }
    };
    const handleLogout = async () => {
        await fetch('/api/v1/auth/logout', { method: 'POST', credentials: 'include' });
        navigate('/login');
    };
    const card = {
        maxWidth: 700, margin: '40px auto', background: '#fff',
        borderRadius: 10, padding: '32px 36px',
        boxShadow: '0 2px 16px rgba(0,0,0,0.1)',
    };
    return (_jsx("div", { style: { background: '#f5f5f5', minHeight: '100vh' }, children: _jsxs("div", { style: card, children: [_jsxs("div", { style: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 28 }, children: [_jsx("h1", { style: { fontSize: 22, color: '#222' }, children: "Home" }), _jsx("button", { onClick: handleLogout, style: {
                                padding: '6px 16px', background: '#fff', border: '1px solid #ccc',
                                borderRadius: 6, cursor: 'pointer', fontSize: 13, color: '#555',
                            }, children: "Logout" })] }), _jsxs("div", { style: {
                        border: '2px dashed #ccc', borderRadius: 8, padding: 24,
                        textAlign: 'center', marginBottom: 20, background: '#fafafa',
                    }, children: [_jsxs("p", { style: { marginBottom: 12, color: '#666', fontSize: 14 }, children: ["Select a ", _jsx("strong", { children: ".txt" }), " file (max 1 MB) to preview its contents"] }), _jsx("input", { ref: inputRef, type: "file", accept: ".txt", onChange: handleFileChange, style: { marginBottom: 12 } }), _jsx("br", {}), _jsx("button", { onClick: handleUpload, disabled: !fileName || loading, style: {
                                padding: '8px 24px', background: !fileName || loading ? '#bbb' : '#1976d2',
                                color: '#fff', border: 'none', borderRadius: 6,
                                cursor: !fileName || loading ? 'not-allowed' : 'pointer',
                                fontSize: 14, fontWeight: 600,
                            }, children: loading ? 'Uploading…' : 'Upload & Preview' }), loading && _jsx(ProgressBar, { progress: progress })] }), error && (_jsxs("div", { style: {
                        background: '#ffeef0', border: '1px solid #f5c6cb',
                        borderRadius: 6, padding: '10px 14px', marginBottom: 16,
                        color: '#c62828', fontSize: 14,
                    }, children: ["\u26A0 ", error] })), preview && (_jsxs("div", { children: [_jsxs("div", { style: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }, children: [_jsxs("strong", { style: { fontSize: 14, color: '#444' }, children: ["Preview \u2014 ", fileName] }), _jsxs("span", { style: { fontSize: 12, color: '#888' }, children: [preview.length, " chars"] })] }), _jsx("pre", { style: {
                                background: '#f8f8f8', border: '1px solid #e0e0e0',
                                borderRadius: 6, padding: 16, maxHeight: 400,
                                overflowY: 'auto', fontSize: 13, lineHeight: 1.6,
                                whiteSpace: 'pre-wrap', wordBreak: 'break-word',
                            }, children: preview })] })), showToast && _jsx(Toast, { message: "Upload successful", onClose: () => setShowToast(false) })] }) }));
};
export default HomePage;
