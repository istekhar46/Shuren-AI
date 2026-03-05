import { useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
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
    <div className="flex-1 overflow-y-auto py-4 space-y-4">
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
            <div className="text-[15px] leading-relaxed wrap-break-word markdown-content">
              {message.status === 'searching' && (
                <div className="flex items-center gap-2 mt-1 mb-2 px-3 py-1.5 rounded-md border" 
                  style={{ 
                    background: 'rgba(167, 139, 250, 0.08)', 
                    borderColor: 'rgba(167, 139, 250, 0.2)' 
                  }}>
                  <div className="flex items-center gap-1.5 h-4">
                    <div className="w-1.5 h-1.5 rounded-full animate-bounce" style={{ background: 'var(--color-violet)', animationDelay: '0ms' }} />
                    <div className="w-1.5 h-1.5 rounded-full animate-bounce" style={{ background: 'var(--color-violet)', animationDelay: '150ms' }} />
                    <div className="w-1.5 h-1.5 rounded-full animate-bounce" style={{ background: 'var(--color-violet)', animationDelay: '300ms' }} />
                  </div>
                  <span className="text-xs font-medium" style={{ color: 'var(--color-violet)' }}>Searching web...</span>
                </div>
              )}
              {message.content ? (
                <>
                  <ReactMarkdown
                     remarkPlugins={[remarkGfm]}
                     components={{
                        p: ({node, ...props}) => <p className="mb-3 last:mb-0" {...props} />,
                        ul: ({node, ...props}) => <ul className="list-disc pl-5 mb-3 space-y-1" {...props} />,
                        ol: ({node, ...props}) => <ol className="list-decimal pl-5 mb-3 space-y-1" {...props} />,
                        li: ({node, ...props}) => <li className="" {...props} />,
                        h1: ({node, ...props}) => <h1 className="text-xl font-bold mb-3 mt-5" {...props} />,
                        h2: ({node, ...props}) => <h2 className="text-lg font-bold mb-3 mt-4" {...props} />,
                        h3: ({node, ...props}) => <h3 className="text-md font-bold mb-2 mt-3" {...props} />,
                        h4: ({node, ...props}) => <h4 className="font-bold mb-2 mt-2" {...props} />,
                        strong: ({node, ...props}) => <strong className="font-bold" {...props} />,
                        hr: ({node, ...props}) => <hr className="my-4 border-t border-current opacity-20" {...props} />,
                        table: ({node, ...props}) => <div className="overflow-x-auto mb-3"><table className="w-full text-left text-sm border-collapse" {...props} /></div>,
                        th: ({node, ...props}) => <th className="border-b-2 border-current opacity-70 p-2" {...props} />,
                        td: ({node, ...props}) => <td className="border-b border-current opacity-50 p-2" {...props} />,
                     }}
                  >
                    {message.content}
                  </ReactMarkdown>
                  {message.isStreaming && !message.status && (
                    <span
                      className="inline-block ml-1 w-2 h-4 animate-pulse"
                      style={{ background: 'var(--color-violet)' }}
                      aria-label="typing"
                      role="status"
                    >
                      ▊
                    </span>
                  )}
                </>
              ) : message.isStreaming && !message.status ? (
                <div className="flex items-center gap-1.5 h-6 px-1 py-1" aria-label="Agent is typing" role="status">
                  <div className="w-2 h-2 rounded-full animate-bounce" style={{ background: 'var(--color-violet)', animationDelay: '0ms' }} />
                  <div className="w-2 h-2 rounded-full animate-bounce" style={{ background: 'var(--color-violet)', animationDelay: '150ms' }} />
                  <div className="w-2 h-2 rounded-full animate-bounce" style={{ background: 'var(--color-violet)', animationDelay: '300ms' }} />
                </div>
              ) : null}
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
