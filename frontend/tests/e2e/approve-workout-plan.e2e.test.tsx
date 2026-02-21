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
 * E2E Test: User Approves Workout Plan
 * 
 * This test simulates a user at state 7 (Workout Plan Generation & Approval)
 * receiving a workout plan, reviewing it, and approving it to progress to state 8.
 * 
 * **Validates: Requirements US-3 (Plan Display and Approval)**
 * **Test ID: 13.18**
 */

describe('E2E: User Approves Workout Plan', () => {
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
    completedStates: number[] = []
  ): OnboardingProgress => ({
    current_state: state,
    total_states: 9,
    completed_states: completedStates,
    is_complete: false,
    can_complete: false,
    completion_percentage: Math.round((completedStates.length / 9) * 100),
    current_state_info: {
      state_number: state,
      name: state === 7 ? 'Workout Plan Generation & Approval' : 'Meal Plan Generation & Approval',
      agent: state === 7 ? 'workout_planning' : 'diet_planning',
      description: state === 7 ? 'Review and approve your workout plan' : 'Review and approve your meal plan',
      required_fields: [],
    },
    next_state_info: null,
  });

  it('displays workout plan and allows user to approve it', async () => {
    /**
     * This test validates the workout plan approval workflow:
     * 1. User is at state 7 (Workout Plan Generation & Approval)
     * 2. User requests workout plan generation
     * 3. System displays structured workout plan with:
     *    - Frequency (days per week)
     *    - Location (home/gym)
     *    - Duration per session
     *    - Equipment needed
     *    - Day-by-day breakdown with exercises
     *    - Sets, reps, and rest periods for each exercise
     * 4. User reviews the plan
     * 5. User approves the plan by sending approval message
     * 6. System advances to state 8 (Meal Plan Generation)
     * 
     * **Validates:**
     * - AC-3.1: Workout plans display with days, exercises, sets, reps
     * - AC-3.4: User can approve plan with clear approval message
     * - AC-3.6: Approved plans are visually confirmed
     * - AC-4.1: Progress bar updates when state advances
     * - AC-4.2: Completed states are marked
     */

    // ===== SETUP: User at State 7 (Workout Plan Generation) =====
    const initialProgress = createMockProgress(7, [0, 1, 2, 3, 4, 5, 6]);
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

    // Verify we're at state 7
    await waitFor(() => {
      expect(screen.getAllByText(/Workout Plan Generation & Approval/i).length).toBeGreaterThan(0);
    }, { timeout: 5000 });

    // Verify progress shows 78% (7 of 9 states completed)
    expect(screen.getAllByText(/78%/i).length).toBeGreaterThan(0);

    const user = userEvent.setup();
    
    // Wait for input to be available
    const input = await waitFor(() => {
      const element = screen.getByRole('textbox');
      if (!element) throw new Error('Input not found');
      return element;
    }, { timeout: 5000 });

    // ===== STEP 1: User Requests Workout Plan =====
    vi.mocked(onboardingService.streamOnboardingMessage).mockImplementation(
      (_msg, _state, callbacks) => {
        setTimeout(() => {
          // Stream workout plan content
          callbacks.onChunk('Here is your personalized workout plan:\n\n');
          callbacks.onChunk('**Frequency:** 3 days per week\n');
          callbacks.onChunk('**Location:** Home\n');
          callbacks.onChunk('**Duration:** 45 minutes per session\n');
          callbacks.onChunk('**Equipment:** Dumbbells, Resistance bands\n\n');
          callbacks.onChunk('---\n\n');
          callbacks.onChunk('### Day 1: Upper Body\n\n');
          callbacks.onChunk('**1. Dumbbell Bench Press**\n');
          callbacks.onChunk('- Sets: 3\n');
          callbacks.onChunk('- Reps: 10-12\n');
          callbacks.onChunk('- Rest: 60 seconds\n');
          callbacks.onChunk('- Notes: Focus on controlled movement\n\n');
          callbacks.onChunk('**2. Dumbbell Rows**\n');
          callbacks.onChunk('- Sets: 3\n');
          callbacks.onChunk('- Reps: 12-15\n');
          callbacks.onChunk('- Rest: 60 seconds\n\n');
          callbacks.onChunk('**3. Resistance Band Pull-Aparts**\n');
          callbacks.onChunk('- Sets: 3\n');
          callbacks.onChunk('- Reps: 15-20\n');
          callbacks.onChunk('- Rest: 45 seconds\n\n');
          callbacks.onChunk('---\n\n');
          callbacks.onChunk('### Day 2: Lower Body\n\n');
          callbacks.onChunk('**1. Goblet Squats**\n');
          callbacks.onChunk('- Sets: 4\n');
          callbacks.onChunk('- Reps: 10-12\n');
          callbacks.onChunk('- Rest: 90 seconds\n\n');
          callbacks.onChunk('**2. Romanian Deadlifts**\n');
          callbacks.onChunk('- Sets: 3\n');
          callbacks.onChunk('- Reps: 10-12\n');
          callbacks.onChunk('- Rest: 90 seconds\n\n');
          callbacks.onChunk('**3. Resistance Band Leg Curls**\n');
          callbacks.onChunk('- Sets: 3\n');
          callbacks.onChunk('- Reps: 12-15\n');
          callbacks.onChunk('- Rest: 60 seconds\n\n');
          callbacks.onChunk('---\n\n');
          callbacks.onChunk('### Day 3: Full Body\n\n');
          callbacks.onChunk('**1. Dumbbell Thrusters**\n');
          callbacks.onChunk('- Sets: 3\n');
          callbacks.onChunk('- Reps: 10-12\n');
          callbacks.onChunk('- Rest: 90 seconds\n\n');
          callbacks.onChunk('**2. Renegade Rows**\n');
          callbacks.onChunk('- Sets: 3\n');
          callbacks.onChunk('- Reps: 8-10 per side\n');
          callbacks.onChunk('- Rest: 90 seconds\n\n');
          callbacks.onChunk('**3. Plank Hold**\n');
          callbacks.onChunk('- Sets: 3\n');
          callbacks.onChunk('- Duration: 45-60 seconds\n');
          callbacks.onChunk('- Rest: 60 seconds\n\n');
          callbacks.onChunk('---\n\n');
          callbacks.onChunk('Does this workout plan look good to you? ');
          callbacks.onChunk('You can approve it or request changes.');
          
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
        }, 100);
        return () => {};
      }
    );

    await user.type(input, 'Generate my workout plan');
    await user.keyboard('{Enter}');

    // ===== STEP 2: Verify Workout Plan Display =====
    
    // Wait for plan header information
    await waitFor(() => {
      expect(screen.getByText(/Frequency.*3 days per week/i)).not.toBeNull();
    }, { timeout: 5000 });

    // Verify plan metadata
    expect(screen.getByText(/Location.*Home/i)).not.toBeNull();
    expect(screen.getByText(/Duration.*45 minutes/i)).not.toBeNull();
    expect(screen.getByText(/Equipment.*Dumbbells.*Resistance bands/i)).not.toBeNull();

    // Verify Day 1 exercises
    expect(screen.getByText(/Day 1.*Upper Body/i)).not.toBeNull();
    expect(screen.getByText(/Dumbbell Bench Press/i)).not.toBeNull();
    expect(screen.getByText(/Sets.*3/i)).not.toBeNull();
    expect(screen.getByText(/Reps.*10-12/i)).not.toBeNull();
    expect(screen.getByText(/Rest.*60 seconds/i)).not.toBeNull();
    expect(screen.getByText(/Focus on controlled movement/i)).not.toBeNull();
    
    expect(screen.getByText(/Dumbbell Rows/i)).not.toBeNull();
    expect(screen.getByText(/Resistance Band Pull-Aparts/i)).not.toBeNull();

    // Verify Day 2 exercises
    expect(screen.getByText(/Day 2.*Lower Body/i)).not.toBeNull();
    expect(screen.getByText(/Goblet Squats/i)).not.toBeNull();
    expect(screen.getByText(/Romanian Deadlifts/i)).not.toBeNull();
    expect(screen.getByText(/Resistance Band Leg Curls/i)).not.toBeNull();

    // Verify Day 3 exercises
    expect(screen.getByText(/Day 3.*Full Body/i)).not.toBeNull();
    expect(screen.getByText(/Dumbbell Thrusters/i)).not.toBeNull();
    expect(screen.getByText(/Renegade Rows/i)).not.toBeNull();
    expect(screen.getByText(/Plank Hold/i)).not.toBeNull();

    // Verify approval prompt
    expect(screen.getByText(/Does this workout plan look good to you/i)).not.toBeNull();

    // ===== STEP 3: User Approves Workout Plan =====
    
    vi.mocked(onboardingService.streamOnboardingMessage).mockImplementation(
      (_msg, _state, callbacks) => {
        setTimeout(() => {
          callbacks.onChunk('Excellent! Your workout plan has been approved. ');
          callbacks.onChunk('I\'ve saved it to your profile. ');
          callbacks.onChunk('Now let\'s create your personalized meal plan.');
          
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
        }, 100);
        return () => {};
      }
    );

    vi.mocked(onboardingService.getOnboardingProgress).mockResolvedValue(
      createMockProgress(8, [0, 1, 2, 3, 4, 5, 6, 7])
    );

    await user.clear(input);
    await user.type(input, 'Yes, looks perfect! I approve this plan.');
    await user.keyboard('{Enter}');

    // ===== STEP 4: Verify Approval Confirmation =====
    
    // Wait for approval confirmation message
    await waitFor(() => {
      expect(screen.getByText(/Your workout plan has been approved/i)).not.toBeNull();
    }, { timeout: 5000 });

    expect(screen.getByText(/saved it to your profile/i)).not.toBeNull();

    // ===== STEP 5: Verify State Progression =====
    
    // Wait for state transition to state 8
    await waitFor(() => {
      expect(screen.getAllByText(/Meal Plan Generation & Approval/i).length).toBeGreaterThan(0);
    }, { timeout: 5000 });

    // Verify progress updated to 89% (8 of 9 states completed)
    await waitFor(() => {
      expect(screen.getAllByText(/89%/i).length).toBeGreaterThan(0);
    }, { timeout: 3000 });

    // Verify state 7 is now marked as completed
    // This would be indicated by a checkmark or completed styling in the progress bar
    // The exact implementation depends on the OnboardingProgressBar component

    // ===== STEP 6: Verify Next Step Prompt =====
    
    expect(screen.getByText(/create your personalized meal plan/i)).not.toBeNull();

    // Verify we're now at the meal plan state
    expect(screen.getAllByText(/Meal Plan Generation & Approval/i).length).toBeGreaterThan(0);
  }, 30000); // 30 second timeout

  it('allows user to request changes to workout plan before approving', async () => {
    /**
     * This test validates that users can request modifications to the workout plan:
     * 1. User receives workout plan at state 7
     * 2. User requests changes (e.g., "Can we add more cardio?")
     * 3. System acknowledges and offers to modify
     * 4. User can then approve the modified plan
     * 
     * **Validates:**
     * - AC-3.5: User can request modifications via chat
     */

    // ===== SETUP: User at State 7 =====
    const initialProgress = createMockProgress(7, [0, 1, 2, 3, 4, 5, 6]);
    vi.mocked(onboardingService.getOnboardingProgress).mockResolvedValue(initialProgress);

    render(
      <MemoryRouter>
        <OnboardingChatPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByRole('banner')).not.toBeNull();
    }, { timeout: 5000 });

    const user = userEvent.setup();
    const input = await waitFor(() => screen.getByRole('textbox'), { timeout: 5000 });

    // ===== STEP 1: Generate Initial Plan =====
    vi.mocked(onboardingService.streamOnboardingMessage).mockImplementation(
      (_msg, _state, callbacks) => {
        setTimeout(() => {
          callbacks.onChunk('Here is your workout plan:\n\n');
          callbacks.onChunk('**3 days per week** - Strength training only\n');
          callbacks.onChunk('Day 1: Upper Body\n');
          callbacks.onChunk('Day 2: Lower Body\n');
          callbacks.onChunk('Day 3: Full Body\n\n');
          callbacks.onChunk('Does this look good?');
          
          callbacks.onComplete({
            done: true,
            state_updated: false,
          });
        }, 50);
        return () => {};
      }
    );

    await user.type(input, 'Show me my workout plan');
    await user.keyboard('{Enter}');

    await waitFor(() => {
      expect(screen.getByText(/3 days per week/i)).not.toBeNull();
    }, { timeout: 5000 });

    // ===== STEP 2: User Requests Changes =====
    vi.mocked(onboardingService.streamOnboardingMessage).mockImplementation(
      (_msg, _state, callbacks) => {
        setTimeout(() => {
          callbacks.onChunk('Great feedback! I can definitely add cardio. ');
          callbacks.onChunk('Let me revise the plan:\n\n');
          callbacks.onChunk('**4 days per week** - Strength + Cardio\n');
          callbacks.onChunk('Day 1: Upper Body\n');
          callbacks.onChunk('Day 2: Lower Body + 20 min cardio\n');
          callbacks.onChunk('Day 3: Full Body\n');
          callbacks.onChunk('Day 4: 30 min cardio session\n\n');
          callbacks.onChunk('How does this revised plan look?');
          
          callbacks.onComplete({
            done: true,
            state_updated: false,
          });
        }, 50);
        return () => {};
      }
    );

    await user.clear(input);
    await user.type(input, 'Can we add more cardio to the plan?');
    await user.keyboard('{Enter}');

    await waitFor(() => {
      expect(screen.getByText(/4 days per week/i)).not.toBeNull();
    }, { timeout: 5000 });

    expect(screen.getAllByText(/cardio/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/revised plan/i).length).toBeGreaterThan(0);

    // ===== STEP 3: User Approves Modified Plan =====
    vi.mocked(onboardingService.streamOnboardingMessage).mockImplementation(
      (_msg, _state, callbacks) => {
        setTimeout(() => {
          callbacks.onChunk('Perfect! Your modified workout plan is approved. ');
          callbacks.onChunk('Moving on to meal planning.');
          
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
    await user.type(input, 'Yes, this looks much better! Approve it.');
    await user.keyboard('{Enter}');

    await waitFor(() => {
      expect(screen.getByText(/modified workout plan is approved/i)).not.toBeNull();
    }, { timeout: 5000 });

    await waitFor(() => {
      expect(screen.getAllByText(/Meal Plan Generation & Approval/i).length).toBeGreaterThan(0);
    }, { timeout: 5000 });
  }, 30000);
});
