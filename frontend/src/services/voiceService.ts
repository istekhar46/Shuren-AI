import api from './api';
import type {
  AgentType,
} from '../types';
import type {
  VoiceSessionResponse,
  VoiceSessionStatus,
  ActiveSessionsResponse,
} from '../types/voice.types';

export const voiceService = {
  /**
   * Start a new voice session
   * @param agentType - Type of agent to start session with
   * @returns Voice session details with LiveKit connection info
   */
  async startSession(agentType: AgentType): Promise<VoiceSessionResponse> {
    const response = await api.post<VoiceSessionResponse>('/voice-sessions/start', {
      agent_type: agentType,
    });
    return response.data;
  },

  /**
   * Get status of a voice session
   * @param roomName - LiveKit room name
   * @returns Session status with participant information
   */
  async getStatus(roomName: string): Promise<VoiceSessionStatus> {
    const response = await api.get<VoiceSessionStatus>(`/voice-sessions/${roomName}/status`);
    return response.data;
  },

  /**
   * End a voice session
   * @param roomName - LiveKit room name
   */
  async endSession(roomName: string): Promise<void> {
    await api.delete(`/voice-sessions/${roomName}`);
  },

  /**
   * Get all active voice sessions
   * @returns List of active sessions
   */
  async getActiveSessions(): Promise<ActiveSessionsResponse> {
    const response = await api.get<ActiveSessionsResponse>('/voice-sessions/active');
    return response.data;
  },
};
