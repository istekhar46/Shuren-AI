import { useState, useEffect, useCallback, useRef } from 'react';
import { Room, RoomEvent } from 'livekit-client';
import { voiceService } from '../services/voiceService';
import type {
  AgentType,
  TranscriptionMessage,
  SessionStatus,
} from '../types';

export const useVoiceSession = () => {
  const [room, setRoom] = useState<Room | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [transcription, setTranscription] = useState<TranscriptionMessage[]>([]);
  const [sessionStatus, setSessionStatus] = useState<SessionStatus>({
    connected: false,
    participantCount: 0,
    duration: 0,
  });
  const [latency, setLatency] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [roomName, setRoomName] = useState<string | null>(null);
  const [isStarting, setIsStarting] = useState(false);

  const durationIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const startSession = useCallback(async (agentType: AgentType) => {
    if (isStarting) return;
    
    try {
      setIsStarting(true);
      setError(null);

      // Request microphone permission
      try {
        await navigator.mediaDevices.getUserMedia({ audio: true });
      } catch (permissionError) {
        if (permissionError instanceof Error) {
          if (permissionError.name === 'NotAllowedError') {
            throw new Error('Microphone permission denied. Please allow microphone access to use voice sessions.');
          } else if (permissionError.name === 'NotFoundError') {
            throw new Error('No microphone found. Please connect a microphone to use voice sessions.');
          } else {
            throw new Error(`Microphone access error: ${permissionError.message}`);
          }
        }
        throw new Error('Failed to access microphone');
      }

      // Get room token from backend
      let sessionData;
      try {
        sessionData = await voiceService.startSession(agentType);
      } catch (apiError) {
        if (apiError instanceof Error) {
          throw new Error(`Failed to create voice session: ${apiError.message}`);
        }
        throw new Error('Failed to create voice session');
      }

      // Create LiveKit room
      const newRoom = new Room({
        adaptiveStream: true,
        dynacast: true,
      });

      // Set up event listeners
      newRoom.on(RoomEvent.Connected, () => {
        setIsConnected(true);
        setSessionStatus((prev) => ({ ...prev, connected: true }));
        setError(null); // Clear any previous errors on successful connection
      });

      newRoom.on(RoomEvent.Disconnected, () => {
        setIsConnected(false);
        setSessionStatus((prev) => ({ ...prev, connected: false }));
      });

      newRoom.on(RoomEvent.ParticipantConnected, () => {
        setSessionStatus((prev) => ({
          ...prev,
          participantCount: newRoom.remoteParticipants.size + 1,
        }));
      });

      newRoom.on(RoomEvent.ParticipantDisconnected, () => {
        setSessionStatus((prev) => ({
          ...prev,
          participantCount: newRoom.remoteParticipants.size + 1,
        }));
      });

      // Handle connection errors
      newRoom.on(RoomEvent.ConnectionQualityChanged, (quality) => {
        if (quality === 'poor') {
          setError('Poor connection quality detected');
        }
      });

      newRoom.on(RoomEvent.Reconnecting, () => {
        setError('Connection lost, reconnecting...');
      });

      newRoom.on(RoomEvent.Reconnected, () => {
        setError(null);
      });

      // Listen for transcription data (from agent)
      newRoom.on(RoomEvent.DataReceived, (payload: Uint8Array) => {
        try {
          const decoder = new TextDecoder();
          const data = JSON.parse(decoder.decode(payload));

          if (data.type === 'transcription') {
            setTranscription((prev) => [
              ...prev,
              {
                id: data.id || `${Date.now()}-${Math.random()}`,
                speaker: data.speaker,
                text: data.text,
                timestamp: new Date(data.timestamp),
                isFinal: data.isFinal,
              },
            ]);
          }

          if (data.type === 'latency') {
            setLatency(data.value);
          }
        } catch (parseError) {
          console.error('Failed to parse data packet:', parseError);
        }
      });

      // Connect to room
      try {
        await newRoom.connect(sessionData.livekit_url, sessionData.token);
      } catch (connectionError) {
        if (connectionError instanceof Error) {
          throw new Error(`Failed to join room: ${connectionError.message}`);
        }
        throw new Error('Failed to join room');
      }

      setRoom(newRoom);
      setRoomName(sessionData.room_name);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to start voice session';
      setError(errorMessage);
      throw err;
    } finally {
      setIsStarting(false);
    }
  }, [isStarting]);

  const endSession = useCallback(async () => {
    if (room && roomName) {
      try {
        // Disconnect from LiveKit room
        try {
          await room.disconnect();
        } catch (disconnectError) {
          console.error('Error disconnecting from room:', disconnectError);
          // Continue with cleanup even if disconnect fails
        }

        // Notify backend to end session
        try {
          await voiceService.endSession(roomName);
        } catch (apiError) {
          console.error('Error ending session on backend:', apiError);
          // Continue with local cleanup even if backend call fails
        }

        // Clean up local state
        setRoom(null);
        setRoomName(null);
        setIsConnected(false);
        setTranscription([]);
        setSessionStatus({ connected: false, participantCount: 0, duration: 0 });
        setLatency(0);
        setError(null);
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : 'Failed to end session';
        setError(errorMessage);
        console.error('Error in endSession:', err);
      }
    }
  }, [room, roomName]);

  // Track session duration
  useEffect(() => {
    if (isConnected) {
      durationIntervalRef.current = setInterval(() => {
        setSessionStatus((prev) => ({
          ...prev,
          duration: prev.duration + 1,
        }));
      }, 1000);
    } else {
      if (durationIntervalRef.current) {
        clearInterval(durationIntervalRef.current);
        durationIntervalRef.current = null;
      }
    }

    return () => {
      if (durationIntervalRef.current) {
        clearInterval(durationIntervalRef.current);
      }
    };
  }, [isConnected]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (room) {
        room.disconnect();
      }
      if (durationIntervalRef.current) {
        clearInterval(durationIntervalRef.current);
      }
    };
  }, [room]);

  const toggleMicrophone = useCallback(async () => {
    if (!room) return;
    
    try {
      const currentState = room.localParticipant.isMicrophoneEnabled;
      await room.localParticipant.setMicrophoneEnabled(!currentState);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to toggle microphone';
      setError(errorMessage);
      console.error('Error toggling microphone:', err);
    }
  }, [room]);

  return {
    room,
    isConnected,
    transcription,
    sessionStatus,
    latency,
    error,
    roomName,
    isStarting,
    startSession,
    endSession,
    toggleMicrophone,
  };
};
