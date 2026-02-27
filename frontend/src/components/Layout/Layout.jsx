import React from 'react';
import Header from './Header';
import Sidebar from './Sidebar';

const Layout = ({ children }) => {
  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Header />
      <div style={{ display: 'flex', flex: 1 }}>
        <Sidebar />
        <main style={{ flex: 1, padding: '2rem', overflowY: 'auto', backgroundColor: 'var(--bg-color)' }}>
          {children}
        </main>
      </div>
    </div>
  );
};

export default Layout;
