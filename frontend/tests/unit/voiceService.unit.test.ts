import { describe, it, expect, vi, beforeEach } from 'vitest';
import { voiceService } from '../../src/services/voiceService';
import api from '../../src/services/api';
import type {
  VoiceSessionResponse,
  VoiceSessionStatus,
  ActiveSessionsResponse,
} from '../../src/types/voice.types';

// Mock the api module
vi.mock('../../src/services/api');

describe('voiceService Unit Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('startSession', () => {
    it('should call POST /voice-sessions/start and return session details', async () => {
      const mockSession: VoiceSessionResponse = {
        room_name: 'room-abc123',
        token: 'livekit-token-xyz',
        livekit_url: 'wss://livekit.example.com',
        agent_type: 'workout',
        expires_at: '2024-01-15T19:00:00Z',
      };

      vi.mocked(api.post).mockResolvedValue({
        data: mockSession,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      });

      const result = await voiceService.startSession('workout');

      expect(api.post).toHaveBeenCalledWith('/voice-sessions/start', {
        agent_type: 'workout',
      });
      expect(api.post).toHaveBeenCalledTimes(1);
      expect(result).toEqual(mockSession);
      expect(result.roomName).toBe('room-abc123');
      expect(result.agentType).toBe('workout');
    });

    it('should start session with diet agent', async () => {
      const mockSession: VoiceSessionResponse = {
        room_name: 'room-def456',
        token: 'livekit-token-abc',
        livekit_url: 'wss://livekit.example.com',
        agent_type: 'diet',
        expires_at: '2024-01-15T19:00:00Z',
      };

      vi.mocked(api.post).mockResolvedValue({
        data: mockSession,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      });

      const result = await voiceService.startSession('diet');

      expect(api.post).toHaveBeenCalledWith('/voice-sessions/start', {
        agent_type: 'diet',
      });
      expect(result.agent_type).toBe('diet');
    });

    it('should throw error when API call fails', async () => {
      const mockError = new Error('Network error');
      vi.mocked(api.post).mockRejectedValue(mockError);

      await expect(voiceService.startSession('workout')).rejects.toThrow('Network error');
    });

    it('should throw error when user is not authenticated (401)', async () => {
      const mockError = {
        response: {
          status: 401,
          data: { detail: 'Not authenticated' },
        },
      };
      vi.mocked(api.post).mockRejectedValue(mockError);

      await expect(voiceService.startSession('workout')).rejects.toThrow();
    });
  });

  describe('getStatus', () => {
    it('should call GET /voice-sessions/{roomName}/status and return status', async () => {
      const mockStatus: VoiceSessionStatus = {
        room_name: 'room-abc123',
        active: true,
        participants: 2,
        agent_connected: true,
        created_at: '2024-01-15T18:00:00Z',
      };

      vi.mocked(api.get).mockResolvedValue({
        data: mockStatus,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      });

      const result = await voiceService.getStatus('room-abc123');

      expect(api.get).toHaveBeenCalledWith('/voice-sessions/room-abc123/status');
      expect(api.get).toHaveBeenCalledTimes(1);
      expect(result).toEqual(mockStatus);
      expect(result.active).toBe(true);
      expect(result.participants).toBe(2);
    });

    it('should return inactive status when session ended', async () => {
      const mockStatus: VoiceSessionStatus = {
        room_name: 'room-abc123',
        active: false,
        participants: 0,
        agent_connected: false,
        created_at: '2024-01-15T18:00:00Z',
      };

      vi.mocked(api.get).mockResolvedValue({
        data: mockStatus,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      });

      const result = await voiceService.getStatus('room-abc123');

      expect(result.active).toBe(false);
      expect(result.participants).toBe(0);
    });

    it('should throw error when room not found (404)', async () => {
      const mockError = {
        response: {
          status: 404,
          data: { detail: 'Room not found' },
        },
      };
      vi.mocked(api.get).mockRejectedValue(mockError);

      await expect(voiceService.getStatus('invalid-room')).rejects.toThrow();
    });

    it('should throw error when API call fails', async () => {
      const mockError = new Error('Network error');
      vi.mocked(api.get).mockRejectedValue(mockError);

      await expect(voiceService.getStatus('room-abc123')).rejects.toThrow('Network error');
    });
  });

  describe('endSession', () => {
    it('should call DELETE /voice-sessions/{roomName}', async () => {
      vi.mocked(api.delete).mockResolvedValue({
        data: undefined,
        status: 204,
        statusText: 'No Content',
        headers: {},
        config: {} as any,
      });

      await voiceService.endSession('room-abc123');

      expect(api.delete).toHaveBeenCalledWith('/voice-sessions/room-abc123');
      expect(api.delete).toHaveBeenCalledTimes(1);
    });

    it('should throw error when room not found (404)', async () => {
      const mockError = {
        response: {
          status: 404,
          data: { detail: 'Room not found' },
        },
      };
      vi.mocked(api.delete).mockRejectedValue(mockError);

      await expect(voiceService.endSession('invalid-room')).rejects.toThrow();
    });

    it('should throw error when API call fails', async () => {
      const mockError = new Error('Network error');
      vi.mocked(api.delete).mockRejectedValue(mockError);

      await expect(voiceService.endSession('room-abc123')).rejects.toThrow('Network error');
    });
  });

  describe('getActiveSessions', () => {
    it('should call GET /voice-sessions/active and return active sessions', async () => {
      const mockActiveSessions: ActiveSessionsResponse = {
        sessions: [
          {
            room_name: 'room-abc123',
            agent_type: 'workout',
            participants: 2,
            created_at: '2024-01-15T18:00:00Z',
          },
          {
            room_name: 'room-def456',
            agent_type: 'diet',
            participants: 1,
            created_at: '2024-01-15T18:30:00Z',
          },
        ],
      };

      vi.mocked(api.get).mockResolvedValue({
        data: mockActiveSessions,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      });

      const result = await voiceService.getActiveSessions();

      expect(api.get).toHaveBeenCalledWith('/voice-sessions/active');
      expect(api.get).toHaveBeenCalledTimes(1);
      expect(result).toEqual(mockActiveSessions);
      expect(result.sessions).toHaveLength(2);
      expect(result.sessions[0].agent_type).toBe('workout');
    });

    it('should return empty array when no active sessions', async () => {
      const mockActiveSessions: ActiveSessionsResponse = {
        sessions: [],
      };

      vi.mocked(api.get).mockResolvedValue({
        data: mockActiveSessions,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      });

      const result = await voiceService.getActiveSessions();

      expect(result.sessions).toHaveLength(0);
    });

    it('should throw error when API call fails', async () => {
      const mockError = new Error('Network error');
      vi.mocked(api.get).mockRejectedValue(mockError);

      await expect(voiceService.getActiveSessions()).rejects.toThrow('Network error');
    });

    it('should throw error when user is not authenticated (401)', async () => {
      const mockError = {
        response: {
          status: 401,
          data: { detail: 'Not authenticated' },
        },
      };
      vi.mocked(api.get).mockRejectedValue(mockError);

      await expect(voiceService.getActiveSessions()).rejects.toThrow();
    });
  });
});
