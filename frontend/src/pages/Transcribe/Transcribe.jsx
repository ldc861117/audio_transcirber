import React, { useState, useRef, useCallback, useEffect } from 'react';
import { useConfigStore, PROVIDER_DEFAULTS } from '../../stores/configStore';
import TranscriptView from '../../components/Transcript/TranscriptView';
import ExportPanel from '../../components/Transcript/ExportPanel';
import Recorder from '../../components/Recorder/Recorder';
import { api } from '../../api/client';

const Transcribe = () => {
  const { provider, model, baseUrl, apiKey, enableDiarization, setField } = useConfigStore();
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [taskId, setTaskId] = useState(null);
  const [taskData, setTaskData] = useState(null);
  const [error, setError] = useState('');
  const fileInputRef = useRef(null);
  const pollRef = useRef(null);

  // Poll task status
  const pollStatus = useCallback((id) => {
    if (pollRef.current) clearInterval(pollRef.current);
    pollRef.current = setInterval(async () => {
      try {
        const res = await api.transcriptions.status(id);
        setTaskData(res.data);
        if (res.data.status === 'done' || res.data.status === 'error') {
          clearInterval(pollRef.current);
          pollRef.current = null;
        }
      } catch (err) {
        console.error('Poll failed', err);
      }
    }, 1500);
  }, []);

  useEffect(() => {
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, []);

  const handleFileSelect = (e) => {
    const selected = e.target.files?.[0];
    if (selected) { setFile(selected); setError(''); }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const dropped = e.dataTransfer.files?.[0];
    if (dropped) { setFile(dropped); setError(''); }
  };

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setError('');
    setTaskData(null);

    const formData = new FormData();
    formData.append('audio', file);
    formData.append('provider', provider);
    formData.append('model', model);
    if (baseUrl) formData.append('base_url', baseUrl);
    if (apiKey) formData.append('api_key', apiKey);
    formData.append('enable_diarization', enableDiarization ? 'true' : 'false');

    try {
      const res = await api.transcriptions.upload(formData);
      const id = res.data.task_id;
      setTaskId(id);
      setTaskData({ status: 'queued', filename: file.name });
      pollStatus(id);
    } catch (err) {
      setError(err.response?.data?.error || '上传失败');
    } finally {
      setUploading(false);
    }
  };

  const isDone = taskData?.status === 'done';
  const isActive = taskData && !isDone && taskData.status !== 'error';
  const progress = taskData ? Math.round((taskData.completed_chunks || 0) / Math.max(taskData.total_chunks || 1, 1) * 100) : 0;

  return (
    <div>
      <h1 style={{ fontSize: '2rem', marginBottom: '2rem' }}>新建转写任务</h1>

      {/* Recording */}
      <Recorder onRecorded={(f) => { setFile(f); setError(''); }} />

      {/* Upload area */}
      <div className="card" style={{ padding: '2rem', marginBottom: '1.5rem' }}>
        <h3 style={{ marginBottom: '1rem' }}>上传音频文件</h3>
        <div
          onClick={() => fileInputRef.current?.click()}
          onDrop={handleDrop}
          onDragOver={e => e.preventDefault()}
          style={{
            border: '2px dashed var(--border)', borderRadius: '12px',
            padding: '3rem', textAlign: 'center', cursor: 'pointer',
            backgroundColor: file ? 'rgba(94,151,246,0.05)' : 'transparent',
            transition: 'all 0.2s',
          }}
        >
          {file ? (
            <div>
              <span style={{ fontSize: '2rem' }}>🎵</span>
              <p style={{ fontWeight: 600, marginTop: '0.5rem' }}>{file.name}</p>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
                {(file.size / 1024 / 1024).toFixed(1)} MB · 点击更换
              </p>
            </div>
          ) : (
            <div>
              <span style={{ fontSize: '2.5rem', display: 'block', marginBottom: '0.5rem' }}>📁</span>
              <p style={{ fontWeight: 600 }}>点击或拖拽音频文件到此处</p>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>支持 MP3, WAV, M4A, FLAC 等</p>
            </div>
          )}
          <input ref={fileInputRef} type="file" accept="audio/*" onChange={handleFileSelect} style={{ display: 'none' }} />
        </div>
      </div>

      {/* Options strip */}
      <div className="card" style={{ padding: '1.25rem 2rem', marginBottom: '1.5rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <span style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
            Provider: <strong style={{ color: 'var(--text-primary)' }}>{provider}</strong>
          </span>
          <span style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
            模型: <strong style={{ color: 'var(--text-primary)' }}>{model}</strong>
          </span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer', fontSize: '0.9rem' }}>
            <input type="checkbox" checked={enableDiarization}
              onChange={e => setField('enableDiarization', e.target.checked)} />
            🎤 说话人识别
          </label>
          <button className="btn-primary" onClick={handleUpload}
            disabled={!file || uploading || isActive}
            style={{ padding: '0.6rem 2rem' }}>
            {uploading ? '⏳ 上传中...' : isActive ? '⏳ 处理中...' : '🚀 开始转写'}
          </button>
        </div>
      </div>

      {error && (
        <div style={{ marginBottom: '1.5rem', padding: '1rem', borderRadius: '8px', backgroundColor: 'rgba(255,59,48,0.1)', color: '#ff3b30' }}>
          ❌ {error}
        </div>
      )}

      {/* Progress */}
      {isActive && (
        <div className="card" style={{ padding: '2rem', marginBottom: '1.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
            <span style={{ fontWeight: 600 }}>
              {taskData.status === 'splitting' ? '✂️ 分割音频...' :
               taskData.status === 'transcribing' ? `📝 转写中 ${taskData.current_chunk || 0}/${taskData.total_chunks || '?'}` :
               taskData.status === 'diarizing' ? '🎤 识别说话人...' : '⏳ 处理中...'}
            </span>
            <span style={{ color: 'var(--text-secondary)' }}>{progress}%</span>
          </div>
          <div style={{ height: '6px', backgroundColor: 'var(--bg-tertiary)', borderRadius: '3px', overflow: 'hidden' }}>
            <div style={{ height: '100%', width: `${progress}%`, backgroundColor: '#5e97f6', borderRadius: '3px', transition: 'width 0.3s' }} />
          </div>
        </div>
      )}

      {/* Error result */}
      {taskData?.status === 'error' && (
        <div className="card" style={{ padding: '2rem', marginBottom: '1.5rem' }}>
          <div style={{ color: '#ff3b30' }}>
            <h3>❌ 转写失败</h3>
            <pre style={{ marginTop: '1rem', fontSize: '0.8rem', whiteSpace: 'pre-wrap', opacity: 0.7 }}>
              {taskData.error}
            </pre>
          </div>
        </div>
      )}

      {/* Transcript result */}
      {isDone && (
        <div className="card" style={{ padding: '2rem' }}>
          <TranscriptView
            transcript={taskData.transcript}
            speakers={taskData.speakers || []}
            enableDiarization={taskData.enable_diarization}
          />
          <ExportPanel taskId={taskId} />
        </div>
      )}
    </div>
  );
};

export default Transcribe;
