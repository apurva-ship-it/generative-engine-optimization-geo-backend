import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
/**
 * Responsive table that displays a list of files.
 * At screens < 640px (Tailwind's `sm`) the table becomes horizontally scrollable.
 */
const FileListTable = ({ files }) => {
    const formatSize = (size) => {
        if (size < 1024)
            return `${size} B`;
        const i = Math.floor(Math.log(size) / Math.log(1024));
        const sizes = ["B", "KB", "MB", "GB", "TB"];
        return `${(size / Math.pow(1024, i)).toFixed(1)} ${sizes[i]}`;
    };
    const formatDate = (date) => {
        const d = new Date(date);
        return d.toLocaleString();
    };
    return (_jsx("div", { className: "overflow-x-visible sm:overflow-x-auto", children: _jsxs("table", { className: "min-w-full border-collapse", children: [_jsx("thead", { children: _jsxs("tr", { className: "bg-gray-100", children: [_jsx("th", { className: "p-2 text-left text-sm font-medium text-gray-700", children: "Name" }), _jsx("th", { className: "p-2 text-left text-sm font-medium text-gray-700", children: "Size" }), _jsx("th", { className: "p-2 text-left text-sm font-medium text-gray-700", children: "Last Modified" }), _jsx("th", { className: "p-2 text-left text-sm font-medium text-gray-700", children: "Versions" })] }) }), _jsx("tbody", { children: files.map((file) => (_jsxs("tr", { className: "border-b border-gray-200 even:bg-gray-50", children: [_jsx("td", { className: "p-2 text-sm text-gray-900", children: file.name }), _jsx("td", { className: "p-2 text-sm text-gray-900", children: formatSize(file.size) }), _jsx("td", { className: "p-2 text-sm text-gray-900", children: formatDate(file.lastModified) }), _jsx("td", { className: "p-2 text-sm text-gray-900", children: file.versionCount })] }, file.name))) })] }) }));
};
export default FileListTable;
