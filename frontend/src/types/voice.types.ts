/**
 * Voice Session Type Definitions
 * 
 * These types define the structure of voice session-related requests and responses
 * for the Shuren API. They align with the backend FastAPI endpoints.
 */

/**
 * Voice session request payload
 * Sent to POST /voice-sessions/start
 * Used to start a new voice coaching session
 */
export interface VoiceSessionRequest {
  agent_type: string;
}

/**
 * Voice session response
 * Returned by POST /voice-sessions/start
 * Contains LiveKit connection details
 */
export interface VoiceSessionResponse {
  room_name: string;
  token: string;
  livekit_url: string;
  agent_type: string;
  expires_at: string;
}

/**
 * Voice session status
 * Returned by GET /voice-sessions/{room_name}/status
 * Contains current session state and participant information
 */
export interface VoiceSessionStatus {
  room_name: string;
  active: boolean;
  participants: number;
  agent_connected: boolean;
  created_at: string | null;
}

/**
 * Active sessions response
 * Returned by GET /voice-sessions/active
 * Contains list of all active voice sessions
 */
export interface ActiveSessionsResponse {
  sessions: SessionSummary[];
}

/**
 * Session summary
 * Brief information about a voice session
 */
export interface SessionSummary {
  room_name: string;
  agent_type: string;
  participants: number;
  created_at: string | null;
}
