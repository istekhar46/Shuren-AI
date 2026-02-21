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
 * Integration Test: Complete Onboarding Flow (All 9 States)
 * 
 * This test verifies the complete agent-driven onboarding flow through all 9 states.
 * Tests state progression, agent interactions, and completion workflow.
 * 
 * **Validates: Requirements 1.1, 1.2, 1.3, 3.4, 3.5**
 */

describe('Onboarding Agent Flow Integration Test', () => {
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
      agent: 'onboarding',
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


  it('loads initial onboarding state and displays progress', async () => {
    // **Validates: Requirements 1.1, 1.2**
    
    const mockProgress = createMockProgress(0, []);
    vi.mocked(onboardingService.getOnboardingProgress).mockResolvedValue(mockProgress);

    render(
      <MemoryRouter>
        <OnboardingChatPage />
      </MemoryRouter>
    );

    // Wait for loading to complete
    await waitFor(() => {
      const element = screen.queryByText(/0%/i);
      expect(element).not.toBeNull();
    }, { timeout: 5000 });

    // Verify state name is displayed
    expect(screen.getByText(/Fitness Level Assessment/i)).not.toBeNull();
    
    // Verify progress shows 0%
    expect(screen.getByText(/0%/i)).not.toBeNull();
    
    // Verify Complete Onboarding button is NOT present
    expect(screen.queryByText(/Complete Onboarding/i)).not.not.toBeNull();
  });

  it('shows Complete Onboarding button when all states are done', async () => {
    // **Validates: Requirements 1.2, 3.7**
    
    const mockProgress = createMockProgress(8, [0, 1, 2, 3, 4, 5, 6, 7, 8], true);
    vi.mocked(onboardingService.getOnboardingProgress).mockResolvedValue(mockProgress);

    render(
      <MemoryRouter>
        <OnboardingChatPage />
      </MemoryRouter>
    );

    // Wait for page to load
    await waitFor(() => {
      expect(screen.getByText(/100%/i)).not.toBeNull();
    }, { timeout: 5000 });

    // Wait for Complete button to appear
    await waitFor(() => {
      expect(screen.getByText(/Complete Onboarding/i)).not.toBeNull();
    }, { timeout: 3000 });

    // Verify 100% progress
    expect(screen.getByText(/100%/i)).not.toBeNull();
  });

  it('prevents completion before all states are finished', async () => {
    // **Validates: Requirements 1.2, 3.7**
    
    const mockProgress = createMockProgress(5, [0, 1, 2, 3, 4], false);
    vi.mocked(onboardingService.getOnboardingProgress).mockResolvedValue(mockProgress);

    render(
      <MemoryRouter>
        <OnboardingChatPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/56%/i)).not.toBeNull();
    }, { timeout: 5000 });

    // Verify progress shows correct percentage
    expect(screen.getByText(/56%/i)).not.toBeNull();

    // Verify Complete Onboarding button is NOT present
    expect(screen.queryByText(/Complete Onboarding/i)).not.not.toBeNull();
  });

  it('redirects to dashboard if onboarding is already complete', async () => {
    // **Validates: Requirements 1.2**
    
    const completeProgress: OnboardingProgress = {
      current_state: 9,
      total_states: 9,
      completed_states: [0, 1, 2, 3, 4, 5, 6, 7, 8],
      is_complete: true,
      can_complete: true,
      completion_percentage: 100,
      current_state_info: {
        state_number: 9,
        name: 'Complete',
        agent: 'onboarding',
        description: 'Onboarding complete',
        required_fields: [],
      },
      next_state_info: null,
    };

    vi.mocked(onboardingService.getOnboardingProgress).mockResolvedValue(completeProgress);

    render(
      <MemoryRouter>
        <OnboardingChatPage />
      </MemoryRouter>
    );

    // Should redirect to dashboard
    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/dashboard');
    }, { timeout: 5000 });
  });
});


/**
 * Plan Approval Workflow Tests
 * 
 * Tests the complete workflow for approving workout and meal plans
 * during the onboarding process.
 * 
 * **Validates: Requirements 3.5, 3.6**
 */
