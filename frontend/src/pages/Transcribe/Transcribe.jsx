import React, { useState, useRef, useCallback, useEffect } from 'react';
import { useConfigStore, PROVIDER_DEFAULTS } from '../../stores/configStore';
import TranscriptView from '../../components/Transcript/TranscriptView';
import ExportPanel from '../../components/Transcript/ExportPanel';
import Recorder from '../../components/Recorder/Recorder';
import { api } from '../../api/endpoints';
import {
  Upload,
  FileAudio,
  Music,
  Mic,
  Rocket,
  Loader2,
  CheckCircle2,
  AlertCircle,
  Scissors,
  FileText
} from 'lucide-react';

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
        const task = res.data.data || res.data;  // API wraps in {data: {...}}
        setTaskData(task);
        if (task.status === 'done' || task.status === 'error') {
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
      const uploadData = res.data.data || res.data;
      const id = uploadData.task_id;
      setTaskId(id);
      setTaskData({ status: 'queued', filename: file.name });
      pollStatus(id);
    } catch (err) {
      const errorData = err.response?.data?.error;
      setError(typeof errorData === 'object' ? errorData.message : (errorData || '上传失败'));
    } finally {
      setUploading(false);
    }
  };

  const isDone = taskData?.status === 'done';
  const isActive = taskData && !isDone && taskData.status !== 'error';
  const progress = taskData ? Math.round((taskData.completed_chunks || 0) / Math.max(taskData.total_chunks || 1, 1) * 100) : 0;

  const getStatusIcon = () => {
    if (taskData.status === 'splitting') return <Scissors className="animate-pulse" size={20} />;
    if (taskData.status === 'transcribing') return <FileText className="animate-pulse" size={20} />;
    if (taskData.status === 'diarizing') return <Mic className="animate-pulse" size={20} />;
    return <Loader2 className="animate-spin" size={20} />;
  };

  return (
    <div style={{ maxWidth: '1000px', margin: '0 auto' }}>
      <h1 style={{ fontSize: '2rem', marginBottom: '2rem', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        <FileAudio size={32} color="var(--accent-primary)" />
        新建转写任务
      </h1>

      {/* Recording */}
      <Recorder onRecorded={(f) => { setFile(f); setError(''); }} />

      {/* Upload area */}
      <div className="card" style={{ padding: '2rem', marginBottom: '1.5rem' }}>
        <h3 style={{ marginBottom: '1.25rem', fontSize: '1.1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Upload size={18} />
          上传音频文件
        </h3>
        <div
          onClick={() => fileInputRef.current?.click()}
          onDrop={handleDrop}
          onDragOver={e => e.preventDefault()}
          style={{
            border: '2px dashed var(--bg-tertiary)', borderRadius: '12px',
            padding: '3rem', textAlign: 'center', cursor: 'pointer',
            backgroundColor: file ? 'rgba(59,130,246,0.05)' : 'transparent',
            transition: 'var(--transition)',
          }}
          className="hover-bright"
        >
          {file ? (
            <div>
              <Music size={48} color="var(--accent-primary)" style={{ margin: '0 auto 1rem' }} />
              <p style={{ fontWeight: 600, marginTop: '0.5rem' }}>{file.name}</p>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
                {(file.size / 1024 / 1024).toFixed(1)} MB · 点击更换
              </p>
            </div>
          ) : (
            <div>
              <Upload size={48} color="var(--text-secondary)" style={{ opacity: 0.5, margin: '0 auto 1rem' }} />
              <p style={{ fontWeight: 600 }}>点击或拖拽音频文件到此处</p>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>支持 MP3, WAV, M4A, FLAC 等</p>
            </div>
          )}
          <input ref={fileInputRef} type="file" accept="audio/*,video/*,audio/mp4,audio/x-m4a,audio/aac,.m4a,.mp3,.wav,.ogg,.flac,.aac,.wma,.opus,.webm,.mp4,.mov,.mkv,.caf" onChange={handleFileSelect} style={{ display: 'none' }} />
        </div>
      </div>

      {/* Options strip */}
      <div className="card" style={{ padding: '1.25rem 2rem', marginBottom: '1.5rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <span style={{ color: 'var(--text-secondary)', fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Provider</span>
            <strong style={{ color: 'var(--text-primary)', fontSize: '0.9rem' }}>{provider}</strong>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <span style={{ color: 'var(--text-secondary)', fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>模型</span>
            <strong style={{ color: 'var(--text-primary)', fontSize: '0.9rem' }}>{model}</strong>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', cursor: 'pointer', fontSize: '0.9rem' }} className="hover-bright">
            <input type="checkbox" checked={enableDiarization}
              onChange={e => setField('enableDiarization', e.target.checked)}
              style={{ width: '16px', height: '16px' }} />
            <Mic size={16} />
            说话人识别
          </label>
          <button className="btn-primary" onClick={handleUpload}
            disabled={!file || uploading || isActive}
            style={{
              padding: '0.75rem 2rem',
              display: 'flex',
              alignItems: 'center',
              gap: '0.6rem',
              minWidth: '160px',
              justifyContent: 'center'
            }}>
            {uploading ? (
              <><Loader2 className="animate-spin" size={18} /> 上传中...</>
            ) : isActive ? (
              <><Loader2 className="animate-spin" size={18} /> 处理中...</>
            ) : (
              <><Rocket size={18} /> 开始转写</>
            )}
          </button>
        </div>
      </div>

      {error && (
        <div style={{
          marginBottom: '1.5rem',
          padding: '1rem 1.5rem',
          borderRadius: '12px',
          backgroundColor: 'rgba(239,68,68,0.1)',
          color: 'var(--error)',
          display: 'flex',
          alignItems: 'center',
          gap: '0.75rem',
          border: '1px solid rgba(239,68,68,0.2)'
        }}>
          <AlertCircle size={20} />
          <span>{error}</span>
        </div>
      )}

      {/* Progress */}
      {isActive && (
        <div className="card" style={{ padding: '2rem', marginBottom: '1.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1rem', alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              {getStatusIcon()}
              <span style={{ fontWeight: 600 }}>
                {taskData.status === 'splitting' ? '分割音频...' :
                 taskData.status === 'transcribing' ? `转写中 ${taskData.current_chunk || 0}/${taskData.total_chunks || '?'}` :
                 taskData.status === 'diarizing' ? '识别说话人...' : '处理中...'}
              </span>
            </div>
            <span style={{ color: 'var(--accent-primary)', fontWeight: 700, fontSize: '1.1rem' }}>{progress}%</span>
          </div>
          <div style={{ height: '8px', backgroundColor: 'var(--bg-tertiary)', borderRadius: '4px', overflow: 'hidden' }}>
            <div style={{ height: '100%', width: `${progress}%`, backgroundColor: 'var(--accent-primary)', borderRadius: '4px', transition: 'width 0.5s cubic-bezier(0.4, 0, 0.2, 1)' }} />
          </div>
        </div>
      )}

      {/* Error result */}
      {taskData?.status === 'error' && (
        <div className="card" style={{ padding: '2rem', marginBottom: '1.5rem', border: '1px solid rgba(239,68,68,0.3)' }}>
          <div style={{ color: 'var(--error)' }}>
            <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
              <AlertCircle size={24} />
              转写失败
            </h3>
            <pre style={{
              marginTop: '1rem',
              fontSize: '0.85rem',
              whiteSpace: 'pre-wrap',
              opacity: 0.8,
              backgroundColor: 'rgba(0,0,0,0.2)',
              padding: '1rem',
              borderRadius: '8px'
            }}>
              {taskData.error}
            </pre>
          </div>
        </div>
      )}

      {/* Transcript result */}
      {isDone && (
        <div className="card" style={{ padding: '2rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1.5rem', color: 'var(--success)' }}>
            <CheckCircle2 size={24} />
            <h3 style={{ margin: 0 }}>转写完成</h3>
          </div>
          <TranscriptView
            taskId={taskId}
            transcript={taskData.transcript}
            speakers={taskData.speakers || []}
            enableDiarization={taskData.enable_diarization}
            onUpdate={(updatedData) => setTaskData(prev => ({ ...prev, ...updatedData }))}
          />
          <ExportPanel taskId={taskId} filename={taskData?.filename || file?.name} />
        </div>
      )}
    </div>
  );
};

export default Transcribe;
