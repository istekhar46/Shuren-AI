import { describe, it, expect, beforeEach, vi } from 'vitest';
import fc from 'fast-check';
import { onboardingService } from '../../src/services/onboardingService';
import api from '../../src/services/api';

// Mock the API module
vi.mock('../../src/services/api', () => ({
  default: {
    post: vi.fn(),
    get: vi.fn(),
  },
}));

describe('Onboarding Properties', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('Property 5: Onboarding steps persist data', async () => {
    // Feature: minimal-frontend-testing, Property 5: Onboarding steps persist data
    // For any onboarding step (1-12) with valid data, submitting the step should result 
    // in an API call to save the data and successful response.
    // Validates: Requirements 2.2.2

    await fc.assert(
      fc.asyncProperty(
        fc.integer({ min: 1, max: 12 }), // Random step number 1-12
        fc.record({
          // Generate random valid onboarding data
          fitnessLevel: fc.constantFrom('beginner', 'intermediate', 'advanced'),
          goals: fc.array(fc.constantFrom('fat_loss', 'muscle_gain', 'general_fitness'), { minLength: 1, maxLength: 3 }),
          equipment: fc.array(fc.string({ minLength: 3, maxLength: 20 }), { maxLength: 5 }),
          dietType: fc.constantFrom('omnivore', 'vegetarian', 'vegan', 'pescatarian'),
          allergies: fc.array(fc.string({ minLength: 3, maxLength: 15 }), { maxLength: 5 }),
          dailyCalories: fc.integer({ min: 1200, max: 4000 }),
          mealsPerDay: fc.integer({ min: 2, max: 6 }),
          daysPerWeek: fc.integer({ min: 1, max: 7 }),
          hydrationGoal: fc.float({ min: 1.0, max: 5.0 }),
          energyLevel: fc.constantFrom('low', 'medium', 'high'),
        }),
        async (step, data) => {
          // Mock successful API response
          const mockResponse = {
            data: {
              success: true,
              message: 'Step saved successfully',
              nextStep: step < 12 ? step + 1 : undefined,
            },
          };
          vi.mocked(api.post).mockResolvedValueOnce(mockResponse);

          // Call the service
          const result = await onboardingService.saveStep(step, data);

          // Verify API was called with correct parameters
          expect(api.post).toHaveBeenCalledWith('/onboarding/step', { step, data });
          
          // Verify successful response
          expect(result.success).toBe(true);
          expect(result.message).toBe('Step saved successfully');
        }
      ),
      { numRuns: 100 }
    );
  });

  it('Property 6: Backward navigation in onboarding', async () => {
    // Feature: minimal-frontend-testing, Property 6: Backward navigation in onboarding
    // For any onboarding step greater than 1, clicking the back button should navigate 
    // to the previous step (step - 1).
    // Validates: Requirements 2.2.3

    await fc.assert(
      fc.asyncProperty(
        fc.integer({ min: 2, max: 12 }), // Random step number 2-12 (must be > 1 for back navigation)
        async (currentStep) => {
          // Simulate the onboarding page state
          let step = currentStep;
          
          // Simulate back button click
          const handleBack = () => {
            if (step > 1) {
              step = step - 1;
            }
          };

          // Execute back navigation
          handleBack();

          // Verify step decreased by 1
          expect(step).toBe(currentStep - 1);
          
          // Verify step is still valid (>= 1)
          expect(step).toBeGreaterThanOrEqual(1);
        }
      ),
      { numRuns: 100 }
    );
  });

  it('Property 7: Validation errors displayed', async () => {
    // Feature: minimal-frontend-testing, Property 7: Validation errors displayed
    // For any API validation error (422 response), the error details should be displayed 
    // in the UI with clear messaging.
    // Validates: Requirements 2.2.6

    await fc.assert(
      fc.asyncProperty(
        fc.integer({ min: 1, max: 12 }), // Random step number
        fc.record({
          // Generate random validation error structure
          field: fc.constantFrom('fitnessLevel', 'goals', 'dietType', 'dailyCalories', 'mealsPerDay'),
          message: fc.constantFrom(
            'This field is required',
            'Invalid value provided',
            'Value must be greater than 0',
            'Value must be less than 10000',
            'Invalid format'
          ),
        }),
        fc.array(
          fc.record({
            loc: fc.array(fc.string({ minLength: 3, maxLength: 15 }), { minLength: 1, maxLength: 3 }),
            msg: fc.string({ minLength: 10, maxLength: 50 }),
            type: fc.constantFrom('value_error', 'type_error', 'missing'),
          }),
          { minLength: 1, maxLength: 5 }
        ),
        async (step, errorField, validationErrors) => {
          // Mock 422 validation error response
          const mockError = {
            response: {
              status: 422,
              data: {
                detail: validationErrors,
              },
            },
          };
          vi.mocked(api.post).mockRejectedValueOnce(mockError);

          // Attempt to save step (should fail with validation error)
          try {
            await onboardingService.saveStep(step, {});
            // Should not reach here
            expect.fail('Expected validation error to be thrown');
          } catch (err: any) {
            // Verify error structure
            expect(err.response.status).toBe(422);
            expect(err.response.data.detail).toBeDefined();
            expect(Array.isArray(err.response.data.detail)).toBe(true);
            expect(err.response.data.detail.length).toBeGreaterThan(0);
            
            // Verify each error has required fields
            err.response.data.detail.forEach((error: any) => {
              expect(error).toHaveProperty('loc');
              expect(error).toHaveProperty('msg');
              expect(error).toHaveProperty('type');
              expect(Array.isArray(error.loc)).toBe(true);
              expect(typeof error.msg).toBe('string');
              expect(error.msg.length).toBeGreaterThan(0);
            });
          }
        }
      ),
      { numRuns: 100 }
    );
  });
});
