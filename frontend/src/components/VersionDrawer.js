import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useEffect, useState } from 'react';
const VersionDrawer = ({ fileId, onClose }) => {
    const [versions, setVersions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [restoringId, setRestoringId] = useState(null);
    const fetchVersions = async () => {
        setLoading(true);
        setError(null);
        try {
            const res = await fetch(`/api/v1/files/${fileId}/versions`, {
                credentials: 'include',
            });
            if (!res.ok)
                throw new Error(`Error ${res.status}`);
            const data = await res.json();
            setVersions(data);
        }
        catch (err) {
            setError(err.message || 'Failed to load versions');
        }
        finally {
            setLoading(false);
        }
    };
    useEffect(() => { fetchVersions(); }, [fileId]);
    const handleRestore = async (versionId) => {
        setRestoringId(versionId);
        try {
            const res = await fetch(`/api/v1/files/${fileId}/versions/${versionId}/restore`, {
                method: 'POST',
                credentials: 'include',
            });
            if (!res.ok)
                throw new Error(`Error ${res.status}`);
            await fetchVersions();
        }
        catch (err) {
            setError(err.message || 'Failed to restore version');
        }
        finally {
            setRestoringId(null);
        }
    };
    const formatDate = (ts) => new Date(ts).toLocaleString();
    const formatSize = (bytes) => `${(bytes / 1024).toFixed(1)} KB`;
    return (_jsx("div", { role: "dialog", "aria-modal": "true", style: {
            position: 'fixed', inset: 0,
            background: 'rgba(0,0,0,0.45)',
            display: 'flex', justifyContent: 'flex-end',
            zIndex: 1000,
        }, onClick: e => { if (e.target === e.currentTarget)
            onClose(); }, children: _jsxs("div", { style: {
                width: 340, background: '#fff', height: '100%',
                overflowY: 'auto', padding: 24, boxShadow: '-4px 0 16px rgba(0,0,0,0.15)',
            }, children: [_jsxs("div", { style: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }, children: [_jsx("h2", { style: { fontSize: 18, fontWeight: 600, margin: 0 }, children: "Version History" }), _jsx("button", { onClick: onClose, "aria-label": "Close", style: {
                                background: 'none', border: 'none', fontSize: 20,
                                cursor: 'pointer', color: '#555', lineHeight: 1,
                            }, children: "\u2715" })] }), loading && _jsx("p", { style: { color: '#888', fontSize: 14 }, children: "Loading\u2026" }), error && _jsx("p", { style: { color: '#c62828', fontSize: 14 }, children: error }), !loading && !error && versions.length === 0 && (_jsx("p", { style: { color: '#888', fontSize: 14 }, children: "No versions available." })), _jsx("ul", { style: { listStyle: 'none', padding: 0, margin: 0 }, children: versions.map(v => (_jsxs("li", { style: {
                            borderBottom: '1px solid #f0f0f0', padding: '12px 0',
                            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                        }, children: [_jsxs("div", { children: [_jsx("p", { style: { margin: 0, fontSize: 13, color: '#222', fontWeight: 500 }, children: formatDate(v.timestamp) }), _jsx("p", { style: { margin: '2px 0 0', fontSize: 12, color: '#888' }, children: v.email }), _jsx("p", { style: { margin: '2px 0 0', fontSize: 12, color: '#888' }, children: formatSize(v.size) })] }), _jsx("button", { onClick: () => handleRestore(v.id), disabled: restoringId === v.id, "aria-label": `Restore version from ${formatDate(v.timestamp)}`, style: {
                                    padding: '6px 14px',
                                    background: restoringId === v.id ? '#90caf9' : '#1976d2',
                                    color: '#fff', border: 'none', borderRadius: 6,
                                    cursor: restoringId === v.id ? 'not-allowed' : 'pointer',
                                    fontSize: 13, fontWeight: 500, whiteSpace: 'nowrap',
                                }, children: restoringId === v.id ? 'Restoring…' : 'Restore' })] }, v.id))) })] }) }));
};
export default VersionDrawer;
