import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, cleanup } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { OnboardingChatPage } from '../../src/pages/OnboardingChatPage';
import { onboardingService } from '../../src/services/onboardingService';
import type { OnboardingProgress, OnboardingChatResponse } from '../../src/types/onboarding.types';

// Mock the services
vi.mock('../../src/services/onboardingService');

// Mock react-router-dom's useNavigate
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

/**
 * OnboardingChatPage Unit Tests
 * 
 * Simplified test suite focusing on critical functionality.
 * Tests cover core requirements with minimal overhead.
 * 
 * Requirements: US-2.1, US-2.6
 */
describe('OnboardingChatPage Unit Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.resetAllMocks();
    mockNavigate.mockClear();
  });

  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
    vi.resetAllMocks();
  });

  const createMockProgress = (state: number = 1, completedStates: number[] = []): OnboardingProgress => ({
    current_state: state,
    total_states: 9,
    completed_states: completedStates,
    is_complete: false,
    completion_percentage: Math.round((state / 9) * 100 * 100) / 100,
    current_state_info: {
      state_number: state,
      name: state === 1 ? 'Fitness Level Assessment' : 'Primary Fitness Goals',
      agent: 'onboarding',
      description: state === 1 ? 'Tell us about your current fitness level' : 'What are your primary fitness goals?',
      required_fields: state === 1 ? ['fitness_level'] : ['goals'],
    },
  });

  describe('Core functionality', () => {
    it('should fetch progress and display welcome message on first load', async () => {
      const mockProgress = createMockProgress();
      vi.mocked(onboardingService.getOnboardingProgress).mockResolvedValue(mockProgress);

      render(
        <MemoryRouter>
          <OnboardingChatPage />
        </MemoryRouter>
      );

      // Should show loading state initially
      expect(screen.getByText('Loading your onboarding progress...')).toBeInTheDocument();

      // Wait for progress to be fetched and page to load
      await waitFor(() => {
        expect(screen.getByText('Onboarding')).toBeInTheDocument();
      }, { timeout: 5000 });

      // Should display welcome message
      await waitFor(() => {
        expect(screen.getByText(/Welcome to Shuren!/)).toBeInTheDocument();
      }, { timeout: 3000 });

      expect(onboardingService.getOnboardingProgress).toHaveBeenCalledTimes(1);
    }, 30000);

    it('should redirect to dashboard if onboarding is already complete', async () => {
      const completeProgress: OnboardingProgress = {
        current_state: 9,
        total_states: 9,
        completed_states: [1, 2, 3, 4, 5, 6, 7, 8, 9],
        is_complete: true,
        completion_percentage: 100,
        current_state_info: {
          state_number: 9,
          name: 'Supplement Preferences',
          agent: 'onboarding',
          description: 'Final step',
          required_fields: [],
        },
      };

      vi.mocked(onboardingService.getOnboardingProgress).mockResolvedValue(completeProgress);

      render(
        <MemoryRouter>
          <OnboardingChatPage />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/dashboard', { replace: true });
      }, { timeout: 5000 });
    }, 30000);

    it('should handle error when fetching progress fails', async () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      vi.mocked(onboardingService.getOnboardingProgress).mockRejectedValue(
        new Error('Network error')
      );

      render(
        <MemoryRouter>
          <OnboardingChatPage />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/Failed to load onboarding progress/)).toBeInTheDocument();
      }, { timeout: 5000 });

      expect(consoleErrorSpy).toHaveBeenCalledWith(
        'Failed to fetch onboarding progress:',
        expect.any(Error)
      );

      consoleErrorSpy.mockRestore();
    }, 30000);

    it('should not send empty messages', async () => {
      const mockProgress = createMockProgress();
      vi.mocked(onboardingService.getOnboardingProgress).mockResolvedValue(mockProgress);

      render(
        <MemoryRouter>
          <OnboardingChatPage />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Onboarding')).toBeInTheDocument();
      }, { timeout: 5000 });

      const sendButton = screen.getByRole('button', { name: /Send/i });

      // Try to send without typing
      await userEvent.click(sendButton);

      // Should not call sendOnboardingMessage
      expect(onboardingService.sendOnboardingMessage).not.toHaveBeenCalled();
    }, 30000);
  });
});
