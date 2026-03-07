import React, { useState, useEffect } from 'react';
import { api } from '../../api/endpoints';

const Speakers = () => {
  const [profiles, setProfiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editingId, setEditingId] = useState(null);
  const [editName, setEditName] = useState('');
  const [playingClip, setPlayingClip] = useState(null);
  const [selected, setSelected] = useState(new Set());
  const audioRef = React.useRef(null);

  const fetchProfiles = async () => {
    try {
      const res = await api.speakers.list();
      setProfiles(res.data.profiles || []);
    } catch (err) {
      console.error('Failed to load speakers:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchProfiles(); }, []);

  const handleRename = async (profileId) => {
    if (!editName.trim()) return;
    try {
      await api.speakers.rename(profileId, editName.trim());
      setEditingId(null);
      setEditName('');
      fetchProfiles();
    } catch (err) {
      alert('重命名失败: ' + (err.response?.data?.error || err.message));
    }
  };

  const handleDelete = async (profileId, name) => {
    if (!confirm(`确定删除声纹 "${name}" 吗？`)) return;
    try {
      await api.speakers.delete(profileId);
      setSelected(prev => { const n = new Set(prev); n.delete(profileId); return n; });
      fetchProfiles();
    } catch (err) {
      alert('删除失败: ' + (err.response?.data?.error || err.message));
    }
  };

  const handleMerge = async () => {
    const ids = Array.from(selected);
    if (ids.length < 2) { alert('请至少选择 2 个声纹进行合并'); return; }
    const keepId = ids[0];
    try {
      for (let i = 1; i < ids.length; i++) {
        await api.speakers.merge(keepId, ids[i]);
      }
      setSelected(new Set());
      fetchProfiles();
    } catch (err) {
      alert('合并失败: ' + (err.response?.data?.error || err.message));
    }
  };

  const toggleSelect = (id) => {
    setSelected(prev => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  const playClip = (clipUrl) => {
    if (playingClip === clipUrl) {
      audioRef.current?.pause();
      setPlayingClip(null);
      return;
    }
    setPlayingClip(clipUrl);
    if (audioRef.current) {
      audioRef.current.src = clipUrl;
      audioRef.current.play();
    }
  };

  if (loading) {
    return (
      <div className="card" style={{ textAlign: 'center', padding: '3rem 0' }}>
        <p>加载中...</p>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <h1 style={{ margin: 0 }}>声纹库</h1>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          {selected.size >= 2 && (
            <button onClick={handleMerge} className="btn-primary"
              style={{ padding: '6px 16px', fontSize: '0.85rem' }}>
              🔗 合并选中 ({selected.size})
            </button>
          )}
          <button onClick={() => { setLoading(true); fetchProfiles(); }}
            style={{
              padding: '6px 14px', fontSize: '0.85rem', borderRadius: '8px',
              border: '1px solid var(--border)', backgroundColor: 'var(--bg-secondary)',
              color: 'var(--text-primary)', cursor: 'pointer',
            }}>
            🔄 刷新
          </button>
        </div>
      </div>

      <audio ref={audioRef} onEnded={() => setPlayingClip(null)} style={{ display: 'none' }} />

      {profiles.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: '3rem 0' }}>
          <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>👥</div>
          <h3>暂无声纹数据</h3>
          <p style={{ color: 'var(--text-secondary)', marginTop: '0.5rem' }}>
            启用说话人识别进行转写后，声纹数据将自动保存到这里
          </p>
        </div>
      ) : (
        <>
          {/* Stats banner */}
          <div style={{
            padding: '0.75rem 1.25rem', marginBottom: '1rem', borderRadius: '8px',
            backgroundColor: 'var(--bg-secondary)', fontSize: '0.85rem',
            color: 'var(--text-secondary)', display: 'flex', gap: '1.5rem',
          }}>
            <span>共 <strong style={{ color: 'var(--text-primary)' }}>{profiles.length}</strong> 个声纹</span>
            <span>共 <strong style={{ color: 'var(--text-primary)' }}>
              {profiles.reduce((sum, p) => sum + (p.clip_count || 0), 0)}
            </strong> 个音频片段</span>
            {selected.size > 0 && (
              <span style={{ color: 'var(--accent-primary, #5e97f6)' }}>
                已选 {selected.size} 个
                <button onClick={() => setSelected(new Set())}
                  style={{ marginLeft: '4px', background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-secondary)', fontSize: '0.8rem' }}>
                  清除
                </button>
              </span>
            )}
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {profiles.map(profile => (
              <div key={profile.id} className="card" style={{
                border: selected.has(profile.id) ? '2px solid var(--accent-primary, #5e97f6)' : undefined,
                transition: 'border 0.15s',
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    {/* Checkbox for multi-select */}
                    <input type="checkbox" checked={selected.has(profile.id)}
                      onChange={() => toggleSelect(profile.id)}
                      style={{ width: '16px', height: '16px', cursor: 'pointer' }} />

                    {/* Avatar */}
                    <div style={{
                      width: '40px', height: '40px', borderRadius: '50%',
                      background: 'linear-gradient(135deg, var(--accent-primary), var(--accent-secondary, #7c4dff))',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      color: 'white', fontWeight: 'bold', fontSize: '1.1rem', flexShrink: 0,
                    }}>
                      {(profile.name || '?')[0].toUpperCase()}
                    </div>

                    {/* Name + meta */}
                    <div>
                      {editingId === profile.id ? (
                        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                          <input
                            type="text" value={editName}
                            onChange={(e) => setEditName(e.target.value)}
                            onKeyDown={(e) => e.key === 'Enter' && handleRename(profile.id)}
                            style={{ padding: '4px 8px', fontSize: '0.9rem', width: '150px' }}
                            autoFocus
                          />
                          <button onClick={() => handleRename(profile.id)}
                            style={{ padding: '4px 8px', fontSize: '0.8rem' }}>✓</button>
                          <button onClick={() => setEditingId(null)}
                            style={{ padding: '4px 8px', fontSize: '0.8rem', backgroundColor: 'transparent' }}>✗</button>
                        </div>
                      ) : (
                        <h4 style={{ margin: 0 }}>{profile.name || `说话人 ${profile.id}`}</h4>
                      )}
                      <p style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', margin: '2px 0 0' }}>
                        {profile.clip_count || 0} 个片段
                        {profile.created_at && ` · 创建于 ${new Date(profile.created_at).toLocaleDateString()}`}
                      </p>
                    </div>
                  </div>

                  {/* Actions */}
                  <div style={{ display: 'flex', gap: '0.5rem' }}>
                    <button
                      onClick={() => { setEditingId(profile.id); setEditName(profile.name || ''); }}
                      style={{ padding: '4px 10px', fontSize: '0.8rem', backgroundColor: 'var(--bg-tertiary)', borderRadius: '6px', border: '1px solid var(--border)', cursor: 'pointer', color: 'var(--text-primary)' }}>
                      ✏️
                    </button>
                    <button
                      onClick={() => handleDelete(profile.id, profile.name)}
                      style={{ padding: '4px 10px', fontSize: '0.8rem', backgroundColor: 'var(--bg-tertiary)', borderRadius: '6px', border: '1px solid var(--border)', cursor: 'pointer', color: 'var(--error, #f44336)' }}>
                      🗑️
                    </button>
                  </div>
                </div>

                {/* Audio clips */}
                {profile.clips && profile.clips.length > 0 && (
                  <div style={{ marginTop: '0.75rem', display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
                    {profile.clips.map((clip, i) => {
                      const url = `/api/speakers/${profile.id}/clips/${clip}`;
                      return (
                        <button key={i} onClick={() => playClip(url)}
                          style={{
                            padding: '3px 10px', fontSize: '0.75rem', borderRadius: '16px',
                            border: '1px solid var(--border)', cursor: 'pointer',
                            backgroundColor: playingClip === url ? 'var(--accent-primary)' : 'var(--bg-tertiary)',
                            color: playingClip === url ? 'white' : 'var(--text-primary)',
                            transition: 'all 0.15s',
                          }}>
                          {playingClip === url ? '⏹' : '▶'} 片段 {i + 1}
                        </button>
                      );
                    })}
                  </div>
                )}
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
};

export default Speakers;
