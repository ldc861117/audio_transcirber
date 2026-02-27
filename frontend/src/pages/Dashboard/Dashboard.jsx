import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../stores/authStore';

const Dashboard = () => {
  const { user } = useAuthStore();
  const navigate = useNavigate();

  return (
    <div>
      <div style={{ marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>欢迎回来，{user?.username} 👋</h1>
        <p style={{ color: 'var(--text-secondary)' }}>今天想转写些什么？</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '1.5rem' }}>
        <div className="card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <div>
            <h3 style={{ marginBottom: '1rem' }}>快速转写</h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', marginBottom: '1.5rem' }}>
              上传音频文件或直接录音，快速获取文字记录。
            </p>
          </div>
          <button className="btn-primary" onClick={() => navigate('/transcribe')}>
            立即开始
          </button>
        </div>

        <div className="card">
          <h3 style={{ marginBottom: '1rem' }}>最近任务</h3>
          <div style={{ color: 'var(--text-secondary)', textAlign: 'center', padding: '2rem 0' }}>
            <span style={{ fontSize: '2rem', display: 'block', marginBottom: '0.5rem' }}>📄</span>
            暂无最近任务
          </div>
        </div>
      </div>
      
      <div style={{ marginTop: '2.5rem' }}>
        <h3 style={{ marginBottom: '1rem' }}>使用小贴士</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '1rem' }}>
           {[
             { title: '支持格式', content: '支持 mp3, wav, m4a 等多种主流音频格式。' },
             { title: '说话人识别', content: '开启“说话人识别”可自动区分不同发言人。' },
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
