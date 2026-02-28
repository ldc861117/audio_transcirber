import React, { useState, useEffect } from 'react';
import { useConfigStore, PROVIDER_DEFAULTS } from '../../stores/configStore';
import { api } from '../../api/client';

const Settings = () => {
  const { provider, model, baseUrl, apiKey, setProvider, setField, resetConfig } = useConfigStore();
  const [serverStatus, setServerStatus] = useState([]);
  const [testResult, setTestResult] = useState(null);
  const [testing, setTesting] = useState(false);
  const [showKey, setShowKey] = useState(false);

  const currentProvider = PROVIDER_DEFAULTS[provider] || PROVIDER_DEFAULTS.custom;
  const isServerKey = currentProvider.serverKey === true;
  const isSDK = currentProvider.isZhipuSDK === true;

  useEffect(() => {
    api.providers.list().then(res => {
      setServerStatus(res.data.providers || []);
    }).catch(() => {});
  }, []);

  const handleTestConnection = async () => {
    setTesting(true);
    setTestResult(null);
    try {
      const res = await api.providers.testConnection({
        provider, model, base_url: baseUrl, api_key: apiKey,
      });
      setTestResult({ ok: true, msg: res.data.message || '连接成功' });
    } catch (err) {
      setTestResult({ ok: false, msg: err.response?.data?.error || '连接失败' });
    } finally {
      setTesting(false);
    }
  };

  const inputStyle = {
    width: '100%', padding: '0.75rem', borderRadius: '8px',
    border: '1px solid var(--border)', backgroundColor: 'var(--bg-secondary)',
    color: 'var(--text-primary)', fontSize: '0.9rem',
  };

  const labelStyle = { display: 'block', marginBottom: '0.5rem', fontWeight: 600 };

  return (
    <div>
      <h1 style={{ fontSize: '2rem', marginBottom: '2rem' }}>设置</h1>

      <div className="card" style={{ padding: '2rem', marginBottom: '1.5rem' }}>
        <h2 style={{ fontSize: '1.25rem', marginBottom: '0.5rem' }}>API 配置</h2>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', marginBottom: '1.5rem' }}>
          配置转写使用的 API 提供商和密钥。修改后自动同步到「新建转写」页面。
        </p>

        <div style={{ display: 'grid', gap: '1.25rem' }}>
          {/* Provider select */}
          <div>
            <label style={labelStyle}>Provider</label>
            <select value={provider} onChange={e => setProvider(e.target.value)} style={inputStyle}>
              {Object.entries(PROVIDER_DEFAULTS).map(([key, cfg]) => (
                <option key={key} value={key}>{cfg.displayName || key}</option>
              ))}
            </select>
          </div>

          {/* Model */}
          <div>
            <label style={labelStyle}>模型名称</label>
            <input value={model} onChange={e => setField('model', e.target.value)}
              style={inputStyle} placeholder="模型名称" />
          </div>

          {/* Base URL — hidden for serverKey providers */}
          {!isServerKey && (
            <div>
              <label style={labelStyle}>Base URL</label>
              {isSDK ? (
                <input value="使用官方 SDK 直连" disabled
                  style={{ ...inputStyle, opacity: 0.5 }} />
              ) : (
                <input value={baseUrl} onChange={e => setField('baseUrl', e.target.value)}
                  placeholder="https://api.example.com/v1" style={inputStyle} />
              )}
            </div>
          )}

          {/* API Key — disabled for serverKey providers */}
          <div>
            <label style={labelStyle}>
              API Key
              {currentProvider.link && (
                <a href={currentProvider.link} target="_blank" rel="noopener noreferrer"
                  style={{ fontSize: '0.8rem', marginLeft: '8px', color: 'var(--accent-primary, #5e97f6)' }}>
                  {isServerKey ? '🔗 查看官网' : '🔗 获取 Key'}
                </a>
              )}
            </label>
            {isServerKey ? (
              <div style={{
                ...inputStyle, opacity: 0.5, display: 'flex', alignItems: 'center',
                gap: '0.5rem', color: 'var(--text-secondary)',
              }}>
                🔒 服务端环境变量管理（无需手动配置）
              </div>
            ) : (
              <div style={{ position: 'relative' }}>
                <input type={showKey ? 'text' : 'password'} value={apiKey}
                  onChange={e => setField('apiKey', e.target.value)}
                  placeholder="sk-..." style={inputStyle} />
                <button onClick={() => setShowKey(!showKey)} style={{
                  position: 'absolute', right: '10px', top: '50%', transform: 'translateY(-50%)',
                  background: 'none', border: 'none', cursor: 'pointer', fontSize: '1rem',
                }}>
                  {showKey ? '🙈' : '👁️'}
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Actions */}
        <div style={{ display: 'flex', gap: '1rem', marginTop: '1.5rem' }}>
          <button className="btn-primary" onClick={handleTestConnection} disabled={testing}
            style={{ flex: 1 }}>
            {testing ? '⏳ 测试中...' : '🔗 测试连接'}
          </button>
          <button onClick={resetConfig}
            style={{ padding: '0.75rem 1.5rem', borderRadius: '8px', border: '1px solid var(--border)', backgroundColor: 'transparent', color: 'var(--text-secondary)', cursor: 'pointer' }}>
            重置
          </button>
        </div>

        {testResult && (
          <div style={{ marginTop: '1rem', padding: '0.75rem 1rem', borderRadius: '8px',
            backgroundColor: testResult.ok ? 'rgba(52,199,89,0.1)' : 'rgba(255,59,48,0.1)',
            color: testResult.ok ? '#34c759' : '#ff3b30', fontSize: '0.875rem' }}>
            {testResult.ok ? '✅' : '❌'} {testResult.msg}
          </div>
        )}
      </div>

      {/* Server status */}
      {serverStatus.length > 0 && (
        <div className="card" style={{ padding: '2rem' }}>
          <h3 style={{ marginBottom: '1rem' }}>服务端状态</h3>
          <div style={{ display: 'grid', gap: '0.75rem' }}>
            {serverStatus.map(p => (
              <div key={p.provider} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.5rem 0', borderBottom: '1px solid var(--border)' }}>
                <span>{p.provider}</span>
                <span style={{ color: p.has_key ? '#34c759' : '#ff9500', fontSize: '0.85rem' }}>
                  {p.has_key ? '✅ 已配置' : '⚠️ 需要提供 API Key'}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default Settings;
