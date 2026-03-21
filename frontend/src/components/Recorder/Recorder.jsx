import React, { useState, useRef, useEffect, useCallback } from 'react';
import { api } from '../../api/endpoints';
import {
  Mic,
  Circle,
  Square,
  AlertCircle,
  Settings2,
  Volume2,
  Save,
  CheckCircle2,
  Loader2,
  HardDrive
} from 'lucide-react';

const CHUNK_INTERVAL_MS = 30_000; // 30s per chunk upload

const Recorder = ({ onRecorded, onSaved }) => {
  const [recording, setRecording] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const [mics, setMics] = useState([]);
  const [selectedMic, setSelectedMic] = useState('');
  const [micOn, setMicOn] = useState(true);
  const [sysOn, setSysOn] = useState(true);
  const [error, setError] = useState('');
  const [sleepSaved, setSleepSaved] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saveResult, setSaveResult] = useState(null);
  const [chunksUploaded, setChunksUploaded] = useState(0);

  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]); // in-memory fallback
  const timerRef = useRef(null);
  const startTimeRef = useRef(0);
  const audioCtxRef = useRef(null);
  const micGainRef = useRef(null);
  const sysGainRef = useRef(null);
  const micStreamRef = useRef(null);
  const sysStreamRef = useRef(null);
  const lastTickRef = useRef(Date.now());
  const recordingRef = useRef(false);
  const sessionIdRef = useRef(null);
  const chunkIndexRef = useRef(0);
  const uploadQueueRef = useRef(Promise.resolve()); // serialize uploads

  // Enumerate microphones on mount
  useEffect(() => {
    (async () => {
      try {
        await navigator.mediaDevices.getUserMedia({ audio: true });
        const devices = await navigator.mediaDevices.enumerateDevices();
        const audioInputs = devices.filter(d => d.kind === 'audioinput');
        setMics(audioInputs);
        if (audioInputs.length > 0) setSelectedMic(audioInputs[0].deviceId);
      } catch {
        setMics([]);
      }
    })();
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
      stopAllStreams();
    };
  }, []);

  // ── Upload a single chunk to the backend ──
  const uploadChunk = useCallback(async (blob) => {
    const sessionId = sessionIdRef.current;
    if (!sessionId || blob.size === 0) return;

    const formData = new FormData();
    formData.append('chunk', blob, `chunk_${chunkIndexRef.current}.webm`);

    try {
      await api.recordings.appendChunk(sessionId, formData);
      chunkIndexRef.current += 1;
      setChunksUploaded(prev => prev + 1);
    } catch (err) {
      console.error('[Recorder] Chunk upload failed:', err);
      // Keep in memory as fallback - don't crash
    }
  }, []);

  // Queue chunk upload to ensure sequential ordering
  const enqueueChunkUpload = useCallback((blob) => {
    // Always keep in-memory copy as fallback
    chunksRef.current.push(blob);

    uploadQueueRef.current = uploadQueueRef.current
      .then(() => uploadChunk(blob))
      .catch(err => console.error('[Recorder] Upload queue error:', err));
  }, [uploadChunk]);

  // ── Finalize: concat on server + trigger transcription ──
  const finalizeSession = useCallback(async () => {
    const sessionId = sessionIdRef.current;
    if (!sessionId) return;

    setSaving(true);
    setSaveResult(null);

    try {
      // Wait for any pending chunk uploads to finish
      await uploadQueueRef.current;

      const res = await api.recordings.finalize(sessionId, { auto_transcribe: true });
      const data = res.data?.data;
      const taskId = data?.task_id;

      setSaveResult({ success: true, taskId, sizeMb: data?.size_mb });
      onSaved?.(taskId);
    } catch (err) {
      console.error('[Recorder] Finalize failed:', err);
      // Fallback: try to save the in-memory Blob directly
      try {
        await fallbackUpload();
      } catch {
        setSaveResult({ success: false });
      }
    } finally {
      setSaving(false);
      sessionIdRef.current = null;
    }
  }, [onSaved]);

  // Fallback: upload full recording from in-memory chunks
  const fallbackUpload = useCallback(async () => {
    if (chunksRef.current.length === 0) {
      setSaveResult({ success: false });
      return;
    }
    const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
    const formData = new FormData();
    formData.append('audio', new File([blob], `recording_${Date.now()}.webm`, { type: 'audio/webm' }));
    formData.append('provider', 'gemini');
    const res = await api.transcriptions.upload(formData);
    const taskId = res.data?.data?.task_id || res.data?.task_id;
    setSaveResult({ success: true, taskId });
    onSaved?.(taskId);
  }, [onSaved]);

  // Emergency save for sleep/crash detection
  const emergencySave = useCallback(() => {
    // Chunks are already streaming to backend, just finalize
    stopAllStreams();
    finalizeSession();
  }, [finalizeSession]);

  const emergencyStop = useCallback(() => {
    if (!recordingRef.current) return;
    recordingRef.current = false;

    const recorder = mediaRecorderRef.current;
    if (recorder && recorder.state !== 'inactive') {
      try {
        recorder.stop();
      } catch {
        emergencySave();
      }
    } else {
      emergencySave();
    }

    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
    setRecording(false);
    setSleepSaved(true);
    setTimeout(() => setSleepSaved(false), 5000);
  }, [emergencySave]);

  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible' && recordingRef.current) {
        const now = Date.now();
        const gap = now - lastTickRef.current;
        if (gap > 30000) {
          console.warn(`[Recorder] System sleep detected (gap: ${Math.round(gap / 1000)}s). Auto-stopping.`);
          emergencyStop();
        }
      }
    };

    const handleBeforeUnload = (e) => {
      if (recordingRef.current) {
        emergencyStop();
        e.preventDefault();
        e.returnValue = '';
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }, [emergencyStop]);

  const stopAllStreams = () => {
    micStreamRef.current?.getTracks().forEach(t => t.stop());
    sysStreamRef.current?.getTracks().forEach(t => t.stop());
    audioCtxRef.current?.close().catch(() => {});
    micStreamRef.current = null;
    sysStreamRef.current = null;
    audioCtxRef.current = null;
    micGainRef.current = null;
    sysGainRef.current = null;
  };

  const startRecording = async () => {
    setError('');
    setSleepSaved(false);
    setSaveResult(null);
    setChunksUploaded(0);
    chunksRef.current = [];
    chunkIndexRef.current = 0;
    uploadQueueRef.current = Promise.resolve();

    try {
      // 0. Create recording session on backend FIRST
      const sessionRes = await api.recordings.start();
      const sessionId = sessionRes.data?.data?.session_id;
      if (!sessionId) throw new Error('无法创建录音会话');
      sessionIdRef.current = sessionId;

      // 1. Get microphone
      const micConstraints = selectedMic
        ? { audio: { deviceId: { exact: selectedMic } } }
        : { audio: true };
      const micStream = await navigator.mediaDevices.getUserMedia(micConstraints);
      micStreamRef.current = micStream;

      // 2. Get system audio via screen share
      let sysStream;
      try {
        sysStream = await navigator.mediaDevices.getDisplayMedia({
          video: true,
          audio: true,
        });
        sysStream.getVideoTracks().forEach(t => t.stop());
      } catch (displayErr) {
        console.error('[Recorder] getDisplayMedia failed:', displayErr?.name, displayErr?.message);
        micStream.getTracks().forEach(t => t.stop());
        throw new Error(`屏幕共享失败: ${displayErr?.message || '未知错误'}`);
      }
      sysStreamRef.current = sysStream;

      if (sysStream.getAudioTracks().length === 0) {
        console.warn('[Recorder] No audio tracks in system stream');
        micStream.getTracks().forEach(t => t.stop());
        sysStream.getTracks().forEach(t => t.stop());
        throw new Error('未检测到系统音轨，请确保勾选了"共享音频"');
      }

      // 3. Mix via AudioContext
      const ctx = new AudioContext();
      await ctx.resume();
      audioCtxRef.current = ctx;
      const dest = ctx.createMediaStreamDestination();

      const micGain = ctx.createGain();
      const micSrc = ctx.createMediaStreamSource(micStream);
      micSrc.connect(micGain);
      micGain.connect(dest);
      micGainRef.current = micGain;

      const sysGain = ctx.createGain();
      const sysSrc = ctx.createMediaStreamSource(sysStream);
      sysSrc.connect(sysGain);
      sysGain.connect(dest);
      sysGainRef.current = sysGain;

      // 4. Record with 30s timeslice — each chunk is streamed to backend
      const recorder = new MediaRecorder(dest.stream, { mimeType: 'audio/webm' });
      mediaRecorderRef.current = recorder;

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          enqueueChunkUpload(e.data);
        }
      };

      recorder.onstop = () => {
        // On stop: finalize the server-side session
        stopAllStreams();
        finalizeSession();
      };

      recorder.start(CHUNK_INTERVAL_MS);
      setRecording(true);
      recordingRef.current = true;
      setMicOn(true);
      setSysOn(true);

      // Timer
      startTimeRef.current = Date.now();
      lastTickRef.current = Date.now();
      setElapsed(0);
      timerRef.current = setInterval(() => {
        lastTickRef.current = Date.now();
        setElapsed(Date.now() - startTimeRef.current);
      }, 1000);

      // Stop when screen share ends
      sysStream.getVideoTracks()[0]?.addEventListener('ended', () => {
        stopRecording();
      });

    } catch (err) {
      setError(err.message);
      setRecording(false);
      recordingRef.current = false;
      sessionIdRef.current = null;
    }
  };

  const stopRecording = useCallback(() => {
    recordingRef.current = false;
    if (mediaRecorderRef.current?.state !== 'inactive') {
      mediaRecorderRef.current?.stop();
    }
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
    setRecording(false);
  }, []);

  const toggleMic = () => {
    if (!micGainRef.current || !audioCtxRef.current) return;
    const next = !micOn;
    setMicOn(next);
    micGainRef.current.gain.setValueAtTime(next ? 1 : 0, audioCtxRef.current.currentTime);
  };

  const toggleSys = () => {
    if (!sysGainRef.current || !audioCtxRef.current) return;
    const next = !sysOn;
    setSysOn(next);
    sysGainRef.current.gain.setValueAtTime(next ? 1 : 0, audioCtxRef.current.currentTime);
  };

  const formatTime = (ms) => {
    const s = Math.floor(ms / 1000) % 60;
    const m = Math.floor(ms / 60000);
    return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
  };

  return (
    <div style={{
      borderRadius: '16px',
      border: recording ? '2px solid var(--error)' : '1px solid var(--bg-tertiary)',
      padding: '1.5rem',
      marginBottom: '1.5rem',
      backgroundColor: recording ? 'rgba(239,68,68,0.04)' : 'var(--bg-secondary)',
      transition: 'var(--transition)',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: recording ? '1rem' : 0, flexWrap: 'wrap', gap: '1rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div style={{
            width: '40px',
            height: '40px',
            borderRadius: '50%',
            backgroundColor: recording ? 'var(--error)' : 'var(--bg-tertiary)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'white'
          }}>
            <Mic size={20} className={recording ? 'animate-pulse' : ''} />
          </div>
          <div>
            <div style={{ fontWeight: 600, fontSize: '1rem' }}>实时录制</div>
            {recording ? (
              <div style={{
                fontSize: '0.85rem',
                fontWeight: 700,
                color: 'var(--error)',
                display: 'flex',
                alignItems: 'center',
                gap: '0.4rem',
                marginTop: '0.1rem'
              }}>
                <span className="animate-pulse">●</span> {formatTime(elapsed)}
              </div>
            ) : (
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.1rem' }}>
                支持混合麦克风与系统音轨
              </div>
            )}
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          {!recording && mics.length > 0 && (
            <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
              <Settings2 size={14} style={{ position: 'absolute', left: '10px', color: 'var(--text-secondary)' }} />
              <select
                value={selectedMic}
                onChange={e => setSelectedMic(e.target.value)}
                style={{
                  padding: '6px 12px 6px 30px',
                  fontSize: '0.85rem',
                  borderRadius: '10px',
                  border: '1px solid var(--bg-tertiary)',
                  backgroundColor: 'var(--bg-tertiary)',
                  color: 'var(--text-primary)',
                  maxWidth: '180px',
                  cursor: 'pointer'
                }}
                className="hover-bright"
              >
                {mics.map(m => (
                  <option key={m.deviceId} value={m.deviceId}>
                    {m.label || '默认麦克风'}
                  </option>
                ))}
              </select>
            </div>
          )}

          {!recording ? (
            <button onClick={startRecording} className="btn-primary" style={{
              padding: '0.6rem 1.25rem', fontSize: '0.875rem', display: 'flex',
              alignItems: 'center', gap: '0.5rem',
            }}>
              <Circle size={16} fill="white" />
              开始录制
            </button>
          ) : (
            <button onClick={stopRecording} style={{
              padding: '0.6rem 1.25rem', fontSize: '0.875rem', borderRadius: '10px',
              backgroundColor: 'var(--error)', color: 'white', border: 'none',
              cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.5rem',
              fontWeight: 600
            }} className="hover-bright">
              <Square size={16} fill="white" />
              停止录制
            </button>
          )}
        </div>
      </div>

      {/* Source toggles + chunk counter during recording */}
      {recording && (
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '1rem',
          flexWrap: 'wrap',
          padding: '0.75rem',
          backgroundColor: 'rgba(0,0,0,0.1)',
          borderRadius: '12px',
          marginTop: '0.5rem'
        }}>
          <button onClick={toggleMic} style={{
            padding: '6px 14px', fontSize: '0.8rem', borderRadius: '20px',
            border: '1px solid',
            cursor: 'pointer',
            backgroundColor: micOn ? 'rgba(59,130,246,0.1)' : 'transparent',
            borderColor: micOn ? 'var(--accent-primary)' : 'var(--bg-tertiary)',
            color: micOn ? 'var(--accent-primary)' : 'var(--text-secondary)',
            display: 'flex',
            alignItems: 'center',
            gap: '0.4rem',
            fontWeight: 500,
            transition: 'var(--transition)'
          }}>
            <Mic size={14} />
            Mic {micOn ? '已开启' : '已静音'}
          </button>
          <button onClick={toggleSys} style={{
            padding: '6px 14px', fontSize: '0.8rem', borderRadius: '20px',
            border: '1px solid',
            cursor: 'pointer',
            backgroundColor: sysOn ? 'rgba(59,130,246,0.1)' : 'transparent',
            borderColor: sysOn ? 'var(--accent-primary)' : 'var(--bg-tertiary)',
            color: sysOn ? 'var(--accent-primary)' : 'var(--text-secondary)',
            display: 'flex',
            alignItems: 'center',
            gap: '0.4rem',
            fontWeight: 500,
            transition: 'var(--transition)'
          }}>
            <Volume2 size={14} />
            系统音 {sysOn ? '已开启' : '已静音'}
          </button>
          <span style={{
            fontSize: '0.75rem',
            color: 'var(--text-secondary)',
            marginLeft: 'auto',
            display: 'flex',
            alignItems: 'center',
            gap: '0.4rem'
          }}>
            <HardDrive size={12} />
            已保存 {chunksUploaded} 个分块
          </span>
        </div>
      )}

      {error && (
        <div style={{
          marginTop: '1rem',
          padding: '0.75rem 1rem',
          backgroundColor: 'rgba(239,68,68,0.1)',
          borderRadius: '10px',
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
          color: 'var(--error)',
          fontSize: '0.85rem'
        }}>
          <AlertCircle size={16} />
          {error}
        </div>
      )}

      {sleepSaved && (
        <div style={{
          marginTop: '1rem',
          padding: '0.75rem 1rem',
          backgroundColor: 'rgba(245,158,11,0.1)',
          borderRadius: '10px',
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
          color: 'var(--warning)',
          fontSize: '0.85rem',
          fontWeight: 600
        }}>
          <AlertCircle size={16} />
          检测到系统休眠，录音已自动保存
        </div>
      )}

      {saving && (
        <div style={{
          marginTop: '1rem',
          padding: '0.75rem 1rem',
          backgroundColor: 'rgba(59,130,246,0.1)',
          borderRadius: '10px',
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
          color: 'var(--accent-primary)',
          fontSize: '0.85rem',
          fontWeight: 600
        }}>
          <Loader2 size={16} className="animate-spin" />
          正在合并分块并保存...
        </div>
      )}

      {saveResult && (
        <div style={{
          marginTop: '1rem',
          padding: '0.75rem 1rem',
          backgroundColor: saveResult.success ? 'rgba(16,185,129,0.1)' : 'rgba(239,68,68,0.1)',
          borderRadius: '10px',
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
          color: saveResult.success ? 'var(--success)' : 'var(--error)',
          fontSize: '0.85rem',
          fontWeight: 600
        }}>
          {saveResult.success ? <CheckCircle2 size={16} /> : <AlertCircle size={16} />}
          {saveResult.success
            ? `录音已保存${saveResult.sizeMb ? ` (${saveResult.sizeMb} MB)` : ''}，转写已开始`
            : '保存失败，请手动上传'}
        </div>
      )}

      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }
      `}</style>
    </div>
  );
};

export default Recorder;
