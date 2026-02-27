import React, { useRef } from 'react';

const DropZone = ({ onFileSelect, selectedFile, onCancel }) => {
  const fileInputRef = useRef(null);

  const handleDragOver = (e) => {
    e.preventDefault();
    e.currentTarget.style.borderColor = 'var(--accent-primary)';
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.currentTarget.style.borderColor = 'var(--bg-tertiary)';
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.currentTarget.style.borderColor = 'var(--bg-tertiary)';
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      onFileSelect(e.dataTransfer.files[0]);
    }
  };

  return (
    <div
      onClick={() => !selectedFile && fileInputRef.current.click()}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      style={{
        border: '2px dashed var(--bg-tertiary)',
        borderRadius: 'var(--border-radius)',
        padding: '3rem',
        textAlign: 'center',
        cursor: selectedFile ? 'default' : 'pointer',
        transition: 'var(--transition)',
        backgroundColor: selectedFile ? 'rgba(59, 130, 246, 0.05)' : 'transparent',
        position: 'relative'
      }}
    >
      <input
        type="file"
        ref={fileInputRef}
        onChange={(e) => e.target.files[0] && onFileSelect(e.target.files[0])}
        style={{ display: 'none' }}
        accept="audio/*"
      />
      
      {!selectedFile ? (
        <>
          <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>📁</div>
          <h3 style={{ marginBottom: '0.5rem' }}>点击或拖拽音频文件到此处</h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>支持 MP3, WAV, M4A, FLAC 等</p>
        </>
      ) : (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '1rem' }}>
          <div style={{ fontSize: '2rem' }}>🎵</div>
          <div style={{ textAlign: 'left' }}>
            <div style={{ fontWeight: '600' }}>{selectedFile.name}</div>
            <div style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
              {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
            </div>
          </div>
          <button 
            onClick={(e) => { e.stopPropagation(); onCancel(); }}
            style={{ 
              marginLeft: '1rem', 
              backgroundColor: 'var(--bg-tertiary)', 
              color: 'var(--text-primary)',
              padding: '0.5rem 1rem',
              fontSize: '0.75rem'
            }}
          >
            取消
          </button>
        </div>
      )}
    </div>
  );
};

export default DropZone;
