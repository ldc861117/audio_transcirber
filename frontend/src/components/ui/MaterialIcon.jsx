import React from 'react';

/**
 * MaterialIcon — Google Material Symbols wrapper
 * 
 * @param {string} name - Material Symbol name (e.g. 'graphic_eq', 'mic')
 * @param {number} size - Icon size in pixels
 * @param {boolean} filled - Use Filled variant
 * @param {string} className - Additional CSS classes
 * @param {object} style - Additional inline styles
 */
const MaterialIcon = ({
  name,
  size = 24,
  filled = false,
  className = '',
  style = {},
  ...props
}) => {
  const classes = [
    'material-symbols-rounded',
    filled ? 'filled' : '',
    className,
  ].filter(Boolean).join(' ');

  return (
    <span
      className={classes}
      style={{
        fontSize: `${size}px`,
        lineHeight: 1,
        ...style,
      }}
      {...props}
    >
      {name}
    </span>
  );
};

export default MaterialIcon;
