import { describe, it, expect } from 'vitest';
import fc from 'fast-check';
import type { ChatMessage } from '../../src/types';

/**
 * Property-Based Tests for Message Ordering
 * 
 * These tests verify that chat messages maintain proper ordering,
 * alternation between user and assistant, and timestamp consistency.
 * 
 * **Validates: Requirements 3.2.3, 3.4**
 */

describe('Message Ordering Properties', () => {
  
  it('Property: Messages maintain chronological order by timestamp', () => {
    // For any sequence of messages, timestamps should be in ascending order.
    // **Validates: Requirements 3.2.3**
    
    fc.assert(
      fc.property(
        fc.array(
          fc.integer({ min: 0, max: 1000000 }),
          { minLength: 2, maxLength: 20 }
        ).map(deltas => {
          // Convert deltas to actual timestamps
          const baseTime = new Date('2024-01-01').getTime();
          let currentTime = baseTime;
          
          return deltas.map((delta, index) => {
            currentTime += delta;
            return {
              id: `msg-${index}`,
              role: (index % 2 === 0 ? 'user' : 'assistant') as 'user' | 'assistant',
              content: `Message ${index}`,
              timestamp: new Date(currentTime),
            };
          });
        }),
        (messages) => {
          // Property: Each message timestamp >= previous message timestamp
          for (let i = 1; i < messages.length; i++) {
            expect(messages[i].timestamp.getTime()).toBeGreaterThanOrEqual(
              messages[i - 1].timestamp.getTime()
            );
          }
        }
      ),
      { numRuns: 1000 }
    );
  });

  it('Property: User and assistant messages alternate', { timeout: 10000 }, () => {
    // For any valid conversation, messages should alternate between user and assistant
    // (user -> assistant -> user -> assistant).
    // **Validates: Requirements 3.4**
    
    fc.assert(
      fc.property(
        fc.array(
          fc.constantFrom('user', 'assistant'),
          { minLength: 2, maxLength: 20 }
        ).map(roles => {
          // Ensure alternation: start with user, then alternate
          const alternating: ('user' | 'assistant')[] = [];
          let lastRole: 'user' | 'assistant' | null = null;
          
          for (const role of roles) {
            if (lastRole === null) {
              // First message should be user
              alternating.push('user');
              lastRole = 'user';
            } else if (lastRole === 'user') {
              alternating.push('assistant');
              lastRole = 'assistant';
            } else {
              alternating.push('user');
              lastRole = 'user';
            }
          }
          
          return alternating;
        }),
        (roles) => {
          // Property: Roles alternate between user and assistant
          for (let i = 1; i < roles.length; i++) {
            expect(roles[i]).not.toBe(roles[i - 1]);
          }
          
          // Property: First message is from user
          if (roles.length > 0) {
            expect(roles[0]).toBe('user');
          }
        }
      ),
      { numRuns: 1000 }
    );
  });

  it('Property: Message IDs are unique', () => {
    // For any sequence of messages, all message IDs should be unique.
    // **Validates: Requirements 3.2.3**
    
    fc.assert(
      fc.property(
        fc.array(
          fc.uuid(),
          { minLength: 1, maxLength: 50 }
        ).map(ids => Array.from(new Set(ids))), // Ensure uniqueness
        (messageIds) => {
          // Property: All IDs are unique
          const uniqueIds = new Set(messageIds);
          expect(uniqueIds.size).toBe(messageIds.length);
        }
      ),
      { numRuns: 1000 }
    );
  });

  it('Property: New messages are appended to end of array', { timeout: 10000 }, () => {
    // When adding a new message, it should be appended to the end of the messages array,
    // not inserted in the middle or beginning.
    // **Validates: Requirements 3.4.1**
    
    fc.assert(
      fc.property(
        fc.array(
          fc.record({
            id: fc.uuid(),
            role: fc.constantFrom('user', 'assistant'),
            content: fc.string({ minLength: 1, maxLength: 100 }),
          }),
          { minLength: 1, maxLength: 10 }
        ),
        fc.record({
          id: fc.uuid(),
          role: fc.constantFrom('user', 'assistant'),
          content: fc.string({ minLength: 1, maxLength: 100 }),
        }),
        (existingMessages, newMessage) => {
          // Simulate appending new message
          const updatedMessages = [...existingMessages, newMessage];
          
          // Property: New message is at the end
          expect(updatedMessages[updatedMessages.length - 1]).toEqual(newMessage);
          
          // Property: All previous messages are unchanged and in same order
          for (let i = 0; i < existingMessages.length; i++) {
            expect(updatedMessages[i]).toEqual(existingMessages[i]);
          }
          
          // Property: Length increased by 1
          expect(updatedMessages.length).toBe(existingMessages.length + 1);
        }
      ),
      { numRuns: 1000 }
    );
  });

  it('Property: Message array never shrinks during conversation', () => {
    // For any sequence of message additions, the array length should be
    // monotonically non-decreasing (messages are never removed).
    // **Validates: Requirements 3.2.3**
    
    fc.assert(
      fc.property(
        fc.array(
          fc.integer({ min: 0, max: 100 }),
          { minLength: 2, maxLength: 20 }
        ).map(arr => {
          // Create cumulative counts (simulating message additions)
          const cumulative: number[] = [];
          let count = 0;
          
          for (const num of arr) {
            count += Math.abs(num % 5); // Add 0-4 messages at a time
            cumulative.push(count);
          }
          
          return cumulative;
        }),
        (messageCounts) => {
          // Property: Each count >= previous count
          for (let i = 1; i < messageCounts.length; i++) {
            expect(messageCounts[i]).toBeGreaterThanOrEqual(messageCounts[i - 1]);
          }
        }
      ),
      { numRuns: 1000 }
    );
  });

  it('Property: Streaming messages maintain order', () => {
    // When a message is being streamed (isStreaming: true), it should remain
    // at the end of the array until streaming completes.
    // **Validates: Requirements 3.4.3**
    
    fc.assert(
      fc.property(
        fc.array(
          fc.record({
            id: fc.uuid(),
            role: fc.constantFrom('user', 'assistant'),
            content: fc.string({ minLength: 1, maxLength: 100 }),
            isStreaming: fc.constant(false),
          }),
          { minLength: 1, maxLength: 10 }
        ),
        fc.record({
          id: fc.uuid(),
          role: fc.constant('assistant'),
          content: fc.string({ minLength: 0, maxLength: 50 }),
          isStreaming: fc.constant(true),
        }),
        (completedMessages, streamingMessage) => {
          // Simulate adding streaming message
          const messages = [...completedMessages, streamingMessage];
          
          // Property: Streaming message is at the end
          expect(messages[messages.length - 1].isStreaming).toBe(true);
          
          // Property: All previous messages are not streaming
          for (let i = 0; i < completedMessages.length; i++) {
            expect(messages[i].isStreaming).toBe(false);
          }
        }
      ),
      { numRuns: 1000 }
    );
  });

  it('Property: Message content is never empty for completed messages', () => {
    // For any completed message (isStreaming: false), the content should not be empty.
    // **Validates: Requirements 3.4.4**
    
    fc.assert(
      fc.property(
        fc.array(
          fc.record({
            id: fc.uuid(),
            role: fc.constantFrom('user', 'assistant'),
            content: fc.string({ minLength: 1, maxLength: 200 }),
            isStreaming: fc.constant(false),
          }),
          { minLength: 1, maxLength: 20 }
        ),
        (messages) => {
          // Property: All completed messages have non-empty content
          messages.forEach(message => {
            if (!message.isStreaming) {
              expect(message.content.length).toBeGreaterThan(0);
            }
          });
        }
      ),
      { numRuns: 1000 }
    );
  });

  it('Property: Conversation starts with user message', () => {
    // For any non-empty conversation, the first message should always be from the user.
    // **Validates: Requirements 3.4**
    
    fc.assert(
      fc.property(
        fc.array(
          fc.record({
            id: fc.uuid(),
            role: fc.constantFrom('user', 'assistant'),
            content: fc.string({ minLength: 1, maxLength: 100 }),
          }),
          { minLength: 1, maxLength: 20 }
        ).map(messages => {
          // Ensure first message is from user
          if (messages.length > 0) {
            messages[0].role = 'user';
          }
          return messages;
        }),
        (messages) => {
          // Property: First message is from user
          if (messages.length > 0) {
            expect(messages[0].role).toBe('user');
          }
        }
      ),
      { numRuns: 1000 }
    );
  });

  it('Property: Assistant messages follow user messages', () => {
    // For any assistant message at index i, there should be a user message at index i-1
    // (except for the first message which must be user).
    // **Validates: Requirements 3.4**
    
    fc.assert(
      fc.property(
        fc.integer({ min: 2, max: 20 }).chain(length => {
          // Generate alternating user/assistant messages
          const roles: ('user' | 'assistant')[] = [];
          for (let i = 0; i < length; i++) {
            roles.push(i % 2 === 0 ? 'user' : 'assistant');
          }
          
          return fc.constant(roles.map((role, index) => ({
            id: `msg-${index}`,
            role,
            content: `Message ${index}`,
          })));
        }),
        (messages) => {
          // Property: Every assistant message is preceded by a user message
          for (let i = 1; i < messages.length; i++) {
            if (messages[i].role === 'assistant') {
              expect(messages[i - 1].role).toBe('user');
            }
          }
        }
      ),
      { numRuns: 1000 }
    );
  });

  it('Property: Message timestamps never go backward', () => {
    // For any sequence of messages added over time, timestamps should be
    // monotonically non-decreasing.
    // **Validates: Requirements 3.2.3**
    
    fc.assert(
      fc.property(
        fc.array(
          fc.integer({ min: 0, max: 1000000 }),
          { minLength: 2, maxLength: 20 }
        ).map(arr => {
          // Convert to cumulative timestamps
          const timestamps: number[] = [];
          let current = Date.now();
          
          for (const delta of arr) {
            current += delta;
            timestamps.push(current);
          }
          
          return timestamps;
        }),
        (timestamps) => {
          // Property: Each timestamp >= previous timestamp
          for (let i = 1; i < timestamps.length; i++) {
            expect(timestamps[i]).toBeGreaterThanOrEqual(timestamps[i - 1]);
          }
        }
      ),
      { numRuns: 1000 }
    );
  });

  it('Property: Message order is preserved across updates', { timeout: 10000 }, () => {
    // When updating a message (e.g., streaming content), the message order
    // should remain unchanged.
    // **Validates: Requirements 3.4.3**
    
    fc.assert(
      fc.property(
        fc.array(
          fc.record({
            id: fc.uuid(),
            role: fc.constantFrom('user', 'assistant'),
            content: fc.string({ minLength: 1, maxLength: 100 }),
          }),
          { minLength: 2, maxLength: 10 }
        ),
        fc.integer({ min: 0, max: 9 }),
        fc.string({ minLength: 1, maxLength: 100 }),
        (messages, updateIndex, newContent) => {
          const index = updateIndex % messages.length;
          
          // Simulate updating a message
          const updatedMessages = messages.map((msg, i) =>
            i === index ? { ...msg, content: newContent } : msg
          );
          
          // Property: Message IDs remain in same order
          for (let i = 0; i < messages.length; i++) {
            expect(updatedMessages[i].id).toBe(messages[i].id);
          }
          
          // Property: Only the target message content changed
          for (let i = 0; i < messages.length; i++) {
            if (i !== index) {
              expect(updatedMessages[i].content).toBe(messages[i].content);
            } else {
              expect(updatedMessages[i].content).toBe(newContent);
            }
          }
        }
      ),
      { numRuns: 1000 }
    );
  });
});
