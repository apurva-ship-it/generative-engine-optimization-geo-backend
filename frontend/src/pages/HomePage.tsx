import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';

const MAX_SIZE = 1 * 1024 * 1024; // 1 MB

const HomePage: React.FC = () => {
  const navigate = useNavigate();
  const [preview, setPreview] = useState<string>('');
  const [error, setError] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [fileName, setFileName] = useState<string>('');
  const inputRef = useRef<HTMLInputElement>(null);

  // Redirect to /login if no auth cookie is present
  useEffect(() => {
    fetch('/api/v1/users/me', { credentials: 'include' })
      .then(r => { if (!r.ok) navigate('/login'); })
      .catch(() => navigate('/login'));
  }, [navigate]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setPreview('');
    setError('');
    const file = e.target.files?.[0];
    if (!file) return;

    const ext = file.name.split('.').pop()?.toLowerCase();
    if (ext !== 'txt') {
      setError('Only .txt files are supported.');
      if (inputRef.current) inputRef.current.value = '';
      return;
    }
    if (file.size > MAX_SIZE) {
      setError(`File is too large (${(file.size / 1024).toFixed(0)} KB). Maximum size is 1 MB.`);
      if (inputRef.current) inputRef.current.value = '';
      return;
    }

    setFileName(file.name);

    // Immediate local preview using FileReader
    const reader = new FileReader();
    reader.onload = () => setPreview(reader.result as string);
    reader.readAsText(file);
  };

  const handleUpload = async () => {
    const file = inputRef.current?.files?.[0];
    if (!file) return;

    setLoading(true);
    setError('');
    try {
      const formData = new FormData();
      formData.append('file', file);
      const res = await fetch('/api/v1/files/upload', {
        method: 'POST',
        credentials: 'include',
        body: formData,
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        setError(data.error || 'Upload failed');
        setPreview('');
        return;
      }
      setPreview(data.content);
    } catch {
      setError('Network error — is the backend running?');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    await fetch('/api/v1/auth/logout', { method: 'POST', credentials: 'include' });
    navigate('/login');
  };

  const card: React.CSSProperties = {
    maxWidth: 700, margin: '40px auto', background: '#fff',
    borderRadius: 10, padding: '32px 36px',
    boxShadow: '0 2px 16px rgba(0,0,0,0.1)',
  };

  return (
    <div style={{ background: '#f5f5f5', minHeight: '100vh' }}>
      <div style={card}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 28 }}>
          <h1 style={{ fontSize: 22, color: '#222' }}>Home</h1>
          <button
            onClick={handleLogout}
            style={{
              padding: '6px 16px', background: '#fff', border: '1px solid #ccc',
              borderRadius: 6, cursor: 'pointer', fontSize: 13, color: '#555',
            }}
          >
            Logout
          </button>
        </div>

        <div style={{
          border: '2px dashed #ccc', borderRadius: 8, padding: 24,
          textAlign: 'center', marginBottom: 20, background: '#fafafa',
        }}>
          <p style={{ marginBottom: 12, color: '#666', fontSize: 14 }}>
            Select a <strong>.txt</strong> file (max 1 MB) to preview its contents
          </p>
          <input
            ref={inputRef}
            type="file"
            accept=".txt"
            onChange={handleFileChange}
            style={{ marginBottom: 12 }}
          />
          <br />
          <button
            onClick={handleUpload}
            disabled={!fileName || loading}
            style={{
              padding: '8px 24px', background: !fileName || loading ? '#bbb' : '#1976d2',
              color: '#fff', border: 'none', borderRadius: 6,
              cursor: !fileName || loading ? 'not-allowed' : 'pointer',
              fontSize: 14, fontWeight: 600,
            }}
          >
            {loading ? 'Uploading…' : 'Upload & Preview'}
          </button>
        </div>

        {error && (
          <div style={{
            background: '#ffeef0', border: '1px solid #f5c6cb',
            borderRadius: 6, padding: '10px 14px', marginBottom: 16,
            color: '#c62828', fontSize: 14,
          }}>
            ⚠ {error}
          </div>
        )}

        {preview && (
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
              <strong style={{ fontSize: 14, color: '#444' }}>Preview — {fileName}</strong>
              <span style={{ fontSize: 12, color: '#888' }}>{preview.length} chars</span>
            </div>
            <pre style={{
              background: '#f8f8f8', border: '1px solid #e0e0e0',
              borderRadius: 6, padding: 16, maxHeight: 400,
              overflowY: 'auto', fontSize: 13, lineHeight: 1.6,
              whiteSpace: 'pre-wrap', wordBreak: 'break-word',
            }}>
              {preview}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
};

export default HomePage;
