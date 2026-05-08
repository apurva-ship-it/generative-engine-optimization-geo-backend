import React from 'react';
import ProfilePage from './pages/ProfilePage';

const mockUser = {
  id: 'usr_001',
  name: 'Ashish Gupta',
  email: 'ashish@example.com',
};

const App: React.FC = () => <ProfilePage user={mockUser} />;

export default App;
