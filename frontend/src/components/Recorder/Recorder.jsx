import React, { useState, useRef, useEffect, useCallback } from 'react';
import { api } from '../../api/client';

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
  const [saveResult, setSaveResult] = useState(null); // { success, taskId } or null

  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);
  const timerRef = useRef(null);
  const startTimeRef = useRef(0);
  const audioCtxRef = useRef(null);
  const micGainRef = useRef(null);
  const sysGainRef = useRef(null);
  const micStreamRef = useRef(null);
  const sysStreamRef = useRef(null);
  const lastTickRef = useRef(Date.now());
  const recordingRef = useRef(false); // stable ref for event listeners

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

  // ── System sleep/hibernation detection ──
  // Auto-save file to backend history with 'recorded' status
  const autoSaveToHistory = useCallback(async (file) => {
    setSaving(true);
    setSaveResult(null);
    try {
      const formData = new FormData();
      formData.append('audio', file);
      const res = await api.recordings.save(formData);
      const taskId = res.data.task_id;
      setSaveResult({ success: true, taskId });
      onSaved?.(taskId);
    } catch (err) {
      console.error('Auto-save failed:', err);
      setSaveResult({ success: false });
    } finally {
      setSaving(false);
    }
  }, [onSaved]);

  // Emergency save: build a file from whatever chunks we have collected so far
  const emergencySave = useCallback(() => {
    if (chunksRef.current.length > 0) {
      const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
      const file = new File([blob], `recording_${Date.now()}.webm`, { type: 'audio/webm' });
      stopAllStreams();
      onRecorded?.(file);
      autoSaveToHistory(file);
    } else {
      stopAllStreams();
    }
  }, [onRecorded, autoSaveToHistory]);

  const emergencyStop = useCallback(() => {
    if (!recordingRef.current) return;
    recordingRef.current = false;

    // Try to gracefully stop MediaRecorder to flush remaining data
    const recorder = mediaRecorderRef.current;
    if (recorder && recorder.state !== 'inactive') {
      try {
        recorder.stop();
      } catch {
        // If stop() fails (interrupted context), do emergency save with existing chunks
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
    // Detect system wake from sleep via visibilitychange + time-jump
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible' && recordingRef.current) {
        const now = Date.now();
        const gap = now - lastTickRef.current;
        // If more than 30 seconds have passed since the last tick, the system likely slept
        if (gap > 30000) {
          console.warn(`[Recorder] System sleep detected (gap: ${Math.round(gap / 1000)}s). Auto-stopping recording.`);
          emergencyStop();
        }
      }
    };

    // Fallback: beforeunload to attempt save if page is closing
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
    chunksRef.current = [];

    try {
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
          video: { width: 1 },
          audio: true,
        });
      } catch {
        micStream.getTracks().forEach(t => t.stop());
        throw new Error('取消了屏幕共享或未勾选"共享音频"');
      }
      sysStreamRef.current = sysStream;

      if (sysStream.getAudioTracks().length === 0) {
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

      // 4. Record — use timeslice (5s) to flush data periodically for crash safety
      const recorder = new MediaRecorder(dest.stream, { mimeType: 'audio/webm' });
      mediaRecorderRef.current = recorder;

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };

      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
        const file = new File([blob], `recording_${Date.now()}.webm`, { type: 'audio/webm' });
        stopAllStreams();
        onRecorded?.(file);
        autoSaveToHistory(file);
      };

      recorder.start(5000); // flush data every 5 seconds
      setRecording(true);
      recordingRef.current = true;
      setMicOn(true);
      setSysOn(true);

      // Timer — also updates lastTickRef for sleep detection
      startTimeRef.current = Date.now();
      lastTickRef.current = Date.now();
      setElapsed(0);
      timerRef.current = setInterval(() => {
        lastTickRef.current = Date.now();
        setElapsed(Date.now() - startTimeRef.current);
      }, 1000);

      // Stop when screen share ends (user clicks "Stop sharing")
      sysStream.getVideoTracks()[0]?.addEventListener('ended', () => {
        stopRecording();
      });

    } catch (err) {
      setError(err.message);
      setRecording(false);
      recordingRef.current = false;
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
      borderRadius: '12px',
      border: recording ? '2px solid #ff3b30' : '2px solid var(--border)',
      padding: '1.25rem 1.5rem',
      marginBottom: '1.5rem',
      backgroundColor: recording ? 'rgba(255,59,48,0.04)' : 'var(--bg-secondary)',
      transition: 'all 0.3s ease',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: recording ? '0.75rem' : 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <span style={{ fontSize: '1.3rem' }}>🎙️</span>
          <span style={{ fontWeight: 600, fontSize: '0.95rem' }}>实时录制</span>
          {recording && (
            <span style={{
              padding: '2px 10px', borderRadius: '12px', fontSize: '0.8rem',
              fontWeight: 600, fontVariantNumeric: 'tabular-nums',
              backgroundColor: 'rgba(255,59,48,0.12)', color: '#ff3b30',
              animation: 'pulse 1.5s ease-in-out infinite',
            }}>
              ● {formatTime(elapsed)}
            </span>
          )}
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          {!recording && mics.length > 0 && (
            <select
              value={selectedMic}
              onChange={e => setSelectedMic(e.target.value)}
              style={{
                padding: '4px 8px', fontSize: '0.8rem', borderRadius: '6px',
                border: '1px solid var(--border)', backgroundColor: 'var(--bg-primary)',
                color: 'var(--text-primary)', maxWidth: '200px',
              }}
            >
              {mics.map(m => (
                <option key={m.deviceId} value={m.deviceId}>
                  {m.label || '默认麦克风'}
                </option>
              ))}
            </select>
          )}

          {!recording ? (
            <button onClick={startRecording} className="btn-primary" style={{
              padding: '6px 16px', fontSize: '0.85rem', display: 'flex',
              alignItems: 'center', gap: '6px',
            }}>
              🔴 开始录制
            </button>
          ) : (
            <button onClick={stopRecording} style={{
              padding: '6px 16px', fontSize: '0.85rem', borderRadius: '8px',
              backgroundColor: '#ff3b30', color: 'white', border: 'none',
              cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px',
            }}>
              ⏹ 停止录制
            </button>
          )}
        </div>
      </div>

      {/* Source toggles shown during recording */}
      {recording && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
          <button onClick={toggleMic} style={{
            padding: '4px 12px', fontSize: '0.8rem', borderRadius: '16px',
            border: '1px solid var(--border)', cursor: 'pointer',
            backgroundColor: micOn ? 'rgba(94,151,246,0.15)' : 'var(--bg-tertiary)',
            color: micOn ? '#5e97f6' : 'var(--text-secondary)',
            opacity: micOn ? 1 : 0.5, transition: 'all 0.2s',
          }}>
            🎤 Mic {micOn ? 'ON' : 'OFF'}
          </button>
          <button onClick={toggleSys} style={{
            padding: '4px 12px', fontSize: '0.8rem', borderRadius: '16px',
            border: '1px solid var(--border)', cursor: 'pointer',
            backgroundColor: sysOn ? 'rgba(94,151,246,0.15)' : 'var(--bg-tertiary)',
            color: sysOn ? '#5e97f6' : 'var(--text-secondary)',
            opacity: sysOn ? 1 : 0.5, transition: 'all 0.2s',
          }}>
            🔊 Sys {sysOn ? 'ON' : 'OFF'}
          </button>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
            点击切换音源 · 停止屏幕共享也会结束录制
          </span>
        </div>
      )}

      {!recording && !error && (
        <p style={{ margin: '0.5rem 0 0', fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
          同时录制系统声音和麦克风。点击后请选择屏幕并勾选"共享音频"。
        </p>
      )}

      {error && (
        <p style={{ margin: '0.5rem 0 0', fontSize: '0.8rem', color: '#ff3b30' }}>
          ❌ {error}
        </p>
      )}

      {sleepSaved && (
        <p style={{ margin: '0.5rem 0 0', fontSize: '0.8rem', color: '#FF9500', fontWeight: 600 }}>
          ⚠️ 检测到系统休眠，录音已自动保存
        </p>
      )}

      {saving && (
        <p style={{ margin: '0.5rem 0 0', fontSize: '0.8rem', color: '#5e97f6', fontWeight: 600 }}>
          💾 正在保存录音到历史记录...
        </p>
      )}

      {saveResult && (
        <p style={{
          margin: '0.5rem 0 0', fontSize: '0.8rem', fontWeight: 600,
          color: saveResult.success ? '#34c759' : '#ff3b30',
        }}>
          {saveResult.success ? '✅ 录音已保存到历史记录' : '❌ 保存失败，请手动上传'}
        </p>
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
