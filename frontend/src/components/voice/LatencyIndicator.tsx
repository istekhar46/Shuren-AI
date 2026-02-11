import React from 'react';

interface LatencyIndicatorProps {
  latency: number;
}

export const LatencyIndicator: React.FC<LatencyIndicatorProps> = ({
  latency,
}) => {
  const getLatencyColor = (ms: number) => {
    if (ms < 100) return 'text-green-600';
    if (ms < 300) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getLatencyLabel = (ms: number) => {
    if (ms < 100) return 'Excellent';
    if (ms < 300) return 'Good';
    return 'Poor';
  };

  return (
    <div className="flex items-center gap-2 p-3 bg-gray-50 border border-gray-300 rounded-lg">
      <span className="text-sm text-gray-600">Latency:</span>
      <span className={`text-sm font-semibold ${getLatencyColor(latency)}`}>
        {latency}ms
      </span>
      <span className={`text-xs ${getLatencyColor(latency)}`}>
        ({getLatencyLabel(latency)})
      </span>
    </div>
  );
};
