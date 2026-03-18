import React, { useRef, useEffect, useState } from 'react';
import { ChevronDown, ChevronUp, Terminal } from 'lucide-react';

const STAGE_COLORS = {
  splitting:    '#6366f1',
  censusing:    '#8b5cf6',
  transcribing: '#3b82f6',
  stitching:    '#06b6d4',
  diarizing:    '#f59e0b',
  done:         '#22c55e',
  error:        '#ef4444',
  persist:      '#6b7280',
};

const EventLog = ({ pipelineLog, status }) => {
  const [expanded, setExpanded] = useState(false);
  const scrollRef = useRef(null);

  useEffect(() => {
    if (expanded && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [pipelineLog, expanded]);

  if (!pipelineLog || pipelineLog.length === 0) return null;

  const formatTime = (isoStr) => {
    try {
      const d = new Date(isoStr);
      return d.toLocaleTimeString('zh-CN', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
    } catch { return ''; }
  };

  const visibleEntries = expanded ? pipelineLog : pipelineLog.slice(-3);

  return (
    <div style={{ marginTop: '1rem' }}>
      <button
        onClick={() => setExpanded(!expanded)}
        style={{
          background: 'none',
          border: 'none',
          cursor: 'pointer',
          padding: '0.4rem 0',
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
          color: 'var(--text-secondary)',
          fontSize: '0.8rem',
          width: '100%',
        }}
      >
        <Terminal size={14} />
        <span>处理日志 ({pipelineLog.length})</span>
        {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
      </button>

      <div
        ref={scrollRef}
        style={{
          maxHeight: expanded ? '240px' : '96px',
          overflow: 'auto',
          backgroundColor: 'rgba(0,0,0, 0.15)',
          borderRadius: '8px',
          padding: '0.5rem 0.75rem',
          fontFamily: 'ui-monospace, "SF Mono", Monaco, "Cascadia Code", monospace',
          fontSize: '0.75rem',
          lineHeight: '1.7',
          transition: 'max-height 0.3s ease',
        }}
      >
        {visibleEntries.map((entry, idx) => (
          <div key={idx} style={{
            display: 'flex',
            gap: '0.5rem',
            alignItems: 'baseline',
            opacity: entry.error ? 1 : 0.85,
          }}>
            <span style={{ color: 'var(--text-secondary)', flexShrink: 0 }}>
              {formatTime(entry.timestamp)}
            </span>
            <span style={{
              backgroundColor: STAGE_COLORS[entry.stage] || '#6b7280',
              color: 'white',
              padding: '0 0.35rem',
              borderRadius: '3px',
              fontSize: '0.65rem',
              fontWeight: 600,
              flexShrink: 0,
              textTransform: 'uppercase',
            }}>
              {entry.stage}
            </span>
            <span style={{
              color: entry.error ? 'var(--error)' : 'var(--text-primary)',
              wordBreak: 'break-word',
            }}>
              {entry.message}
            </span>
          </div>
        ))}
        {!expanded && pipelineLog.length > 3 && (
          <div style={{ color: 'var(--text-secondary)', fontSize: '0.7rem', textAlign: 'center', paddingTop: '0.25rem' }}>
            ↑ 点击展开查看全部 {pipelineLog.length} 条
          </div>
        )}
      </div>
    </div>
  );
};

export default EventLog;
