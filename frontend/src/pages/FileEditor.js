import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
const FileEditor = () => {
    const { id } = useParams();
    const navigate = useNavigate();
    const [file, setFile] = useState(null);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState('');
    const [successMsg, setSuccessMsg] = useState('');
    useEffect(() => {
        if (!id) {
            navigate('/');
            return;
        }
        fetch('/api/v1/auth/me', { credentials: 'include' })
            .then(r => { if (!r.ok)
            throw new Error('unauth'); })
            .catch(() => navigate('/login'));
        fetch(`/api/v1/files/${id}/content`, { credentials: 'include' })
            .then(async (res) => {
            if (!res.ok) {
                const data = await res.json().catch(() => ({}));
                throw new Error(data.detail || data.error || 'Failed to load file');
            }
            return res.json();
        })
            .then(data => setFile(data))
            .catch(e => setError(e.message))
            .finally(() => setLoading(false));
    }, [id, navigate]);
    const handleSave = async () => {
        if (!file || !id)
            return;
        setSaving(true);
        setError('');
        setSuccessMsg('');
        try {
            const formData = new FormData();
            const blob = new Blob([file.content], { type: 'text/plain' });
            formData.append('file', blob, file.name || 'file.txt');
            const res = await fetch(`/api/v1/files/${id}/content`, {
                method: 'PUT',
                credentials: 'include',
                body: formData,
            });
            if (!res.ok) {
                const data = await res.json().catch(() => ({}));
                throw new Error(data.detail || data.error || 'Save failed');
            }
            const data = await res.json();
            setSuccessMsg(`Saved. Version: ${data.version_id ?? 'OK'}`);
            setTimeout(() => navigate('/'), 1500);
        }
        catch (e) {
            setError(e.message);
        }
        finally {
            setSaving(false);
        }
    };
    if (loading)
        return (_jsx("div", { style: { padding: 24, color: '#555' }, children: "Loading\u2026" }));
    if (error && !file)
        return (_jsxs("div", { style: { padding: 24, color: '#c62828' }, children: ["Error: ", error] }));
    return (_jsx("div", { style: { background: '#f5f5f5', minHeight: '100vh', padding: 24 }, children: _jsxs("div", { style: {
                maxWidth: 800, margin: '0 auto', background: '#fff',
                borderRadius: 10, padding: '32px 36px',
                boxShadow: '0 2px 16px rgba(0,0,0,0.1)',
            }, children: [_jsxs("h1", { style: { fontSize: 20, marginBottom: 20, color: '#222' }, children: ["Edit \u2014 ", file?.name || id] }), _jsx("textarea", { value: file?.content ?? '', onChange: e => file && setFile({ ...file, content: e.target.value }), rows: 24, style: {
                        width: '100%', padding: 12, fontSize: 13, fontFamily: 'monospace',
                        border: '1px solid #ddd', borderRadius: 6, resize: 'vertical',
                        boxSizing: 'border-box', lineHeight: 1.6,
                    } }), error && (_jsx("div", { style: {
                        marginTop: 10, padding: '8px 12px', background: '#ffeef0',
                        border: '1px solid #f5c6cb', borderRadius: 6, color: '#c62828', fontSize: 13,
                    }, children: error })), successMsg && (_jsx("div", { style: {
                        marginTop: 10, padding: '8px 12px', background: '#e8f5e9',
                        border: '1px solid #c8e6c9', borderRadius: 6, color: '#2e7d32', fontSize: 13,
                    }, children: successMsg })), _jsxs("div", { style: { marginTop: 16, display: 'flex', gap: 10 }, children: [_jsx("button", { onClick: handleSave, disabled: saving, style: {
                                padding: '8px 24px', background: saving ? '#90caf9' : '#1976d2',
                                color: '#fff', border: 'none', borderRadius: 6,
                                cursor: saving ? 'not-allowed' : 'pointer', fontSize: 14, fontWeight: 600,
                            }, children: saving ? 'Saving…' : 'Save' }), _jsx("button", { onClick: () => navigate('/'), style: {
                                padding: '8px 20px', background: '#f5f5f5',
                                color: '#555', border: '1px solid #ccc', borderRadius: 6,
                                cursor: 'pointer', fontSize: 14,
                            }, children: "Cancel" })] })] }) }));
};
export default FileEditor;
