import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
const FileEditorPage = () => {
    const { fileId } = useParams();
    const [content, setContent] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [saving, setSaving] = useState(false);
    const [versionId, setVersionId] = useState('');
    useEffect(() => {
        if (!fileId)
            return;
        setLoading(true);
        fetch(`/api/v1/files/${fileId}/content`, { credentials: 'include' })
            .then(async (res) => {
            if (!res.ok) {
                const txt = await res.text();
                throw new Error(txt || 'Failed to load file');
            }
            return res.json();
        })
            .then(data => {
            setContent(data.content);
            setVersionId(data.version_id);
        })
            .catch(err => setError(err.message))
            .finally(() => setLoading(false));
    }, [fileId]);
    const handleSave = async () => {
        if (!fileId)
            return;
        setSaving(true);
        try {
            const res = await fetch(`/api/v1/files/${fileId}/content`, {
                method: 'PUT',
                headers: { 'Content-Type': 'text/plain' },
                credentials: 'include',
                body: content,
            });
            const data = (await res.json());
            if (!res.ok) {
                throw new Error('Save failed');
            }
            setVersionId(data.version_id);
        }
        catch (e) {
            setError(e.message || 'Network error');
        }
        finally {
            setSaving(false);
        }
    };
    if (loading)
        return _jsx("p", { className: "p-6 text-center", children: "Loading file\u2026" });
    if (error)
        return _jsxs("p", { className: "p-6 text-red-600", children: ["Error: ", error] });
    return (_jsxs("div", { className: "p-6 max-w-4xl mx-auto", children: [_jsxs("h2", { className: "text-xl font-semibold mb-4", children: ["Editing file ", fileId] }), _jsx("textarea", { className: "w-full h-64 p-2 border rounded", value: content, onChange: e => setContent(e.target.value), disabled: saving }), _jsxs("div", { className: "mt-4 flex items-center", children: [_jsx("button", { onClick: handleSave, disabled: saving, className: `px-4 py-2 rounded text-white ${saving ? 'bg-gray-400' : 'bg-blue-600'} mr-2`, children: saving ? 'Saving…' : 'Save' }), versionId && (_jsxs("span", { className: "text-sm text-gray-600", children: ["Last Version ID: ", versionId] }))] })] }));
};
export default FileEditorPage;
