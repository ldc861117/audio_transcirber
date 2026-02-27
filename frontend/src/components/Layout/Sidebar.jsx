import React from 'react';
import { NavLink } from 'react-router-dom';

const Sidebar = () => {
  const links = [
    { to: '/', label: '仪表盘', icon: '📊' },
    { to: '/transcribe', label: '新转写', icon: '🚀' },
    { to: '/history', label: '历史记录', icon: '🕒' },
    { to: '/speakers', label: '声纹库', icon: '👥' },
    { to: '/settings', label: '设置', icon: '⚙️' },
  ];

  return (
    <aside style={{
      width: '240px',
      backgroundColor: 'var(--bg-secondary)',
      height: 'calc(100vh - 64px)',
      padding: '1rem',
      borderRight: '1px solid var(--bg-tertiary)'
    }}>
      <nav style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
        {links.map(link => (
          <NavLink
            key={link.to}
            to={link.to}
            style={({ isActive }) => ({
              display: 'flex',
              alignItems: 'center',
              gap: '0.75rem',
              padding: '0.75rem 1rem',
              borderRadius: 'var(--border-radius)',
              textDecoration: 'none',
              color: isActive ? 'white' : 'var(--text-secondary)',
              backgroundColor: isActive ? 'var(--bg-tertiary)' : 'transparent',
              transition: 'var(--transition)'
            })}
          >
            <span>{link.icon}</span>
            <span>{link.label}</span>
          </NavLink>
        ))}
      </nav>
    </aside>
  );
};

export default Sidebar;
