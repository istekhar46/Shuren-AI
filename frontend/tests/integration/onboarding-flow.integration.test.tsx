import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from '../../src/contexts/AuthContext';
import OnboardingPage from '../../src/pages/OnboardingPage';
import api from '../../src/services/api';

// Mock the API module
vi.mock('../../src/services/api', () => ({
  default: {
    post: vi.fn(),
    get: vi.fn(),
  },
}));

// Mock useNavigate
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe('Onboarding Flow Integration Test', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockNavigate.mockClear();
    
    // Mock localStorage
    const localStorageMock = {
      getItem: vi.fn((key: string) => {
        if (key === 'auth_token') return 'mock-token';
        if (key === 'auth_user') return JSON.stringify({ id: '1', email: 'test@example.com' });
        return null;
      }),
      setItem: vi.fn(),
      removeItem: vi.fn(),
      clear: vi.fn(),
    };
    Object.defineProperty(window, 'localStorage', { value: localStorageMock });
  });

  it('completes full onboarding flow from step 1 to 12, locks profile, and redirects to dashboard', async () => {
    // Feature: minimal-frontend-testing
    // Test complete onboarding flow from step 1 to 12
    // Verify profile lock and redirect
    // Validates: Requirements 2.2.5
    //
    // NOTE: This is a simplified integration test that verifies the core flow:
    // - All 12 steps can be navigated through
    // - Each step saves data via API
    // - Step 12 locks the profile
    // - User is redirected to dashboard after completion
    //
    // The test uses minimal valid data for each step to focus on the flow mechanics
    // rather than comprehensive data validation (which is covered by unit tests).

    const user = userEvent.setup();

    // Mock initial progress check - user is at step 1
    vi.mocked(api.get).mockResolvedValueOnce({
      data: { currentStep: 1, completed: false },
    });

    // Mock all API responses for all 12 steps upfront
    for (let step = 1; step <= 12; step++) {
      vi.mocked(api.post).mockResolvedValueOnce({
        data: { 
          success: true, 
          message: 'Step saved successfully', 
          nextStep: step < 12 ? step + 1 : undefined,
          ...(step === 12 && { profileLocked: true }),
        },
      });
    }

    // Render the onboarding page
    render(
      <BrowserRouter>
        <AuthProvider>
          <OnboardingPage />
        </AuthProvider>
      </BrowserRouter>
    );

    // Wait for initial load
    await waitFor(() => {
      expect(screen.getByText(/Step 1 of 12/i)).toBeInTheDocument();
    }, { timeout: 10000 });

    // STEP 1: Fitness Level
    const beginnerButton = screen.getByRole('button', { name: /Beginner/i });
    await user.click(beginnerButton);
    await user.click(screen.getByRole('button', { name: /Next/i }));
    
    await waitFor(() => {
      expect(api.post).toHaveBeenNthCalledWith(1, '/onboarding/step', expect.objectContaining({ step: 1 }));
      expect(screen.getByText(/Step 2 of 12/i)).toBeInTheDocument();
    }, { timeout: 10000 });

    // STEP 2: Goals
    const goalSelect = screen.getByRole('combobox');
    await user.selectOptions(goalSelect, 'general_fitness');
    await user.click(screen.getByRole('button', { name: /Add Goal/i }));
    await user.click(screen.getByRole('button', { name: /Next/i }));
    
    await waitFor(() => {
      expect(api.post).toHaveBeenNthCalledWith(2, '/onboarding/step', expect.objectContaining({ step: 2 }));
      expect(screen.getByText(/Step 3 of 12/i)).toBeInTheDocument();
    }, { timeout: 10000 });

    // STEP 3: Physical Constraints (can skip)
    await user.click(screen.getByRole('button', { name: /Next/i }));
    
    await waitFor(() => {
      expect(api.post).toHaveBeenNthCalledWith(3, '/onboarding/step', expect.objectContaining({ step: 3 }));
      expect(screen.getByText(/Step 4 of 12/i)).toBeInTheDocument();
    }, { timeout: 10000 });

    // STEP 4: Dietary Preferences
    const omnivoreButton = screen.getByRole('button', { name: /Omnivore/i });
    await user.click(omnivoreButton);
    await user.click(screen.getByRole('button', { name: /Next/i }));
    
    await waitFor(() => {
      expect(api.post).toHaveBeenNthCalledWith(4, '/onboarding/step', expect.objectContaining({ step: 4 }));
      expect(screen.getByText(/Step 5 of 12/i)).toBeInTheDocument();
    }, { timeout: 10000 });

    // STEPS 5-11: Fill minimal required data and proceed
    // For simplicity, we'll fill required fields where needed
    for (let step = 5; step <= 11; step++) {
      // Step 5 requires calorie input
      if (step === 5) {
        // Get all number inputs on the page
        const numberInputs = screen.getAllByRole('spinbutton');
        // First input is calories, then protein, carbs, fats
        await user.type(numberInputs[0], '2000'); // Daily Calorie Target
        await user.type(numberInputs[1], '150');  // Protein
        await user.type(numberInputs[2], '200');  // Carbs
        await user.type(numberInputs[3], '60');   // Fats
      }

      // Step 6 requires at least one meal time
      if (step === 6) {
        // Get all time inputs using within and container
        const timeInputs = document.querySelectorAll('input[type="time"]');
        if (timeInputs.length > 0) {
          await user.type(timeInputs[0] as HTMLElement, '08:00'); // Breakfast time
        }
      }

      // Step 7 requires selecting at least one preferred day and workout time
      if (step === 7) {
        // Click on Monday, Wednesday, Friday buttons (3 days to match default)
        const mondayButton = screen.getByRole('button', { name: /monday/i });
        await user.click(mondayButton);
        const wednesdayButton = screen.getByRole('button', { name: /wednesday/i });
        await user.click(wednesdayButton);
        const fridayButton = screen.getByRole('button', { name: /friday/i });
        await user.click(fridayButton);
        
        // Fill in preferred workout time
        const timeInputs = document.querySelectorAll('input[type="time"]');
        if (timeInputs.length > 0) {
          await user.type(timeInputs[0] as HTMLElement, '09:00'); // Workout time
        }
      }

      // Step 9 requires selecting energy level, stress level, and sleep quality
      if (step === 9) {
        // Select Medium energy level
        const mediumEnergyButton = screen.getByRole('button', { name: /Medium.*Moderate energy/i });
        await user.click(mediumEnergyButton);
        
        // Select Medium stress level
        const mediumStressButton = screen.getByRole('button', { name: /Medium.*Manageable stress/i });
        await user.click(mediumStressButton);
        
        // Select Good sleep quality
        const goodSleepButton = screen.getByRole('button', { name: /Good.*Generally sleep well/i });
        await user.click(goodSleepButton);
      }

      await user.click(screen.getByRole('button', { name: /Next/i }));
      
      await waitFor(() => {
        expect(api.post).toHaveBeenNthCalledWith(step, '/onboarding/step', expect.objectContaining({ step }));
        if (step < 11) {
          expect(screen.getByText(new RegExp(`Step ${step + 1} of 12`, 'i'))).toBeInTheDocument();
        }
      }, { timeout: 10000 });
    }

    // STEP 12: Confirmation (locks profile)
    await waitFor(() => {
      expect(screen.getByText(/Step 12 of 12/i)).toBeInTheDocument();
      expect(screen.getByText(/Complete Your Profile/i)).toBeInTheDocument();
    }, { timeout: 10000 });

    const confirmCheckbox = screen.getByRole('checkbox');
    await user.click(confirmCheckbox);
    await user.click(screen.getByRole('button', { name: /Complete Onboarding/i }));

    // Verify final API call includes profile lock
    await waitFor(() => {
      expect(api.post).toHaveBeenNthCalledWith(12, '/onboarding/step', {
        step: 12,
        data: expect.objectContaining({ 
          confirmed: true,
          lockProfile: true,
        }),
      });
    }, { timeout: 10000 });

    // Verify redirect to dashboard
    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/dashboard');
    }, { timeout: 10000 });

    // Verify all 12 steps were saved
    expect(api.post).toHaveBeenCalledTimes(12);
  }, 60000); // 60 second timeout for this comprehensive test

  it('handles validation errors during onboarding flow', async () => {
    // Test that validation errors are properly displayed and don't break the flow
    const user = userEvent.setup();

    // Mock initial progress check
    vi.mocked(api.get).mockResolvedValueOnce({
      data: { currentStep: 1, completed: false },
    });

    render(
      <BrowserRouter>
        <AuthProvider>
          <OnboardingPage />
        </AuthProvider>
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Step 1 of 12/i)).toBeInTheDocument();
    });

    // Mock validation error response
    vi.mocked(api.post).mockRejectedValueOnce({
      response: {
        status: 422,
        data: {
          detail: [
            {
              loc: ['body', 'fitnessLevel'],
              msg: 'This field is required',
              type: 'value_error.missing',
            },
          ],
        },
      },
    });

    // Try to proceed without selecting fitness level
    const nextButton = screen.getByRole('button', { name: /Next/i });
    await user.click(nextButton);

    // Verify error is displayed
    await waitFor(() => {
      expect(screen.getByText(/Please select your fitness level/i)).toBeInTheDocument();
    });

    // Verify we're still on step 1
    expect(screen.getByText(/Step 1 of 12/i)).toBeInTheDocument();
  });

  it('allows backward navigation through onboarding steps', async () => {
    // Test that users can navigate back through completed steps
    const user = userEvent.setup();

    // Mock initial progress check - user is at step 3
    vi.mocked(api.get).mockResolvedValueOnce({
      data: { currentStep: 3, completed: false },
    });

    render(
      <BrowserRouter>
        <AuthProvider>
          <OnboardingPage />
        </AuthProvider>
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Step 3 of 12/i)).toBeInTheDocument();
    });

    // Click Back button
    const backButton = screen.getByRole('button', { name: /Back/i });
    await user.click(backButton);

    // Verify we moved to step 2
    await waitFor(() => {
      expect(screen.getByText(/Step 2 of 12/i)).toBeInTheDocument();
    });

    // Click Back again
    await user.click(screen.getByRole('button', { name: /Back/i }));

    // Verify we moved to step 1
    await waitFor(() => {
      expect(screen.getByText(/Step 1 of 12/i)).toBeInTheDocument();
    });
  });

  it('redirects to dashboard if onboarding is already completed', async () => {
    // Test that completed users are redirected
    
    // Mock progress check showing completed onboarding
    vi.mocked(api.get).mockResolvedValueOnce({
      data: { currentStep: 12, completed: true },
    });

    render(
      <BrowserRouter>
        <AuthProvider>
          <OnboardingPage />
        </AuthProvider>
      </BrowserRouter>
    );

    // Verify redirect to dashboard
    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/dashboard');
    });
  });
});
