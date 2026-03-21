import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuthStore } from '../../stores/authStore';

const Login = () => {
  const [mode, setMode] = useState('email'); // 'email' | 'username'
  const [identifier, setIdentifier] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  
  const login = useAuthStore(state => state.login);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);
    try {
      // Send the correct field name based on mode
      const credentials = mode === 'email'
        ? { email: identifier, password }
        : { username: identifier, password };
      await login(credentials);
      navigate('/');
    } catch (err) {
      setError(err.response?.data?.error?.message || '登录失败');
    } finally {
      setIsLoading(false);
    }
  };

  const handleModeSwitch = (newMode) => {
    setMode(newMode);
    setIdentifier('');
    setError('');
  };

  const tabStyle = (active) => ({
    flex: 1,
    padding: '0.5rem',
    border: 'none',
    borderBottom: active ? '2px solid var(--accent-primary)' : '2px solid transparent',
    background: 'none',
    color: active ? 'var(--accent-primary)' : 'var(--text-secondary)',
    fontWeight: active ? 600 : 400,
    cursor: 'pointer',
    transition: 'all 0.2s ease',
    fontSize: '0.875rem',
  });

  return (
    <div style={{
      height: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      backgroundColor: 'var(--bg-color)'
    }}>
      <div className="card" style={{ width: '400px' }}>
        <h1 style={{ marginBottom: '1.5rem', textAlign: 'center' }}>登录</h1>
        {/* Mode toggle */}
        <div style={{ display: 'flex', marginBottom: '1rem', borderBottom: '1px solid var(--border-color, #e0e0e0)' }}>
          <button type="button" style={tabStyle(mode === 'email')} onClick={() => handleModeSwitch('email')}>
            邮箱登录
          </button>
          <button type="button" style={tabStyle(mode === 'username')} onClick={() => handleModeSwitch('username')}>
            用户名登录
          </button>
        </div>
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <label>{mode === 'email' ? '电子邮箱' : '用户名'}</label>
            <input
              type={mode === 'email' ? 'email' : 'text'}
              value={identifier}
              onChange={(e) => setIdentifier(e.target.value)}
              required
              placeholder={mode === 'email' ? '请输入您的邮箱' : '请输入您的用户名'}
              autoComplete={mode === 'email' ? 'email' : 'username'}
            />
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <label>密码</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              placeholder="请输入密码"
            />
          </div>
          {error && <div style={{ color: 'var(--error)', fontSize: '0.875rem' }}>{error}</div>}
          <button type="submit" className="btn-primary" disabled={isLoading} style={{ marginTop: '0.5rem' }}>
            {isLoading ? '登录中...' : '登录'}
          </button>
        </form>
        <div style={{ marginTop: '1.5rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
          没有账号？ <Link to="/register" style={{ color: 'var(--accent-primary)', textDecoration: 'none' }}>去注册</Link>
        </div>
      </div>
    </div>
  );
};

export default Login;
