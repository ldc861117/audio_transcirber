import React from 'react';

/**
 * GlassCard — Glassmorphism container component
 * 
 * @param {'panel'|'card'|'subtle'} variant - Glass intensity
 * @param {boolean} glow - Add AI glow effect
 * @param {function} onClick - Click handler
 * @param {string} className - Additional CSS classes
 * @param {object} style - Additional inline styles
 * @param {ReactNode} children - Content
 */
const GlassCard = ({
  variant = 'card',
  glow = false,
  onClick,
  className = '',
  style = {},
  children,
  ...props
}) => {
  const variantClass = {
    panel: 'glass-panel',
    card: 'glass-card',
    subtle: 'glass-subtle',
  }[variant] || 'glass-card';

  const classes = [
    variantClass,
    glow ? 'ai-glow' : '',
    onClick ? 'press-effect' : '',
    className,
  ].filter(Boolean).join(' ');

  return (
    <div
      className={classes}
      onClick={onClick}
      style={{
        padding: '1.5rem',
        borderRadius: 'var(--border-radius)',
        cursor: onClick ? 'pointer' : 'default',
        transition: 'var(--transition)',
        ...style,
      }}
      {...props}
    >
      {children}
    </div>
  );
};

export default GlassCard;
