import React, { useState, useEffect } from 'react';
import { api } from '../../api/client';

const Speakers = () => {
  const [profiles, setProfiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editingId, setEditingId] = useState(null);
  const [editName, setEditName] = useState('');
  const [playingClip, setPlayingClip] = useState(null);
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
      fetchProfiles();
    } catch (err) {
      alert('删除失败: ' + (err.response?.data?.error || err.message));
    }
  };

  const handleMerge = async (keepId, mergeId) => {
    try {
      await api.speakers.merge(keepId, mergeId);
      fetchProfiles();
    } catch (err) {
      alert('合并失败: ' + (err.response?.data?.error || err.message));
    }
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
      <h1 style={{ marginBottom: '2rem' }}>声纹库</h1>

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
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {profiles.map(profile => (
            <div key={profile.id} className="card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                  <div style={{
                    width: '40px', height: '40px', borderRadius: '50%',
                    background: 'linear-gradient(135deg, var(--accent-primary), var(--accent-secondary, #7c4dff))',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    color: 'white', fontWeight: 'bold', fontSize: '1.1rem'
                  }}>
                    {(profile.name || '?')[0].toUpperCase()}
                  </div>
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
                        <button onClick={() => handleRename(profile.id)} style={{ padding: '4px 8px', fontSize: '0.8rem' }}>
                          ✓
                        </button>
                        <button onClick={() => setEditingId(null)} style={{ padding: '4px 8px', fontSize: '0.8rem', backgroundColor: 'transparent' }}>
                          ✗
                        </button>
                      </div>
                    ) : (
                      <h4 style={{ margin: 0 }}>{profile.name || `说话人 ${profile.id}`}</h4>
                    )}
                    <p style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', margin: '2px 0 0' }}>
                      {profile.clip_count || 0} 个音频片段
                    </p>
                  </div>
                </div>
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  <button
                    onClick={() => { setEditingId(profile.id); setEditName(profile.name || ''); }}
                    style={{ padding: '4px 10px', fontSize: '0.8rem', backgroundColor: 'var(--bg-tertiary)' }}
                  >
                    ✏️ 重命名
                  </button>
                  <button
                    onClick={() => handleDelete(profile.id, profile.name)}
                    style={{ padding: '4px 10px', fontSize: '0.8rem', backgroundColor: 'var(--bg-tertiary)', color: 'var(--error, #f44336)' }}
                  >
                    🗑️ 删除
                  </button>
                </div>
              </div>

              {/* Audio clips */}
              {profile.clips && profile.clips.length > 0 && (
                <div style={{ marginTop: '1rem', display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                  {profile.clips.map((clip, i) => (
                    <button
                      key={i}
                      onClick={() => playClip(`/api/speakers/${profile.id}/clips/${clip}`)}
                      style={{
                        padding: '4px 10px', fontSize: '0.75rem',
                        backgroundColor: playingClip === `/api/speakers/${profile.id}/clips/${clip}` ? 'var(--accent-primary)' : 'var(--bg-tertiary)',
                        color: playingClip === `/api/speakers/${profile.id}/clips/${clip}` ? 'white' : 'var(--text-primary)',
                        borderRadius: '16px'
                      }}
                    >
                      {playingClip === `/api/speakers/${profile.id}/clips/${clip}` ? '⏹ 停止' : `▶ 片段 ${i + 1}`}
                    </button>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default Speakers;
