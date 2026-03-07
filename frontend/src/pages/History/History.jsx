import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import { api } from '../../api/client';
import { useConfigStore } from '../../stores/configStore';
import TranscriptView from '../../components/Transcript/TranscriptView';
import ExportPanel from '../../components/Transcript/ExportPanel';

const ACTIVE_STATUSES = ['queued', 'splitting', 'transcribing', 'diarizing'];

const STATUS_MAP = {
  recorded: { label: '🎙️ 未转写', color: '#FF9500', bg: 'rgba(255,149,0,0.1)' },
  queued: { label: '⏳ 排队中', color: '#5e97f6', bg: 'rgba(94,151,246,0.1)' },
  splitting: { label: '✂️ 分割中', color: '#5e97f6', bg: 'rgba(94,151,246,0.1)' },
  transcribing: { label: '📝 转写中', color: '#5e97f6', bg: 'rgba(94,151,246,0.1)' },
  diarizing: { label: '🎤 识别中', color: '#5e97f6', bg: 'rgba(94,151,246,0.1)' },
  done: { label: '✅ 完成', color: '#34c759', bg: 'rgba(52,199,89,0.1)' },
  error: { label: '❌ 失败', color: '#ff3b30', bg: 'rgba(255,59,48,0.1)' },
};

const STATUS_TEXT = {
  queued: '排队中...',
  splitting: '分割音频...',
  transcribing: '转写中',
  diarizing: '识别说话人...',
};

