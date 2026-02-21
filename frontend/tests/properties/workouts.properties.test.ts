import { describe, it, expect, beforeEach, vi } from 'vitest';
import fc from 'fast-check';
import { workoutService } from '../../src/services/workoutService';
import api from '../../src/services/api';
import type { WorkoutLog } from '../../src/types';

// Mock the API module
vi.mock('../../src/services/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

describe('Workout Properties', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('Property 13: Workout set logging persists', async () => {
    // Feature: minimal-frontend-testing, Property 13: Workout set logging persists
    // For any exercise set with reps and weight data, logging the set should result
    // in an API call with the correct exercise ID, set number, reps, and weight.
    // Validates: Requirements 2.6.3

    await fc.assert(
      fc.asyncProperty(
        fc.uuid(), // Random session ID
        fc.uuid(), // Random exercise ID
        fc.integer({ min: 1, max: 10 }), // Random set number (1-10)
        fc.integer({ min: 1, max: 50 }), // Random reps (1-50)
        fc.option(fc.float({ min: 0, max: 500 }), { nil: undefined }), // Optional weight (0-500 lbs)
        async (sessionId, exerciseId, setNumber, reps, weight) => {
          // Clear mocks for this iteration
          vi.clearAllMocks();

          // Create workout log data
          const workoutLog: WorkoutLog = {
            sessionId,
            exerciseId,
            setNumber,
            reps,
            weight,
          };

          // Mock API response (successful log)
          vi.mocked(api.post).mockResolvedValueOnce({ data: {} });

          // Call the service to log the set
          await workoutService.logSet(workoutLog);

          // Verify API was called exactly once
          expect(api.post).toHaveBeenCalledTimes(1);

          // Verify API was called with correct endpoint and data
          expect(api.post).toHaveBeenCalledWith('/workouts/log', workoutLog);

          // Get the actual call arguments
          const callArgs = vi.mocked(api.post).mock.calls[0];
          expect(callArgs[0]).toBe('/workouts/log');
          
          const loggedData = callArgs[1] as WorkoutLog;

          // Verify all required fields are present and match input
          expect(loggedData).toEqual(workoutLog);

          // Verify data types
          expect(typeof loggedData.sessionId).toBe('string');
          expect(typeof loggedData.exerciseId).toBe('string');
          expect(typeof loggedData.setNumber).toBe('number');
          expect(typeof loggedData.reps).toBe('number');
          
          // Verify valid ranges
          expect(loggedData.setNumber).toBeGreaterThan(0);
          expect(loggedData.reps).toBeGreaterThan(0);
          
          if (weight !== undefined) {
            expect(typeof loggedData.weight).toBe('number');
            expect(loggedData.weight).toBeGreaterThanOrEqual(0);
          } else {
            expect(loggedData.weight).toBeUndefined();
          }
        }
      ),
      { numRuns: 100 }
    );
  });
});
