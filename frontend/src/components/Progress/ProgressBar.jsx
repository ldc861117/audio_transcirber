import React from 'react';

const ProgressBar = ({ progress, status }) => {
  return (
    <div style={{ margin: '1.5rem 0' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem', fontSize: '0.875rem' }}>
        <span>{status || '处理中...'}</span>
        <span>{Math.round(progress)}%</span>
      </div>
      <div style={{ height: '8px', backgroundColor: 'var(--bg-tertiary)', borderRadius: '4px', overflow: 'hidden' }}>
        <div 
          style={{ 
            height: '100%', 
            width: `${progress}%`, 
            background: 'var(--accent-gradient)',
            transition: 'width 0.3s ease'
          }} 
        />
      </div>
    </div>
  );
};

export default ProgressBar;
