import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useSubscriptionStore } from '../../stores/subscriptionStore';
import { Clock } from 'lucide-react';

const QuotaBar = () => {
  const navigate = useNavigate();
  const { usage, fetchUsage } = useSubscriptionStore();

  useEffect(() => {
    fetchUsage();
  }, [fetchUsage]);

  if (!usage) return null;

  const { minutes_used, monthly_minutes_limit } = usage;
  
  // Handle unlimited (pro)
  if (monthly_minutes_limit === -1) {
    return (
      <div 
        onClick={() => navigate('/account')}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
          cursor: 'pointer',
          padding: '4px 8px',
          borderRadius: 'var(--border-radius)',
          backgroundColor: 'rgba(255, 255, 255, 0.05)'
        }}
        className="hover-bright"
      >
        <Clock size={14} />
        <span style={{ fontSize: '0.8rem' }}>配额: ∞</span>
      </div>
    );
  }

  const percentage = Math.min(100, (minutes_used / monthly_minutes_limit) * 100);
  
  let barColor = 'var(--accent-primary)';
  if (percentage > 90) barColor = 'var(--error)';
  else if (percentage > 60) barColor = '#f59e0b'; // amber-500

  return (
    <div 
      onClick={() => navigate('/account')}
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: '4px',
        cursor: 'pointer',
        minWidth: '120px'
      }}
      className="hover-bright"
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
        <span>已用 {Math.round(minutes_used)} / {monthly_minutes_limit} 分</span>
      </div>
      <div style={{
        height: '6px',
        backgroundColor: 'var(--bg-tertiary)',
        borderRadius: '3px',
        overflow: 'hidden'
      }}>
        <div style={{
          height: '100%',
          width: `${percentage}%`,
          backgroundColor: barColor,
          transition: 'width 0.3s ease'
        }} />
      </div>
    </div>
  );
};

export default QuotaBar;
