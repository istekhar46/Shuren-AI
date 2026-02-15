import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, cleanup } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import * as fc from 'fast-check';
import { OnboardingChatPage } from '../../src/pages/OnboardingChatPage';
import { onboardingService } from '../../src/services/onboardingService';
import type { OnboardingProgress } from '../../src/types/onboarding.types';

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

// Feature: frontend-onboarding-integration, Property 7: Questions presented for all states

/**
 * OnboardingChatPage - Property Tests
 * 
 * Property-based tests for the OnboardingChatPage component
 * to verify universal correctness properties across all valid inputs.
 */
describe('OnboardingChatPage - Property Tests', () => {
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

  /**
   * Helper function to create mock progress data for any state
   */
  const createMockProgress = (
    state: number,
    completedStates: number[] = []
  ): OnboardingProgress => {
    // State metadata mapping
    const stateMetadata = {
      1: {
        name: 'Fitness Level Assessment',
        description: 'What is your current fitness level? Are you a beginner, intermediate, or advanced?',
        agent: 'onboarding',
      },
      2: {
        name: 'Primary Fitness Goals',
        description: 'What are your primary fitness goals? (e.g., fat loss, muscle gain, general fitness)',
        agent: 'onboarding',
      },
      3: {
        name: 'Workout Preferences & Constraints',
        description: 'Do you have access to a gym, or will you be working out at home? What equipment do you have?',
        agent: 'workout_planning',
      },
      4: {
        name: 'Diet Preferences & Restrictions',
        description: 'Do you follow any specific diet? (e.g., vegetarian, vegan, keto) Do you have any food allergies?',
        agent: 'diet_planning',
      },
      5: {
        name: 'Fixed Meal Plan Selection',
        description: 'How many meals per day do you prefer? What is your daily calorie target?',
        agent: 'diet_planning',
      },
      6: {
        name: 'Meal Timing Schedule',
        description: 'What times do you prefer to eat your meals? (e.g., breakfast at 8am, lunch at 12pm)',
        agent: 'scheduling',
      },
      7: {
        name: 'Workout Schedule',
        description: 'How many days per week can you commit to working out? What times work best for you?',
        agent: 'scheduling',
      },
      8: {
        name: 'Hydration Schedule',
        description: 'How much water do you want to drink daily? When should we remind you?',
        agent: 'scheduling',
      },
      9: {
        name: 'Supplement Preferences',
        description: 'Are you interested in supplement guidance? Do you currently take any supplements?',
        agent: 'supplement_guidance',
      },
    };

    const metadata = stateMetadata[state as keyof typeof stateMetadata] || stateMetadata[1];

    return {
      current_state: state,
      total_states: 9,
      completed_states: completedStates,
      is_complete: false,
      completion_percentage: Math.round((state / 9) * 100 * 100) / 100,
      current_state_info: {
        state_number: state,
        name: metadata.name,
        agent: metadata.agent,
        description: metadata.description,
        required_fields: [],
      },
    };
  };

  /**
   * Property 7: Questions presented for all states
   * 
   * For any onboarding state from 1-9, when the chat interface loads that state,
   * the UI should display question content from the agent (either from initial load
   * or first agent message).
   * 
   * Validates: Requirements US-2.3
   */
  it('Property 7: Questions presented for all states - question content is displayed for any state 1-9', { timeout: 60000 }, async () => {
    await fc.assert(
      fc.asyncProperty(
        // Generate random state numbers from 1 to 9
        fc.integer({ min: 1, max: 9 }),
        async (currentState) => {
          // Calculate completed states (all states before current)
          const completedStates = Array.from(
            { length: currentState - 1 },
            (_, i) => i + 1
          );

          // Create mock progress with default question text
          const mockProgress = createMockProgress(currentState, completedStates);

          // Mock the service to return our progress
          vi.mocked(onboardingService.getOnboardingProgress).mockResolvedValue(mockProgress);

          // Render the component
          const { unmount } = render(
            <MemoryRouter>
              <OnboardingChatPage />
            </MemoryRouter>
          );

          // Wait for the component to load
          await waitFor(
            () => {
              expect(onboardingService.getOnboardingProgress).toHaveBeenCalled();
            },
            { timeout: 3000 }
          );

          // Property: Question content (description) should be displayed in the UI
          const description = mockProgress.current_state_info.description;
          expect(description).toBeTruthy();
          expect(description.length).toBeGreaterThan(0);

          await waitFor(
            () => {
              const bodyText = document.body.textContent || '';
              expect(bodyText).toContain(description);
            },
            { timeout: 3000 }
          );

          // Clean up
          unmount();
          vi.clearAllMocks();
        }
      ),
      { numRuns: 20 } // Reduced for performance
    );
  });
});
