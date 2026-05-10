import React, { useEffect, useState } from 'react';
import { format } from 'date-fns';

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
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [restoringId, setRestoringId] = useState<string | null>(null);

  const token = localStorage.getItem('token');

  const fetchVersions = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`/api/files/${fileId}/versions`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      if (!res.ok) {
        throw new Error(`Error ${res.status}`);
      }
      const data: Version[] = await res.json();
      setVersions(data);
    } catch (err) {
      setError((err as Error).message || 'Error fetching versions');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchVersions();
  }, [fileId, token]);

  const handleRestore = async (id: string) => {
    setRestoringId(id);
    try {
      const res = await fetch(`/api/files/${fileId}/versions/${id}/restore`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      if (!res.ok) {
        throw new Error(`Error ${res.status}`);
      }
      await fetchVersions();
    } catch (err) {
      setError((err as Error).message || 'Error restoring version');
    } finally {
      setRestoringId(null);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex justify-end">
      <div className="w-80 bg-white p-4 h-full overflow-auto">
        <button className="text-right mb-4" onClick={onClose} aria-label="Close">
          ✕
        </button>
        <h2 className="text-xl font-semibold mb-2">Versions</h2>
        {loading && <p>Loading...</p>}
        {error && <p className="text-red-500">{error}</p>}
        {!loading && !error && versions.length === 0 && <p>No versions available.</p>}
        <ul>
          {versions.map((v) => (
            <li key={v.id} className="border-b py-2 flex justify-between items-center">
              <div>
                <p>{format(new Date(v.timestamp), 'PPpp')}</p>
                <p className="text-sm text-gray-600">{v.email}</p>
                <p className="text-sm text-gray-600">{(v.size / 1024).toFixed(2)} KB</p>
              </div>
              <button
                className="px-2 py-1 bg-blue-500 text-white rounded disabled:opacity-50"
                onClick={() => handleRestore(v.id)}
                disabled={restoringId === v.id}
                aria-label={`Restore version from ${v.email}`}
              >
                {restoringId === v.id ? 'Restoring...' : 'Restore'}
              </button>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
};

export default VersionDrawer;
