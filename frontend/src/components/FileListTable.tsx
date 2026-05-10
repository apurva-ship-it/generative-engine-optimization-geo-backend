import React from "react";

export interface FileInfo {
  name: string;
  size: number; // bytes
  lastModified: string | Date;
  versionCount: number;
}

interface FileListTableProps {
  files: FileInfo[];
}

/**
 * Responsive table that displays a list of files.
 * At screens < 640px (Tailwind's `sm`) the table becomes horizontally scrollable.
 */
const FileListTable: React.FC<FileListTableProps> = ({ files }) => {
  const formatSize = (size: number): string => {
    if (size < 1024) return `${size} B`;
    const i = Math.floor(Math.log(size) / Math.log(1024));
    const sizes = ["B", "KB", "MB", "GB", "TB"];
    return `${(size / Math.pow(1024, i)).toFixed(1)} ${sizes[i]}`;
  };

  const formatDate = (date: string | Date): string => {
    const d = new Date(date);
    return d.toLocaleString();
  };

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full border-collapse">
        <thead>
          <tr className="bg-gray-100">
            <th className="p-2 text-left text-sm font-medium text-gray-700">Name</th>
            <th className="p-2 text-left text-sm font-medium text-gray-700">Size</th>
            <th className="p-2 text-left text-sm font-medium text-gray-700">Last Modified</th>
            <th className="p-2 text-left text-sm font-medium text-gray-700">Versions</th>
          </tr>
        </thead>
        <tbody>
          {files.map((file) => (
            <tr key={file.name} className="border-b border-gray-200 even:bg-gray-50">
              <td className="p-2 text-sm text-gray-900">{file.name}</td>
              <td className="p-2 text-sm text-gray-900">{formatSize(file.size)}</td>
              <td className="p-2 text-sm text-gray-900">{formatDate(file.lastModified)}</td>
              <td className="p-2 text-sm text-gray-900">{file.versionCount}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default FileListTable;
