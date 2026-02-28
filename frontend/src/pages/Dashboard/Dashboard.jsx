import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../stores/authStore';
import { api } from '../../api/client';
import {
  Rocket,
  Clock,
  ChevronRight,
  CheckCircle2,
  AlertCircle,
  Loader2,
  FileAudio,
  Mic,
  Settings,
  Info
} from 'lucide-react';

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
      queued: <><Clock size={14} /> 排队中</>,
      splitting: <><Loader2 size={14} className="animate-spin" /> 分割中</>,
      transcribing: <><Loader2 size={14} className="animate-spin" /> 转写中</>,
      diarizing: <><Mic size={14} className="animate-pulse" /> 识别中</>,
      done: <><CheckCircle2 size={14} color="var(--success)" /> 完成</>,
      error: <><AlertCircle size={14} color="var(--error)" /> 失败</>,
    };
    return map[s] || s;
  };

  const formatDate = (iso) => {
    if (!iso) return '';
    const d = new Date(iso);
    return d.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div style={{ maxWidth: '1000px', margin: '0 auto' }}>
      <div style={{ marginBottom: '2.5rem' }}>
        <h1 style={{ fontSize: '2.25rem', marginBottom: '0.75rem', fontWeight: 800 }}>
          欢迎回来，{user?.username} <span style={{ color: 'var(--accent-primary)' }}>👋</span>
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '1.1rem' }}>今天想转写些什么？</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.5rem' }}>
        <div className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between', border: '1px solid var(--bg-tertiary)' }}>
          <div>
            <div style={{
              width: '48px',
              height: '48px',
              borderRadius: '12px',
              background: 'var(--accent-gradient)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: '1.5rem',
              color: 'white'
            }}>
              <Rocket size={24} />
            </div>
            <h3 style={{ marginBottom: '0.75rem', fontSize: '1.25rem' }}>快速转写</h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem', marginBottom: '2rem', lineHeight: 1.6 }}>
              上传音频文件或使用内置录音机，快速获取高质量的文字记录。
            </p>
          </div>
          <button className="btn-primary" onClick={() => navigate('/transcribe')} style={{ padding: '0.75rem', fontSize: '1rem' }}>
            立即开始
          </button>
        </div>

        <div className="card" style={{ border: '1px solid var(--bg-tertiary)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
            <h3 style={{ fontSize: '1.25rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Clock size={20} color="var(--accent-primary)" />
              最近任务
            </h3>
            {recentTasks.length > 0 && (
              <span onClick={() => navigate('/history')}
                className="hover-bright"
                style={{ color: 'var(--accent-primary)', cursor: 'pointer', fontSize: '0.9rem', display: 'flex', alignItems: 'center', gap: '0.25rem', fontWeight: 600 }}>
                查看全部 <ChevronRight size={16} />
              </span>
            )}
          </div>
          {loading ? (
            <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-secondary)' }}>
              <Loader2 className="animate-spin" style={{ margin: '0 auto 1rem' }} />
              加载中...
            </div>
          ) : recentTasks.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-secondary)' }}>
              <FileAudio size={48} style={{ opacity: 0.1, margin: '0 auto 1rem' }} />
              <p>暂无转写记录</p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {recentTasks.map(task => (
                <div key={task.id} onClick={() => navigate(`/history?task=${task.id}`)}
                  style={{
                    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                    padding: '0.85rem 1rem', borderRadius: '12px', cursor: 'pointer',
                    backgroundColor: 'var(--bg-tertiary)', border: '1px solid transparent',
                    transition: 'all 0.2s'
                  }}
                  className="hover-bright"
                >
                  <div style={{ minWidth: 0 }}>
                    <span style={{ fontSize: '0.9rem', fontWeight: 600, display: 'block', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', marginBottom: '0.2rem' }}>
                      {task.filename}
                    </span>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>{formatDate(task.created_at)}</span>
                  </div>
                  <span style={{
                    fontSize: '0.75rem',
                    flexShrink: 0,
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.4rem',
                    padding: '4px 8px',
                    borderRadius: '6px',
                    backgroundColor: 'rgba(0,0,0,0.2)'
                  }}>
                    {statusLabel(task.status)}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <div style={{ marginTop: '3rem' }}>
        <h3 style={{ marginBottom: '1.25rem', fontSize: '1.25rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Info size={20} color="var(--accent-primary)" />
          使用小贴士
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '1rem' }}>
          {[
            { icon: <FileAudio size={18} />, title: '支持格式', content: '支持 mp3, wav, m4a, flac 等多种主流音频格式。' },
            { icon: <Mic size={18} />, title: '说话人识别', content: '转写时开启"说话人识别"可自动区分不同发言人。' },
            { icon: <Settings size={18} />, title: 'API 配置', content: '在设置中配置您自己的 API Key 以获得更稳定的体验。' }
          ].map((tip, idx) => (
            <div key={idx} className="card" style={{ padding: '1.25rem', backgroundColor: 'var(--bg-tertiary)', border: '1px solid rgba(255,255,255,0.05)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.6rem', color: 'var(--accent-primary)' }}>
                {tip.icon}
                <h4 style={{ fontSize: '0.95rem', fontWeight: 700, margin: 0 }}>{tip.title}</h4>
              </div>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>{tip.content}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
