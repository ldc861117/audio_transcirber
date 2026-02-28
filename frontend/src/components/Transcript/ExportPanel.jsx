import React, { useState } from 'react';
import { api } from '../../api/client';

const FORMATS = [
  { value: 'txt', label: '📄 TXT', desc: '纯文本' },
  { value: 'srt', label: '🎬 SRT', desc: '字幕文件' },
  { value: 'docx', label: '📘 Word', desc: 'Word 文档' },
  { value: 'pdf', label: '📕 PDF', desc: 'PDF 文档' },
];

const ExportPanel = ({ taskId }) => {
  const [exporting, setExporting] = useState(null);

  if (!taskId) return null;

  const handleExport = async (format) => {
    setExporting(format);
    try {
      const response = await api.exports.download(taskId, format);
      const blob = new Blob([response.data]);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `transcription_${taskId}.${format}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      alert('导出失败: ' + (err.response?.data?.error || err.message));
    } finally {
      setExporting(null);
    }
  };

  return (
    <div style={{ marginTop: '1.5rem' }}>
      <h4 style={{ marginBottom: '0.75rem', fontSize: '0.9rem' }}>💾 导出</h4>
      <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
        {FORMATS.map(f => (
          <button key={f.value} onClick={() => handleExport(f.value)}
            disabled={exporting !== null}
            style={{
              padding: '0.5rem 1rem', borderRadius: '8px',
              border: '1px solid var(--border)',
              backgroundColor: exporting === f.value ? 'var(--bg-tertiary)' : 'transparent',
              color: 'var(--text-primary)', cursor: 'pointer',
              fontSize: '0.85rem', opacity: exporting !== null ? 0.6 : 1,
            }}>
            {exporting === f.value ? '⏳' : f.label} {f.desc}
          </button>
        ))}
      </div>
    </div>
  );
};

export default ExportPanel;
