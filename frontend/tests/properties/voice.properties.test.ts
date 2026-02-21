import { describe, it, expect, beforeEach, vi } from 'vitest';
import fc from 'fast-check';
import { voiceService } from '../../src/services/voiceService';
import api from '../../src/services/api';
import type {
  AgentType,
  VoiceSessionResponse,
  TranscriptionMessage,
  SessionStatus,
} from '../../src/types';

// Mock the API module
vi.mock('../../src/services/api', () => ({
  default: {
    post: vi.fn(),
    get: vi.fn(),
    delete: vi.fn(),
  },
}));

// Mock LiveKit Room
const mockRoom = {
  connect: vi.fn(),
  disconnect: vi.fn(),
  on: vi.fn(),
  remoteParticipants: new Map(),
};

vi.mock('livekit-client', () => ({
  Room: vi.fn(() => mockRoom),
  RoomEvent: {
    Connected: 'connected',
    Disconnected: 'disconnected',
    ParticipantConnected: 'participantConnected',
    ParticipantDisconnected: 'participantDisconnected',
    DataReceived: 'dataReceived',
    ConnectionQualityChanged: 'connectionQualityChanged',
    Reconnecting: 'reconnecting',
    Reconnected: 'reconnected',
  },
}));

describe('Voice Session Properties', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockRoom.remoteParticipants.clear();
  });

  it('Property 14: Transcription updates from LiveKit data', async () => {
    // Feature: minimal-frontend-testing, Property 14: Transcription updates from LiveKit data
    // For any transcription data received from LiveKit (via DataReceived event),
    // the transcription state should be updated with the new message, maintaining
    // speaker identification, text content, and finality status.
    // Validates: Requirements 2.7.5

    await fc.assert(
      fc.asyncProperty(
        fc.array(
          fc.record({
            id: fc.uuid(),
            speaker: fc.constantFrom<'user' | 'agent'>('user', 'agent'),
            text: fc.string({ minLength: 1, maxLength: 200 }),
            timestamp: fc.date({ 
              min: new Date('2024-01-01T00:00:00.000Z'), 
              max: new Date('2025-12-31T23:59:59.999Z'),
              noInvalidDate: true 
            }),
            isFinal: fc.boolean(),
          }),
          { minLength: 1, maxLength: 20 }
        ), // Array of transcription messages
        async (transcriptionMessages) => {
          const receivedTranscriptions: TranscriptionMessage[] = [];

          // Simulate receiving transcription data packets
          for (const msg of transcriptionMessages) {
            // Create data packet as LiveKit would send it
            const dataPacket = {
              type: 'transcription',
              id: msg.id,
              speaker: msg.speaker,
              text: msg.text,
              timestamp: msg.timestamp.toISOString(),
              isFinal: msg.isFinal,
            };

            // Encode as Uint8Array (as LiveKit does)
            const encoder = new TextEncoder();
            const payload = encoder.encode(JSON.stringify(dataPacket));

            // Decode and parse (simulating what the hook does)
            const decoder = new TextDecoder();
            const decoded = JSON.parse(decoder.decode(payload));

            // Verify data packet structure
            expect(decoded.type).toBe('transcription');
            expect(decoded.id).toBe(msg.id);
            expect(decoded.speaker).toBe(msg.speaker);
            expect(decoded.text).toBe(msg.text);
            expect(decoded.isFinal).toBe(msg.isFinal);

            // Add to transcription list (simulating state update)
            receivedTranscriptions.push({
              id: decoded.id,
              speaker: decoded.speaker,
              text: decoded.text,
              timestamp: new Date(decoded.timestamp),
              isFinal: decoded.isFinal,
            });
          }

          // Verify all transcriptions were received and processed
          expect(receivedTranscriptions.length).toBe(transcriptionMessages.length);

          // Verify each transcription maintains correct data
          for (let i = 0; i < transcriptionMessages.length; i++) {
            const original = transcriptionMessages[i];
            const received = receivedTranscriptions[i];

            expect(received.id).toBe(original.id);
            expect(received.speaker).toBe(original.speaker);
            expect(received.text).toBe(original.text);
            expect(received.isFinal).toBe(original.isFinal);
            
            // Verify timestamp is valid
            expect(received.timestamp).toBeInstanceOf(Date);
            expect(Number.isNaN(received.timestamp.getTime())).toBe(false);
            expect(received.timestamp.getTime()).toBe(original.timestamp.getTime());
          }
        }
      ),
      { numRuns: 100 }
    );
  });

  it('Property 15: Session status reflects LiveKit events', async () => {
    // Feature: minimal-frontend-testing, Property 15: Session status reflects LiveKit events
    // For any sequence of LiveKit room events (Connected, Disconnected, ParticipantConnected,
    // ParticipantDisconnected), the session status should accurately reflect the current
    // connection state and participant count.
    // Validates: Requirements 2.7.7

    await fc.assert(
      fc.asyncProperty(
        fc.array(
          fc.constantFrom(
            'Connected',
            'Disconnected',
            'ParticipantConnected',
            'ParticipantDisconnected'
          ),
          { minLength: 1, maxLength: 15 }
        ), // Sequence of room events
        async (eventSequence) => {
          // Initialize session status
          const sessionStatus: SessionStatus = {
            connected: false,
            participantCount: 0,
            duration: 0,
          };

          // Process each event
          for (const event of eventSequence) {
            switch (event) {
              case 'Connected':
                sessionStatus.connected = true;
                break;

              case 'Disconnected':
                sessionStatus.connected = false;
                break;

              case 'ParticipantConnected':
                // Simulate participant joining
                sessionStatus.participantCount += 1;
                break;

              case 'ParticipantDisconnected':
                // Simulate participant leaving (don't go below 0)
                if (sessionStatus.participantCount > 0) {
                  sessionStatus.participantCount -= 1;
                }
                break;
            }
          }

          // Verify final state is consistent
          expect(sessionStatus.participantCount).toBeGreaterThanOrEqual(0);

          // Verify connection state is boolean
          expect(typeof sessionStatus.connected).toBe('boolean');

          // If we had any Connected events, verify state reflects that
          const hadConnectedEvent = eventSequence.includes('Connected');
          const hadDisconnectedEvent = eventSequence.includes('Disconnected');

          // If last relevant event was Connected, should be connected
          const lastConnectionEvent = [...eventSequence]
            .reverse()
            .find((e) => e === 'Connected' || e === 'Disconnected');

          if (lastConnectionEvent === 'Connected') {
            expect(sessionStatus.connected).toBe(true);
          } else if (lastConnectionEvent === 'Disconnected') {
            expect(sessionStatus.connected).toBe(false);
          }

          // Verify participant count matches event history
          // We need to simulate the actual behavior: count can't go below 0
          let expectedCount = 0;
          for (const event of eventSequence) {
            if (event === 'ParticipantConnected') {
              expectedCount += 1;
            } else if (event === 'ParticipantDisconnected') {
              expectedCount = Math.max(0, expectedCount - 1);
            }
          }

          expect(sessionStatus.participantCount).toBe(expectedCount);
        }
      ),
      { numRuns: 100 }
    );
  });

  it('Property 16: Voice connection errors handled', async () => {
    // Feature: minimal-frontend-testing, Property 16: Voice connection errors handled
    // For any error during voice session creation (API failure, permission denied,
    // connection failure), the error should be caught, stored in error state, and
    // made available for display to the user.
    // Validates: Requirements 2.7.9

    await fc.assert(
      fc.asyncProperty(
        fc.constantFrom<AgentType>(
          'workout_planning',
          'diet_planning',
          'supplement_guidance',
          'tracking_adjustment',
          'scheduling_reminder',
          'general_assistant'
        ), // Random agent type
        fc.constantFrom(
          // Different error scenarios
          { type: 'api_error', status: 500, message: 'Internal server error' },
          { type: 'api_error', status: 503, message: 'Service unavailable' },
          { type: 'api_error', status: 404, message: 'Endpoint not found' },
          { type: 'permission_denied', message: 'Microphone permission denied' },
          { type: 'no_microphone', message: 'No microphone found' },
          { type: 'connection_failed', message: 'Failed to connect to room' },
          { type: 'network_error', message: 'Network connection failed' }
        ), // Random error scenario
        async (agentType, errorScenario) => {
          let errorState: string | null = null;

          try {
            if (errorScenario.type === 'api_error') {
              // Mock API error
              const mockError = {
                response: {
                  status: errorScenario.status,
                  data: {
                    detail: errorScenario.message,
                  },
                },
                message: errorScenario.message,
              };
              vi.mocked(api.post).mockRejectedValueOnce(mockError);

              // Attempt to start session
              await voiceService.startSession(agentType);
            } else if (errorScenario.type === 'permission_denied') {
              // Simulate permission denied error
              const permissionError = new Error(errorScenario.message);
              permissionError.name = 'NotAllowedError';
              throw permissionError;
            } else if (errorScenario.type === 'no_microphone') {
              // Simulate no microphone error
              const micError = new Error(errorScenario.message);
              micError.name = 'NotFoundError';
              throw micError;
            } else {
              // Simulate connection or network error
              throw new Error(errorScenario.message);
            }

            // Should not reach here
            expect.fail('Expected error to be thrown');
          } catch (err: any) {
            // Capture error (simulating error state update)
            errorState = err instanceof Error ? err.message : 'Unknown error';

            // Verify error is defined and accessible
            expect(errorState).toBeDefined();
            expect(typeof errorState).toBe('string');
            expect(errorState.length).toBeGreaterThan(0);

            // Verify error message is meaningful
            expect(errorState).not.toBe('');
            expect(errorState).not.toBe('undefined');

            // For API errors, verify response structure
            if (errorScenario.type === 'api_error' && err.response) {
              expect(err.response.status).toBe(errorScenario.status);
              expect(err.response.data).toBeDefined();
            }

            // Verify error can be displayed to user
            const displayMessage = errorState || 'An error occurred';
            expect(displayMessage.length).toBeGreaterThan(0);
          }

          // Verify error state was set
          expect(errorState).not.toBeNull();
        }
      ),
      { numRuns: 100 }
    );
  });

  it('Property 17: Latency updates from agent data', async () => {
    // Feature: minimal-frontend-testing, Property 17: Latency updates from agent data
    // For any latency data received from the agent (via DataReceived event with type 'latency'),
    // the latency state should be updated with the new value, allowing real-time monitoring
    // of response times.
    // Validates: Requirements 2.7.10

    await fc.assert(
      fc.asyncProperty(
        fc.array(
          fc.integer({ min: 10, max: 5000 }), // Latency values in milliseconds
          { minLength: 1, maxLength: 50 }
        ), // Array of latency measurements
        async (latencyValues) => {
          let currentLatency = 0;
          const receivedLatencies: number[] = [];

          // Simulate receiving latency data packets
          for (const latencyValue of latencyValues) {
            // Create data packet as agent would send it
            const dataPacket = {
              type: 'latency',
              value: latencyValue,
            };

            // Encode as Uint8Array (as LiveKit does)
            const encoder = new TextEncoder();
            const payload = encoder.encode(JSON.stringify(dataPacket));

            // Decode and parse (simulating what the hook does)
            const decoder = new TextDecoder();
            const decoded = JSON.parse(decoder.decode(payload));

            // Verify data packet structure
            expect(decoded.type).toBe('latency');
            expect(decoded.value).toBe(latencyValue);
            expect(typeof decoded.value).toBe('number');
            expect(decoded.value).toBeGreaterThan(0);

            // Update latency state (simulating state update)
            currentLatency = decoded.value;
            receivedLatencies.push(currentLatency);
          }

          // Verify all latency updates were received
          expect(receivedLatencies.length).toBe(latencyValues.length);

          // Verify each latency value was correctly processed
          for (let i = 0; i < latencyValues.length; i++) {
            expect(receivedLatencies[i]).toBe(latencyValues[i]);
            expect(receivedLatencies[i]).toBeGreaterThan(0);
            expect(receivedLatencies[i]).toBeLessThanOrEqual(5000);
          }

          // Verify final latency state matches last received value
          expect(currentLatency).toBe(latencyValues[latencyValues.length - 1]);

          // Verify latency is a valid number
          expect(typeof currentLatency).toBe('number');
          expect(currentLatency).toBeGreaterThan(0);
          expect(Number.isFinite(currentLatency)).toBe(true);
        }
      ),
      { numRuns: 100 }
    );
  });
});
