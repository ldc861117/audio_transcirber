import React, { useState, useEffect, useRef } from 'react';
import { api } from '../../api/client';
import DropZone from '../../components/AudioUpload/DropZone';
import ProgressBar from '../../components/Progress/ProgressBar';
import ChunkGrid from '../../components/Progress/ChunkGrid';
import { useTranscribeStore } from '../../stores/transcribeStore';

const STORAGE_KEY = 'audio_transcriber_config';

const loadSavedConfig = () => {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    return saved ? JSON.parse(saved) : null;
  } catch { return null; }
};

const saveConfig = (provider, config) => {
  localStorage.setItem(STORAGE_KEY, JSON.stringify({ provider, ...config }));
};

const Transcribe = () => {
  const saved = loadSavedConfig();
  const [selectedFile, setSelectedFile] = useState(null);
  const [provider, setProvider] = useState(saved?.provider || 'gemini');
  const [config, setConfig] = useState({
    baseUrl: saved?.baseUrl || '',
    model: saved?.model || 'gemini-3-flash-preview',
    apiKey: saved?.apiKey || '',
    maxMinutes: saved?.maxMinutes || 10,
    maxMB: saved?.maxMB || 20,
    enableDiarization: saved?.enableDiarization || false
  });
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState('');
  const [serverKeyStatus, setServerKeyStatus] = useState({});

  const { currentTaskId, uploadFile, updateTaskStatus, tasks, clearCurrentTask } = useTranscribeStore();
  const currentTask = tasks[currentTaskId];
  const pollIntervalRef = useRef(null);

  // Load built-in providers + server key status
  const [availableProviders, setAvailableProviders] = useState({});
  useEffect(() => {
    api.providers.list().then(res => {
      setAvailableProviders(res.data);
      // Check which providers have server-side API keys
      const keyStatus = {};
      Object.entries(res.data).forEach(([name, info]) => {
        keyStatus[name] = info.has_key || false;
      });
      setServerKeyStatus(keyStatus);

      // If no saved config, auto-set from server defaults
      if (!saved && res.data.gemini) {
        setConfig(prev => ({
          ...prev,
          model: res.data.gemini.model || 'gemini-3-flash-preview',
          baseUrl: res.data.gemini.base_url || '',
        }));
      }
    }).catch(() => {});

    // Check test mode
    api.providers.testConfig().then(res => {
      if (res.data.test_mode && res.data.has_config) {
        setProvider('custom');
        setConfig(prev => ({
          ...prev,
          baseUrl: res.data.base_url,
          model: res.data.model,
          apiKey: res.data.api_key_set ? '(server-env)' : ''
        }));
      }
    }).catch(() => {});
  }, []);

  // Save config whenever it changes
  useEffect(() => {
    saveConfig(provider, config);
  }, [provider, config]);

  const handleProviderChange = (e) => {
    const p = e.target.value;
    setProvider(p);
    if (availableProviders[p]) {
      setConfig(prev => ({
        ...prev,
        model: availableProviders[p].model,
        baseUrl: availableProviders[p].base_url || ''
      }));
    } else if (p === 'custom') {
      setConfig(prev => ({ ...prev, model: '', baseUrl: '' }));
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;
    setError('');
    setIsUploading(true);

    const formData = new FormData();
    formData.append('audio', selectedFile);
    formData.append('provider', provider);
    formData.append('base_url', config.baseUrl);
    formData.append('api_key', config.apiKey);
    formData.append('model', config.model);
    formData.append('max_minutes', config.maxMinutes);
    formData.append('max_mb', config.maxMB);
    formData.append('enable_diarization', config.enableDiarization);

    try {
      await uploadFile(formData);
    } catch (err) {
      setError(err.response?.data?.error || '上传失败');
      setIsUploading(false);
    }
  };

  useEffect(() => {
    if (currentTaskId && currentTask?.status !== 'done' && currentTask?.status !== 'error') {
      pollIntervalRef.current = setInterval(() => {
        updateTaskStatus(currentTaskId);
      }, 2000);
    } else {
      clearInterval(pollIntervalRef.current);
      if (currentTask?.status === 'done' || currentTask?.status === 'error') {
        setIsUploading(false);
      }
    }
    return () => clearInterval(pollIntervalRef.current);
  }, [currentTaskId, currentTask?.status]);

  const calculateProgress = () => {
    if (!currentTask) return 0;
    if (currentTask.status === 'done') return 100;
    if (currentTask.status === 'splitting') return 10;
    if (currentTask.status === 'transcribing') {
      const total = currentTask.total_chunks || 1;
      const done = currentTask.completed_chunks || 0;
      return 10 + (done / total) * 80;
    }
    if (currentTask.status === 'diarizing') return 95;
    return 0;
  };

  const hasServerKey = serverKeyStatus[provider];

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto' }}>
      <h1 style={{ marginBottom: '2rem' }}>新建转写任务</h1>

      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <h3 style={{ marginBottom: '1rem' }}>1. API 配置</h3>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <label>Provider</label>
            <select value={provider} onChange={handleProviderChange}>
              <option value="gemini">🔮 Gemini (推荐)</option>
              <option value="zhipu">🧠 智谱 AI</option>
              <option value="modelscope">🪐 ModelScope</option>
              <option value="custom">⚙️ 自定义 (OpenAI 兼容)</option>
            </select>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <label>模型</label>
            <input
              type="text"
              value={config.model}
              onChange={(e) => setConfig({...config, model: e.target.value})}
              placeholder="例如: gemini-3-flash-preview"
            />
          </div>
          {(provider === 'custom' || provider === 'modelscope') && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', gridColumn: 'span 2' }}>
              <label>Base URL</label>
              <input
                type="text"
                value={config.baseUrl}
                onChange={(e) => setConfig({...config, baseUrl: e.target.value})}
                placeholder="https://api.example.com/v1"
              />
            </div>
          )}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', gridColumn: 'span 2' }}>
            <label>
              API Key
              {hasServerKey && (
                <span style={{ color: 'var(--success, #4caf50)', fontSize: '0.8rem', marginLeft: '0.5rem' }}>
                  ✅ 服务端已配置
                </span>
              )}
            </label>
            <input
              type="password"
              value={config.apiKey}
              onChange={(e) => setConfig({...config, apiKey: e.target.value})}
              placeholder={hasServerKey ? '服务端已配置，此处可留空' : '请输入 API Key'}
            />
          </div>
        </div>

        <div style={{ marginTop: '1rem', display: 'flex', gap: '1.5rem', flexWrap: 'wrap' }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={config.enableDiarization}
              onChange={(e) => setConfig({...config, enableDiarization: e.target.checked})}
            />
            开启说话人识别
          </label>
        </div>
      </div>

      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <h3 style={{ marginBottom: '1rem' }}>2. 上传音频</h3>
        <DropZone
          onFileSelect={setSelectedFile}
          selectedFile={selectedFile}
          onCancel={() => setSelectedFile(null)}
        />

        {error && <div style={{ color: 'var(--error)', marginTop: '1rem' }}>{error}</div>}

        <button
          className="btn-primary"
          onClick={handleUpload}
          disabled={!selectedFile || isUploading}
          style={{ width: '100%', marginTop: '1.5rem', height: '48px' }}
        >
          {isUploading ? '处理中...' : '开始转写'}
        </button>
      </div>

      {currentTask && (
        <div className="card" style={{ marginBottom: '1.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3>3. 转写进度</h3>
            {currentTask.status === 'done' && (
              <button onClick={clearCurrentTask} style={{ backgroundColor: 'transparent', color: 'var(--accent-primary)' }}>
                清除任务
              </button>
            )}
          </div>

          <ProgressBar progress={calculateProgress()} status={currentTask.status} />
          <ChunkGrid chunks={currentTask.chunk_results} />

          {currentTask.status === 'error' && (
            <div style={{ color: 'var(--error)', marginTop: '1rem', padding: '1rem', backgroundColor: 'rgba(244,67,54,0.1)', borderRadius: '8px' }}>
              ❌ {currentTask.error || '转写失败，请检查 API 配置'}
            </div>
          )}

          {currentTask.status === 'done' && (
            <div style={{ marginTop: '2rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                <h4>转写结果</h4>
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  <button className="btn-primary" style={{ padding: '4px 12px', fontSize: '0.8rem' }} onClick={() => navigator.clipboard.writeText(currentTask.transcript)}>复制</button>
                </div>
              </div>
              <div style={{
                backgroundColor: 'var(--bg-tertiary)',
                padding: '1rem',
                borderRadius: '8px',
                whiteSpace: 'pre-wrap',
                maxHeight: '400px',
                overflowY: 'auto',
                fontSize: '0.9rem',
                lineHeight: '1.6'
              }}>
                {currentTask.transcript}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default Transcribe;
