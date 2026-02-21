import React from 'react';

interface VoiceControlsProps {
  isConnected: boolean;
  isStarting: boolean;
  isMicrophoneEnabled?: boolean;
  onStart: () => void;
  onEnd: () => void;
  onToggleMicrophone?: () => void;
}

export const VoiceControls: React.FC<VoiceControlsProps> = ({
  isConnected,
  isStarting,
  isMicrophoneEnabled = true,
  onStart,
  onEnd,
  onToggleMicrophone,
}) => {
  return (
    <div className="flex gap-4">
      {!isConnected ? (
        <button
          onClick={onStart}
          disabled={isStarting}
          className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors font-medium"
        >
          {isStarting ? 'Starting...' : 'Start Voice Session'}
        </button>
      ) : (
        <>
          {onToggleMicrophone && (
            <button
              onClick={onToggleMicrophone}
              className={`px-6 py-3 rounded-lg transition-colors font-medium ${
                isMicrophoneEnabled
                  ? 'bg-blue-600 text-white hover:bg-blue-700'
                  : 'bg-gray-600 text-white hover:bg-gray-700'
              }`}
              title={isMicrophoneEnabled ? 'Mute microphone' : 'Unmute microphone'}
            >
              {isMicrophoneEnabled ? '🎤 Mute' : '🔇 Unmute'}
            </button>
          )}
          <button
            onClick={onEnd}
            className="px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors font-medium"
          >
            End Session
          </button>
        </>
      )}
    </div>
  );
};