const History = () => {
  const [searchParams] = useSearchParams();
  const [tasks, setTasks] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [expandedId, setExpandedId] = useState(searchParams.get('task') || null);
  const [expandedData, setExpandedData] = useState(null);
  const [transcribing, setTranscribing] = useState({}); // { taskId: true }
  const [activeProgress, setActiveProgress] = useState({}); // { taskId: { status, total_chunks, completed_chunks, current_chunk, ... } }
  const progressPollRef = useRef(null);

  const { provider, model, baseUrl, apiKey, enableDiarization } = useConfigStore();

  const fetchTasks = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.transcriptions.list({ page, per_page: 15, search });
      setTasks(res.data.items || []);
      setTotal(res.data.total || 0);
    } catch (err) {
      console.error('Failed to load history', err);
    } finally {
      setLoading(false);
    }
  }, [page, search]);

  useEffect(() => { fetchTasks(); }, [fetchTasks]);

  // Poll progress for all active tasks
  useEffect(() => {
    const activeTasks = tasks.filter(t => ACTIVE_STATUSES.includes(t.status));
    if (activeTasks.length === 0) {
      if (progressPollRef.current) {
        clearInterval(progressPollRef.current);
        progressPollRef.current = null;
      }
      return;
    }

    const pollActiveProgress = async () => {
      const updates = {};
      let anyFinished = false;
      for (const task of activeTasks) {
        try {
          const res = await api.transcriptions.status(task.id);
          updates[task.id] = res.data;
          if (res.data.status === 'done' || res.data.status === 'error') {
            anyFinished = true;
          }
        } catch (err) {
          // ignore poll errors
        }
      }
      setActiveProgress(prev => ({ ...prev, ...updates }));
      if (anyFinished) {
        fetchTasks(); // Refresh task list when any task finishes
      }
    };

    // Poll immediately on mount
    pollActiveProgress();

    if (progressPollRef.current) clearInterval(progressPollRef.current);
    progressPollRef.current = setInterval(pollActiveProgress, 1500);

    return () => {
      if (progressPollRef.current) {
        clearInterval(progressPollRef.current);
        progressPollRef.current = null;
      }
    };
  }, [tasks, fetchTasks]);

  // Auto-expand task detail if navigated with ?task=xxx
  useEffect(() => {
    if (expandedId && !expandedData) {
      api.transcriptions.status(expandedId)
        .then(res => setExpandedData(res.data))
        .catch(() => setExpandedData(null));
    }
  }, [expandedId]);

  const handleExpand = async (taskId) => {
    if (expandedId === taskId) {
      setExpandedId(null);
      setExpandedData(null);
      return;
    }
    setExpandedId(taskId);
    setExpandedData(null);
    try {
      const res = await api.transcriptions.status(taskId);
      setExpandedData(res.data);
    } catch (err) {
      setExpandedData({ error: '无法加载详情' });
    }
  };

  const handleDelete = async (taskId, e) => {
    e.stopPropagation();
    if (!confirm('确定删除此任务？')) return;
    try {
      await api.transcriptions.delete(taskId);
      fetchTasks();
      if (expandedId === taskId) { setExpandedId(null); setExpandedData(null); }
    } catch (err) {
      alert('删除失败');
    }
  };

  const handleTranscribe = async (taskId, e) => {
    e.stopPropagation();
    setTranscribing(prev => ({ ...prev, [taskId]: true }));
    try {
      await api.recordings.transcribe(taskId, {
        provider,
        model,
        base_url: baseUrl,
        api_key: apiKey,
        enable_diarization: enableDiarization,
      });
      // Refresh list to show updated status
      fetchTasks();
    } catch (err) {
      alert(err.response?.data?.error || '启动转写失败');
    } finally {
      setTranscribing(prev => ({ ...prev, [taskId]: false }));
    }
  };

  const getTaskProgress = (taskId) => {
    const prog = activeProgress[taskId];
    if (!prog) return null;
    const total = Math.max(prog.total_chunks || 1, 1);
    const completed = prog.completed_chunks || 0;
    const pct = Math.round((completed / total) * 100);
    return { ...prog, pct, total, completed };
  };

  const formatDate = (iso) => {
    if (!iso) return '';
    return new Date(iso).toLocaleString('zh-CN', {
      year: 'numeric', month: '2-digit', day: '2-digit',
      hour: '2-digit', minute: '2-digit',
    });
  };

  const formatDuration = (seconds) => {
    if (!seconds || seconds === 0) return '';
    const m = Math.floor(seconds / 60);
    const s = Math.round(seconds % 60);
    return `${m}:${String(s).padStart(2, '0')}`;
  };

  const totalPages = Math.ceil(total / 15);

  const renderStatusBadge = (status) => {
    const info = STATUS_MAP[status] || { label: status, color: 'var(--text-secondary)', bg: 'var(--bg-tertiary)' };
    return (
      <span style={{
        padding: '3px 10px', borderRadius: '12px', fontSize: '0.8rem',
        fontWeight: 600, color: info.color, backgroundColor: info.bg,
        whiteSpace: 'nowrap',
      }}>
        {info.label}
      </span>
    );
  };

  return (
    <div>
      <h1 style={{ fontSize: '2rem', marginBottom: '2rem' }}>历史记录</h1>

      {/* Search bar */}
      <div style={{ marginBottom: '1.5rem' }}>
        <input value={search} onChange={e => { setSearch(e.target.value); setPage(1); }}
          placeholder="🔍 搜索文件名..."
          style={{
            width: '100%', maxWidth: '400px', padding: '0.75rem 1rem',
            borderRadius: '8px', border: '1px solid var(--border)',
            backgroundColor: 'var(--bg-secondary)', color: 'var(--text-primary)',
            fontSize: '0.9rem',
          }} />
      </div>

      {loading ? (
        <div className="card" style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-secondary)' }}>加载中...</div>
      ) : tasks.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: '4rem' }}>
          <span style={{ fontSize: '3rem', display: 'block', marginBottom: '1rem' }}>🕒</span>
          <h3>暂无历史记录</h3>
          <p style={{ color: 'var(--text-secondary)', marginTop: '0.5rem' }}>录制或上传音频后，记录将在此显示</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          {tasks.map(task => {
            const isActive = ACTIVE_STATUSES.includes(task.status);
            const prog = getTaskProgress(task.id);
            const liveStatus = prog?.status || task.status;
            const liveStatusInfo = STATUS_MAP[liveStatus] || STATUS_MAP[task.status];

            return (
            <div key={task.id}>
              <div onClick={() => handleExpand(task.id)}
                className="card" style={{
                  padding: '1rem 1.5rem', cursor: 'pointer',
                  display: 'grid', gridTemplateColumns: '1fr auto auto auto',
                  alignItems: 'center', gap: '1rem',
                  borderLeft: expandedId === task.id ? '3px solid #5e97f6' : '3px solid transparent',
                }}>
                <div style={{ minWidth: 0 }}>
                  <span style={{ fontWeight: 600, display: 'block', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {task.filename}
                  </span>
                  <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                    {formatDate(task.created_at)} · {task.file_size_mb?.toFixed(1)} MB
                    {task.duration_seconds > 0 && ` · ${formatDuration(task.duration_seconds)}`}
                    {task.provider && ` · ${task.provider}`}
                  </span>

                  {/* Inline progress bar for active tasks */}
                  {isActive && prog && (
                    <div style={{ marginTop: '0.5rem' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.25rem' }}>
                        <span style={{ fontSize: '0.75rem', color: '#5e97f6', fontWeight: 600 }}>
                          {STATUS_TEXT[liveStatus] || '处理中...'}
                          {liveStatus === 'transcribing' && prog.total > 0 && ` ${prog.completed}/${prog.total}`}
                        </span>
                        <span style={{ fontSize: '0.75rem', color: '#5e97f6', fontWeight: 700 }}>
                          {prog.pct}%
                        </span>
                      </div>
                      <div style={{
                        height: '4px', backgroundColor: 'var(--bg-tertiary)',
                        borderRadius: '2px', overflow: 'hidden',
                      }}>
                        <div style={{
                          height: '100%', width: `${prog.pct}%`,
                          background: 'linear-gradient(90deg, #5e97f6, #34c759)',
                          borderRadius: '2px',
                          transition: 'width 0.5s cubic-bezier(0.4, 0, 0.2, 1)',
                        }} />
                      </div>
                    </div>
                  )}
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  {renderStatusBadge(liveStatus)}

                  {/* Transcribe button for saved recordings */}
                  {(task.status === 'recorded' || task.status === 'error') && (
                    <button
                      onClick={(e) => handleTranscribe(task.id, e)}
                      disabled={transcribing[task.id]}
                      style={{
                        padding: '4px 12px', borderRadius: '6px', fontSize: '0.8rem',
                        fontWeight: 600, border: '1px solid #5e97f6',
                        backgroundColor: 'rgba(94,151,246,0.1)', color: '#5e97f6',
                        cursor: transcribing[task.id] ? 'wait' : 'pointer',
                        opacity: transcribing[task.id] ? 0.6 : 1,
                        transition: 'all 0.2s',
                        whiteSpace: 'nowrap',
                      }}
                    >
                      {transcribing[task.id] ? '⏳ 启动中...' : '🚀 开始转写'}
                    </button>
                  )}
                </div>

                <button onClick={(e) => handleDelete(task.id, e)}
                  style={{ padding: '0.3rem 0.6rem', borderRadius: '6px', border: '1px solid var(--border)', backgroundColor: 'transparent', color: '#ff3b30', cursor: 'pointer', fontSize: '0.8rem' }}>
                  🗑️
                </button>
                <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                  {expandedId === task.id ? '▲' : '▼'}
                </span>
              </div>

              {expandedId === task.id && (
                <div className="card" style={{ padding: '1.5rem', marginTop: '0.25rem', borderLeft: '3px solid #5e97f6' }}>
                  {task.status === 'recorded' ? (
                    <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-secondary)' }}>
                      <span style={{ fontSize: '2rem', display: 'block', marginBottom: '0.5rem' }}>🎙️</span>
                      <p>此录音尚未转写，点击上方「开始转写」按钮进行转写</p>
                    </div>
                  ) : isActive ? (
                    /* Active task: show detailed progress */
                    <div style={{ padding: '1.5rem' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                          <span style={{ fontSize: '1.5rem' }}>
                            {liveStatus === 'splitting' ? '✂️' :
                             liveStatus === 'transcribing' ? '📝' :
                             liveStatus === 'diarizing' ? '🎤' : '⏳'}
                          </span>
                          <div>
                            <span style={{ fontWeight: 600, fontSize: '1rem' }}>
                              {STATUS_TEXT[liveStatus] || '处理中...'}
                            </span>
                            {liveStatus === 'transcribing' && prog && (
                              <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginLeft: '0.5rem' }}>
                                {prog.completed}/{prog.total} 分段
                              </span>
                            )}
                          </div>
                        </div>
                        <span style={{ color: '#5e97f6', fontWeight: 700, fontSize: '1.25rem' }}>
                          {prog?.pct || 0}%
                        </span>
                      </div>
                      <div style={{
                        height: '8px', backgroundColor: 'var(--bg-tertiary)',
                        borderRadius: '4px', overflow: 'hidden',
                      }}>
                        <div style={{
                          height: '100%', width: `${prog?.pct || 0}%`,
                          background: 'linear-gradient(90deg, #5e97f6, #34c759)',
                          borderRadius: '4px',
                          transition: 'width 0.5s cubic-bezier(0.4, 0, 0.2, 1)',
                        }} />
                      </div>
                      {prog?.current_chunk > 0 && (
                        <p style={{ marginTop: '0.75rem', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                          正在处理第 {prog.current_chunk} 段 (共 {prog.total} 段)
                        </p>
                      )}
                    </div>
                  ) : expandedData ? (
                    <>
                      <TranscriptView
                        transcript={expandedData.transcript}
                        speakers={expandedData.speakers || []}
                        enableDiarization={expandedData.enable_diarization}
                      />
                      <ExportPanel taskId={task.id} />
                    </>
                  ) : (
                    <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-secondary)' }}>加载中...</div>
                  )}
                </div>
              )}
            </div>
            );
          })}

          {/* Pagination */}
          {totalPages > 1 && (
            <div style={{ display: 'flex', justifyContent: 'center', gap: '0.5rem', marginTop: '1rem' }}>
              <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}
                style={{ padding: '0.4rem 0.8rem', borderRadius: '6px', border: '1px solid var(--border)', backgroundColor: 'transparent', color: 'var(--text-primary)', cursor: 'pointer' }}>
                ← 上一页
              </button>
              <span style={{ padding: '0.4rem 0.8rem', color: 'var(--text-secondary)' }}>
                {page} / {totalPages}
              </span>
              <button onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page === totalPages}
                style={{ padding: '0.4rem 0.8rem', borderRadius: '6px', border: '1px solid var(--border)', backgroundColor: 'transparent', color: 'var(--text-primary)', cursor: 'pointer' }}>
                下一页 →
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default History;
