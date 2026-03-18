import React, { useState } from 'react';
import { api } from '../../api/endpoints';
import { Download, FileText, Film, FileDown, Loader2 } from 'lucide-react';

const FORMATS = [
  { value: 'txt', label: 'TXT', icon: <FileText size={16} />, desc: '纯文本' },
  { value: 'srt', label: 'SRT', icon: <Film size={16} />, desc: '字幕文件' },
  { value: 'docx', label: 'Word', icon: <FileDown size={16} />, desc: 'Word 文档' },
  { value: 'pdf', label: 'PDF', icon: <FileDown size={16} />, desc: 'PDF 文档' },
];

const ExportPanel = ({ taskId, filename }) => {
  const [exporting, setExporting] = useState(null);

  if (!taskId) return null;

  const handleExport = async (format) => {
    setExporting(format);
    try {
      const response = await api.exports.download(taskId, format);

      // Try to get filename from Content-Disposition header
      let downloadName = '';
      const disposition = response.headers?.['content-disposition'];
      if (disposition) {
        const match = disposition.match(/filename\*?=(?:UTF-8''|"?)([^";]+)/i);
        if (match) downloadName = decodeURIComponent(match[1].replace(/"/g, ''));
      }
      // Fallback: use prop filename or taskId
      if (!downloadName) {
        const baseName = filename
          ? filename.replace(/\.[^/.]+$/, '')  // strip original extension
          : `transcription_${taskId.slice(0, 8)}`;
        downloadName = `${baseName}.${format}`;
      }

      const blob = new Blob([response.data]);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = downloadName;
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
    <div style={{ marginTop: '2rem', paddingTop: '1.5rem', borderTop: '1px solid var(--bg-tertiary)' }}>
      <h4 style={{ marginBottom: '1rem', fontSize: '0.9rem', display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-secondary)' }}>
        <Download size={16} />
        导出文件
      </h4>
      <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
        {FORMATS.map(f => (
          <button key={f.value} onClick={() => handleExport(f.value)}
            disabled={exporting !== null}
            style={{
              padding: '0.6rem 1.25rem',
              borderRadius: '10px',
              border: '1px solid var(--bg-tertiary)',
              backgroundColor: 'var(--bg-tertiary)',
              color: 'var(--text-primary)',
              cursor: 'pointer',
              fontSize: '0.875rem',
              opacity: exporting !== null && exporting !== f.value ? 0.5 : 1,
              display: 'flex',
              alignItems: 'center',
              gap: '0.6rem',
              transition: 'var(--transition)'
            }}
            className="hover-bright"
          >
            {exporting === f.value ? <Loader2 size={16} className="animate-spin" /> : f.icon}
            <span>{f.label}</span>
            <span style={{ fontSize: '0.75rem', opacity: 0.5 }}>{f.desc}</span>
          </button>
        ))}
      </div>
    </div>
  );
};

export default ExportPanel;
