import React from 'react';
import { useAuthStore } from '../../stores/authStore';
import { useNavigate } from 'react-router-dom';

const Header = () => {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  return (
    <header style={{
      height: '64px',
      backgroundColor: 'var(--bg-secondary)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '0 2rem',
      borderBottom: '1px solid var(--bg-tertiary)',
      position: 'sticky',
      top: 0,
      zIndex: 100
    }}>
      <div style={{ fontSize: '1.5rem', fontWeight: 'bold', background: 'var(--accent-gradient)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
        AudioTranscriber
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <span>{user?.username}</span>
        <button onClick={handleLogout} style={{ backgroundColor: 'transparent', color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
          退出
        </button>
      </div>
    </header>
  );
};

export default Header;
