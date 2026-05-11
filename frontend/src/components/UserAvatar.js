import { jsx as _jsx } from "react/jsx-runtime";
const SIZE_MAP = { sm: 32, md: 48, lg: 96 };
const UserAvatar = ({ name, avatarUrl, size = 'md' }) => {
    const px = SIZE_MAP[size];
    const initials = name
        .split(' ')
        .map((n) => n[0])
        .join('')
        .toUpperCase()
        .slice(0, 2);
    if (avatarUrl) {
        return (_jsx("img", { src: avatarUrl, alt: name, width: px, height: px, style: { borderRadius: '50%', objectFit: 'cover' } }));
    }
    return (_jsx("div", { style: {
            width: px,
            height: px,
            borderRadius: '50%',
            background: '#6366f1',
            color: '#fff',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: px / 3,
            fontWeight: 600,
        }, children: initials }));
};
export default UserAvatar;
