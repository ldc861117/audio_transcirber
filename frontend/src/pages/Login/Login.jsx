import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuthStore } from '../../stores/authStore';

const Login = () => {
  const [username, setUsername] = useState('');
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
      await login({ username, password });
      navigate('/');
    } catch (err) {
      setError(err.response?.data?.error || '登录失败');
    } finally {
      setIsLoading(false);
    }
  };

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
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <label>用户名</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <label>密码</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
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
