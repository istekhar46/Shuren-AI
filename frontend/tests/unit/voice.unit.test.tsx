import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { VoicePage } from '../../src/pages/VoicePage';
import { VoiceControls } from '../../src/components/voice/VoiceControls';
import { AgentSelector } from '../../src/components/voice/AgentSelector';
import { ErrorDisplay } from '../../src/components/voice/ErrorDisplay';
import * as useVoiceSessionModule from '../../src/hooks/useVoiceSession';
import type { AgentType } from '../../src/types';

// Mock the voice service
vi.mock('../../src/services/voiceService', () => ({
  voiceService: {
    startSession: vi.fn(),
    getStatus: vi.fn(),
    endSession: vi.fn(),
  },
}));

// Mock the useVoiceSession hook for VoicePage tests
vi.mock('../../src/hooks/useVoiceSession');

// Mock navigator.mediaDevices
const mockGetUserMedia = vi.fn();
Object.defineProperty(global.navigator, 'mediaDevices', {
  value: {
    getUserMedia: mockGetUserMedia,
  },
  writable: true,
});

describe('Voice Components Unit Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('VoiceControls', () => {
    it('should render start button when not connected', () => {
      const onStart = vi.fn();
      const onEnd = vi.fn();
      
      render(
        <VoiceControls
          isConnected={false}
          isStarting={false}
          onStart={onStart}
          onEnd={onEnd}
        />
      );

      expect(screen.getByRole('button', { name: /start voice session/i })).toBeInTheDocument();
      expect(screen.queryByRole('button', { name: /end session/i })).not.toBeInTheDocument();
    });

    it('should render end button when connected', () => {
      const onStart = vi.fn();
      const onEnd = vi.fn();
      
      render(
        <VoiceControls
          isConnected={true}
          isStarting={false}
          onStart={onStart}
          onEnd={onEnd}
        />
      );

      expect(screen.getByRole('button', { name: /end session/i })).toBeInTheDocument();
      expect(screen.queryByRole('button', { name: /start voice session/i })).not.toBeInTheDocument();
    });

    it('should call onStart when start button is clicked', async () => {
      const onStart = vi.fn();
      const onEnd = vi.fn();
      const user = userEvent.setup();
      
      render(
        <VoiceControls
          isConnected={false}
          isStarting={false}
          onStart={onStart}
          onEnd={onEnd}
        />
      );

      const startButton = screen.getByRole('button', { name: /start voice session/i });
      await user.click(startButton);

      expect(onStart).toHaveBeenCalledTimes(1);
    });

    it('should call onEnd when end button is clicked', async () => {
      const onStart = vi.fn();
      const onEnd = vi.fn();
      const user = userEvent.setup();
      
      render(
        <VoiceControls
          isConnected={true}
          isStarting={false}
          onStart={onStart}
          onEnd={onEnd}
        />
      );

      const endButton = screen.getByRole('button', { name: /end session/i });
      await user.click(endButton);

      expect(onEnd).toHaveBeenCalledTimes(1);
    });

    it('should disable start button when starting', () => {
      const onStart = vi.fn();
      const onEnd = vi.fn();
      
      render(
        <VoiceControls
          isConnected={false}
          isStarting={true}
          onStart={onStart}
          onEnd={onEnd}
        />
      );

      const startButton = screen.getByRole('button', { name: /starting/i });
      expect(startButton).toBeDisabled();
    });

    it('should show "Starting..." text when starting', () => {
      const onStart = vi.fn();
      const onEnd = vi.fn();
      
      render(
        <VoiceControls
          isConnected={false}
          isStarting={true}
          onStart={onStart}
          onEnd={onEnd}
        />
      );

      expect(screen.getByText('Starting...')).toBeInTheDocument();
    });

    it('should not call onStart when button is disabled', async () => {
      const onStart = vi.fn();
      const onEnd = vi.fn();
      const user = userEvent.setup();
      
      render(
        <VoiceControls
          isConnected={false}
          isStarting={true}
          onStart={onStart}
          onEnd={onEnd}
        />
      );

      const startButton = screen.getByRole('button', { name: /starting/i });
      await user.click(startButton);

      expect(onStart).not.toHaveBeenCalled();
    });

    it('should render mute button when connected and onToggleMicrophone is provided', () => {
      const onStart = vi.fn();
      const onEnd = vi.fn();
      const onToggleMicrophone = vi.fn();
      
      render(
        <VoiceControls
          isConnected={true}
          isStarting={false}
          isMicrophoneEnabled={true}
          onStart={onStart}
          onEnd={onEnd}
          onToggleMicrophone={onToggleMicrophone}
        />
      );

      expect(screen.getByRole('button', { name: /mute/i })).toBeInTheDocument();
    });

    it('should call onToggleMicrophone when mute button is clicked', async () => {
      const onStart = vi.fn();
      const onEnd = vi.fn();
      const onToggleMicrophone = vi.fn();
      const user = userEvent.setup();
      
      render(
        <VoiceControls
          isConnected={true}
          isStarting={false}
          isMicrophoneEnabled={true}
          onStart={onStart}
          onEnd={onEnd}
          onToggleMicrophone={onToggleMicrophone}
        />
      );

      const muteButton = screen.getByRole('button', { name: /mute/i });
      await user.click(muteButton);

      expect(onToggleMicrophone).toHaveBeenCalledTimes(1);
    });

    it('should show unmute button when microphone is disabled', () => {
      const onStart = vi.fn();
      const onEnd = vi.fn();
      const onToggleMicrophone = vi.fn();
      
      render(
        <VoiceControls
          isConnected={true}
          isStarting={false}
          isMicrophoneEnabled={false}
          onStart={onStart}
          onEnd={onEnd}
          onToggleMicrophone={onToggleMicrophone}
        />
      );

      expect(screen.getByRole('button', { name: /unmute/i })).toBeInTheDocument();
    });

    it('should not render mute button when onToggleMicrophone is not provided', () => {
      const onStart = vi.fn();
      const onEnd = vi.fn();
      
      render(
        <VoiceControls
          isConnected={true}
          isStarting={false}
          onStart={onStart}
          onEnd={onEnd}
        />
      );

      expect(screen.queryByRole('button', { name: /mute/i })).not.toBeInTheDocument();
      expect(screen.queryByRole('button', { name: /unmute/i })).not.toBeInTheDocument();
    });
  });

  describe('AgentSelector', () => {
    it('should render with default value', () => {
      const onChange = vi.fn();
      
      render(<AgentSelector value="general_assistant" onChange={onChange} />);

      const select = screen.getByLabelText(/select agent/i);
      expect(select).toBeInTheDocument();
      expect(select).toHaveValue('general_assistant');
    });

    it('should call onChange when agent is selected', async () => {
      const onChange = vi.fn();
      const user = userEvent.setup();
      
      render(<AgentSelector value="general_assistant" onChange={onChange} />);

      const select = screen.getByLabelText(/select agent/i);
      await user.selectOptions(select, 'workout_planning');

      expect(onChange).toHaveBeenCalledWith('workout_planning');
    });

    it('should display all agent options', () => {
      const onChange = vi.fn();
      
      render(<AgentSelector value="general_assistant" onChange={onChange} />);

      const options = screen.getAllByRole('option');
      expect(options).toHaveLength(6);

      expect(screen.getByRole('option', { name: /General Assistant/i })).toBeInTheDocument();
      expect(screen.getByRole('option', { name: /Workout Planning/i })).toBeInTheDocument();
      expect(screen.getByRole('option', { name: /Diet Planning/i })).toBeInTheDocument();
      expect(screen.getByRole('option', { name: /Supplement Guidance/i })).toBeInTheDocument();
      expect(screen.getByRole('option', { name: /Tracking & Adjustment/i })).toBeInTheDocument();
      expect(screen.getByRole('option', { name: /Scheduling & Reminder/i })).toBeInTheDocument();
    });

    it('should be disabled when disabled prop is true', () => {
      const onChange = vi.fn();
      
      render(<AgentSelector value="general_assistant" onChange={onChange} disabled />);

      const select = screen.getByLabelText(/select agent/i);
      expect(select).toBeDisabled();
    });

    it('should not call onChange when disabled', async () => {
      const onChange = vi.fn();
      const user = userEvent.setup();
      
      render(<AgentSelector value="general_assistant" onChange={onChange} disabled />);

      const select = screen.getByLabelText(/select agent/i);
      await user.click(select);

      expect(onChange).not.toHaveBeenCalled();
    });
  });

  describe('ErrorDisplay', () => {
    it('should display error message', () => {
      render(<ErrorDisplay error="Test error message" />);

      expect(screen.getByText('Error')).toBeInTheDocument();
      expect(screen.getByText('Test error message')).toBeInTheDocument();
    });

    it('should render dismiss button when onDismiss is provided', () => {
      const onDismiss = vi.fn();
      
      render(<ErrorDisplay error="Test error" onDismiss={onDismiss} />);

      expect(screen.getByLabelText('Dismiss error')).toBeInTheDocument();
    });

    it('should not render dismiss button when onDismiss is not provided', () => {
      render(<ErrorDisplay error="Test error" />);

      expect(screen.queryByLabelText('Dismiss error')).not.toBeInTheDocument();
    });

    it('should call onDismiss when dismiss button is clicked', async () => {
      const onDismiss = vi.fn();
      const user = userEvent.setup();
      
      render(<ErrorDisplay error="Test error" onDismiss={onDismiss} />);

      const dismissButton = screen.getByLabelText('Dismiss error');
      await user.click(dismissButton);

      expect(onDismiss).toHaveBeenCalledTimes(1);
    });
  });

  describe('VoicePage Integration', () => {
    beforeEach(() => {
      vi.clearAllMocks();
    });

    it('should render all voice components when not connected', () => {
      const mockUseVoiceSession = {
        room: null,
        isConnected: false,
        transcription: [],
        sessionStatus: { connected: false, participantCount: 0, duration: 0 },
        latency: 0,
        error: null,
        roomName: null,
        isStarting: false,
        startSession: vi.fn(),
        endSession: vi.fn(),
      };

      vi.mocked(useVoiceSessionModule.useVoiceSession).mockReturnValue(mockUseVoiceSession);

      render(<VoicePage />);

      expect(screen.getByText('Voice Session')).toBeInTheDocument();
      expect(screen.getByText('Start a Voice Session')).toBeInTheDocument();
      expect(screen.getByLabelText(/select agent/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /start voice session/i })).toBeInTheDocument();
    });

    it('should start session with selected agent type', async () => {
      const mockStartSession = vi.fn();
      const mockUseVoiceSession = {
        room: null,
        isConnected: false,
        transcription: [],
        sessionStatus: { connected: false, participantCount: 0, duration: 0 },
        latency: 0,
        error: null,
        roomName: null,
        isStarting: false,
        startSession: mockStartSession,
        endSession: vi.fn(),
      };

      vi.mocked(useVoiceSessionModule.useVoiceSession).mockReturnValue(mockUseVoiceSession);

      const user = userEvent.setup();
      render(<VoicePage />);

      // Select workout planning agent
      const agentSelect = screen.getByLabelText(/select agent/i);
      await user.selectOptions(agentSelect, 'workout_planning');

      // Click start button
      const startButton = screen.getByRole('button', { name: /start voice session/i });
      await user.click(startButton);

      expect(mockStartSession).toHaveBeenCalledWith('workout_planning');
    });

    it('should end session when end button is clicked', async () => {
      const mockEndSession = vi.fn();
      const mockRoom = {
        localParticipant: {
          isMicrophoneEnabled: true,
        },
      };
      
      const mockUseVoiceSession = {
        room: mockRoom as any,
        isConnected: true,
        transcription: [],
        sessionStatus: { connected: true, participantCount: 2, duration: 30 },
        latency: 50,
        error: null,
        roomName: 'test-room',
        isStarting: false,
        startSession: vi.fn(),
        endSession: mockEndSession,
        toggleMicrophone: vi.fn(),
      };

      vi.mocked(useVoiceSessionModule.useVoiceSession).mockReturnValue(mockUseVoiceSession);

      const user = userEvent.setup();
      render(<VoicePage />);

      const endButton = screen.getByRole('button', { name: /end session/i });
      await user.click(endButton);

      expect(mockEndSession).toHaveBeenCalledTimes(1);
    });

    it('should display error message when error occurs', () => {
      const mockUseVoiceSession = {
        room: null,
        isConnected: false,
        transcription: [],
        sessionStatus: { connected: false, participantCount: 0, duration: 0 },
        latency: 0,
        error: 'Microphone permission denied',
        roomName: null,
        isStarting: false,
        startSession: vi.fn(),
        endSession: vi.fn(),
      };

      vi.mocked(useVoiceSessionModule.useVoiceSession).mockReturnValue(mockUseVoiceSession);

      render(<VoicePage />);

      expect(screen.getByText('Error')).toBeInTheDocument();
      expect(screen.getByText('Microphone permission denied')).toBeInTheDocument();
    });

    it('should dismiss error message when dismiss button is clicked', async () => {
      const mockUseVoiceSession = {
        room: null,
        isConnected: false,
        transcription: [],
        sessionStatus: { connected: false, participantCount: 0, duration: 0 },
        latency: 0,
        error: 'Test error',
        roomName: null,
        isStarting: false,
        startSession: vi.fn(),
        endSession: vi.fn(),
      };

      vi.mocked(useVoiceSessionModule.useVoiceSession).mockReturnValue(mockUseVoiceSession);

      const user = userEvent.setup();
      render(<VoicePage />);

      expect(screen.getByText('Test error')).toBeInTheDocument();

      const dismissButton = screen.getByLabelText('Dismiss error');
      await user.click(dismissButton);

      expect(screen.queryByText('Test error')).not.toBeInTheDocument();
    });

    it('should disable agent selector when starting', () => {
      const mockUseVoiceSession = {
        room: null,
        isConnected: false,
        transcription: [],
        sessionStatus: { connected: false, participantCount: 0, duration: 0 },
        latency: 0,
        error: null,
        roomName: null,
        isStarting: true,
        startSession: vi.fn(),
        endSession: vi.fn(),
      };

      vi.mocked(useVoiceSessionModule.useVoiceSession).mockReturnValue(mockUseVoiceSession);

      render(<VoicePage />);

      const agentSelect = screen.getByLabelText(/select agent/i);
      expect(agentSelect).toBeDisabled();
    });

    it('should show active session UI when connected', () => {
      const mockRoom = {
        localParticipant: {
          isMicrophoneEnabled: true,
        },
      };
      
      const mockUseVoiceSession = {
        room: mockRoom as any,
        isConnected: true,
        transcription: [],
        sessionStatus: { connected: true, participantCount: 2, duration: 45 },
        latency: 75,
        error: null,
        roomName: 'test-room',
        isStarting: false,
        startSession: vi.fn(),
        endSession: vi.fn(),
        toggleMicrophone: vi.fn(),
      };

      vi.mocked(useVoiceSessionModule.useVoiceSession).mockReturnValue(mockUseVoiceSession);

      render(<VoicePage />);

      expect(screen.getByText('Active Session')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /end session/i })).toBeInTheDocument();
      expect(screen.queryByText('Start a Voice Session')).not.toBeInTheDocument();
    });

    it('should clear error when starting new session', async () => {
      const mockStartSession = vi.fn();
      const mockUseVoiceSession = {
        room: null,
        isConnected: false,
        transcription: [],
        sessionStatus: { connected: false, participantCount: 0, duration: 0 },
        latency: 0,
        error: 'Previous error',
        roomName: null,
        isStarting: false,
        startSession: mockStartSession,
        endSession: vi.fn(),
        toggleMicrophone: vi.fn(),
      };

      vi.mocked(useVoiceSessionModule.useVoiceSession).mockReturnValue(mockUseVoiceSession);

      const user = userEvent.setup();
      const { rerender } = render(<VoicePage />);

      expect(screen.getByText('Previous error')).toBeInTheDocument();

      // Click start button
      const startButton = screen.getByRole('button', { name: /start voice session/i });
      await user.click(startButton);

      // Update mock to simulate error cleared
      mockUseVoiceSession.error = null;
      vi.mocked(useVoiceSessionModule.useVoiceSession).mockReturnValue(mockUseVoiceSession);
      rerender(<VoicePage />);

      expect(screen.queryByText('Previous error')).not.toBeInTheDocument();
    });

    it('should render mute button when connected', () => {
      const mockRoom = {
        localParticipant: {
          isMicrophoneEnabled: true,
        },
      };
      
      const mockUseVoiceSession = {
        room: mockRoom as any,
        isConnected: true,
        transcription: [],
        sessionStatus: { connected: true, participantCount: 2, duration: 30 },
        latency: 50,
        error: null,
        roomName: 'test-room',
        isStarting: false,
        startSession: vi.fn(),
        endSession: vi.fn(),
        toggleMicrophone: vi.fn(),
      };

      vi.mocked(useVoiceSessionModule.useVoiceSession).mockReturnValue(mockUseVoiceSession);

      render(<VoicePage />);

      expect(screen.getByRole('button', { name: /mute/i })).toBeInTheDocument();
    });

    it('should call toggleMicrophone when mute button is clicked', async () => {
      const mockToggleMicrophone = vi.fn();
      const mockRoom = {
        localParticipant: {
          isMicrophoneEnabled: true,
        },
      };
      
      const mockUseVoiceSession = {
        room: mockRoom as any,
        isConnected: true,
        transcription: [],
        sessionStatus: { connected: true, participantCount: 2, duration: 30 },
        latency: 50,
        error: null,
        roomName: 'test-room',
        isStarting: false,
        startSession: vi.fn(),
        endSession: vi.fn(),
        toggleMicrophone: mockToggleMicrophone,
      };

      vi.mocked(useVoiceSessionModule.useVoiceSession).mockReturnValue(mockUseVoiceSession);

      const user = userEvent.setup();
      render(<VoicePage />);

      const muteButton = screen.getByRole('button', { name: /mute/i });
      await user.click(muteButton);

      expect(mockToggleMicrophone).toHaveBeenCalledTimes(1);
    });

    it('should show unmute button when microphone is muted', () => {
      const mockRoom = {
        localParticipant: {
          isMicrophoneEnabled: false,
        },
      };
      
      const mockUseVoiceSession = {
        room: mockRoom as any,
        isConnected: true,
        transcription: [],
        sessionStatus: { connected: true, participantCount: 2, duration: 30 },
        latency: 50,
        error: null,
        roomName: 'test-room',
        isStarting: false,
        startSession: vi.fn(),
        endSession: vi.fn(),
        toggleMicrophone: vi.fn(),
      };

      vi.mocked(useVoiceSessionModule.useVoiceSession).mockReturnValue(mockUseVoiceSession);

      render(<VoicePage />);

      expect(screen.getByRole('button', { name: /unmute/i })).toBeInTheDocument();
    });
  });
});
