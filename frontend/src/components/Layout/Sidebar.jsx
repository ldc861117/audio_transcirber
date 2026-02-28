import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, FileAudio, History, Users, Settings, X } from 'lucide-react';
import { motion as Motion, AnimatePresence } from 'framer-motion';

const Sidebar = ({ isOpen, isMobile, closeSidebar }) => {
  const links = [
    { to: '/', label: '仪表盘', icon: <LayoutDashboard size={20} /> },
    { to: '/transcribe', label: '新转写', icon: <FileAudio size={20} /> },
    { to: '/history', label: '历史记录', icon: <History size={20} /> },
    { to: '/speakers', label: '声纹库', icon: <Users size={20} /> },
    { to: '/settings', label: '设置', icon: <Settings size={20} /> },
  ];

  const sidebarVariants = {
    open: {
      x: 0,
      width: '240px',
      transition: { type: 'spring', stiffness: 300, damping: 30 }
    },
    closed: {
      x: isMobile ? '-100%' : 0,
      width: isMobile ? '240px' : '80px',
      transition: { type: 'spring', stiffness: 300, damping: 30 }
    }
  };

  return (
    <Motion.aside
      initial={false}
      animate={isOpen ? 'open' : 'closed'}
      variants={sidebarVariants}
      style={{
        backgroundColor: 'var(--bg-secondary)',
        height: 'calc(100vh - 64px)',
        padding: '1rem',
        borderRight: '1px solid var(--bg-tertiary)',
        position: isMobile ? 'fixed' : 'relative',
        top: 0,
        left: 0,
        zIndex: 100,
        overflowX: 'hidden'
      }}
    >
      {isMobile && isOpen && (
        <button
          onClick={closeSidebar}
          style={{
            position: 'absolute',
            right: '1rem',
            top: '1rem',
            backgroundColor: 'transparent',
            color: 'var(--text-secondary)'
          }}
        >
          <X size={24} />
        </button>
      )}

      <nav style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginTop: isMobile ? '3rem' : '0' }}>
        {links.map(link => (
          <NavLink
            key={link.to}
            to={link.to}
            onClick={() => isMobile && closeSidebar()}
            style={({ isActive }) => ({
              display: 'flex',
              alignItems: 'center',
              gap: '0.75rem',
              padding: '0.75rem 1rem',
              borderRadius: 'var(--border-radius)',
              textDecoration: 'none',
              color: isActive ? 'white' : 'var(--text-secondary)',
              backgroundColor: isActive ? 'var(--bg-tertiary)' : 'transparent',
              transition: 'var(--transition)',
              whiteSpace: 'nowrap'
            })}
            className="sidebar-link"
          >
            <span style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minWidth: '20px' }}>
              {link.icon}
            </span>
            {(isOpen || isMobile) && <span>{link.label}</span>}
          </NavLink>
        ))}
      </nav>
    </Motion.aside>
  );
};

export default Sidebar;
