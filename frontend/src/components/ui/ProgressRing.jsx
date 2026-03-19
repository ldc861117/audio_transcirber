import React from 'react';

/**
 * ProgressRing — Circular progress indicator
 * 
 * @param {number} percentage - 0-100 progress value
 * @param {number} size - Diameter in pixels
 * @param {number} strokeWidth - Ring thickness in pixels
 * @param {string} color - CSS color for the progress arc
 * @param {string} trackColor - CSS color for the background track
 * @param {boolean} showLabel - Show percentage text in center
 */
const ProgressRing = ({
  percentage = 0,
  size = 48,
  strokeWidth = 4,
  color = 'var(--accent-primary)',
  trackColor = 'var(--bg-tertiary)',
  showLabel = true,
}) => {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (percentage / 100) * circumference;

  return (
    <div style={{ position: 'relative', width: size, height: size }}>
      <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
        {/* Track */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={trackColor}
          strokeWidth={strokeWidth}
        />
        {/* Progress */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          style={{ transition: 'stroke-dashoffset 0.5s ease' }}
        />
      </svg>
      {showLabel && (
        <div style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: size * 0.22,
          fontFamily: 'var(--font-headline)',
          fontWeight: 700,
          color: 'var(--text-primary)',
        }}>
          {Math.round(percentage)}%
        </div>
      )}
    </div>
  );
};

export default ProgressRing;
