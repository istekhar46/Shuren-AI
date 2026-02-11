import { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { useChat } from '../hooks/useChat';
import { AgentSelector } from '../components/chat/AgentSelector';
import { MessageList } from '../components/chat/MessageList';
import { MessageInput } from '../components/chat/MessageInput';
import { LoadingIndicator } from '../components/chat/LoadingIndicator';
import type { AgentType } from '../types';

export const ChatPage = () => {
  const location = useLocation();
  const state = location.state as { prefillMessage?: string; agentType?: AgentType } | null;
  
  const [selectedAgent, setSelectedAgent] = useState<AgentType>(
    state?.agentType || 'general_assistant'
  );
  const { messages, loading, error, sendMessage, clearMessages } = useChat();
  const [dismissedError, setDismissedError] = useState(false);
  const [initialMessage, setInitialMessage] = useState<string | null>(
    state?.prefillMessage || null
  );

  // Auto-send initial message if provided
  useEffect(() => {
    if (initialMessage) {
      handleSendMessage(initialMessage);
      setInitialMessage(null);
    }
  }, [initialMessage]);

  const handleSendMessage = async (message: string) => {
    setDismissedError(false);
    await sendMessage(message, selectedAgent);
  };

  const handleDismissError = () => {
    setDismissedError(true);
  };

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-300 p-4 shadow-sm">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">AI Chat</h1>
          <div className="flex items-center gap-4">
            <div className="flex-1">
              <AgentSelector
                value={selectedAgent}
                onChange={setSelectedAgent}
                disabled={loading}
              />
            </div>
            <button
              onClick={clearMessages}
              disabled={loading || messages.length === 0}
              className="px-4 py-2 text-sm bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 disabled:bg-gray-100 disabled:cursor-not-allowed transition-colors"
            >
              Clear Chat
            </button>
          </div>
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 max-w-4xl w-full mx-auto flex flex-col overflow-hidden">
        <MessageList messages={messages} />
        {loading && <LoadingIndicator />}
        {error && !dismissedError && (
          <div className="mx-4 mb-2 px-4 py-3 bg-red-100 border-l-4 border-red-500 text-red-700 rounded relative">
            <button
              onClick={handleDismissError}
              className="absolute top-2 right-2 text-red-700 hover:text-red-900"
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
        <MessageInput onSend={handleSendMessage} disabled={loading} />
      </div>
    </div>
  );
};
