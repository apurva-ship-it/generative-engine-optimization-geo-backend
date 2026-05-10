import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';

interface FileContentResponse {
  content: string;
  version_id: string;
}

const FileEditorPage: React.FC = () => {
  const { fileId } = useParams<{ fileId: string }>();

  const [content, setContent] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');
  const [saving, setSaving] = useState<boolean>(false);
  const [versionId, setVersionId] = useState<string>('');

  useEffect(() => {
    if (!fileId) return;
    setLoading(true);
    fetch(`/api/v1/files/${fileId}/content`, { credentials: 'include' })
      .then(async res => {
        if (!res.ok) {
          const txt = await res.text();
          throw new Error(txt || 'Failed to load file');
        }
        return res.json() as Promise<FileContentResponse>;
      })
      .then(data => {
        setContent(data.content);
        setVersionId(data.version_id);
      })
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  }, [fileId]);

  const handleSave = async () => {
    if (!fileId) return;
    setSaving(true);
    try {
      const res = await fetch(`/api/v1/files/${fileId}/content`, {
        method: 'PUT',
        headers: { 'Content-Type': 'text/plain' },
        credentials: 'include',
        body: content,
      });
      const data = (await res.json()) as FileContentResponse;
      if (!res.ok) {
        throw new Error('Save failed');
      }
      setVersionId(data.version_id);
    } catch (e: any) {
      setError(e.message || 'Network error');
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <p className="p-6 text-center">Loading file…</p>;
  if (error) return <p className="p-6 text-red-600">Error: {error}</p>;

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h2 className="text-xl font-semibold mb-4">Editing file {fileId}</h2>
      <textarea
        className="w-full h-64 p-2 border rounded"
        value={content}
        onChange={e => setContent(e.target.value)}
        disabled={saving}
      />
      <div className="mt-4 flex items-center">
        <button
          onClick={handleSave}
          disabled={saving}
          className={`px-4 py-2 rounded text-white ${saving ? 'bg-gray-400' : 'bg-blue-600'} mr-2`}
        >{saving ? 'Saving…' : 'Save'}</button>
        {versionId && (
          <span className="text-sm text-gray-600">Last Version ID: {versionId}</span>
        )}
      </div>
    </div>
  );
};

export default FileEditorPage;
