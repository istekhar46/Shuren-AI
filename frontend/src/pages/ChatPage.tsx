import { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { useChat } from '../hooks/useChat';
import { MessageList } from '../components/chat/MessageList';
import { MessageInput } from '../components/chat/MessageInput';

export const ChatPage = () => {
  const location = useLocation();
  const state = location.state as { prefillMessage?: string } | null;
  
  const { messages, error, sendMessage, isStreaming, retryLastMessage } = useChat(false); //clearMessages is commented
  const [dismissedError, setDismissedError] = useState(false);
  const [initialMessage, setInitialMessage] = useState<string | null>(
    state?.prefillMessage || null
  );

  useEffect(() => {
    if (initialMessage) {
      handleSendMessage(initialMessage);
      setInitialMessage(null);
    }
  }, [initialMessage]);

  const handleSendMessage = async (message: string) => {
    setDismissedError(false);
    await sendMessage(message);
  };

  const handleDismissError = () => {
    setDismissedError(true);
  };

  return (
    <div className="h-screen flex flex-col" style={{ background: 'var(--color-bg-primary)' }}>
      {/* Header */}
      {/* <div
        className="py-4 pt-0 shadow-sm"
        style={{ background: 'var(--color-bg-primary)', borderBottom: '1px solid var(--color-border)' }}
      >
        <div className="max-w-4xl mx-auto">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold" style={{ color: 'var(--color-text-primary)' }}>AI Chat</h1>
            <button
              onClick={clearMessages}
              disabled={isStreaming || messages.length === 0}
              className="ds-btn-ghost text-sm disabled:opacity-40 disabled:cursor-not-allowed"
            >
              Clear Chat
            </button>
          </div>
        </div>
      </div> */}

      {/* Messages Area */}
      <div className="flex-1 max-w-4xl w-full mx-auto flex flex-col overflow-hidden">
        <MessageList messages={messages} onRetry={retryLastMessage} />
        {error && !dismissedError && (
          <div
            className="mx-4 mb-2 px-4 py-3 rounded relative"
            style={{ background: 'rgba(239,68,68,0.12)', borderLeft: '4px solid #ef4444', color: '#f87171' }}
          >
            <button
              onClick={handleDismissError}
              className="absolute top-2 right-2 hover:opacity-80"
              style={{ color: '#f87171' }}
              aria-label="Dismiss error"
            >
              ✕
            </button>
            <p className="font-semibold">Error</p>
            <p className="pr-6">{error}</p>
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="max-w-4xl w-full mx-auto">
        <MessageInput 
          onSend={handleSendMessage} 
          disabled={isStreaming}
          placeholder={isStreaming ? 'Waiting for response...' : 'Type a message...'}
        />
      </div>
    </div>
  );
};
