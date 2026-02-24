import React from 'react';

interface LoadingSpinnerProps {
  message?: string;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  message,
  size = 'md',
  className = '',
}) => {
  const sizeClasses = {
    sm: 'w-6 h-6',
    md: 'w-12 h-12',
    lg: 'w-16 h-16',
  };

  return (
    <div className={`flex flex-col items-center justify-center ${className}`}>
      <div
        className={`${sizeClasses[size]} rounded-full animate-spin`}
        style={{ borderWidth: size === 'sm' ? 2 : 4, borderColor: 'var(--color-violet)', borderTopColor: 'transparent' }}
        role="status"
        aria-label="Loading"
      />
      {message && (
        <p className="mt-4 text-center" style={{ color: 'var(--color-text-muted)' }}>{message}</p>
      )}
    </div>
  );
};
