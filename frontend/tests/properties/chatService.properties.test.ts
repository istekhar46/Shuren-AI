import { describe, it, expect, beforeEach, vi } from 'vitest';
import fc from 'fast-check';
import { chatService } from '../../src/services/chatService';

describe('ChatService Property Tests', () => {
  let mockEventSource: any;

  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    
    // Mock EventSource
    mockEventSource = {
      onmessage: null,
      onerror: null,
      close: vi.fn(),
    };
    
    (globalThis as any).EventSource = vi.fn(function (this: any, url: string) {
      return mockEventSource;
    });
    
    localStorage.setItem('auth_token', 'test-token');
  });

  it('Property 5: Callback Routing Correctness', async () => {
    // Feature: chat-text-streaming, Property 5: Callback Routing Correctness
    // **Validates: Requirements 2.4, 2.5, 2.6**
    // For any SSE event received (chunk, completion, or error), the Chat_Service 
    // should invoke the corresponding callback (onChunk, onComplete, or onError) 
    // with the correct data extracted from the event

    await fc.assert(
      fc.asyncProperty(
        fc.string({ minLength: 1, maxLength: 500 }), // Random message
        fc.array(
          fc.oneof(
            // Generate random SSE events
            fc.record({
              type: fc.constant('chunk'),
              data: fc.record({
                chunk: fc.string({ minLength: 1, maxLength: 100 }),
              }),
            }),
            fc.record({
              type: fc.constant('done'),
              data: fc.record({
                done: fc.constant(true),
                agent_type: fc.constantFrom(
                  'conversational_assistant',
                  'workout_planning',
                  'diet_planning',
                  'supplement_guidance',
                  'tracking_adjustment',
                  'scheduling_reminder'
                ),
              }),
            }),
            fc.record({
              type: fc.constant('error'),
              data: fc.record({
                error: fc.string({ minLength: 1, maxLength: 200 }),
              }),
            })
          ),
          { minLength: 1, maxLength: 20 }
        ), // Array of random events
        async (message, events) => {
          // Track callback invocations
          const chunkCalls: string[] = [];
          const completeCalls: (string | undefined)[] = [];
          const errorCalls: string[] = [];

          const callbacks = {
            onChunk: vi.fn((chunk: string) => chunkCalls.push(chunk)),
            onComplete: vi.fn((agentType?: string) => completeCalls.push(agentType)),
            onError: vi.fn((error: string) => errorCalls.push(error)),
          };

          // Start streaming
          const cancelFn = chatService.streamMessage(message, callbacks, false);

          // Simulate each event
          for (const event of events) {
            const sseEvent = {
              data: JSON.stringify(event.data),
            };

            mockEventSource.onmessage(sseEvent);

            // If it's a done or error event, the stream should close
            if (event.type === 'done' || event.type === 'error') {
              break;
            }
          }

          // Verify callbacks were invoked correctly
          const chunkEvents = events.filter(e => e.type === 'chunk');
          const doneEvents = events.filter(e => e.type === 'done');
          const errorEvents = events.filter(e => e.type === 'error');

          // Find first terminal event (done or error)
          const firstTerminalIndex = events.findIndex(
            e => e.type === 'done' || e.type === 'error'
          );
          const eventsBeforeTerminal = firstTerminalIndex >= 0 
            ? events.slice(0, firstTerminalIndex + 1)
            : events;

          // Count events before terminal
          const chunksBeforeTerminal = eventsBeforeTerminal.filter(e => e.type === 'chunk');
          const doneBeforeTerminal = eventsBeforeTerminal.filter(e => e.type === 'done');
          const errorBeforeTerminal = eventsBeforeTerminal.filter(e => e.type === 'error');

          // Verify chunk callbacks
          expect(callbacks.onChunk).toHaveBeenCalledTimes(chunksBeforeTerminal.length);
          for (let i = 0; i < chunksBeforeTerminal.length; i++) {
            expect(chunkCalls[i]).toBe(chunksBeforeTerminal[i].data.chunk);
          }

          // Verify completion callbacks
          if (doneBeforeTerminal.length > 0) {
            expect(callbacks.onComplete).toHaveBeenCalledTimes(1);
            expect(completeCalls[0]).toBe(doneBeforeTerminal[0].data.agent_type);
          } else {
            expect(callbacks.onComplete).not.toHaveBeenCalled();
          }

          // Verify error callbacks
          if (errorBeforeTerminal.length > 0) {
            expect(callbacks.onError).toHaveBeenCalledTimes(1);
            expect(errorCalls[0]).toBe(errorBeforeTerminal[0].data.error);
          } else {
            expect(callbacks.onError).not.toHaveBeenCalled();
          }

          // Cleanup
          cancelFn();
        }
      ),
      { numRuns: 100 }
    );
  });

  it('Property 5.1: Chunk events always invoke onChunk', async () => {
    // Validates that chunk events always and only invoke onChunk callback
    await fc.assert(
      fc.asyncProperty(
        fc.string({ minLength: 1, maxLength: 500 }), // Random message
        fc.array(
          fc.string({ minLength: 1, maxLength: 100 }),
          { minLength: 1, maxLength: 50 }
        ), // Array of chunk strings
        async (message, chunks) => {
          const callbacks = {
            onChunk: vi.fn(),
            onComplete: vi.fn(),
            onError: vi.fn(),
          };

          chatService.streamMessage(message, callbacks, false);

          // Send all chunk events
          for (const chunk of chunks) {
            const event = {
              data: JSON.stringify({ chunk }),
            };
            mockEventSource.onmessage(event);
          }

          // Verify only onChunk was called, with correct data
          expect(callbacks.onChunk).toHaveBeenCalledTimes(chunks.length);
          expect(callbacks.onComplete).not.toHaveBeenCalled();
          expect(callbacks.onError).not.toHaveBeenCalled();

          // Verify each chunk was passed correctly
          for (let i = 0; i < chunks.length; i++) {
            expect(callbacks.onChunk).toHaveBeenNthCalledWith(i + 1, chunks[i]);
          }
        }
      ),
      { numRuns: 100 }
    );
  });

  it('Property 5.2: Completion events always invoke onComplete', async () => {
    // Validates that completion events always and only invoke onComplete callback
    await fc.assert(
      fc.asyncProperty(
        fc.string({ minLength: 1, maxLength: 500 }), // Random message
        fc.constantFrom(
          'conversational_assistant',
          'workout_planning',
          'diet_planning',
          'supplement_guidance',
          'tracking_adjustment',
          'scheduling_reminder'
        ), // Random agent type
        async (message, agentType) => {
          const callbacks = {
            onChunk: vi.fn(),
            onComplete: vi.fn(),
            onError: vi.fn(),
          };

          chatService.streamMessage(message, callbacks, false);

          // Send completion event
          const event = {
            data: JSON.stringify({ done: true, agent_type: agentType }),
          };
          mockEventSource.onmessage(event);

          // Verify only onComplete was called, with correct agent type
          expect(callbacks.onComplete).toHaveBeenCalledTimes(1);
          expect(callbacks.onComplete).toHaveBeenCalledWith(agentType);
          expect(callbacks.onChunk).not.toHaveBeenCalled();
          expect(callbacks.onError).not.toHaveBeenCalled();

          // Verify connection was closed
          expect(mockEventSource.close).toHaveBeenCalled();
        }
      ),
      { numRuns: 100 }
    );
  });

  it('Property 5.3: Error events always invoke onError', async () => {
    // Validates that error events always and only invoke onError callback
    await fc.assert(
      fc.asyncProperty(
        fc.string({ minLength: 1, maxLength: 500 }), // Random message
        fc.string({ minLength: 1, maxLength: 200 }), // Random error message
        async (message, errorMessage) => {
          const callbacks = {
            onChunk: vi.fn(),
            onComplete: vi.fn(),
            onError: vi.fn(),
          };

          chatService.streamMessage(message, callbacks, false);

          // Send error event
          const event = {
            data: JSON.stringify({ error: errorMessage }),
          };
          mockEventSource.onmessage(event);

          // Verify only onError was called, with correct error message
          expect(callbacks.onError).toHaveBeenCalledTimes(1);
          expect(callbacks.onError).toHaveBeenCalledWith(errorMessage);
          expect(callbacks.onChunk).not.toHaveBeenCalled();
          expect(callbacks.onComplete).not.toHaveBeenCalled();

          // Verify connection was closed
          expect(mockEventSource.close).toHaveBeenCalled();
        }
      ),
      { numRuns: 100 }
    );
  });

  it('Property 5.4: Connection errors invoke onError', async () => {
    // Validates that EventSource connection errors invoke onError callback
    await fc.assert(
      fc.asyncProperty(
        fc.string({ minLength: 1, maxLength: 500 }), // Random message
        async (message) => {
          const callbacks = {
            onChunk: vi.fn(),
            onComplete: vi.fn(),
            onError: vi.fn(),
          };

          chatService.streamMessage(message, callbacks, false);

          // Trigger connection error
          mockEventSource.onerror();

          // Verify only onError was called
          expect(callbacks.onError).toHaveBeenCalledTimes(1);
          expect(callbacks.onError).toHaveBeenCalledWith('Connection error');
          expect(callbacks.onChunk).not.toHaveBeenCalled();
          expect(callbacks.onComplete).not.toHaveBeenCalled();

          // Verify connection was closed
          expect(mockEventSource.close).toHaveBeenCalled();
        }
      ),
      { numRuns: 100 }
    );
  });

  it('Property 5.5: Malformed JSON invokes onError', async () => {
    // Validates that malformed JSON in events invokes onError callback
    await fc.assert(
      fc.asyncProperty(
        fc.string({ minLength: 1, maxLength: 500 }), // Random message
        fc.string({ minLength: 1, maxLength: 200 }).filter(s => {
          try {
            JSON.parse(s);
            return false; // Valid JSON, skip
          } catch {
            return true; // Invalid JSON, use it
          }
        }), // Random invalid JSON string
        async (message, invalidJson) => {
          const callbacks = {
            onChunk: vi.fn(),
            onComplete: vi.fn(),
            onError: vi.fn(),
          };

          chatService.streamMessage(message, callbacks, false);

          // Send malformed event
          const event = {
            data: invalidJson,
          };
          mockEventSource.onmessage(event);

          // Verify only onError was called
          expect(callbacks.onError).toHaveBeenCalledTimes(1);
          expect(callbacks.onError).toHaveBeenCalledWith('Failed to parse response');
          expect(callbacks.onChunk).not.toHaveBeenCalled();
          expect(callbacks.onComplete).not.toHaveBeenCalled();

          // Verify connection was closed
          expect(mockEventSource.close).toHaveBeenCalled();
        }
      ),
      { numRuns: 100 }
    );
  });
});
