import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { render, screen, waitFor, cleanup } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { OnboardingChatPage } from '../../src/pages/OnboardingChatPage';
import { onboardingService } from '../../src/services/onboardingService';
import type { OnboardingProgress } from '../../src/types/onboarding.types';

// Mock the onboarding service
vi.mock('../../src/services/onboardingService');

// Mock useNavigate
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

/**
 * E2E Test: New User Completes Onboarding
 * 
 * This test simulates a complete end-to-end onboarding journey for a new user,
 * progressing through all 9 states, approving plans, and completing onboarding.
 * 
 * **Validates: Requirements US-1, US-2, US-3, US-4, US-5, US-6**
 * **Test ID: 13.17**
 */

describe('E2E: New User Completes Onboarding', () => {
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

  const createMockProgress = (
    state: number,
    completedStates: number[] = [],
    canComplete: boolean = false
  ): OnboardingProgress => ({
    current_state: state,
    total_states: 9,
    completed_states: completedStates,
    is_complete: false,
    can_complete: canComplete,
    completion_percentage: Math.round((completedStates.length / 9) * 100),
    current_state_info: {
      state_number: state,
      name: getStateName(state),
      agent: getAgentType(state),
      description: getStateDescription(state),
      required_fields: [],
    },
    next_state_info: null,
  });

  const getStateName = (state: number): string => {
    const names = [
      'Fitness Level Assessment',
      'Primary Fitness Goals',
      'Workout Preferences & Constraints',
      'Dietary Preferences & Restrictions',
      'Meal Planning Preferences',
      'Workout Schedule & Timing',
      'Lifestyle & Baseline Assessment',
      'Workout Plan Generation & Approval',
      'Meal Plan Generation & Approval',
    ];
    return names[state] || 'Unknown';
  };

  const getAgentType = (state: number): string => {
    if (state <= 2) return 'fitness_assessment';
    if (state <= 4) return 'goal_setting';
    if (state === 5 || state === 7) return 'workout_planning';
    if (state === 6 || state === 8) return 'diet_planning';
    return 'onboarding';
  };

  const getStateDescription = (state: number): string => {
    const descriptions = [
      'Tell us about your current fitness level',
      'What are your primary fitness goals?',
      'What are your workout preferences?',
      'Tell us about your dietary preferences',
      'How many meals per day do you prefer?',
      'When do you prefer to work out?',
      'Tell us about your lifestyle',
      'Review and approve your workout plan',
      'Review and approve your meal plan',
    ];
    return descriptions[state] || 'Unknown';
  };

  it('completes full onboarding journey from state 0 to completion', async () => {
    /**
     * This test simulates a new user going through the complete onboarding process:
     * 1. Starts at state 0 (Fitness Level Assessment)
     * 2. Progresses through all 9 states by answering questions
     * 3. Reviews and approves workout plan at state 7
     * 4. Reviews and approves meal plan at state 8
     * 5. Completes onboarding and redirects to dashboard
     * 
     * **Validates:**
     * - US-1: Agent-based onboarding flow
     * - US-2: Agent context display
     * - US-3: Plan display and approval
     * - US-4: State progression
     * - US-5: Streaming response handling
     * - US-6: Onboarding completion
     */

    // ===== STATE 0: Fitness Level Assessment =====
    const initialProgress = createMockProgress(0, []);
    vi.mocked(onboardingService.getOnboardingProgress).mockResolvedValue(initialProgress);

    render(
      <MemoryRouter>
        <OnboardingChatPage />
      </MemoryRouter>
    );

    // Wait for initial load
    await waitFor(() => {
      expect(screen.getByRole('banner')).not.toBeNull();
    }, { timeout: 5000 });

    // Verify initial state
    const progressElements = screen.getAllByText(/0%/i);
    expect(progressElements.length).toBeGreaterThan(0);
    expect(screen.queryByText(/Complete Onboarding/i)).toBeNull();

    const user = userEvent.setup();
    
    // Wait for input to be available
    const input = await waitFor(() => {
      const element = screen.getByRole('textbox');
      if (!element) throw new Error('Input not found');
      return element;
    }, { timeout: 5000 });

    // State 0 -> State 1
    vi.mocked(onboardingService.streamOnboardingMessage).mockImplementation(
      (_msg, _state, callbacks) => {
        setTimeout(() => {
          callbacks.onChunk('Great! I understand you\'re a beginner. ');
          callbacks.onChunk('Let\'s move on to your fitness goals.');
          callbacks.onComplete({
            done: true,
            state_updated: true,
            progress: {
              current_state: 1,
              total_states: 9,
              completed_states: [0],
              completion_percentage: 11,
              is_complete: false,
              can_complete: false,
            },
          });
        }, 50);
        return () => {};
      }
    );

    vi.mocked(onboardingService.getOnboardingProgress).mockResolvedValue(
      createMockProgress(1, [0])
    );

    await user.type(input, 'I am a beginner');
    await user.keyboard('{Enter}');

    await waitFor(() => {
      expect(screen.getByRole('banner')).not.toBeNull();
    }, { timeout: 5000 });

    await waitFor(() => {
      expect(screen.getByText(/Primary Fitness Goals/i)).not.toBeNull();
    }, { timeout: 5000 });

    expect(screen.getAllByText(/11%/i).length).toBeGreaterThan(0);

    // ===== STATE 1: Primary Fitness Goals =====
    vi.mocked(onboardingService.streamOnboardingMessage).mockImplementation(
      (_msg, _state, callbacks) => {
        setTimeout(() => {
          callbacks.onChunk('Excellent goal! Fat loss is achievable. ');
          callbacks.onChunk('Let\'s discuss your workout preferences.');
          callbacks.onComplete({
            done: true,
            state_updated: true,
            progress: {
              current_state: 2,
              total_states: 9,
              completed_states: [0, 1],
              completion_percentage: 22,
              is_complete: false,
              can_complete: false,
            },
          });
        }, 50);
        return () => {};
      }
    );

    vi.mocked(onboardingService.getOnboardingProgress).mockResolvedValue(
      createMockProgress(2, [0, 1])
    );

    await user.clear(input);
    await user.type(input, 'I want to lose fat');
    await user.keyboard('{Enter}');

    await waitFor(() => {
      expect(screen.getByRole('banner')).not.toBeNull();
    }, { timeout: 5000 });

    await waitFor(() => {
      expect(screen.getByText(/Workout Preferences & Constraints/i)).not.toBeNull();
    }, { timeout: 5000 });

    expect(screen.getAllByText(/22%/i).length).toBeGreaterThan(0);

    // ===== STATE 2: Workout Preferences =====
    vi.mocked(onboardingService.streamOnboardingMessage).mockImplementation(
      (_msg, _state, callbacks) => {
        setTimeout(() => {
          callbacks.onChunk('Perfect! Home workouts with dumbbells. ');
          callbacks.onChunk('Now let\'s talk about your diet.');
          callbacks.onComplete({
            done: true,
            state_updated: true,
            progress: {
              current_state: 3,
              total_states: 9,
              completed_states: [0, 1, 2],
              completion_percentage: 33,
              is_complete: false,
              can_complete: false,
            },
          });
        }, 50);
        return () => {};
      }
    );

    vi.mocked(onboardingService.getOnboardingProgress).mockResolvedValue(
      createMockProgress(3, [0, 1, 2])
    );

    await user.clear(input);
    await user.type(input, 'I prefer home workouts with dumbbells');
    await user.keyboard('{Enter}');

    await waitFor(() => {
      expect(screen.getByRole('banner')).not.toBeNull();
    }, { timeout: 5000 });

    await waitFor(() => {
      expect(screen.getByText(/Dietary Preferences & Restrictions/i)).not.toBeNull();
    }, { timeout: 5000 });

    expect(screen.getAllByText(/33%/i).length).toBeGreaterThan(0);

    // ===== STATE 3: Dietary Preferences =====
    vi.mocked(onboardingService.streamOnboardingMessage).mockImplementation(
      (_msg, _state, callbacks) => {
        setTimeout(() => {
          callbacks.onChunk('Got it! Vegetarian diet with no dairy. ');
          callbacks.onChunk('How many meals do you prefer per day?');
          callbacks.onComplete({
            done: true,
            state_updated: true,
            progress: {
              current_state: 4,
              total_states: 9,
              completed_states: [0, 1, 2, 3],
              completion_percentage: 44,
              is_complete: false,
              can_complete: false,
            },
          });
        }, 50);
        return () => {};
      }
    );

    vi.mocked(onboardingService.getOnboardingProgress).mockResolvedValue(
      createMockProgress(4, [0, 1, 2, 3])
    );

    await user.clear(input);
    await user.type(input, 'I am vegetarian and lactose intolerant');
    await user.keyboard('{Enter}');

    await waitFor(() => {
      expect(screen.getByRole('banner')).not.toBeNull();
    }, { timeout: 5000 });

    await waitFor(() => {
      expect(screen.getByText(/Meal Planning Preferences/i)).not.toBeNull();
    }, { timeout: 5000 });

    expect(screen.getAllByText(/44%/i).length).toBeGreaterThan(0);

    // ===== STATE 4: Meal Planning Preferences =====
    vi.mocked(onboardingService.streamOnboardingMessage).mockImplementation(
      (_msg, _state, callbacks) => {
        setTimeout(() => {
          callbacks.onChunk('4 meals per day sounds great! ');
          callbacks.onChunk('When do you prefer to work out?');
          callbacks.onComplete({
            done: true,
            state_updated: true,
            progress: {
              current_state: 5,
              total_states: 9,
              completed_states: [0, 1, 2, 3, 4],
              completion_percentage: 56,
              is_complete: false,
              can_complete: false,
            },
          });
        }, 50);
        return () => {};
      }
    );

    vi.mocked(onboardingService.getOnboardingProgress).mockResolvedValue(
      createMockProgress(5, [0, 1, 2, 3, 4])
    );

    await user.clear(input);
    await user.type(input, '4 meals per day');
    await user.keyboard('{Enter}');

    await waitFor(() => {
      expect(screen.getByRole('banner')).not.toBeNull();
    }, { timeout: 5000 });

    await waitFor(() => {
      expect(screen.getByText(/Workout Schedule & Timing/i)).not.toBeNull();
    }, { timeout: 5000 });

    expect(screen.getAllByText(/56%/i).length).toBeGreaterThan(0);

    // ===== STATE 5: Workout Schedule =====
    vi.mocked(onboardingService.streamOnboardingMessage).mockImplementation(
      (_msg, _state, callbacks) => {
        setTimeout(() => {
          callbacks.onChunk('Morning workouts, 3 days per week. Perfect! ');
          callbacks.onChunk('Tell me about your lifestyle.');
          callbacks.onComplete({
            done: true,
            state_updated: true,
            progress: {
              current_state: 6,
              total_states: 9,
              completed_states: [0, 1, 2, 3, 4, 5],
              completion_percentage: 67,
              is_complete: false,
              can_complete: false,
            },
          });
        }, 50);
        return () => {};
      }
    );

    vi.mocked(onboardingService.getOnboardingProgress).mockResolvedValue(
      createMockProgress(6, [0, 1, 2, 3, 4, 5])
    );

    await user.clear(input);
    await user.type(input, 'Morning workouts, 3 days per week');
    await user.keyboard('{Enter}');

    await waitFor(() => {
      expect(screen.getByRole('banner')).not.toBeNull();
    }, { timeout: 5000 });

    await waitFor(() => {
      expect(screen.getByText(/Lifestyle & Baseline Assessment/i)).not.toBeNull();
    }, { timeout: 5000 });

    expect(screen.getAllByText(/67%/i).length).toBeGreaterThan(0);

    // ===== STATE 6: Lifestyle Assessment =====
    vi.mocked(onboardingService.streamOnboardingMessage).mockImplementation(
      (_msg, _state, callbacks) => {
        setTimeout(() => {
          callbacks.onChunk('Thanks for sharing! ');
          callbacks.onChunk('Now I\'ll create your personalized workout plan.');
          callbacks.onComplete({
            done: true,
            state_updated: true,
            progress: {
              current_state: 7,
              total_states: 9,
              completed_states: [0, 1, 2, 3, 4, 5, 6],
              completion_percentage: 78,
              is_complete: false,
              can_complete: false,
            },
          });
        }, 50);
        return () => {};
      }
    );

    vi.mocked(onboardingService.getOnboardingProgress).mockResolvedValue(
      createMockProgress(7, [0, 1, 2, 3, 4, 5, 6])
    );

    await user.clear(input);
    await user.type(input, 'I sleep 7 hours, moderate stress, office job');
    await user.keyboard('{Enter}');

    await waitFor(() => {
      expect(screen.getByRole('banner')).not.toBeNull();
    }, { timeout: 5000 });

    await waitFor(() => {
      expect(screen.getByText(/Workout Plan Generation & Approval/i)).not.toBeNull();
    }, { timeout: 5000 });

    expect(screen.getAllByText(/78%/i).length).toBeGreaterThan(0);

    // ===== STATE 7: Workout Plan Generation =====
    vi.mocked(onboardingService.streamOnboardingMessage).mockImplementation(
      (_msg, _state, callbacks) => {
        setTimeout(() => {
          callbacks.onChunk('Here is your personalized workout plan:\n\n');
          callbacks.onChunk('**3 days per week** at home\n');
          callbacks.onChunk('Duration: 45 minutes per session\n');
          callbacks.onChunk('Equipment: Dumbbells, Resistance bands\n\n');
          callbacks.onChunk('Day 1: Upper Body\n');
          callbacks.onChunk('- Dumbbell Press: 3 sets x 10 reps\n');
          callbacks.onChunk('- Dumbbell Rows: 3 sets x 12 reps\n\n');
          callbacks.onChunk('Does this look good to you?');
          callbacks.onComplete({
            done: true,
            state_updated: false,
            progress: {
              current_state: 7,
              total_states: 9,
              completed_states: [0, 1, 2, 3, 4, 5, 6],
              completion_percentage: 78,
              is_complete: false,
              can_complete: false,
            },
          });
        }, 50);
        return () => {};
      }
    );

    await user.clear(input);
    await user.type(input, 'Generate my workout plan');
    await user.keyboard('{Enter}');

    await waitFor(() => {
      expect(screen.getByText(/3 days per week/i)).not.toBeNull();
    }, { timeout: 5000 });

    expect(screen.getByText(/Dumbbells/i)).not.toBeNull();
    expect(screen.getByText(/Dumbbell Press/i)).not.toBeNull();

    // Approve workout plan
    vi.mocked(onboardingService.streamOnboardingMessage).mockImplementation(
      (_msg, _state, callbacks) => {
        setTimeout(() => {
          callbacks.onChunk('Excellent! Your workout plan is approved. ');
          callbacks.onChunk('Now let\'s create your meal plan.');
          callbacks.onComplete({
            done: true,
            state_updated: true,
            progress: {
              current_state: 8,
              total_states: 9,
              completed_states: [0, 1, 2, 3, 4, 5, 6, 7],
              completion_percentage: 89,
              is_complete: false,
              can_complete: false,
            },
          });
        }, 50);
        return () => {};
      }
    );

    vi.mocked(onboardingService.getOnboardingProgress).mockResolvedValue(
      createMockProgress(8, [0, 1, 2, 3, 4, 5, 6, 7])
    );

    await user.clear(input);
    await user.type(input, 'Yes, looks perfect!');
    await user.keyboard('{Enter}');

    await waitFor(() => {
      expect(screen.getByRole('banner')).not.toBeNull();
    }, { timeout: 5000 });

    await waitFor(() => {
      expect(screen.getByText(/Meal Plan Generation & Approval/i)).not.toBeNull();
    }, { timeout: 5000 });

    expect(screen.getAllByText(/89%/i).length).toBeGreaterThan(0);

    // ===== STATE 8: Meal Plan Generation =====
    vi.mocked(onboardingService.streamOnboardingMessage).mockImplementation(
      (_msg, _state, callbacks) => {
        setTimeout(() => {
          callbacks.onChunk('Here is your personalized meal plan:\n\n');
          callbacks.onChunk('**2000 calories per day**\n');
          callbacks.onChunk('Diet: Vegetarian (Dairy-free)\n');
          callbacks.onChunk('4 meals per day\n\n');
          callbacks.onChunk('Macros:\n');
          callbacks.onChunk('- Protein: 120g\n');
          callbacks.onChunk('- Carbs: 220g\n');
          callbacks.onChunk('- Fats: 65g\n\n');
          callbacks.onChunk('Sample Meal 1 (Breakfast):\n');
          callbacks.onChunk('- Oatmeal with berries and almond butter\n');
          callbacks.onChunk('- Calories: 450, Protein: 15g\n\n');
          callbacks.onChunk('Does this work for you?');
          callbacks.onComplete({
            done: true,
            state_updated: false,
            progress: {
              current_state: 8,
              total_states: 9,
              completed_states: [0, 1, 2, 3, 4, 5, 6, 7],
              completion_percentage: 89,
              is_complete: false,
              can_complete: false,
            },
          });
        }, 50);
        return () => {};
      }
    );

    await user.clear(input);
    await user.type(input, 'Generate my meal plan');
    await user.keyboard('{Enter}');

    await waitFor(() => {
      expect(screen.getByText(/2000 calories per day/i)).not.toBeNull();
    }, { timeout: 5000 });

    expect(screen.getByText(/Vegetarian/i)).not.toBeNull();
    expect(screen.getByText(/4 meals per day/i)).not.toBeNull();
    expect(screen.getByText(/Protein: 120g/i)).not.toBeNull();

    // Approve meal plan
    vi.mocked(onboardingService.streamOnboardingMessage).mockImplementation(
      (_msg, _state, callbacks) => {
        setTimeout(() => {
          callbacks.onChunk('Perfect! Your meal plan is approved. ');
          callbacks.onChunk('You\'ve completed all onboarding steps! ');
          callbacks.onChunk('Click "Complete Onboarding" to get started.');
          callbacks.onComplete({
            done: true,
            state_updated: true,
            progress: {
              current_state: 8,
              total_states: 9,
              completed_states: [0, 1, 2, 3, 4, 5, 6, 7, 8],
              completion_percentage: 100,
              is_complete: false,
              can_complete: true,
            },
          });
        }, 50);
        return () => {};
      }
    );

    vi.mocked(onboardingService.getOnboardingProgress).mockResolvedValue(
      createMockProgress(8, [0, 1, 2, 3, 4, 5, 6, 7, 8], true)
    );

    await user.clear(input);
    await user.type(input, 'Yes, looks great!');
    await user.keyboard('{Enter}');

    await waitFor(() => {
      expect(screen.getAllByText(/100%/i).length).toBeGreaterThan(0);
    }, { timeout: 5000 });

    // Wait for Complete Onboarding button
    await waitFor(() => {
      expect(screen.getByText(/Complete Onboarding/i)).not.toBeNull();
    }, { timeout: 3000 });

    // ===== COMPLETE ONBOARDING =====
    vi.mocked(onboardingService.completeOnboarding).mockResolvedValue({
      profile_id: 'profile-123',
      user_id: 'user-123',
      fitness_level: 'beginner',
      is_locked: true,
      onboarding_complete: true,
      message: 'Onboarding completed successfully',
    });

    const completeButton = screen.getByText(/Complete Onboarding/i);
    await user.click(completeButton);

    // Verify redirect to dashboard
    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/dashboard');
    }, { timeout: 3000 });

    // Verify completion API was called
    expect(onboardingService.completeOnboarding).toHaveBeenCalledTimes(1);
  }, 60000); // 60 second timeout for long E2E test
});