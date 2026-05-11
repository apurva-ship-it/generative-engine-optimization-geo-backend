import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState } from 'react';
const MAX_FILES = 5;
const MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024; // 50 MB
const UploadDropzone = ({ onFilesAccepted }) => {
    const [files, setFiles] = useState([]);
    const [error, setError] = useState(null);
    const handleDrop = (e) => {
        e.preventDefault();
        e.stopPropagation();
        const droppedFiles = Array.from(e.dataTransfer.files);
        const filtered = droppedFiles.filter(file => {
            if (file.size > MAX_FILE_SIZE_BYTES) {
                setError(`File ${file.name} exceeds 50 MB size limit.`);
                return false;
            }
            return true;
        });
        if (filtered.length + files.length > MAX_FILES) {
            setError(`Cannot upload more than ${MAX_FILES} files at a time.`);
            return;
        }
        const newFiles = [...files, ...filtered];
        setFiles(newFiles);
        setError(null);
        onFilesAccepted(newFiles);
    };
    const handleDragOver = (e) => {
        e.preventDefault();
        e.stopPropagation();
    };
    return (_jsxs("div", { className: "border-2 border-dashed border-gray-300 rounded-md p-6 text-center", onDrop: handleDrop, onDragOver: handleDragOver, role: "region", "aria-label": "File upload dropzone", children: [_jsx("p", { className: "mb-2", children: "Drag & drop files here, or click to select." }), _jsx("input", { type: "file", multiple: true, accept: "*/*", className: "hidden", onChange: e => {
                    const inputFiles = Array.from(e.target.files ?? []);
                    const filtered = inputFiles.filter(file => file.size <= MAX_FILE_SIZE_BYTES);
                    if (filtered.length + files.length > MAX_FILES) {
                        setError(`Cannot upload more than ${MAX_FILES} files at a time.`);
                        return;
                    }
                    const newFiles = [...files, ...filtered];
                    setFiles(newFiles);
                    setError(null);
                    onFilesAccepted(newFiles);
                }, "aria-label": "File selector" }), error && _jsx("p", { className: "text-red-500", children: error }), _jsx("ul", { className: "mt-4 text-left max-h-40 overflow-y-auto", children: files.map((file, i) => (_jsxs("li", { className: "text-sm", children: [file.name, " \u2013 ", Math.round(file.size / 1024), " KB"] }, i))) })] }));
};
export default UploadDropzone;
