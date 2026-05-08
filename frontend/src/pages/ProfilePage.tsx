import React, { useState } from 'react';
import UserAvatar from '../components/UserAvatar';

interface User {
  id: string;
  name: string;
  email: string;
  avatarUrl?: string;
}

const ProfilePage: React.FC<{ user: User }> = ({ user }) => {
  const [currentUser, setCurrentUser] = useState(user);

  return (
    <div style={{ maxWidth: 600, margin: '0 auto', padding: 24 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
        <UserAvatar name={currentUser.name} avatarUrl={currentUser.avatarUrl} size="lg" />
        <div>
          <h1 style={{ margin: 0 }}>{currentUser.name}</h1>
          <p style={{ margin: 0, color: '#666' }}>{currentUser.email}</p>
        </div>
      </div>

      <section style={{ marginTop: 32 }}>
        <h2>Profile Settings</h2>
        {/* Avatar upload will be added here by the Developer Agent */}
      </section>
    </div>
  );
};

export default ProfilePage;
