import React from 'react';
import { Scissors, Users, FileText, Link2, Mic, CheckCircle2, Loader2 } from 'lucide-react';

const STAGES = [
  { key: 'splitting',    label: '分割',     icon: Scissors },
  { key: 'censusing',    label: '普查',     icon: Users },
  { key: 'transcribing', label: '转写',     icon: FileText },
  { key: 'stitching',    label: '拼接',     icon: Link2 },
  { key: 'diarizing',    label: '分离',     icon: Mic },
  { key: 'done',         label: '完成',     icon: CheckCircle2 },
];

const STAGE_ORDER = STAGES.map(s => s.key);

function getStageState(stageKey, currentStatus, pipelineLog) {
  const currentIdx = STAGE_ORDER.indexOf(currentStatus);
  const stageIdx = STAGE_ORDER.indexOf(stageKey);

  if (currentIdx < 0) return 'pending';
  if (stageIdx < currentIdx) return 'completed';
  if (stageIdx === currentIdx) return 'active';
  return 'pending';
}

function getStageDuration(stageKey, pipelineLog) {
  if (!pipelineLog || pipelineLog.length === 0) return null;
  // Find the last event for this stage that has duration_ms
  const events = pipelineLog.filter(e => e.stage === stageKey && e.duration_ms);
  if (events.length === 0) return null;
  const last = events[events.length - 1];
  const ms = last.duration_ms;
  return ms >= 1000 ? `${(ms / 1000).toFixed(1)}s` : `${ms}ms`;
}

const PipelineTimeline = ({ status, pipelineLog, enableDiarization }) => {
  // Filter stages based on whether diarization is enabled
  const visibleStages = STAGES.filter(s => {
    if (!enableDiarization && (s.key === 'censusing' || s.key === 'diarizing')) return false;
    return true;
  });

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '0', marginBottom: '1.25rem', overflow: 'auto' }}>
      {visibleStages.map((stage, idx) => {
        const state = getStageState(stage.key, status, pipelineLog);
        const duration = getStageDuration(stage.key, pipelineLog);
        const Icon = stage.icon;
        const isLast = idx === visibleStages.length - 1;

        return (
          <React.Fragment key={stage.key}>
            <div style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '0.35rem',
              minWidth: '56px',
              opacity: state === 'pending' ? 0.35 : 1,
              transition: 'opacity 0.3s ease',
            }}>
              <div style={{
                width: '36px',
                height: '36px',
                borderRadius: '50%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                backgroundColor: state === 'completed' ? 'var(--success)'
                  : state === 'active' ? 'var(--accent-primary)'
                  : 'var(--bg-tertiary)',
                color: state === 'pending' ? 'var(--text-secondary)' : 'white',
                transition: 'all 0.3s ease',
              }}>
                {state === 'active' ? (
                  <Loader2 size={16} className="animate-spin" />
                ) : state === 'completed' ? (
                  <CheckCircle2 size={16} />
                ) : (
                  <Icon size={16} />
                )}
              </div>
              <span style={{
                fontSize: '0.7rem',
                fontWeight: state === 'active' ? 700 : 500,
                color: state === 'active' ? 'var(--accent-primary)'
                  : state === 'completed' ? 'var(--success)'
                  : 'var(--text-secondary)',
                whiteSpace: 'nowrap',
              }}>
                {stage.label}
              </span>
              {duration && (
                <span style={{
                  fontSize: '0.6rem',
                  color: 'var(--text-secondary)',
                  opacity: 0.7,
                }}>
                  {duration}
                </span>
              )}
            </div>
            {/* Connector line */}
            {!isLast && (
              <div style={{
                flex: 1,
                height: '2px',
                minWidth: '16px',
                backgroundColor: state === 'completed' ? 'var(--success)' : 'var(--bg-tertiary)',
                marginBottom: duration ? '1.2rem' : '0.8rem',
                transition: 'background-color 0.3s ease',
              }} />
            )}
          </React.Fragment>
        );
      })}
    </div>
  );
};

export default PipelineTimeline;
