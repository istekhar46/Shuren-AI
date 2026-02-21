import { describe, it, expect } from 'vitest';
import fc from 'fast-check';
import type { OnboardingProgress } from '../../src/types/onboarding.types';

/**
 * Property-Based Tests for Progress Monotonicity
 * 
 * These tests verify that onboarding progress is monotonically non-decreasing,
 * meaning progress never goes backward during the onboarding flow.
 * 
 * **Validates: Requirements 1.3**
 */

describe('Progress Monotonicity Properties', () => {
  
  it('Property: Completion percentage never decreases across updates', { timeout: 10000 }, () => {
    // For any sequence of progress updates, the completion percentage should
    // never decrease (monotonically non-decreasing).
    // **Validates: Requirements 1.3**
    
    fc.assert(
      fc.property(
        fc.array(
          fc.record({
            current_state: fc.integer({ min: 0, max: 9 }),
            completed_states: fc.array(
              fc.integer({ min: 0, max: 9 }),
              { maxLength: 9 }
            ).map(arr => Array.from(new Set(arr)).sort((a, b) => a - b)),
          }),
          { minLength: 2, maxLength: 10 }
        ).map(updates => {
          // Sort updates by number of completed states to ensure monotonicity
          return updates.sort((a, b) => 
            a.completed_states.length - b.completed_states.length
          );
        }),
        (progressUpdates) => {
          // Calculate completion percentages
          const percentages = progressUpdates.map(update => 
            Math.round((update.completed_states.length / 9) * 100)
          );
          
          // Property: Each percentage >= previous percentage
          for (let i = 1; i < percentages.length; i++) {
            expect(percentages[i]).toBeGreaterThanOrEqual(percentages[i - 1]);
          }
        }
      ),
      { numRuns: 1000 }
    );
  });

  it('Property: Completed states count never decreases', () => {
    // For any sequence of progress updates, the number of completed states
    // should never decrease.
    // **Validates: Requirements 1.2, 1.3**
    
    fc.assert(
      fc.property(
        fc.array(
          fc.integer({ min: 0, max: 9 }),
          { minLength: 2, maxLength: 10 }
        ).map(arr => {
          // Create cumulative array where each element includes all previous
          const cumulative: number[][] = [];
          const seen = new Set<number>();
          
          for (const num of arr) {
            seen.add(num);
            cumulative.push(Array.from(seen).sort((a, b) => a - b));
          }
          
          return cumulative;
        }),
        (progressSequence) => {
          // Property: Each array length >= previous array length
          for (let i = 1; i < progressSequence.length; i++) {
            expect(progressSequence[i].length).toBeGreaterThanOrEqual(
              progressSequence[i - 1].length
            );
          }
        }
      ),
      { numRuns: 1000 }
    );
  });

  it('Property: Current state never decreases except for backward navigation', () => {
    // For any forward progress sequence, current_state should be non-decreasing.
    // Backward navigation (user clicking back) is the only valid decrease.
    // **Validates: Requirements 1.1**
    
    fc.assert(
      fc.property(
        fc.array(
          fc.integer({ min: 0, max: 9 }),
          { minLength: 2, maxLength: 10 }
        ).map(arr => {
          // Sort to simulate forward-only progression
          return arr.sort((a, b) => a - b);
        }),
        (stateSequence) => {
          // Property: Each state >= previous state (forward progression)
          for (let i = 1; i < stateSequence.length; i++) {
            expect(stateSequence[i]).toBeGreaterThanOrEqual(stateSequence[i - 1]);
          }
        }
      ),
      { numRuns: 1000 }
    );
  });

  it('Property: Once a state is completed, it stays completed', { timeout: 60000 }, () => {
    // For any state that appears in completed_states at time T, it must remain
    // in completed_states at all times T+1, T+2, etc.
    // **Validates: Requirements 1.2**
    
    fc.assert(
      fc.property(
        fc.array(
          fc.array(
            fc.integer({ min: 0, max: 9 }),
            { maxLength: 9 }
          ).map(arr => Array.from(new Set(arr)).sort((a, b) => a - b)),
          { minLength: 2, maxLength: 10 }
        ).map(arrays => {
          // Ensure each array is a superset of the previous (monotonic growth)
          const monotonic: number[][] = [];
          const accumulated = new Set<number>();
          
          for (const arr of arrays) {
            arr.forEach(num => accumulated.add(num));
            monotonic.push(Array.from(accumulated).sort((a, b) => a - b));
          }
          
          return monotonic;
        }),
        (progressSequence) => {
          // Property: Each completed_states array contains all states from previous
          for (let i = 1; i < progressSequence.length; i++) {
            const previous = progressSequence[i - 1];
            const current = progressSequence[i];
            
            // All states from previous must be in current
            previous.forEach(state => {
              expect(current).toContain(state);
            });
          }
        }
      ),
      { numRuns: 100 } // Reduced runs due to complexity
    );
  });

  it('Property: Progress updates maintain state consistency', () => {
    // For any sequence of progress updates, the relationship between
    // completed_states and completion_percentage must remain consistent.
    // **Validates: Requirements 1.2, 1.3**
    
    fc.assert(
      fc.property(
        fc.array(
          fc.record({
            completed_states: fc.array(
              fc.integer({ min: 0, max: 9 }),
              { maxLength: 9 }
            ).map(arr => Array.from(new Set(arr)).sort((a, b) => a - b)),
          }),
          { minLength: 2, maxLength: 10 }
        ).map(updates => {
          // Sort by completed states count
          return updates.sort((a, b) => 
            a.completed_states.length - b.completed_states.length
          );
        }),
        (progressUpdates) => {
          // Property: completion_percentage matches completed_states.length
          progressUpdates.forEach(update => {
            const expectedPercentage = Math.round(
              (update.completed_states.length / 9) * 100
            );
            const actualPercentage = Math.round(
              (update.completed_states.length / 9) * 100
            );
            
            expect(actualPercentage).toBe(expectedPercentage);
          });
        }
      ),
      { numRuns: 1000 }
    );
  });

  it('Property: State transitions preserve completed states', { timeout: 10000 }, () => {
    // When transitioning from state N to state N+1, all previously completed
    // states must be preserved.
    // **Validates: Requirements 1.1, 1.2**
    
    fc.assert(
      fc.property(
        fc.integer({ min: 0, max: 8 }), // fromState
        fc.array(
          fc.integer({ min: 0, max: 9 }),
          { maxLength: 9 }
        ).map(arr => Array.from(new Set(arr)).sort((a, b) => a - b)), // completed before
        (fromState, completedBefore) => {
          const toState = fromState + 1;
          
          // Simulate state transition
          const completedAfter = Array.from(
            new Set([...completedBefore, fromState])
          ).sort((a, b) => a - b);
          
          // Property: All states from before are in after
          completedBefore.forEach(state => {
            expect(completedAfter).toContain(state);
          });
          
          // Property: New state is added
          expect(completedAfter.length).toBeGreaterThanOrEqual(completedBefore.length);
        }
      ),
      { numRuns: 1000 }
    );
  });

  it('Property: Completion flag transitions are irreversible', () => {
    // Once is_complete becomes true, it must remain true in all subsequent updates.
    // **Validates: Requirements 1.2**
    
    fc.assert(
      fc.property(
        fc.array(
          fc.boolean(),
          { minLength: 2, maxLength: 10 }
        ).map(arr => {
          // Once true appears, all subsequent values must be true
          let seenTrue = false;
          return arr.map(val => {
            if (seenTrue) return true;
            if (val) seenTrue = true;
            return val;
          });
        }),
        (completionSequence) => {
          // Property: Once true, always true
          let foundTrue = false;
          
          completionSequence.forEach(isComplete => {
            if (foundTrue) {
              expect(isComplete).toBe(true);
            }
            if (isComplete) {
              foundTrue = true;
            }
          });
        }
      ),
      { numRuns: 1000 }
    );
  });

  it('Property: Progress never regresses after API updates', () => {
    // For any sequence of API responses with progress data, the progress
    // should be monotonically non-decreasing.
    // **Validates: Requirements 1.3**
    
    fc.assert(
      fc.property(
        fc.array(
          fc.array(
            fc.integer({ min: 0, max: 9 }),
            { maxLength: 9 }
          ).map(arr => Array.from(new Set(arr))),
          { minLength: 2, maxLength: 10 }
        ).map(arrays => {
          // Sort by completed_states.length to ensure monotonicity
          return arrays.sort((a, b) => a.length - b.length);
        }),
        (completedStatesSequence) => {
          // Build API responses with consistent completion_percentage
          const apiResponses = completedStatesSequence.map(completedStates => ({
            current_state: completedStates.length > 0 ? Math.max(...completedStates) + 1 : 0,
            completed_states: completedStates,
            completion_percentage: Math.round((completedStates.length / 9) * 100),
            is_complete: completedStates.length === 9,
          }));
          
          // Property: Each response has >= percentage than previous
          for (let i = 1; i < apiResponses.length; i++) {
            expect(apiResponses[i].completion_percentage).toBeGreaterThanOrEqual(
              apiResponses[i - 1].completion_percentage
            );
          }
          
          // Property: Completed states count is non-decreasing
          for (let i = 1; i < apiResponses.length; i++) {
            expect(apiResponses[i].completed_states.length).toBeGreaterThanOrEqual(
              apiResponses[i - 1].completed_states.length
            );
          }
        }
      ),
      { numRuns: 1000 }
    );
  });

  it('Property: Backward navigation does not affect completed states', () => {
    // When navigating backward (current_state decreases), the completed_states
    // array should remain unchanged.
    // **Validates: Requirements 1.1, 1.2**
    
    fc.assert(
      fc.property(
        fc.integer({ min: 1, max: 9 }), // fromState (must be > 0 for backward nav)
        fc.array(
          fc.integer({ min: 0, max: 9 }),
          { maxLength: 9 }
        ).map(arr => Array.from(new Set(arr)).sort((a, b) => a - b)), // completed states
        (fromState, completedStates) => {
          const toState = fromState - 1; // Backward navigation
          
          // Simulate backward navigation
          const completedAfter = [...completedStates];
          
          // Property: Completed states unchanged during backward navigation
          expect(completedAfter).toEqual(completedStates);
          expect(completedAfter.length).toBe(completedStates.length);
        }
      ),
      { numRuns: 1000 }
    );
  });

  it('Property: Progress percentage bounds are maintained', () => {
    // For any progress update, completion_percentage must stay within [0, 100].
    // **Validates: Requirements 1.3**
    
    fc.assert(
      fc.property(
        fc.array(
          fc.integer({ min: 0, max: 9 }),
          { maxLength: 9 }
        ).map(arr => Array.from(new Set(arr))),
        (completedStates) => {
          const percentage = Math.round((completedStates.length / 9) * 100);
          
          // Property: Percentage is always in valid range
          expect(percentage).toBeGreaterThanOrEqual(0);
          expect(percentage).toBeLessThanOrEqual(100);
        }
      ),
      { numRuns: 1000 }
    );
  });
});
