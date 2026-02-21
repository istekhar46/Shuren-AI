import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import fc from 'fast-check';
import { useChat } from '../../src/hooks/useChat';
import { chatService } from '../../src/services/chatService';
import type { ReactNode } from 'react';

// Mock the chat service
vi.mock('../../src/services/chatService', () => ({
  chatService: {
    sendMessage: vi.fn(),
    getHistory: vi.fn(),
    streamMessage: vi.fn(),
    cancelStream: vi.fn(),
  },
}));

// Mock react-router-dom
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: vi.fn(() => vi.fn()),
  };
});

describe('useChat Hook Property Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(chatService.getHistory).mockResolvedValue({
      messages: [],
      total: 0,
    });
  });

  const wrapper = ({ children }: { children: ReactNode }) => (
    <MemoryRouter>{children}</MemoryRouter>
  );

  it('Property 9: Content Accumulation Invariant', { timeout: 30000 }, async () => {
    // Feature: chat-text-streaming, Property 9: Content Accumulation Invariant
    // **Validates: Requirements 3.3, 4.1**
    // For any sequence of chunks received during streaming, the final message 
    // content should equal the concatenation of all chunks in the order they 
    // were received

    await fc.assert(
      fc.asyncProperty(
        fc.string({ minLength: 1, maxLength: 100 }), // Random user message
        fc.array(
          fc.string({ minLength: 0, maxLength: 50 }), // Random chunks (can be empty)
          { minLength: 1, maxLength: 100 } // 1-100 chunks
        ),
        async (userMessage, chunks) => {
          let onChunkCallback: ((chunk: string) => void) | null = null;
          let onCompleteCallback: ((agentType?: string) => void) | null = null;

          vi.mocked(chatService.streamMessage).mockImplementation((msg, callbacks) => {
            onChunkCallback = callbacks.onChunk;
            onCompleteCallback = callbacks.onComplete;
            return vi.fn();
          });

          const { result } = renderHook(() => useChat(false), { wrapper });

          // Wait for initialization
          await waitFor(() => {
            expect(result.current.messages).toEqual([]);
          });

          // Send message
          act(() => {
            result.current.sendMessage(userMessage);
          });

          // Wait for placeholder to be created
          await waitFor(() => {
            expect(result.current.messages.length).toBe(2);
            expect(result.current.messages[1].isStreaming).toBe(true);
          });

          // Send all chunks
          for (const chunk of chunks) {
            act(() => {
              onChunkCallback?.(chunk);
            });
          }

          // Wait for all chunks to be processed
          await waitFor(() => {
            const assistantMessage = result.current.messages[1];
            // The content should equal the concatenation of all chunks
            const expectedContent = chunks.join('');
            expect(assistantMessage.content).toBe(expectedContent);
          });

          // Complete the stream
          act(() => {
            onCompleteCallback?.('general_assistant');
          });

          await waitFor(() => {
            expect(result.current.messages[1].isStreaming).toBe(false);
          });

          // Final verification: content equals concatenation of all chunks
          const finalContent = result.current.messages[1].content;
          const expectedFinalContent = chunks.join('');
          expect(finalContent).toBe(expectedFinalContent);
          expect(finalContent.length).toBe(expectedFinalContent.length);
        }
      ),
      { numRuns: 100 }
    );
  });

  it('Property 9.1: Empty chunks do not affect accumulation', { timeout: 30000 }, async () => {
    // Validates that empty chunks are handled correctly in accumulation
    await fc.assert(
      fc.asyncProperty(
        fc.string({ minLength: 1, maxLength: 100 }), // Random user message
        fc.array(
          fc.oneof(
            fc.string({ minLength: 1, maxLength: 50 }), // Non-empty chunks
            fc.constant('') // Empty chunks
          ),
          { minLength: 5, maxLength: 50 }
        ),
        async (userMessage, chunks) => {
          let onChunkCallback: ((chunk: string) => void) | null = null;

          vi.mocked(chatService.streamMessage).mockImplementation((msg, callbacks) => {
            onChunkCallback = callbacks.onChunk;
            return vi.fn();
          });

          const { result } = renderHook(() => useChat(false), { wrapper });

          await waitFor(() => {
            expect(result.current.messages).toEqual([]);
          });

          act(() => {
            result.current.sendMessage(userMessage);
          });

          await waitFor(() => {
            expect(result.current.messages.length).toBe(2);
          });

          // Send all chunks including empty ones
          for (const chunk of chunks) {
            act(() => {
              onChunkCallback?.(chunk);
            });
          }

          await waitFor(() => {
            const assistantMessage = result.current.messages[1];
            const expectedContent = chunks.join('');
            expect(assistantMessage.content).toBe(expectedContent);
          });
        }
      ),
      { numRuns: 100 }
    );
  });

  it('Property 9.2: Chunk order is preserved', { timeout: 30000 }, async () => {
    // Validates that chunks are accumulated in the exact order received
    await fc.assert(
      fc.asyncProperty(
        fc.string({ minLength: 1, maxLength: 100 }), // Random user message
        fc.array(
          fc.integer({ min: 0, max: 999 }).map(n => `[${n}]`), // Numbered chunks
          { minLength: 10, maxLength: 50 }
        ),
        async (userMessage, chunks) => {
          let onChunkCallback: ((chunk: string) => void) | null = null;

          vi.mocked(chatService.streamMessage).mockImplementation((msg, callbacks) => {
            onChunkCallback = callbacks.onChunk;
            return vi.fn();
          });

          const { result } = renderHook(() => useChat(false), { wrapper });

          await waitFor(() => {
            expect(result.current.messages).toEqual([]);
          });

          act(() => {
            result.current.sendMessage(userMessage);
          });

          await waitFor(() => {
            expect(result.current.messages.length).toBe(2);
          });

          // Send chunks in order
          for (const chunk of chunks) {
            act(() => {
              onChunkCallback?.(chunk);
            });
          }

          await waitFor(() => {
            const assistantMessage = result.current.messages[1];
            const expectedContent = chunks.join('');
            expect(assistantMessage.content).toBe(expectedContent);
            
            // Verify order by checking that each chunk appears in sequence
            let currentIndex = 0;
            for (const chunk of chunks) {
              const foundIndex = assistantMessage.content.indexOf(chunk, currentIndex);
              expect(foundIndex).toBe(currentIndex);
              currentIndex += chunk.length;
            }
          });
        }
      ),
      { numRuns: 100 }
    );
  });

  it('Property 9.3: Unicode and special characters are preserved', { timeout: 30000 }, async () => {
    // Validates that special characters, emojis, and unicode are correctly accumulated
    await fc.assert(
      fc.asyncProperty(
        fc.string({ minLength: 1, maxLength: 100 }), // Random user message
        fc.array(
          fc.oneof(
            fc.string({ minLength: 1, maxLength: 20 }), // Regular strings
            fc.constantFrom('😀', '🎉', '❤️', '🚀', '✨'), // Emojis
            fc.constantFrom('你好', 'مرحبا', 'Привет', 'こんにちは'), // Unicode
            fc.constantFrom('\n', '\t', '\r\n'), // Whitespace
            fc.constantFrom('<', '>', '&', '"', "'") // Special HTML chars
          ),
          { minLength: 5, maxLength: 30 }
        ),
        async (userMessage, chunks) => {
          let onChunkCallback: ((chunk: string) => void) | null = null;

          vi.mocked(chatService.streamMessage).mockImplementation((msg, callbacks) => {
            onChunkCallback = callbacks.onChunk;
            return vi.fn();
          });

          const { result } = renderHook(() => useChat(false), { wrapper });

          await waitFor(() => {
            expect(result.current.messages).toEqual([]);
          });

          act(() => {
            result.current.sendMessage(userMessage);
          });

          await waitFor(() => {
            expect(result.current.messages.length).toBe(2);
          });

          // Send all chunks
          for (const chunk of chunks) {
            act(() => {
              onChunkCallback?.(chunk);
            });
          }

          await waitFor(() => {
            const assistantMessage = result.current.messages[1];
            const expectedContent = chunks.join('');
            expect(assistantMessage.content).toBe(expectedContent);
            
            // Verify each chunk is present
            for (const chunk of chunks) {
              expect(assistantMessage.content).toContain(chunk);
            }
          });
        }
      ),
      { numRuns: 100 }
    );
  });

  it('Property 9.4: Large chunk sequences accumulate correctly', { timeout: 30000 }, async () => {
    // Validates that large numbers of chunks accumulate without data loss
    await fc.assert(
      fc.asyncProperty(
        fc.string({ minLength: 1, maxLength: 100 }), // Random user message
        fc.integer({ min: 100, max: 500 }), // Number of chunks
        async (userMessage, numChunks) => {
          let onChunkCallback: ((chunk: string) => void) | null = null;

          vi.mocked(chatService.streamMessage).mockImplementation((msg, callbacks) => {
            onChunkCallback = callbacks.onChunk;
            return vi.fn();
          });

          const { result } = renderHook(() => useChat(false), { wrapper });

          await waitFor(() => {
            expect(result.current.messages).toEqual([]);
          });

          act(() => {
            result.current.sendMessage(userMessage);
          });

          await waitFor(() => {
            expect(result.current.messages.length).toBe(2);
          });

          // Generate and send many chunks
          const chunks: string[] = [];
          for (let i = 0; i < numChunks; i++) {
            const chunk = `${i} `;
            chunks.push(chunk);
          }

          act(() => {
            for (const chunk of chunks) {
              onChunkCallback?.(chunk);
            }
          });

          await waitFor(() => {
            const assistantMessage = result.current.messages[1];
            const expectedContent = chunks.join('');
            expect(assistantMessage.content).toBe(expectedContent);
            expect(assistantMessage.content.length).toBe(expectedContent.length);
          });
        }
      ),
      { numRuns: 50 } // Fewer runs for performance
    );
  });

  it('Property 9.5: Accumulation survives rapid updates', { timeout: 30000 }, async () => {
    // Validates that rapid chunk updates don't cause race conditions or data loss
    await fc.assert(
      fc.asyncProperty(
        fc.string({ minLength: 1, maxLength: 100 }), // Random user message
        fc.array(
          fc.string({ minLength: 1, maxLength: 10 }),
          { minLength: 20, maxLength: 100 }
        ),
        async (userMessage, chunks) => {
          let onChunkCallback: ((chunk: string) => void) | null = null;

          vi.mocked(chatService.streamMessage).mockImplementation((msg, callbacks) => {
            onChunkCallback = callbacks.onChunk;
            return vi.fn();
          });

          const { result } = renderHook(() => useChat(false), { wrapper });

          await waitFor(() => {
            expect(result.current.messages).toEqual([]);
          });

          act(() => {
            result.current.sendMessage(userMessage);
          });

          await waitFor(() => {
            expect(result.current.messages.length).toBe(2);
          });

          // Send all chunks in a single act (simulating rapid updates)
          act(() => {
            for (const chunk of chunks) {
              onChunkCallback?.(chunk);
            }
          });

          await waitFor(() => {
            const assistantMessage = result.current.messages[1];
            const expectedContent = chunks.join('');
            expect(assistantMessage.content).toBe(expectedContent);
            
            // Verify no chunks were lost
            expect(assistantMessage.content.length).toBe(expectedContent.length);
          });
        }
      ),
      { numRuns: 100 }
    );
  });

  it('Property 9.6: Content length equals sum of chunk lengths', { timeout: 30000 }, async () => {
    // Validates that the final content length equals the sum of all chunk lengths
    await fc.assert(
      fc.asyncProperty(
        fc.string({ minLength: 1, maxLength: 100 }), // Random user message
        fc.array(
          fc.string({ minLength: 0, maxLength: 50 }),
          { minLength: 1, maxLength: 50 }
        ),
        async (userMessage, chunks) => {
          let onChunkCallback: ((chunk: string) => void) | null = null;

          vi.mocked(chatService.streamMessage).mockImplementation((msg, callbacks) => {
            onChunkCallback = callbacks.onChunk;
            return vi.fn();
          });

          const { result } = renderHook(() => useChat(false), { wrapper });

          await waitFor(() => {
            expect(result.current.messages).toEqual([]);
          });

          act(() => {
            result.current.sendMessage(userMessage);
          });

          await waitFor(() => {
            expect(result.current.messages.length).toBe(2);
          });

          // Calculate expected length
          const expectedLength = chunks.reduce((sum, chunk) => sum + chunk.length, 0);

          // Send all chunks
          for (const chunk of chunks) {
            act(() => {
              onChunkCallback?.(chunk);
            });
          }

          await waitFor(() => {
            const assistantMessage = result.current.messages[1];
            expect(assistantMessage.content.length).toBe(expectedLength);
          });
        }
      ),
      { numRuns: 100 }
    );
  });

  it('Property 13: Conversation History Preservation', { timeout: 30000 }, async () => {
    // Feature: chat-text-streaming, Property 13: Conversation History Preservation
    // **Validates: Requirements 3.7**
    // Send random sequences of messages and verify all preserved in order

    await fc.assert(
      fc.asyncProperty(
        fc.array(
          fc.string({ minLength: 1, maxLength: 100 }), // Random user messages
          { minLength: 1, maxLength: 10 } // 1-10 messages
        ),
        fc.array(
          fc.array(
            fc.string({ minLength: 1, maxLength: 50 }), // Chunks for each response
            { minLength: 1, maxLength: 10 }
          ),
          { minLength: 1, maxLength: 10 } // Matching number of responses
        ),
        async (userMessages, responseChunks) => {
          // Ensure we have matching responses for each message
          const numMessages = Math.min(userMessages.length, responseChunks.length);
          const messages = userMessages.slice(0, numMessages);
          const responses = responseChunks.slice(0, numMessages);

          let onChunkCallback: ((chunk: string) => void) | null = null;
          let onCompleteCallback: ((agentType?: string) => void) | null = null;

          vi.mocked(chatService.streamMessage).mockImplementation((msg, callbacks) => {
            onChunkCallback = callbacks.onChunk;
            onCompleteCallback = callbacks.onComplete;
            return vi.fn();
          });

          const { result } = renderHook(() => useChat(false), { wrapper });

          await waitFor(() => {
            expect(result.current.messages).toEqual([]);
          });

          // Send each message and complete its response
          for (let i = 0; i < numMessages; i++) {
            const userMessage = messages[i];
            const chunks = responses[i];

            // Send user message
            act(() => {
              result.current.sendMessage(userMessage);
            });

            // Wait for user message and placeholder
            await waitFor(() => {
              expect(result.current.messages.length).toBe((i + 1) * 2);
            });

            // Send response chunks
            for (const chunk of chunks) {
              act(() => {
                onChunkCallback?.(chunk);
              });
            }

            // Complete the response
            act(() => {
              onCompleteCallback?.('general_assistant');
            });

            // Wait for completion
            await waitFor(() => {
              expect(result.current.isStreaming).toBe(false);
            });
          }

          // Verify all messages are preserved in order
          expect(result.current.messages.length).toBe(numMessages * 2);

          for (let i = 0; i < numMessages; i++) {
            const userMsgIndex = i * 2;
            const assistantMsgIndex = i * 2 + 1;

            // Verify user message
            expect(result.current.messages[userMsgIndex].role).toBe('user');
            expect(result.current.messages[userMsgIndex].content).toBe(messages[i]);

            // Verify assistant message
            expect(result.current.messages[assistantMsgIndex].role).toBe('assistant');
            expect(result.current.messages[assistantMsgIndex].content).toBe(
              responses[i].join('')
            );
            expect(result.current.messages[assistantMsgIndex].isStreaming).toBe(false);
          }

          // Verify no messages were lost
          const userMessageCount = result.current.messages.filter(m => m.role === 'user').length;
          const assistantMessageCount = result.current.messages.filter(m => m.role === 'assistant').length;
          expect(userMessageCount).toBe(numMessages);
          expect(assistantMessageCount).toBe(numMessages);
        }
      ),
      { numRuns: 50 } // Fewer runs due to complexity
    );
  });

  it('Property 13.1: No message duplication', { timeout: 30000 }, async () => {
    // Validates that messages are not duplicated in conversation history
    await fc.assert(
      fc.asyncProperty(
        fc.array(
          fc.string({ minLength: 1, maxLength: 100 }).filter(s => s.trim().length > 0).map((s, i) => `${s}-${i}`), // Unique non-empty messages
          { minLength: 3, maxLength: 8 }
        ),
        async (userMessages) => {
          let onChunkCallback: ((chunk: string) => void) | null = null;
          let onCompleteCallback: ((agentType?: string) => void) | null = null;

          vi.mocked(chatService.streamMessage).mockImplementation((msg, callbacks) => {
            onChunkCallback = callbacks.onChunk;
            onCompleteCallback = callbacks.onComplete;
            return vi.fn();
          });

          const { result } = renderHook(() => useChat(false), { wrapper });

          await waitFor(() => {
            expect(result.current.messages).toEqual([]);
          });

          // Send all messages
          for (const userMessage of userMessages) {
            act(() => {
              result.current.sendMessage(userMessage);
            });

            await waitFor(() => {
              expect(result.current.isStreaming).toBe(true);
            });

            // Complete response
            act(() => {
              onChunkCallback?.('Response');
              onCompleteCallback?.('general_assistant');
            });

            await waitFor(() => {
              expect(result.current.isStreaming).toBe(false);
            });
          }

          // Verify no duplicates
          const userMessageContents = result.current.messages
            .filter(m => m.role === 'user')
            .map(m => m.content);

          const uniqueUserMessages = new Set(userMessageContents);
          expect(uniqueUserMessages.size).toBe(userMessages.length);

          // Verify each original message appears exactly once
          for (const originalMessage of userMessages) {
            const count = userMessageContents.filter(m => m === originalMessage).length;
            expect(count).toBe(1);
          }
        }
      ),
      { numRuns: 100 }
    );
  });

  it('Property 13.2: Message IDs are unique', { timeout: 30000 }, async () => {
    // Validates that all messages have unique IDs
    await fc.assert(
      fc.asyncProperty(
        fc.array(
          fc.string({ minLength: 1, maxLength: 100 }).filter(s => s.trim().length > 0), // Non-empty messages
          { minLength: 2, maxLength: 10 }
        ),
        async (userMessages) => {
          let onChunkCallback: ((chunk: string) => void) | null = null;
          let onCompleteCallback: ((agentType?: string) => void) | null = null;

          vi.mocked(chatService.streamMessage).mockImplementation((msg, callbacks) => {
            onChunkCallback = callbacks.onChunk;
            onCompleteCallback = callbacks.onComplete;
            return vi.fn();
          });

          const { result } = renderHook(() => useChat(false), { wrapper });

          await waitFor(() => {
            expect(result.current.messages).toEqual([]);
          });

          // Send all messages
          for (const userMessage of userMessages) {
            act(() => {
              result.current.sendMessage(userMessage);
            });

            await waitFor(() => {
              expect(result.current.isStreaming).toBe(true);
            });

            act(() => {
              onChunkCallback?.('Response');
              onCompleteCallback?.('general_assistant');
            });

            await waitFor(() => {
              expect(result.current.isStreaming).toBe(false);
            });
          }

          // Verify all IDs are unique
          const messageIds = result.current.messages.map(m => m.id);
          const uniqueIds = new Set(messageIds);
          expect(uniqueIds.size).toBe(messageIds.length);
        }
      ),
      { numRuns: 100 }
    );
  });

  it('Property 13.3: Conversation alternates user/assistant', { timeout: 30000 }, async () => {
    // Validates that conversation follows user -> assistant pattern
    await fc.assert(
      fc.asyncProperty(
        fc.array(
          fc.string({ minLength: 1, maxLength: 100 }).filter(s => s.trim().length > 0), // Non-empty messages
          { minLength: 1, maxLength: 10 }
        ),
        async (userMessages) => {
          let onChunkCallback: ((chunk: string) => void) | null = null;
          let onCompleteCallback: ((agentType?: string) => void) | null = null;

          vi.mocked(chatService.streamMessage).mockImplementation((msg, callbacks) => {
            onChunkCallback = callbacks.onChunk;
            onCompleteCallback = callbacks.onComplete;
            return vi.fn();
          });

          const { result } = renderHook(() => useChat(false), { wrapper });

          await waitFor(() => {
            expect(result.current.messages).toEqual([]);
          });

          // Send all messages
          for (const userMessage of userMessages) {
            act(() => {
              result.current.sendMessage(userMessage);
            });

            await waitFor(() => {
              expect(result.current.isStreaming).toBe(true);
            });

            act(() => {
              onChunkCallback?.('Response');
              onCompleteCallback?.('general_assistant');
            });

            await waitFor(() => {
              expect(result.current.isStreaming).toBe(false);
            });
          }

          // Verify alternating pattern
          for (let i = 0; i < result.current.messages.length; i++) {
            if (i % 2 === 0) {
              expect(result.current.messages[i].role).toBe('user');
            } else {
              expect(result.current.messages[i].role).toBe('assistant');
            }
          }
        }
      ),
      { numRuns: 100 }
    );
  });

  it('Property 13.4: History persists with initial messages', { timeout: 30000 }, async () => {
    // Validates that new messages are appended to existing history
    await fc.assert(
      fc.asyncProperty(
        fc.array(
          fc.record({
            role: fc.constantFrom('user', 'assistant'),
            content: fc.string({ minLength: 1, maxLength: 100 }),
            agent_type: fc.constant('general_assistant'),
            created_at: fc.constant('2024-01-01T09:00:00Z'),
          }),
          { minLength: 1, maxLength: 5 }
        ), // Initial history
        fc.array(
          fc.string({ minLength: 1, maxLength: 100 }),
          { minLength: 1, maxLength: 5 }
        ), // New messages
        async (initialHistory, newMessages) => {
          // Mock history with initial messages
          vi.mocked(chatService.getHistory).mockResolvedValue({
            messages: initialHistory,
            total: initialHistory.length,
          });

          let onChunkCallback: ((chunk: string) => void) | null = null;
          let onCompleteCallback: ((agentType?: string) => void) | null = null;

          vi.mocked(chatService.streamMessage).mockImplementation((msg, callbacks) => {
            onChunkCallback = callbacks.onChunk;
            onCompleteCallback = callbacks.onComplete;
            return vi.fn();
          });

          const { result } = renderHook(() => useChat(false), { wrapper });

          // Wait for history to load
          await waitFor(() => {
            expect(result.current.messages.length).toBe(initialHistory.length);
          });

          const initialMessageCount = result.current.messages.length;

          // Send new messages
          for (const userMessage of newMessages) {
            act(() => {
              result.current.sendMessage(userMessage);
            });

            await waitFor(() => {
              expect(result.current.isStreaming).toBe(true);
            });

            act(() => {
              onChunkCallback?.('Response');
              onCompleteCallback?.('general_assistant');
            });

            await waitFor(() => {
              expect(result.current.isStreaming).toBe(false);
            });
          }

          // Verify history is preserved and new messages appended
          expect(result.current.messages.length).toBe(
            initialMessageCount + newMessages.length * 2
          );

          // Verify initial messages are still at the beginning
          for (let i = 0; i < initialHistory.length; i++) {
            expect(result.current.messages[i].content).toBe(initialHistory[i].content);
          }
        }
      ),
      { numRuns: 50 }
    );
  });

  it('Property 13.5: Timestamps are chronological', { timeout: 30000 }, async () => {
    // Validates that message timestamps are in chronological order
    await fc.assert(
      fc.asyncProperty(
        fc.array(
          fc.string({ minLength: 1, maxLength: 100 }).filter(s => s.trim().length > 0), // Non-empty messages
          { minLength: 2, maxLength: 8 }
        ),
        async (userMessages) => {
          let onChunkCallback: ((chunk: string) => void) | null = null;
          let onCompleteCallback: ((agentType?: string) => void) | null = null;

          vi.mocked(chatService.streamMessage).mockImplementation((msg, callbacks) => {
            onChunkCallback = callbacks.onChunk;
            onCompleteCallback = callbacks.onComplete;
            return vi.fn();
          });

          const { result } = renderHook(() => useChat(false), { wrapper });

          await waitFor(() => {
            expect(result.current.messages).toEqual([]);
          });

          // Send all messages with small delays to ensure different timestamps
          for (const userMessage of userMessages) {
            act(() => {
              result.current.sendMessage(userMessage);
            });

            await waitFor(() => {
              expect(result.current.isStreaming).toBe(true);
            });

            act(() => {
              onChunkCallback?.('Response');
              onCompleteCallback?.('general_assistant');
            });

            await waitFor(() => {
              expect(result.current.isStreaming).toBe(false);
            });

            // Small delay to ensure different timestamps
            await new Promise(resolve => setTimeout(resolve, 10));
          }

          // Verify timestamps are chronological
          for (let i = 1; i < result.current.messages.length; i++) {
            const prevTimestamp = new Date(result.current.messages[i - 1].timestamp);
            const currTimestamp = new Date(result.current.messages[i].timestamp);
            expect(currTimestamp.getTime()).toBeGreaterThanOrEqual(prevTimestamp.getTime());
          }
        }
      ),
      { numRuns: 50 }
    );
  });
});
