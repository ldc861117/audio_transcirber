import React, { useState, useEffect } from 'react';
import { api } from '../../api/client';

const STORAGE_KEY = 'audio_transcriber_config';

const Settings = () => {
  const [providers, setProviders] = useState({});
  const [testResult, setTestResult] = useState(null);
  const [testing, setTesting] = useState(false);

  // Load saved config from localStorage
  const loadConfig = () => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      return saved ? JSON.parse(saved) : {};
    } catch { return {}; }
  };

  const [config, setConfig] = useState(loadConfig);

  useEffect(() => {
    api.providers.list().then(res => setProviders(res.data)).catch(() => {});
  }, []);

  const handleSave = () => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(config));
    setTestResult({ success: true, message: '配置已保存' });
    setTimeout(() => setTestResult(null), 2000);
  };

  const handleTestConnection = async () => {
    setTesting(true);
    setTestResult(null);
    try {
      const provider = config.provider || 'gemini';
      const res = await api.providers.test({
        provider,
        base_url: config.baseUrl || '',
        api_key: config.apiKey || '',
        model: config.model || '',
      });
      setTestResult({ success: true, message: `✅ 连接成功: ${res.data.model || provider}` });
    } catch (err) {
      setTestResult({ success: false, message: `❌ 连接失败: ${err.response?.data?.error || err.message}` });
    } finally {
      setTesting(false);
    }
  };

  const handleReset = () => {
    localStorage.removeItem(STORAGE_KEY);
    setConfig({});
    setTestResult({ success: true, message: '配置已重置' });
    setTimeout(() => setTestResult(null), 2000);
  };

  return (
    <div style={{ maxWidth: '600px', margin: '0 auto' }}>
      <h1 style={{ marginBottom: '2rem' }}>设置</h1>

      {/* API Configuration */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <h3 style={{ marginBottom: '1rem' }}>API 配置</h3>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
          配置当前转写使用的 API 提供商和密钥。修改后自动同步到「新建转写」页面。
        </p>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <label>Provider</label>
            <select
              value={config.provider || 'gemini'}
              onChange={(e) => {
                const p = e.target.value;
                const info = providers[p];
                setConfig(prev => ({
                  ...prev,
                  provider: p,
                  model: info?.model || prev.model || '',
                  baseUrl: info?.base_url || '',
                }));
              }}
            >
              <option value="gemini">🔮 Gemini (推荐)</option>
              <option value="zhipu">🧠 智谱 AI</option>
              <option value="modelscope">🪐 ModelScope</option>
              <option value="custom">⚙️ 自定义 (OpenAI 兼容)</option>
            </select>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <label>模型名称</label>
            <input
              type="text"
              value={config.model || ''}
              onChange={(e) => setConfig({ ...config, model: e.target.value })}
              placeholder="gemini-3-flash-preview"
            />
          </div>

          {(config.provider === 'custom' || config.provider === 'modelscope') && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              <label>Base URL</label>
              <input
                type="text"
                value={config.baseUrl || ''}
                onChange={(e) => setConfig({ ...config, baseUrl: e.target.value })}
                placeholder="https://api.example.com/v1"
              />
            </div>
          )}

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <label>API Key</label>
            <input
              type="password"
              value={config.apiKey || ''}
              onChange={(e) => setConfig({ ...config, apiKey: e.target.value })}
              placeholder="sk-..."
            />
          </div>
        </div>

        {testResult && (
          <div style={{
            marginTop: '1rem', padding: '0.75rem',
            borderRadius: '8px',
            backgroundColor: testResult.success ? 'rgba(76,175,80,0.1)' : 'rgba(244,67,54,0.1)',
            color: testResult.success ? '#4caf50' : '#f44336'
          }}>
            {testResult.message}
          </div>
        )}

        <div style={{ marginTop: '1.5rem', display: 'flex', gap: '0.75rem' }}>
          <button className="btn-primary" onClick={handleSave} style={{ flex: 1 }}>
            💾 保存配置
          </button>
          <button onClick={handleTestConnection} disabled={testing} style={{ flex: 1, backgroundColor: 'var(--bg-tertiary)' }}>
            {testing ? '测试中...' : '🔗 测试连接'}
          </button>
          <button onClick={handleReset} style={{ backgroundColor: 'var(--bg-tertiary)', color: 'var(--error, #f44336)' }}>
            重置
          </button>
        </div>
      </div>

      {/* Server Status */}
      <div className="card">
        <h3 style={{ marginBottom: '1rem' }}>服务端状态</h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          {Object.entries(providers).map(([name, info]) => (
            <div key={name} style={{
              display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              padding: '0.5rem 0', borderBottom: '1px solid var(--border-color, rgba(255,255,255,0.1))'
            }}>
              <span>{name}</span>
              <span style={{
                fontSize: '0.8rem',
                color: info.has_key ? '#4caf50' : 'var(--text-secondary)',
              }}>
                {info.has_key ? '✅ API Key 已配置' : '⚠️ 需要提供 API Key'}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Settings;
