import { useState, type KeyboardEvent } from 'react';

interface MessageInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

export const MessageInput = ({ onSend, disabled, placeholder }: MessageInputProps) => {
  const [message, setMessage] = useState('');

  const handleSend = () => {
    if (message.trim() && !disabled) {
      onSend(message);
      setMessage('');
    }
  };

  const handleKeyPress = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div
      className="p-4"
      style={{ borderTop: '1px solid var(--color-border)', background: 'var(--color-bg-primary)' }}
    >
      <div className="flex gap-2">
        <textarea
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder={placeholder || "Type your message... (Press Enter to send, Shift+Enter for new line)"}
          disabled={disabled}
          rows={3}
          className="flex-1 px-4 py-2 rounded-lg resize-none focus:ring-2 focus:ring-[var(--color-violet)] focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed"
          style={{
            background: 'var(--color-bg-surface)',
            border: '1px solid var(--color-border)',
            color: 'var(--color-text-primary)',
          }}
        />
        <button
          onClick={handleSend}
          disabled={disabled || !message.trim()}
          className="ds-btn-primary px-6 py-2 disabled:opacity-40 disabled:cursor-not-allowed"
        >
          Send
        </button>
      </div>
    </div>
  );
};
