import React, { createContext, useContext, useState } from 'react';
import type { ReactNode } from 'react';
import type {
  AgentType,
  TranscriptionMessage,
  SessionStatus,
} from '../types';

interface VoiceContextType {
  isConnected: boolean;
  roomName: string | null;
  agentType: AgentType | null;
  transcription: TranscriptionMessage[];
  sessionStatus: SessionStatus;
  latency: number;
  error: string | null;
  setIsConnected: (connected: boolean) => void;
  setRoomName: (name: string | null) => void;
  setAgentType: (type: AgentType | null) => void;
  setTranscription: (messages: TranscriptionMessage[]) => void;
  addTranscription: (message: TranscriptionMessage) => void;
  setSessionStatus: (status: SessionStatus) => void;
  setLatency: (latency: number) => void;
  setError: (error: string | null) => void;
  resetSession: () => void;
}

const VoiceContext = createContext<VoiceContextType | undefined>(undefined);

interface VoiceProviderProps {
  children: ReactNode;
}

export const VoiceProvider: React.FC<VoiceProviderProps> = ({ children }) => {
  const [isConnected, setIsConnected] = useState(false);
  const [roomName, setRoomName] = useState<string | null>(null);
  const [agentType, setAgentType] = useState<AgentType | null>(null);
  const [transcription, setTranscription] = useState<TranscriptionMessage[]>([]);
  const [sessionStatus, setSessionStatus] = useState<SessionStatus>({
    connected: false,
    participantCount: 0,
    duration: 0,
  });
  const [latency, setLatency] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const addTranscription = (message: TranscriptionMessage) => {
    setTranscription((prev) => [...prev, message]);
  };

  const resetSession = () => {
    setIsConnected(false);
    setRoomName(null);
    setAgentType(null);
    setTranscription([]);
    setSessionStatus({
      connected: false,
      participantCount: 0,
      duration: 0,
    });
    setLatency(0);
    setError(null);
  };

  const value: VoiceContextType = {
    isConnected,
    roomName,
    agentType,
    transcription,
    sessionStatus,
    latency,
    error,
    setIsConnected,
    setRoomName,
    setAgentType,
    setTranscription,
    addTranscription,
    setSessionStatus,
    setLatency,
    setError,
    resetSession,
  };

  return (
    <VoiceContext.Provider value={value}>{children}</VoiceContext.Provider>
  );
};

export const useVoice = (): VoiceContextType => {
  const context = useContext(VoiceContext);
  if (context === undefined) {
    throw new Error('useVoice must be used within a VoiceProvider');
  }
  return context;
};
