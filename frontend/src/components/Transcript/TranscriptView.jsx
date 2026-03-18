import React, { useState, useEffect } from 'react';
import { Copy, Check, FileText, Mic, Users, Edit3, Save, UserPlus, X } from 'lucide-react';
import { api } from '../../api/endpoints';

const SPEAKER_COLORS = [
  '#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6',
  '#06b6d4', '#ec4899', '#84cc16', '#f97316', '#6366f1',
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

const TranscriptView = ({ taskId, transcript, speakers = [], enableDiarization = false, onUpdate }) => {
  const [copied, setCopied] = useState(false);
  const [editingSpeaker, setEditingSpeaker] = useState(null); // { label, name, matched_profile_id }
  const [libraryProfiles, setLibraryProfiles] = useState([]);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    if (enableDiarization) {
      api.speakers.list().then(res => setLibraryProfiles(res.data.profiles || [])).catch(console.error);
    }
  }, [enableDiarization]);

  if (!transcript) {
    return (
      <div style={{ textAlign: 'center', padding: '4rem 2rem', color: 'var(--text-secondary)' }}>
        <FileText size={48} style={{ opacity: 0.2, margin: '0 auto 1.5rem' }} />
        <p>转写完成后结果将在此显示</p>
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
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <h3 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <FileText size={20} color="var(--accent-primary)" />
          转写结果
        </h3>
        <button onClick={handleCopy}
          style={{
            padding: '0.5rem 1rem',
            borderRadius: '8px',
            border: '1px solid var(--bg-tertiary)',
            backgroundColor: 'var(--bg-tertiary)',
            color: 'var(--text-primary)',
            cursor: 'pointer',
            fontSize: '0.85rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem'
          }}
          className="hover-bright"
        >
          {copied ? <><Check size={16} /> 已复制</> : <><Copy size={16} /> 复制</>}
        </button>
      </div>

      <div style={{
        backgroundColor: 'rgba(0,0,0,0.1)',
        padding: '1.5rem',
        borderRadius: '12px',
        border: '1px solid var(--bg-tertiary)'
      }}>
        {hasSpeakers ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            {segments.map((seg, idx) => {
              const color = getSpeakerColor(seg.speaker, colorMap);
              return (
                <div key={idx} style={{ display: 'flex', gap: '1rem', alignItems: 'flex-start' }}>
                  <span style={{
                    flexShrink: 0, padding: '0.25rem 0.75rem', borderRadius: '8px',
                    backgroundColor: color + '22', color, fontSize: '0.8rem', fontWeight: 600,
                    whiteSpace: 'nowrap', marginTop: '0.15rem',
                    border: `1px solid ${color}33`
                  }}>
                    {seg.speaker}
                  </span>
                  <p style={{ margin: 0, lineHeight: 1.7, color: 'var(--text-primary)', fontSize: '1rem' }}>
                    {seg.text}
                  </p>
                </div>
              );
            })}
          </div>
        ) : (
          <div style={{ lineHeight: 1.8, color: 'var(--text-primary)', fontSize: '1rem', whiteSpace: 'pre-wrap' }}>
            {transcript}
          </div>
        )}
      </div>

      {speakers.length > 0 && (
        <div style={{ marginTop: '2rem', padding: '1.25rem', backgroundColor: 'var(--bg-tertiary)', borderRadius: '12px' }}>
          <h4 style={{ marginBottom: '1rem', fontSize: '0.9rem', display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-secondary)' }}>
            <Users size={16} />
            识别到的说话人 (点击编辑)
          </h4>
          <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
            {speakers.map((sp, idx) => {
              const displayName = sp.matched_name || sp.label;
              const isEditing = editingSpeaker?.label === sp.label;

              return (
                <div key={idx} style={{ position: 'relative' }}>
                  <div
                    onClick={() => !isEditing && setEditingSpeaker({
                      label: sp.label,
                      name: displayName,
                      matched_profile_id: sp.matched_profile_id
                    })}
                    style={{
                      padding: '0.5rem 1rem', borderRadius: '8px',
                      backgroundColor: SPEAKER_COLORS[idx % SPEAKER_COLORS.length] + '22',
                      color: SPEAKER_COLORS[idx % SPEAKER_COLORS.length],
                      fontSize: '0.85rem', fontWeight: 500,
                      border: `1px solid ${SPEAKER_COLORS[idx % SPEAKER_COLORS.length]}33`,
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.5rem',
                      cursor: 'pointer'
                    }}
                    className="hover-bright"
                  >
                    <Mic size={14} />
                    {displayName}
                    {sp.total_duration && <span style={{ opacity: 0.6, fontSize: '0.75rem' }}>{Math.round(sp.total_duration)}s</span>}
                    <Edit3 size={12} style={{ marginLeft: '4px', opacity: 0.5 }} />
                  </div>

                  {isEditing && (
                    <div style={{
                      position: 'absolute', top: '100%', left: 0, marginTop: '8px',
                      backgroundColor: 'var(--bg-secondary)', border: '1px solid var(--border)',
                      borderRadius: '12px', padding: '1rem', zIndex: 100, boxShadow: '0 10px 25px rgba(0,0,0,0.3)',
                      width: '280px'
                    }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                        <span style={{ fontSize: '0.8rem', fontWeight: 600 }}>编辑说话人</span>
                        <X size={16} cursor="pointer" onClick={() => setEditingSpeaker(null)} />
                      </div>

                      <div style={{ marginBottom: '1rem' }}>
                        <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '4px' }}>名称</label>
                        <input
                          type="text"
                          value={editingSpeaker.name}
                          onChange={e => setEditingSpeaker({ ...editingSpeaker, name: e.target.value })}
                          style={{ width: '100%', padding: '6px 10px', fontSize: '0.9rem' }}
                          autoFocus
                        />
                      </div>

                      <div style={{ marginBottom: '1rem' }}>
                        <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '4px' }}>匹配库中已有声纹</label>
                        <select
                          value={editingSpeaker.matched_profile_id || ''}
                          onChange={e => setEditingSpeaker({ ...editingSpeaker, matched_profile_id: e.target.value ? parseInt(e.target.value) : null })}
                          style={{ width: '100%', padding: '6px', fontSize: '0.85rem' }}
                        >
                          <option value="">-- 不关联 --</option>
                          {libraryProfiles.map(p => (
                            <option key={p.id} value={p.id}>{p.name || `说话人 ${p.id}`}</option>
                          ))}
                        </select>
                      </div>

                      <div style={{ display: 'flex', gap: '0.5rem' }}>
                        <button
                          className="btn-primary"
                          disabled={isSaving}
                          onClick={async () => {
                            setIsSaving(true);
                            try {
                              const res = await api.speakers.updateTaskSpeakers(taskId, [editingSpeaker]);
                              if (onUpdate) onUpdate(res.data?.data || res.data);
                              setEditingSpeaker(null);
                            } catch (err) {
                              alert('更新失败: ' + (err.response?.data?.error || err.message));
                            } finally {
                              setIsSaving(false);
                            }
                          }}
                          style={{ flex: 1, padding: '6px', fontSize: '0.85rem', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '4px' }}
                        >
                          <Save size={14} /> 保存修改
                        </button>
                        <button
                          title="保存声纹到库"
                          disabled={isSaving}
                          onClick={async () => {
                            setIsSaving(true);
                            try {
                              const res = await api.speakers.updateTaskSpeakers(taskId, [editingSpeaker], true);
                              if (onUpdate) onUpdate(res.data?.data || res.data);
                              // Refresh library
                              const libRes = await api.speakers.list();
                              setLibraryProfiles(libRes.data.profiles || []);
                              setEditingSpeaker(null);
                            } catch (err) {
                              alert('入库失败: ' + (err.response?.data?.error || err.message));
                            } finally {
                              setIsSaving(false);
                            }
                          }}
                          style={{ padding: '6px 10px', fontSize: '0.85rem', backgroundColor: 'var(--bg-tertiary)', borderRadius: '8px', border: '1px solid var(--border)' }}
                        >
                          <UserPlus size={14} />
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

export default TranscriptView;
