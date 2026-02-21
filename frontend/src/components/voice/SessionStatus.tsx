import React from 'react';
import type { SessionStatus as SessionStatusType } from '../../types';

interface SessionStatusProps {
  status: SessionStatusType;
}

export const SessionStatus: React.FC<SessionStatusProps> = ({ status }) => {
  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="flex flex-col gap-2">
      <h2 className="text-lg font-semibold">Session Status</h2>
      <div className="grid grid-cols-3 gap-4 p-4 bg-gray-50 border border-gray-300 rounded-lg">
        <div className="flex flex-col">
          <span className="text-xs text-gray-600 uppercase">Connection</span>
          <span
            className={`text-sm font-semibold ${
              status.connected ? 'text-green-600' : 'text-red-600'
            }`}
          >
            {status.connected ? 'Connected' : 'Disconnected'}
          </span>
        </div>
        <div className="flex flex-col">
          <span className="text-xs text-gray-600 uppercase">Participants</span>
          <span className="text-sm font-semibold">{status.participantCount}</span>
        </div>
        <div className="flex flex-col">
          <span className="text-xs text-gray-600 uppercase">Duration</span>
          <span className="text-sm font-semibold">
            {formatDuration(status.duration)}
          </span>
        </div>
      </div>
    </div>
  );
};
