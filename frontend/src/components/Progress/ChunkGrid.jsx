import React from 'react';

const ChunkGrid = ({ chunks }) => {
  if (!chunks || chunks.length === 0) return null;

  return (
    <div style={{ marginTop: '1rem' }}>
      <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>分段状态：</div>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
        {chunks.map((chunk, idx) => (
          <div 
            key={idx}
            style={{
              width: '32px',
              height: '32px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              borderRadius: '4px',
              fontSize: '0.75rem',
              backgroundColor: chunk.status === 'done' ? 'var(--success)' : 
                               chunk.status === 'error' ? 'var(--error)' : 'var(--bg-tertiary)',
              color: 'white',
              opacity: chunk.status === 'done' ? 1 : 0.6
            }}
            title={chunk.status}
          >
            {idx + 1}
          </div>
        ))}
      </div>
    </div>
  );
};

export default ChunkGrid;
