import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState } from 'react';
import UserAvatar from '../components/UserAvatar';
const ProfilePage = ({ user }) => {
    const [currentUser] = useState(user);
    return (_jsxs("div", { style: { maxWidth: 600, margin: '0 auto', padding: 24 }, children: [_jsxs("div", { style: { display: 'flex', alignItems: 'center', gap: 16 }, children: [_jsx(UserAvatar, { name: currentUser.name, avatarUrl: currentUser.avatarUrl, size: "lg" }), _jsxs("div", { children: [_jsx("h1", { style: { margin: 0 }, children: currentUser.name }), _jsx("p", { style: { margin: 0, color: '#666' }, children: currentUser.email })] })] }), _jsx("section", { style: { marginTop: 32 }, children: _jsx("h2", { children: "Profile Settings" }) })] }));
};
export default ProfilePage;
