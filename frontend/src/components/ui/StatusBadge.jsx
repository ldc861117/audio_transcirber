import React from 'react';

/**
 * StatusBadge — Colored label for status indicators
 * 
 * @param {'primary'|'success'|'warning'|'error'} variant - Color variant
 * @param {ReactNode} children - Badge text
 * @param {string} className - Additional CSS classes
 */
const StatusBadge = ({
  variant = 'primary',
  children,
  className = '',
  ...props
}) => {
  const classes = [
    'badge',
    `badge-${variant}`,
    className,
  ].filter(Boolean).join(' ');

  return (
    <span className={classes} {...props}>
      {children}
    </span>
  );
};

export default StatusBadge;
