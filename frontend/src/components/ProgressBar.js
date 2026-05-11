import { jsx as _jsx } from "react/jsx-runtime";
const ProgressBar = ({ progress }) => {
    return (_jsx("div", { style: {
            width: '100%',
            backgroundColor: '#e0e0e0',
            borderRadius: 9999,
            height: 16,
            overflow: 'hidden',
            marginTop: 12,
        }, children: _jsx("div", { style: {
                height: '100%',
                width: `${Math.min(100, Math.max(0, progress))}%`,
                backgroundColor: '#1976d2',
                borderRadius: 9999,
                transition: 'width 0.2s ease',
            }, role: "progressbar", "aria-valuenow": progress, "aria-valuemin": 0, "aria-valuemax": 100 }) }));
};
export default ProgressBar;