describe('Plan Approval Workflow', () => {
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

  it('displays workout plan preview when plan is detected', async () => {
    // **Validates: Requirement 3.5 - Plan preview display**
    
    const mockProgress: OnboardingProgress = {
      current_state: 7,
      total_states: 9,
      completed_states: [0, 1, 2, 3, 4, 5, 6],
      is_complete: false,
      can_complete: false,
      completion_percentage: 78,
      current_state_info: {
        state_number: 7,
        name: 'Workout Plan Generation & Approval',
        agent: 'workout_planning',
        description: 'Review and approve your workout plan',
        required_fields: [],
      },
      next_state_info: null,
    };

    vi.mocked(onboardingService.getOnboardingProgress).mockResolvedValue(mockProgress);

    render(
      <MemoryRouter>
        <OnboardingChatPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/78%/i)).not.toBeNull();
    });

    // Mock streaming response with workout plan
    vi.mocked(onboardingService.streamOnboardingMessage).mockImplementation(
      (msg, state, callbacks) => {
        setTimeout(() => {
          callbacks.onChunk('Here is your personalized workout plan:\n\n');
          callbacks.onChunk('**3 days per week** at home\n');
          callbacks.onChunk('Equipment: Dumbbells, Resistance bands\n\n');
          
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

    const user = userEvent.setup();
    const input = screen.getByPlaceholderText(/Type your message/i);
    await user.type(input, 'Generate my workout plan');
    await user.keyboard('{Enter}');

    // Wait for plan content to appear in messages
    await waitFor(() => {
      expect(screen.getByText(/3 days per week/i)).not.toBeNull();
    }, { timeout: 5000 });

    // Verify plan details are displayed
    expect(screen.getByText(/Dumbbells/i)).not.toBeNull();
    expect(screen.getByText(/Resistance bands/i)).not.toBeNull();
  });

  it('approves workout plan and progresses to next state', async () => {
    // **Validates: Requirement 3.5 - Plan approval flow**
    
    const mockProgress: OnboardingProgress = {
      current_state: 7,
      total_states: 9,
      completed_states: [0, 1, 2, 3, 4, 5, 6],
      is_complete: false,
      can_complete: false,
      completion_percentage: 78,
      current_state_info: {
        state_number: 7,
        name: 'Workout Plan Generation & Approval',
        agent: 'workout_planning',
        description: 'Review and approve your workout plan',
        required_fields: [],
      },
      next_state_info: null,
    };

    vi.mocked(onboardingService.getOnboardingProgress).mockResolvedValue(mockProgress);

    render(
      <MemoryRouter>
        <OnboardingChatPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/78%/i)).not.toBeNull();
    });

    // Simulate plan approval by sending approval message
    vi.mocked(onboardingService.streamOnboardingMessage).mockImplementation(
      (msg, state, callbacks) => {
        setTimeout(() => {
          callbacks.onChunk('Great! Your workout plan is approved. ');
          callbacks.onChunk('Moving to meal planning...');
          
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

    // Mock updated progress after approval
    vi.mocked(onboardingService.getOnboardingProgress).mockResolvedValue({
      current_state: 8,
      total_states: 9,
      completed_states: [0, 1, 2, 3, 4, 5, 6, 7],
      is_complete: false,
      can_complete: false,
      completion_percentage: 89,
      current_state_info: {
        state_number: 8,
        name: 'Meal Plan Generation & Approval',
        agent: 'diet_planning',
        description: 'Review and approve your meal plan',
        required_fields: [],
      },
      next_state_info: null,
    });

    const user = userEvent.setup();
    const input = screen.getByPlaceholderText(/Type your message/i);
    await user.type(input, 'Yes, looks perfect!');
    await user.keyboard('{Enter}');

    // Wait for state transition
    await waitFor(() => {
      expect(screen.getByText(/89%/i)).not.toBeNull();
    }, { timeout: 5000 });

    // Verify we moved to meal planning state
    await waitFor(() => {
      expect(screen.getByText(/Meal Plan Generation & Approval/i)).not.toBeNull();
    }, { timeout: 3000 });
  });

  it('displays meal plan preview when plan is detected', async () => {
    // **Validates: Requirement 3.5 - Meal plan preview display**
    
    const mockProgress: OnboardingProgress = {
      current_state: 8,
      total_states: 9,
      completed_states: [0, 1, 2, 3, 4, 5, 6, 7],
      is_complete: false,
      can_complete: false,
      completion_percentage: 89,
      current_state_info: {
        state_number: 8,
        name: 'Meal Plan Generation & Approval',
        agent: 'diet_planning',
        description: 'Review and approve your meal plan',
        required_fields: [],
      },
      next_state_info: null,
    };

    vi.mocked(onboardingService.getOnboardingProgress).mockResolvedValue(mockProgress);

    render(
      <MemoryRouter>
        <OnboardingChatPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/89%/i)).not.toBeNull();
    });

    // Mock streaming response with meal plan
    vi.mocked(onboardingService.streamOnboardingMessage).mockImplementation(
      (msg, state, callbacks) => {
        setTimeout(() => {
          callbacks.onChunk('Here is your personalized meal plan:\n\n');
          callbacks.onChunk('**2200 calories per day**\n');
          callbacks.onChunk('Diet: Vegetarian\n');
          callbacks.onChunk('4 meals per day\n\n');
          
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

    const user = userEvent.setup();
    const input = screen.getByPlaceholderText(/Type your message/i);
    await user.type(input, 'Generate my meal plan');
    await user.keyboard('{Enter}');

    // Wait for meal plan content to appear
    await waitFor(() => {
      expect(screen.getByText(/2200 calories per day/i)).not.toBeNull();
    }, { timeout: 5000 });

    // Verify meal plan details are displayed
    expect(screen.getByText(/Vegetarian/i)).not.toBeNull();
    expect(screen.getByText(/4 meals per day/i)).not.toBeNull();
  });

  it('approves meal plan and enables completion', async () => {
    // **Validates: Requirement 3.5 - Final plan approval enables completion**
    
    const mockProgress: OnboardingProgress = {
      current_state: 8,
      total_states: 9,
      completed_states: [0, 1, 2, 3, 4, 5, 6, 7],
      is_complete: false,
      can_complete: false,
      completion_percentage: 89,
      current_state_info: {
        state_number: 8,
        name: 'Meal Plan Generation & Approval',
        agent: 'diet_planning',
        description: 'Review and approve your meal plan',
        required_fields: [],
      },
      next_state_info: null,
    };

    vi.mocked(onboardingService.getOnboardingProgress).mockResolvedValue(mockProgress);

    render(
      <MemoryRouter>
        <OnboardingChatPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/89%/i)).not.toBeNull();
    });

    // Mock meal plan approval
    vi.mocked(onboardingService.streamOnboardingMessage).mockImplementation(
      (msg, state, callbacks) => {
        setTimeout(() => {
          callbacks.onChunk('Perfect! Your meal plan is approved. ');
          callbacks.onChunk('You\'ve completed onboarding!');
          
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

    // Mock updated progress with can_complete = true
    vi.mocked(onboardingService.getOnboardingProgress).mockResolvedValue({
      current_state: 8,
      total_states: 9,
      completed_states: [0, 1, 2, 3, 4, 5, 6, 7, 8],
      is_complete: false,
      can_complete: true,
      completion_percentage: 100,
      current_state_info: {
        state_number: 8,
        name: 'Meal Plan Generation & Approval',
        agent: 'diet_planning',
        description: 'Review and approve your meal plan',
        required_fields: [],
      },
      next_state_info: null,
    });

    const user = userEvent.setup();
    const input = screen.getByPlaceholderText(/Type your message/i);
    await user.type(input, 'Yes, looks perfect!');
    await user.keyboard('{Enter}');

    // Wait for completion button to appear
    await waitFor(() => {
      expect(screen.getByText(/Complete Onboarding/i)).not.toBeNull();
    }, { timeout: 5000 });

    // Verify 100% progress
    expect(screen.getByText(/100%/i)).not.toBeNull();
  });

  it('completes onboarding and redirects to dashboard', async () => {
    // **Validates: Requirement 3.7 - Onboarding completion flow**
    
    const mockProgress: OnboardingProgress = {
      current_state: 8,
      total_states: 9,
      completed_states: [0, 1, 2, 3, 4, 5, 6, 7, 8],
      is_complete: false,
      can_complete: true,
      completion_percentage: 100,
      current_state_info: {
        state_number: 8,
        name: 'Meal Plan Generation & Approval',
        agent: 'diet_planning',
        description: 'Review and approve your meal plan',
        required_fields: [],
      },
      next_state_info: null,
    };

    vi.mocked(onboardingService.getOnboardingProgress).mockResolvedValue(mockProgress);

    render(
      <MemoryRouter>
        <OnboardingChatPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Complete Onboarding/i)).not.toBeNull();
    }, { timeout: 5000 });

    // Mock completion API call
    vi.mocked(onboardingService.completeOnboarding).mockResolvedValue({
      profile_id: 'profile-123',
      user_id: 'user-123',
      fitness_level: 'beginner',
      is_locked: true,
      onboarding_complete: true,
      message: 'Onboarding completed successfully',
    });

    const user = userEvent.setup();
    const completeButton = screen.getByText(/Complete Onboarding/i);
    await user.click(completeButton);

    // Verify redirect to dashboard
    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/dashboard');
    }, { timeout: 3000 });

    // Verify completion API was called
    expect(onboardingService.completeOnboarding).toHaveBeenCalledTimes(1);
  });
});


