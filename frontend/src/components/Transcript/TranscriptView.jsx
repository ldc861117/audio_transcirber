import React, { useState } from 'react';

const SPEAKER_COLORS = [
  '#5e97f6', '#e57373', '#81c784', '#ffb74d', '#ba68c8',
  '#4dd0e1', '#f06292', '#aed581', '#ff8a65', '#9575cd',
];

function parseSpeakerSegments(text) {
  if (!text) return [];
  const regex = /【(.+?)】([\s\S]*?)(?=【|$)/g;
  const segments = [];
  let match;
  while ((match = regex.exec(text)) !== null) {
    segments.push({ speaker: match[1].trim(), text: match[2].trim() });
  }
  return segments;
}

function getSpeakerColor(speaker, colorMap) {
  if (!colorMap[speaker]) {
    colorMap[speaker] = SPEAKER_COLORS[Object.keys(colorMap).length % SPEAKER_COLORS.length];
  }
  return colorMap[speaker];
}

const TranscriptView = ({ transcript, speakers = [], enableDiarization = false }) => {
  const [copied, setCopied] = useState(false);

  if (!transcript) {
    return (
      <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-secondary)' }}>
        <span style={{ fontSize: '3rem', display: 'block', marginBottom: '1rem' }}>📝</span>
        转写完成后结果将在此显示
      </div>
    );
  }

  const handleCopy = () => {
    navigator.clipboard.writeText(transcript).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  const colorMap = {};
  const segments = enableDiarization ? parseSpeakerSegments(transcript) : [];
  const hasSpeakers = segments.length > 0;

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <h3 style={{ margin: 0 }}>📄 转写结果</h3>
        <button onClick={handleCopy}
          style={{ padding: '0.4rem 0.8rem', borderRadius: '6px', border: '1px solid var(--border)', backgroundColor: 'transparent', color: 'var(--text-secondary)', cursor: 'pointer', fontSize: '0.8rem' }}>
          {copied ? '✅ 已复制' : '📋 复制'}
        </button>
      </div>

      {hasSpeakers ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          {segments.map((seg, idx) => {
            const color = getSpeakerColor(seg.speaker, colorMap);
            return (
              <div key={idx} style={{ display: 'flex', gap: '0.75rem', alignItems: 'flex-start' }}>
                <span style={{
                  flexShrink: 0, padding: '0.25rem 0.6rem', borderRadius: '12px',
                  backgroundColor: color + '22', color, fontSize: '0.8rem', fontWeight: 600,
                  whiteSpace: 'nowrap', marginTop: '0.15rem',
                }}>
                  {seg.speaker}
                </span>
                <p style={{ margin: 0, lineHeight: 1.7, color: 'var(--text-primary)', fontSize: '0.95rem' }}>
                  {seg.text}
                </p>
              </div>
            );
          })}
        </div>
      ) : (
        <div style={{ lineHeight: 1.8, color: 'var(--text-primary)', fontSize: '0.95rem', whiteSpace: 'pre-wrap' }}>
          {transcript}
        </div>
      )}

      {speakers.length > 0 && (
        <div style={{ marginTop: '1.5rem', padding: '1rem', backgroundColor: 'var(--bg-tertiary)', borderRadius: '8px' }}>
          <h4 style={{ marginBottom: '0.75rem', fontSize: '0.9rem' }}>🎤 识别到的说话人</h4>
          <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
            {speakers.map((sp, idx) => (
              <div key={idx} style={{
                padding: '0.4rem 0.8rem', borderRadius: '8px',
                backgroundColor: SPEAKER_COLORS[idx % SPEAKER_COLORS.length] + '22',
                color: SPEAKER_COLORS[idx % SPEAKER_COLORS.length],
                fontSize: '0.85rem', fontWeight: 500,
              }}>
                {sp.matched_name || sp.label}
                {sp.total_duration && <span style={{ marginLeft: '0.5rem', opacity: 0.7 }}>{Math.round(sp.total_duration)}s</span>}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default TranscriptView;
