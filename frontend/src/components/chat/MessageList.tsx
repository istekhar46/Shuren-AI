import { useEffect, useRef } from 'react';
import type { ChatMessage } from '../../types';

interface MessageListProps {
  messages: ChatMessage[];
  onRetry?: () => void;
}

export const MessageList = ({ messages, onRetry }: MessageListProps) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const scrollTimeoutRef = useRef<number | undefined>(undefined);

  useEffect(() => {
    if (scrollTimeoutRef.current !== undefined) {
      clearTimeout(scrollTimeoutRef.current);
    }
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
      <div className="flex-1 flex items-center justify-center" style={{ color: 'var(--color-text-muted)' }}>
        <p>No messages yet. Start a conversation with an AI agent!</p>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-4">
      <div aria-live="polite" aria-atomic="false" className="sr-only">
        {messages[messages.length - 1]?.isStreaming && 'Assistant is responding'}
      </div>

      {messages.map((message) => (
        <div
          key={message.id}
          className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
        >
          <div
            className={`max-w-[70%] rounded-lg px-4 py-2`}
            style={
              message.role === 'user'
                ? { background: 'var(--gradient-accent)', color: '#fff' }
                : { background: 'var(--color-bg-surface)', color: 'var(--color-text-primary)', border: '1px solid var(--color-border)' }
            }
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
            <div className="whitespace-pre-wrap break-words">
              {message.content}
              {message.isStreaming && (
                <span
                  className="inline-block ml-1 w-2 h-4 animate-pulse"
                  style={{ background: 'var(--color-violet)' }}
                  aria-label="typing"
                  role="status"
                >
                  ▊
                </span>
              )}
            </div>

            {message.error && (
              <div className="mt-2 space-y-2">
                <div
                  className="text-sm px-2 py-1 rounded"
                  role="alert"
                  style={{ color: '#f87171', background: 'rgba(239,68,68,0.1)' }}
                >
                  {message.error}
                </div>
                {onRetry && (
                  <button
                    onClick={onRetry}
                    className="text-sm underline"
                    style={{ color: 'var(--color-violet)' }}
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
