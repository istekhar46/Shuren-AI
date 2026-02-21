import React, { useState } from 'react';
import { useVoiceSession } from '../hooks/useVoiceSession';
import { AgentSelector } from '../components/voice/AgentSelector';
import { VoiceControls } from '../components/voice/VoiceControls';
import { TranscriptionDisplay } from '../components/voice/TranscriptionDisplay';
import { SessionStatus } from '../components/voice/SessionStatus';
import { LatencyIndicator } from '../components/voice/LatencyIndicator';
import { ErrorDisplay } from '../components/voice/ErrorDisplay';
import type { AgentType } from '../types';

export const VoicePage: React.FC = () => {
  const [selectedAgent, setSelectedAgent] = useState<AgentType>('general_assistant');
  const [dismissedError, setDismissedError] = useState(false);
  const {
    room,
    isConnected,
    transcription,
    sessionStatus,
    latency,
    error,
    isStarting,
    startSession,
    endSession,
    toggleMicrophone,
  } = useVoiceSession();

  const isMicrophoneEnabled = room?.localParticipant?.isMicrophoneEnabled ?? true;

  const handleStart = async () => {
    setDismissedError(false);
    try {
      await startSession(selectedAgent);
    } catch (err) {
      console.error('Failed to start session:', err);
    }
  };

  const handleEnd = async () => {
    await endSession();
  };

  const handleDismissError = () => {
    setDismissedError(true);
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-6xl">
      <h1 className="text-3xl font-bold mb-8">Voice Session</h1>

      {error && !dismissedError && (
        <div className="mb-6">
          <ErrorDisplay error={error} onDismiss={handleDismissError} />
        </div>
      )}

      <div className="space-y-6">
        {!isConnected ? (
          <div className="bg-white p-6 rounded-lg shadow-md space-y-4">
            <h2 className="text-xl font-semibold">Start a Voice Session</h2>
            <AgentSelector
              value={selectedAgent}
              onChange={setSelectedAgent}
              disabled={isStarting}
            />
            <VoiceControls
              isConnected={isConnected}
              isStarting={isStarting}
              onStart={handleStart}
              onEnd={handleEnd}
            />
          </div>
        ) : (
          <>
            <div className="bg-white p-6 rounded-lg shadow-md space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-semibold">Active Session</h2>
                <VoiceControls
                  isConnected={isConnected}
                  isStarting={isStarting}
                  isMicrophoneEnabled={isMicrophoneEnabled}
                  onStart={handleStart}
                  onEnd={handleEnd}
                  onToggleMicrophone={toggleMicrophone}
                />
              </div>
              <div className="flex gap-4">
                <div className="flex-1">
                  <SessionStatus status={sessionStatus} />
                </div>
                <div className="flex-shrink-0">
                  <LatencyIndicator latency={latency} />
                </div>
              </div>
            </div>

            <div className="bg-white p-6 rounded-lg shadow-md">
              <TranscriptionDisplay messages={transcription} />
            </div>
          </>
        )}
      </div>
    </div>
  );
};