/**
 * Plan Modification Workflow Tests
 * 
 * Tests the complete workflow for requesting modifications to workout and meal plans
 * during the onboarding process.
 * 
 * **Validates: Requirements 3.6 - Plan modification flow**
 */
describe('Plan Modification Workflow', () => {
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

  it('requests workout plan modifications and receives updated plan', async () => {
    // **Validates: Requirement 3.6 - User can request modifications via chat**
    
    const mockProgress: OnboardingProgress = {
      current_state: 7,
      total_states: 9,
      completed_states: [0, 1, 2, 3, 4, 5, 6],
      is_complete: false,
      can_complete: false,
      completion_percentage: 78,
      current_state_info: {
        state_number: 7,
        name: 'Workout Plan Generation & Approval',
        agent: 'workout_planning',
        description: 'Review and approve your workout plan',
        required_fields: [],
      },
      next_state_info: null,
    };

    vi.mocked(onboardingService.getOnboardingProgress).mockResolvedValue(mockProgress);

    render(
      <MemoryRouter>
        <OnboardingChatPage />
      </MemoryRouter>
    );

    // Wait for page to load
    const input = await waitFor(() => {
      const element = screen.queryByPlaceholderText(/Type your message/i);
      if (!element) throw new Error('Input not found');
      return element;
    }, { timeout: 5000 });

    // Mock initial workout plan generation
    vi.mocked(onboardingService.streamOnboardingMessage).mockImplementation(
      (_msg, _state, callbacks) => {
        setTimeout(() => {
          callbacks.onChunk('Here is your personalized workout plan:\n\n');
          callbacks.onChunk('**4 days per week** at gym\n');
          callbacks.onChunk('Equipment: Barbell, Dumbbells, Machines\n\n');
          
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

    const user = userEvent.setup();
    
    // Request initial plan
    await user.type(input, 'Generate my workout plan');
    await user.keyboard('{Enter}');

    // Wait for initial plan
    await waitFor(() => {
      expect(screen.getByText(/4 days per week/i)).not.toBeNull();
    }, { timeout: 5000 });

    // Mock modification request and response
    vi.mocked(onboardingService.streamOnboardingMessage).mockImplementation(
      (_msg, _state, callbacks) => {
        setTimeout(() => {
          callbacks.onChunk('I understand you want to reduce the frequency. ');
          callbacks.onChunk('Here is your updated workout plan:\n\n');
          callbacks.onChunk('**3 days per week** at gym\n');
          callbacks.onChunk('Equipment: Barbell, Dumbbells, Machines\n\n');
          callbacks.onChunk('I\'ve adjusted the plan to 3 days per week while maintaining effectiveness.');
          
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

    // Request modification
    await user.clear(input);
    await user.type(input, 'Can we reduce to 3 days per week?');
    await user.keyboard('{Enter}');

    // Wait for modified plan
    await waitFor(() => {
      expect(screen.getByText(/3 days per week/i)).not.toBeNull();
    }, { timeout: 5000 });

    // Verify modification message is in chat
    expect(screen.getByText(/adjusted the plan to 3 days/i)).not.toBeNull();
  });

  it('requests meal plan modifications and receives updated plan', async () => {
    // **Validates: Requirement 3.6 - User can request meal plan changes**
    
    const mockProgress: OnboardingProgress = {
      current_state: 8,
      total_states: 9,
      completed_states: [0, 1, 2, 3, 4, 5, 6, 7],
      is_complete: false,
      can_complete: false,
      completion_percentage: 89,
      current_state_info: {
        state_number: 8,
        name: 'Meal Plan Generation & Approval',
        agent: 'diet_planning',
        description: 'Review and approve your meal plan',
        required_fields: [],
      },
      next_state_info: null,
    };

    vi.mocked(onboardingService.getOnboardingProgress).mockResolvedValue(mockProgress);

    render(
      <MemoryRouter>
        <OnboardingChatPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByRole('banner')).not.toBeNull();
    });

    // Mock initial meal plan generation
    vi.mocked(onboardingService.streamOnboardingMessage).mockImplementation(
      (_msg, _state, callbacks) => {
        setTimeout(() => {
          callbacks.onChunk('Here is your personalized meal plan:\n\n');
          callbacks.onChunk('**2500 calories per day**\n');
          callbacks.onChunk('Diet: Standard\n');
          callbacks.onChunk('3 meals per day\n\n');
          
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

    const user = userEvent.setup();
    const input = screen.getByPlaceholderText(/Type your message/i);
    
    // Request initial plan
    await user.type(input, 'Generate my meal plan');
    await user.keyboard('{Enter}');

    // Wait for initial plan
    await waitFor(() => {
      expect(screen.getByText(/2500 calories per day/i)).not.toBeNull();
    }, { timeout: 5000 });

    // Mock modification request and response
    vi.mocked(onboardingService.streamOnboardingMessage).mockImplementation(
      (_msg, _state, callbacks) => {
        setTimeout(() => {
          callbacks.onChunk('I\'ve updated your meal plan to include more meals:\n\n');
          callbacks.onChunk('**2500 calories per day**\n');
          callbacks.onChunk('Diet: Standard\n');
          callbacks.onChunk('5 meals per day\n\n');
          callbacks.onChunk('This will help distribute your calories more evenly throughout the day.');
          
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

    // Request modification
    await user.clear(input);
    await user.type(input, 'Can we increase to 5 meals per day?');
    await user.keyboard('{Enter}');

    // Wait for modified plan
    await waitFor(() => {
      expect(screen.getByText(/5 meals per day/i)).not.toBeNull();
    }, { timeout: 5000 });

    // Verify modification message is in chat
    expect(screen.getByText(/distribute your calories more evenly/i)).not.toBeNull();
  });

  it('handles multiple modification iterations before approval', async () => {
    // **Validates: Requirement 3.6 - Multiple modification rounds supported**
    
    const mockProgress: OnboardingProgress = {
      current_state: 7,
      total_states: 9,
      completed_states: [0, 1, 2, 3, 4, 5, 6],
      is_complete: false,
      can_complete: false,
      completion_percentage: 78,
      current_state_info: {
        state_number: 7,
        name: 'Workout Plan Generation & Approval',
        agent: 'workout_planning',
        description: 'Review and approve your workout plan',
        required_fields: [],
      },
      next_state_info: null,
    };

    vi.mocked(onboardingService.getOnboardingProgress).mockResolvedValue(mockProgress);

    render(
      <MemoryRouter>
        <OnboardingChatPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByRole('banner')).not.toBeNull();
    });

    const user = userEvent.setup();
    const input = screen.getByPlaceholderText(/Type your message/i);

    // First plan generation
    vi.mocked(onboardingService.streamOnboardingMessage).mockImplementation(
      (_msg, _state, callbacks) => {
        setTimeout(() => {
          callbacks.onChunk('**4 days per week** at gym\n');
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

    await user.type(input, 'Generate my workout plan');
    await user.keyboard('{Enter}');

    await waitFor(() => {
      expect(screen.getByText(/4 days per week/i)).not.toBeNull();
    }, { timeout: 5000 });

    // First modification
    vi.mocked(onboardingService.streamOnboardingMessage).mockImplementation(
      (_msg, _state, callbacks) => {
        setTimeout(() => {
          callbacks.onChunk('**3 days per week** at gym\n');
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
    await user.type(input, 'Reduce to 3 days');
    await user.keyboard('{Enter}');

    await waitFor(() => {
      expect(screen.getByText(/3 days per week/i)).not.toBeNull();
    }, { timeout: 5000 });

    // Second modification
    vi.mocked(onboardingService.streamOnboardingMessage).mockImplementation(
      (_msg, _state, callbacks) => {
        setTimeout(() => {
          callbacks.onChunk('**3 days per week** at home\n');
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
    await user.type(input, 'Change location to home');
    await user.keyboard('{Enter}');

    await waitFor(() => {
      expect(screen.getByText(/at home/i)).not.toBeNull();
    }, { timeout: 5000 });

    // Final approval
    vi.mocked(onboardingService.streamOnboardingMessage).mockImplementation(
      (_msg, _state, callbacks) => {
        setTimeout(() => {
          callbacks.onChunk('Perfect! Your workout plan is approved.');
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

    // Mock updated progress
    vi.mocked(onboardingService.getOnboardingProgress).mockResolvedValue({
      current_state: 8,
      total_states: 9,
      completed_states: [0, 1, 2, 3, 4, 5, 6, 7],
      is_complete: false,
      can_complete: false,
      completion_percentage: 89,
      current_state_info: {
        state_number: 8,
        name: 'Meal Plan Generation & Approval',
        agent: 'diet_planning',
        description: 'Review and approve your meal plan',
        required_fields: [],
      },
      next_state_info: null,
    });

    await user.clear(input);
    await user.type(input, 'Yes, looks perfect!');
    await user.keyboard('{Enter}');

    // Verify state progression by checking for Diet Planning Agent
    await waitFor(() => {
      expect(screen.getByText(/Diet Planning Agent/i)).not.toBeNull();
    }, { timeout: 5000 });
  });

  it('preserves modification feedback in chat history', async () => {
    // **Validates: Requirement 3.6 - Modification requests are preserved in chat**
    
    const mockProgress: OnboardingProgress = {
      current_state: 7,
      total_states: 9,
      completed_states: [0, 1, 2, 3, 4, 5, 6],
      is_complete: false,
      can_complete: false,
      completion_percentage: 78,
      current_state_info: {
        state_number: 7,
        name: 'Workout Plan Generation & Approval',
        agent: 'workout_planning',
        description: 'Review and approve your workout plan',
        required_fields: [],
      },
      next_state_info: null,
    };

    vi.mocked(onboardingService.getOnboardingProgress).mockResolvedValue(mockProgress);

    render(
      <MemoryRouter>
        <OnboardingChatPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByRole('banner')).not.toBeNull();
    });

    const user = userEvent.setup();
    const input = screen.getByPlaceholderText(/Type your message/i);

    // Generate plan
    vi.mocked(onboardingService.streamOnboardingMessage).mockImplementation(
      (_msg, _state, callbacks) => {
        setTimeout(() => {
          callbacks.onChunk('**4 days per week** at gym\n');
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

    await user.type(input, 'Generate my workout plan');
    await user.keyboard('{Enter}');

    await waitFor(() => {
      expect(screen.getByText(/4 days per week/i)).not.toBeNull();
    }, { timeout: 5000 });

    // Request modification
    const modificationFeedback = 'Can we reduce to 3 days and add more rest time?';
    
    vi.mocked(onboardingService.streamOnboardingMessage).mockImplementation(
      (_msg, _state, callbacks) => {
        setTimeout(() => {
          callbacks.onChunk('Updated plan with your feedback.\n');
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
    await user.type(input, modificationFeedback);
    await user.keyboard('{Enter}');

    // Wait for response
    await waitFor(() => {
      expect(screen.getByText(/Updated plan with your feedback/i)).not.toBeNull();
    }, { timeout: 5000 });

    // Verify user's modification request is visible in chat
    expect(screen.getByText(modificationFeedback)).not.toBeNull();
    
    // Verify both original plan and modification are in history
    expect(screen.getByText(/4 days per week/i)).not.toBeNull();
    expect(screen.getByText(/Updated plan with your feedback/i)).not.toBeNull();
  });
});
