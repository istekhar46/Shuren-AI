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
 * E2E Test: User Requests Meal Plan Changes
 * 
 * This test simulates a user at state 8 (Meal Plan Generation & Approval)
 * receiving a meal plan, requesting modifications, and then approving the revised plan.
 * 
 * **Validates: Requirements US-3 (Plan Display and Approval), AC-3.5**
 * **Test ID: 13.19**
 */

describe('E2E: User Requests Meal Plan Changes', () => {
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
      name: 'Meal Plan Generation & Approval',
      agent: 'diet_planning',
      description: 'Review and approve your meal plan',
      required_fields: [],
    },
    next_state_info: null,
  });

  it('allows user to request changes to meal plan and approve revised version', async () => {
    /**
     * This test validates the meal plan modification workflow:
     * 1. User is at state 8 (Meal Plan Generation & Approval)
     * 2. User requests meal plan generation
     * 3. System displays structured meal plan with:
     *    - Daily calorie target
     *    - Diet type and restrictions
     *    - Meal frequency
     *    - Macro breakdown (protein, carbs, fats)
     *    - Sample meals with nutrition info
     * 4. User requests changes (e.g., "Can we increase protein?")
     * 5. System acknowledges and provides revised plan
     * 6. User reviews and approves the modified plan
     * 7. System advances to completion state
     * 
     * **Validates:**
     * - AC-3.2: Meal plans display with calories, macros, sample meals
     * - AC-3.5: User can request modifications via chat
     * - AC-3.6: Approved plans are visually confirmed
     * - AC-4.1: Progress bar updates when state advances
     */

    // ===== SETUP: User at State 8 (Meal Plan Generation) =====
    const initialProgress = createMockProgress(8, [0, 1, 2, 3, 4, 5, 6, 7]);
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

    // Verify we're at state 8
    await waitFor(() => {
      expect(screen.getAllByText(/Meal Plan Generation & Approval/i).length).toBeGreaterThan(0);
    }, { timeout: 5000 });

    // Verify progress shows 89% (8 of 9 states completed)
    expect(screen.getAllByText(/89%/i).length).toBeGreaterThan(0);

    const user = userEvent.setup();
    
    // Wait for input to be available
    const input = await waitFor(() => {
      const element = screen.getByRole('textbox');
      if (!element) throw new Error('Input not found');
      return element;
    }, { timeout: 5000 });

    // ===== STEP 1: User Requests Initial Meal Plan =====
    vi.mocked(onboardingService.streamOnboardingMessage).mockImplementation(
      (_msg, _state, callbacks) => {
        setTimeout(() => {
          // Stream meal plan content
          callbacks.onChunk('Here is your personalized meal plan:\n\n');
          callbacks.onChunk('**Daily Calorie Target:** 2000 calories\n');
          callbacks.onChunk('**Diet Type:** Vegetarian (Dairy-free)\n');
          callbacks.onChunk('**Meal Frequency:** 4 meals per day\n\n');
          callbacks.onChunk('---\n\n');
          callbacks.onChunk('### Macro Breakdown\n\n');
          callbacks.onChunk('- **Protein:** 100g (20% of calories)\n');
          callbacks.onChunk('- **Carbohydrates:** 250g (50% of calories)\n');
          callbacks.onChunk('- **Fats:** 67g (30% of calories)\n\n');
          callbacks.onChunk('---\n\n');
          callbacks.onChunk('### Sample Meals\n\n');
          callbacks.onChunk('**Meal 1: Breakfast (7:00 AM)**\n');
          callbacks.onChunk('- Oatmeal with berries and almond butter\n');
          callbacks.onChunk('- Calories: 450 | Protein: 15g | Carbs: 65g | Fats: 15g\n\n');
          callbacks.onChunk('**Meal 2: Lunch (12:00 PM)**\n');
          callbacks.onChunk('- Quinoa bowl with chickpeas, vegetables, and tahini\n');
          callbacks.onChunk('- Calories: 550 | Protein: 25g | Carbs: 70g | Fats: 18g\n\n');
          callbacks.onChunk('**Meal 3: Snack (3:00 PM)**\n');
          callbacks.onChunk('- Hummus with carrot sticks and whole grain crackers\n');
          callbacks.onChunk('- Calories: 300 | Protein: 12g | Carbs: 40g | Fats: 12g\n\n');
          callbacks.onChunk('**Meal 4: Dinner (7:00 PM)**\n');
          callbacks.onChunk('- Lentil curry with brown rice and steamed broccoli\n');
          callbacks.onChunk('- Calories: 700 | Protein: 48g | Carbs: 75g | Fats: 22g\n\n');
          callbacks.onChunk('---\n\n');
          callbacks.onChunk('Does this meal plan work for you? ');
          callbacks.onChunk('You can approve it or request changes.');
          
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
        }, 100);
        return () => {};
      }
    );

    await user.type(input, 'Generate my meal plan');
    await user.keyboard('{Enter}');

    // ===== STEP 2: Verify Initial Meal Plan Display =====
    
    // Wait for plan header information
    await waitFor(() => {
      expect(screen.getByText(/Daily Calorie Target.*2000 calories/i)).not.toBeNull();
    }, { timeout: 5000 });

    // Verify plan metadata
    expect(screen.getByText(/Diet Type.*Vegetarian.*Dairy-free/i)).not.toBeNull();
    expect(screen.getByText(/Meal Frequency.*4 meals per day/i)).not.toBeNull();

    // Verify macro breakdown
    expect(screen.getByText(/Protein.*100g/i)).not.toBeNull();
    expect(screen.getByText(/Carbohydrates.*250g/i)).not.toBeNull();
    expect(screen.getByText(/Fats.*67g/i)).not.toBeNull();

    // Verify sample meals
    expect(screen.getByText(/Meal 1.*Breakfast/i)).not.toBeNull();
    expect(screen.getByText(/Oatmeal with berries and almond butter/i)).not.toBeNull();
    expect(screen.getByText(/Calories: 450.*Protein: 15g/i)).not.toBeNull();
    
    expect(screen.getByText(/Meal 2.*Lunch/i)).not.toBeNull();
    expect(screen.getByText(/Quinoa bowl with chickpeas/i)).not.toBeNull();
    
    expect(screen.getByText(/Meal 3.*Snack/i)).not.toBeNull();
    expect(screen.getByText(/Hummus with carrot sticks/i)).not.toBeNull();
    
    expect(screen.getByText(/Meal 4.*Dinner/i)).not.toBeNull();
    expect(screen.getByText(/Lentil curry with brown rice/i)).not.toBeNull();

    // Verify approval prompt
    expect(screen.getByText(/Does this meal plan work for you/i)).not.toBeNull();

    // ===== STEP 3: User Requests Changes to Meal Plan =====
    
    vi.mocked(onboardingService.streamOnboardingMessage).mockImplementation(
      (_msg, _state, callbacks) => {
        setTimeout(() => {
          callbacks.onChunk('Great feedback! I can definitely increase the protein. ');
          callbacks.onChunk('Let me revise your meal plan:\n\n');
          callbacks.onChunk('**Daily Calorie Target:** 2000 calories\n');
          callbacks.onChunk('**Diet Type:** Vegetarian (Dairy-free)\n');
          callbacks.onChunk('**Meal Frequency:** 4 meals per day\n\n');
          callbacks.onChunk('---\n\n');
          callbacks.onChunk('### Revised Macro Breakdown\n\n');
          callbacks.onChunk('- **Protein:** 140g (28% of calories) ⬆️ Increased\n');
          callbacks.onChunk('- **Carbohydrates:** 220g (44% of calories)\n');
          callbacks.onChunk('- **Fats:** 62g (28% of calories)\n\n');
          callbacks.onChunk('---\n\n');
          callbacks.onChunk('### Updated Sample Meals\n\n');
          callbacks.onChunk('**Meal 1: Breakfast (7:00 AM)**\n');
          callbacks.onChunk('- Protein smoothie with oat milk, pea protein, banana, and peanut butter\n');
          callbacks.onChunk('- Calories: 500 | Protein: 35g | Carbs: 55g | Fats: 15g\n\n');
          callbacks.onChunk('**Meal 2: Lunch (12:00 PM)**\n');
          callbacks.onChunk('- Tofu stir-fry with quinoa and mixed vegetables\n');
          callbacks.onChunk('- Calories: 550 | Protein: 40g | Carbs: 60g | Fats: 18g\n\n');
          callbacks.onChunk('**Meal 3: Snack (3:00 PM)**\n');
          callbacks.onChunk('- Edamame with whole grain crackers\n');
          callbacks.onChunk('- Calories: 300 | Protein: 20g | Carbs: 35g | Fats: 10g\n\n');
          callbacks.onChunk('**Meal 4: Dinner (7:00 PM)**\n');
          callbacks.onChunk('- Black bean and lentil chili with brown rice\n');
          callbacks.onChunk('- Calories: 650 | Protein: 45g | Carbs: 70g | Fats: 19g\n\n');
          callbacks.onChunk('---\n\n');
          callbacks.onChunk('How does this revised meal plan look? ');
          callbacks.onChunk('The protein is now significantly higher while maintaining your calorie target.');
          
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
        }, 100);
        return () => {};
      }
    );

    await user.clear(input);
    await user.type(input, 'Can we increase the protein? I want more protein in my diet.');
    await user.keyboard('{Enter}');

    // ===== STEP 4: Verify Revised Meal Plan Display =====
    
    // Wait for revised plan
    await waitFor(() => {
      expect(screen.getByText(/revised meal plan/i)).not.toBeNull();
    }, { timeout: 5000 });

    // Verify updated macro breakdown
    await waitFor(() => {
      expect(screen.getByText(/Protein.*140g.*28%.*Increased/i)).not.toBeNull();
    }, { timeout: 3000 });

    expect(screen.getByText(/Carbohydrates.*220g/i)).not.toBeNull();
    expect(screen.getByText(/Fats.*62g/i)).not.toBeNull();

    // Verify updated meals with higher protein
    expect(screen.getByText(/Protein smoothie with oat milk, pea protein/i)).not.toBeNull();
    expect(screen.getByText(/Calories: 500.*Protein: 35g/i)).not.toBeNull();
    
    expect(screen.getByText(/Tofu stir-fry with quinoa/i)).not.toBeNull();
    expect(screen.getByText(/Calories: 550.*Protein: 40g/i)).not.toBeNull();
    
    expect(screen.getByText(/Edamame with whole grain crackers/i)).not.toBeNull();
    expect(screen.getByText(/Calories: 300.*Protein: 20g/i)).not.toBeNull();
    
    expect(screen.getByText(/Black bean and lentil chili/i)).not.toBeNull();
    expect(screen.getByText(/Calories: 650.*Protein: 45g/i)).not.toBeNull();

    // Verify revision acknowledgment
    expect(screen.getByText(/protein is now significantly higher/i)).not.toBeNull();

    // ===== STEP 5: User Approves Revised Meal Plan =====
    
    vi.mocked(onboardingService.streamOnboardingMessage).mockImplementation(
      (_msg, _state, callbacks) => {
        setTimeout(() => {
          callbacks.onChunk('Perfect! Your meal plan has been approved. ');
          callbacks.onChunk('I\'ve saved it to your profile. ');
          callbacks.onChunk('You\'ve now completed all onboarding steps! ');
          callbacks.onChunk('Click "Complete Onboarding" to get started with your personalized fitness journey.');
          
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
        }, 100);
        return () => {};
      }
    );

    vi.mocked(onboardingService.getOnboardingProgress).mockResolvedValue(
      createMockProgress(8, [0, 1, 2, 3, 4, 5, 6, 7, 8], true)
    );

    await user.clear(input);
    await user.type(input, 'Yes, this looks much better! I approve this meal plan.');
    await user.keyboard('{Enter}');

    // ===== STEP 6: Verify Approval Confirmation =====
    
    // Wait for approval confirmation message
    await waitFor(() => {
      expect(screen.getByText(/Your meal plan has been approved/i)).not.toBeNull();
    }, { timeout: 5000 });

    expect(screen.getAllByText(/saved it to your profile/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/completed all onboarding steps/i).length).toBeGreaterThan(0);

    // ===== STEP 7: Verify Completion State =====
    
    // Verify progress updated to 100%
    await waitFor(() => {
      expect(screen.getAllByText(/100%/i).length).toBeGreaterThan(0);
    }, { timeout: 3000 });

    // Verify Complete Onboarding button appears
    await waitFor(() => {
      expect(screen.getAllByText(/Complete Onboarding/i).length).toBeGreaterThan(0);
    }, { timeout: 3000 });

    // Verify can_complete is true (button should be enabled)
    const completeButtons = screen.getAllByText(/Complete Onboarding/i);
    expect(completeButtons.length).toBeGreaterThan(0);
  }, 30000); // 30 second timeout

  it('allows multiple rounds of meal plan modifications', async () => {
    /**
     * This test validates that users can request multiple modifications:
     * 1. User receives initial meal plan
     * 2. User requests first change (e.g., "reduce carbs")
     * 3. User receives revised plan
     * 4. User requests second change (e.g., "add more variety")
     * 5. User receives second revision
     * 6. User approves final version
     * 
     * **Validates:**
     * - AC-3.5: User can request modifications via chat (multiple times)
     * - System handles iterative refinement
     */

    // ===== SETUP: User at State 8 =====
    const initialProgress = createMockProgress(8, [0, 1, 2, 3, 4, 5, 6, 7]);
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
          callbacks.onChunk('Here is your meal plan:\n\n');
          callbacks.onChunk('**2000 calories** | Protein: 100g | Carbs: 250g | Fats: 67g\n');
          callbacks.onChunk('4 meals per day\n\n');
          callbacks.onChunk('Does this work for you?');
          
          callbacks.onComplete({
            done: true,
            state_updated: false,
          });
        }, 50);
        return () => {};
      }
    );

    await user.type(input, 'Show me my meal plan');
    await user.keyboard('{Enter}');

    await waitFor(() => {
      expect(screen.getByText(/2000 calories/i)).not.toBeNull();
    }, { timeout: 5000 });

    // ===== STEP 2: First Modification Request =====
    vi.mocked(onboardingService.streamOnboardingMessage).mockImplementation(
      (_msg, _state, callbacks) => {
        setTimeout(() => {
          callbacks.onChunk('I can reduce the carbs. Here\'s the updated plan:\n\n');
          callbacks.onChunk('**2000 calories** | Protein: 120g | Carbs: 180g | Fats: 89g\n');
          callbacks.onChunk('Lower carb, higher protein and fats\n\n');
          callbacks.onChunk('How does this look?');
          
          callbacks.onComplete({
            done: true,
            state_updated: false,
          });
        }, 50);
        return () => {};
      }
    );

    await user.clear(input);
    await user.type(input, 'Can we reduce the carbs?');
    await user.keyboard('{Enter}');

    await waitFor(() => {
      expect(screen.getByText(/Carbs: 180g/i)).not.toBeNull();
    }, { timeout: 5000 });

    // ===== STEP 3: Second Modification Request =====
    vi.mocked(onboardingService.streamOnboardingMessage).mockImplementation(
      (_msg, _state, callbacks) => {
        setTimeout(() => {
          callbacks.onChunk('Great idea! I\'ve added more variety:\n\n');
          callbacks.onChunk('**2000 calories** | Protein: 120g | Carbs: 180g | Fats: 89g\n');
          callbacks.onChunk('Now includes: Mexican, Asian, Mediterranean, and American cuisines\n');
          callbacks.onChunk('5 different protein sources throughout the week\n\n');
          callbacks.onChunk('Is this better?');
          
          callbacks.onComplete({
            done: true,
            state_updated: false,
          });
        }, 50);
        return () => {};
      }
    );

    await user.clear(input);
    await user.type(input, 'Can we add more variety to the meals?');
    await user.keyboard('{Enter}');

    await waitFor(() => {
      expect(screen.getByText(/added more variety/i)).not.toBeNull();
    }, { timeout: 5000 });

    expect(screen.getByText(/Mexican, Asian, Mediterranean/i)).not.toBeNull();
    expect(screen.getByText(/5 different protein sources/i)).not.toBeNull();

    // ===== STEP 4: Approve Final Version =====
    vi.mocked(onboardingService.streamOnboardingMessage).mockImplementation(
      (_msg, _state, callbacks) => {
        setTimeout(() => {
          callbacks.onChunk('Excellent! Your meal plan is approved.');
          
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
    await user.type(input, 'Perfect! I approve this plan.');
    await user.keyboard('{Enter}');

    await waitFor(() => {
      expect(screen.getByText(/Your meal plan is approved/i)).not.toBeNull();
    }, { timeout: 5000 });

    await waitFor(() => {
      expect(screen.getAllByText(/100%/i).length).toBeGreaterThan(0);
    }, { timeout: 3000 });
  }, 30000);
});
