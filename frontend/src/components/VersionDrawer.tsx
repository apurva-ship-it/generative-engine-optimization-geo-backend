import React, { useEffect, useState } from 'react';

interface Version {
  id: string;
  timestamp: string;
  size: number;
  email: string;
}

interface VersionDrawerProps {
  fileId: string;
  onClose: () => void;
}

const VersionDrawer: React.FC<VersionDrawerProps> = ({ fileId, onClose }) => {
  const [versions, setVersions] = useState<Version[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [restoringId, setRestoringId] = useState<string | null>(null);

  const fetchVersions = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`/api/v1/files/${fileId}/versions`, {
        credentials: 'include',
      });
      if (!res.ok) throw new Error(`Error ${res.status}`);
      const data: Version[] = await res.json();
      setVersions(data);
    } catch (err) {
      setError((err as Error).message || 'Failed to load versions');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchVersions(); }, [fileId]);

  const handleRestore = async (versionId: string) => {
    setRestoringId(versionId);
    try {
      const res = await fetch(`/api/v1/files/${fileId}/versions/${versionId}/restore`, {
        method: 'POST',
        credentials: 'include',
      });
      if (!res.ok) throw new Error(`Error ${res.status}`);
      await fetchVersions();
    } catch (err) {
      setError((err as Error).message || 'Failed to restore version');
    } finally {
      setRestoringId(null);
    }
  };

  const formatDate = (ts: string) => new Date(ts).toLocaleString();
  const formatSize = (bytes: number) => `${(bytes / 1024).toFixed(1)} KB`;

  return (
    <div
      role="dialog"
      aria-modal="true"
      style={{
        position: 'fixed', inset: 0,
        background: 'rgba(0,0,0,0.45)',
        display: 'flex', justifyContent: 'flex-end',
        zIndex: 1000,
      }}
      onClick={e => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div style={{
        width: 340, background: '#fff', height: '100%',
        overflowY: 'auto', padding: 24, boxShadow: '-4px 0 16px rgba(0,0,0,0.15)',
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
          <h2 style={{ fontSize: 18, fontWeight: 600, margin: 0 }}>Version History</h2>
          <button
            onClick={onClose}
            aria-label="Close"
            style={{
              background: 'none', border: 'none', fontSize: 20,
              cursor: 'pointer', color: '#555', lineHeight: 1,
            }}
          >
            ✕
          </button>
        </div>

        {loading && <p style={{ color: '#888', fontSize: 14 }}>Loading…</p>}
        {error && <p style={{ color: '#c62828', fontSize: 14 }}>{error}</p>}
        {!loading && !error && versions.length === 0 && (
          <p style={{ color: '#888', fontSize: 14 }}>No versions available.</p>
        )}

        <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
          {versions.map(v => (
            <li
              key={v.id}
              style={{
                borderBottom: '1px solid #f0f0f0', padding: '12px 0',
                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              }}
            >
              <div>
                <p style={{ margin: 0, fontSize: 13, color: '#222', fontWeight: 500 }}>
                  {formatDate(v.timestamp)}
                </p>
                <p style={{ margin: '2px 0 0', fontSize: 12, color: '#888' }}>{v.email}</p>
                <p style={{ margin: '2px 0 0', fontSize: 12, color: '#888' }}>{formatSize(v.size)}</p>
              </div>
              <button
                onClick={() => handleRestore(v.id)}
                disabled={restoringId === v.id}
                aria-label={`Restore version from ${formatDate(v.timestamp)}`}
                style={{
                  padding: '6px 14px',
                  background: restoringId === v.id ? '#90caf9' : '#1976d2',
                  color: '#fff', border: 'none', borderRadius: 6,
                  cursor: restoringId === v.id ? 'not-allowed' : 'pointer',
                  fontSize: 13, fontWeight: 500, whiteSpace: 'nowrap',
                }}
              >
                {restoringId === v.id ? 'Restoring…' : 'Restore'}
              </button>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
};

export default VersionDrawer;
