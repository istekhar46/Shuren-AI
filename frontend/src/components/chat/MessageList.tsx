import { useEffect, useRef } from 'react';
import type { ChatMessage } from '../../types';

interface MessageListProps {
  messages: ChatMessage[];
  onRetry?: () => void;
}

export const MessageList = ({ messages, onRetry }: MessageListProps) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const scrollTimeoutRef = useRef<number | undefined>(undefined);

  /**
   * Auto-scroll with debouncing for performance
   * Requirements 4.5, 9.3: Debounce scroll updates to 100ms
   */
  useEffect(() => {
    // Clear existing timeout
    if (scrollTimeoutRef.current !== undefined) {
      clearTimeout(scrollTimeoutRef.current);
    }

    // Debounce scroll updates during rapid streaming
    scrollTimeoutRef.current = window.setTimeout(() => {
      requestAnimationFrame(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
      });
    }, 100);

    return () => {
      if (scrollTimeoutRef.current !== undefined) {
        clearTimeout(scrollTimeoutRef.current);
      }
    };
  }, [messages]);

  if (messages.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center text-gray-500">
        <p>No messages yet. Start a conversation with an AI agent!</p>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-4">
      {/* ARIA live region for accessibility - Requirements 8.1, 8.2, 8.3 */}
      <div 
        aria-live="polite" 
        aria-atomic="false" 
        className="sr-only"
      >
        {messages[messages.length - 1]?.isStreaming && 
          'Assistant is responding'}
      </div>

      {messages.map((message) => (
        <div
          key={message.id}
          className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
        >
          <div
            className={`max-w-[70%] rounded-lg px-4 py-2 ${
              message.role === 'user'
                ? 'bg-blue-500 text-white'
                : message.isStreaming
                ? 'bg-gray-100 text-gray-900'
                : 'bg-gray-200 text-gray-900'
            }`}
            data-streaming={message.isStreaming ? 'true' : 'false'}
            data-testid={`message-${message.role}`}
          >
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-semibold">
                {message.role === 'user' ? 'You' : 'Agent'}
              </span>
              <span className="text-xs opacity-70">
                {new Date(message.timestamp).toLocaleTimeString()}
              </span>
            </div>
            
            {/* Message content with streaming indicator - Requirements 4.1, 4.3, 4.4 */}
            <div className="whitespace-pre-wrap break-words">
              {message.content}
              {message.isStreaming && (
                <span 
                  className="typing-cursor inline-block ml-1 w-2 h-4 bg-gray-900 animate-pulse"
                  aria-label="typing"
                  role="status"
                >
                  ▊
                </span>
              )}
            </div>

            {/* Error display and retry button - Requirements 6.1, 6.2, 6.4 */}
            {message.error && (
              <div className="mt-2 space-y-2">
                <div 
                  className="text-sm text-red-600 bg-red-50 px-2 py-1 rounded"
                  role="alert"
                >
                  {message.error}
                </div>
                {onRetry && (
                  <button
                    onClick={onRetry}
                    className="text-sm text-blue-600 hover:text-blue-800 underline"
                    aria-label="Retry sending message"
                  >
                    Retry
                  </button>
                )}
              </div>
            )}
          </div>
        </div>
      ))}
      <div ref={messagesEndRef} />
    </div>
  );
};
