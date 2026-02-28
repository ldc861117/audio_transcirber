import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../stores/authStore';
import { api } from '../../api/client';

const Dashboard = () => {
  const { user } = useAuthStore();
  const navigate = useNavigate();
  const [recentTasks, setRecentTasks] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.transcriptions.list({ per_page: 5, page: 1 })
      .then(res => {
        setRecentTasks(res.data.items || []);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const statusLabel = (s) => {
    const map = {
      queued: '⏳ 排队中', splitting: '✂️ 分割中', transcribing: '📝 转写中',
      diarizing: '🎤 识别中', done: '✅ 完成', error: '❌ 失败',
    };
    return map[s] || s;
  };

  const formatDate = (iso) => {
    if (!iso) return '';
    const d = new Date(iso);
    return d.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div>
      <div style={{ marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>欢迎回来，{user?.username} 👋</h1>
        <p style={{ color: 'var(--text-secondary)' }}>今天想转写些什么？</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '1.5rem' }}>
        <div className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <div>
            <h3 style={{ marginBottom: '1rem' }}>🚀 快速转写</h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', marginBottom: '1.5rem' }}>
              上传音频文件，快速获取文字记录。
            </p>
          </div>
          <button className="btn-primary" onClick={() => navigate('/transcribe')}>
            立即开始
          </button>
        </div>

        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h3>📋 最近任务</h3>
            {recentTasks.length > 0 && (
              <span onClick={() => navigate('/history')}
                style={{ color: '#5e97f6', cursor: 'pointer', fontSize: '0.85rem' }}>查看全部 →</span>
            )}
          </div>
          {loading ? (
            <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-secondary)' }}>加载中...</div>
          ) : recentTasks.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-secondary)' }}>
              <span style={{ fontSize: '2rem', display: 'block', marginBottom: '0.5rem' }}>📄</span>
              暂无转写记录
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {recentTasks.map(task => (
                <div key={task.id} onClick={() => navigate(`/history?task=${task.id}`)}
                  style={{
                    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                    padding: '0.6rem 0.75rem', borderRadius: '8px', cursor: 'pointer',
                    backgroundColor: 'var(--bg-tertiary)', transition: 'opacity 0.2s',
                  }}>
                  <div style={{ minWidth: 0 }}>
                    <span style={{ fontSize: '0.85rem', fontWeight: 500, display: 'block', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {task.filename}
                    </span>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>{formatDate(task.created_at)}</span>
                  </div>
                  <span style={{ fontSize: '0.75rem', flexShrink: 0 }}>{statusLabel(task.status)}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <div style={{ marginTop: '2.5rem' }}>
        <h3 style={{ marginBottom: '1rem' }}>使用小贴士</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '1rem' }}>
          {[
            { title: '支持格式', content: '支持 mp3, wav, m4a 等多种主流音频格式。' },
            { title: '说话人识别', content: '转写时开启"说话人识别"可自动区分不同发言人。' },
            { title: 'API 配置', content: '在设置中配置您自己的 API Key 以获得更稳定的体验。' }
          ].map((tip, idx) => (
            <div key={idx} className="card" style={{ padding: '1rem', backgroundColor: 'var(--bg-tertiary)' }}>
              <h4 style={{ fontSize: '0.9rem', marginBottom: '0.5rem' }}>{tip.title}</h4>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{tip.content}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
