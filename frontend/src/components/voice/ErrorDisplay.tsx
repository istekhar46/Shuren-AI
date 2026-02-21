import React from 'react';

interface ErrorDisplayProps {
  error: string;
  onDismiss?: () => void;
}

export const ErrorDisplay: React.FC<ErrorDisplayProps> = ({
  error,
  onDismiss,
}) => {
  return (
    <div className="p-4 bg-red-50 border border-red-300 rounded-lg flex items-start justify-between">
      <div className="flex-1">
        <p className="text-red-800 font-medium">Error</p>
        <p className="text-red-700 text-sm mt-1">{error}</p>
      </div>
      {onDismiss && (
        <button
          onClick={onDismiss}
          className="ml-4 text-red-600 hover:text-red-800 font-bold"
          aria-label="Dismiss error"
        >
          ×
        </button>
      )}
    </div>
  );
};
