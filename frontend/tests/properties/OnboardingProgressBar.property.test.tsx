import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import * as fc from 'fast-check';
import { OnboardingProgressBar } from '../../src/components/onboarding/OnboardingProgressBar';
import type { StateMetadata } from '../../src/types/onboarding.types';

// Feature: frontend-onboarding-integration, Property 4: Progress calculation accuracy

describe('OnboardingProgressBar - Property Tests', () => {
  /**
   * Property 4: Progress calculation accuracy
   * 
   * For any onboarding state number n where 1 ≤ n ≤ 9,
   * the displayed progress percentage should equal (n / 9) * 100,
   * and the step indicator should show "Step n of 9".
   * 
   * Validates: Requirements US-2.6, US-4.1
   */
  it('Property 4: Progress calculation accuracy - percentage and step text are correct for any state 1-9', { timeout: 120000 }, () => {
    fc.assert(
      fc.property(
        // Generate random state numbers from 1 to 9
        fc.integer({ min: 1, max: 9 }),
        (currentState) => {
          // Calculate expected percentage
          const expectedPercentage = (currentState / 9) * 100;
          const roundedPercentage = Math.round(expectedPercentage);

          // Create mock state metadata
          const mockStateMetadata: StateMetadata = {
            state_number: currentState,
            name: `State ${currentState}`,
            agent: 'test_agent',
            description: `Description for state ${currentState}`,
            required_fields: [],
          };

          // Generate completed states (all states before current)
          const completedStates = Array.from(
            { length: currentState - 1 },
            (_, i) => i + 1
          );

          // Render component
          const { unmount } = render(
            <OnboardingProgressBar
              currentState={currentState}
              totalStates={9}
              completionPercentage={expectedPercentage}
              stateMetadata={mockStateMetadata}
              completedStates={completedStates}
            />
          );

          // Assert: Step text shows "Step n of 9"
          const stepText = screen.getByText(`Progress: Step ${currentState} of 9`);
          expect(stepText).toBeInTheDocument();

          // Assert: Percentage is displayed correctly (rounded)
          const percentageText = screen.getByText(`${roundedPercentage}%`);
          expect(percentageText).toBeInTheDocument();

          // Assert: Progress bar has correct aria-valuenow
          const progressBar = screen.getByRole('progressbar');
          expect(progressBar).toHaveAttribute('aria-valuenow', String(roundedPercentage));

          // Assert: Progress bar width matches percentage
          const progressBarFill = progressBar.querySelector('div');
          expect(progressBarFill).toHaveStyle({ width: `${expectedPercentage}%` });

          // Clean up
          unmount();
        }
      ),
      { numRuns: 100 } // Run 100 iterations as specified in design
    );
  });

  /**
   * Additional property test: Verify percentage calculation formula
   * 
   * This test explicitly verifies the mathematical relationship:
   * percentage = (currentState / totalStates) * 100
   */
  it('Property 4 (extended): Percentage calculation follows formula (n/9)*100', () => {
    fc.assert(
      fc.property(
        fc.integer({ min: 1, max: 9 }),
        (currentState) => {
          const totalStates = 9;
          const calculatedPercentage = (currentState / totalStates) * 100;

          // Verify the formula produces expected values
          expect(calculatedPercentage).toBeGreaterThanOrEqual(11.11); // State 1
          expect(calculatedPercentage).toBeLessThanOrEqual(100); // State 9

          // Verify specific known values
          if (currentState === 1) {
            expect(Math.round(calculatedPercentage)).toBe(11);
          }
          if (currentState === 5) {
            expect(Math.round(calculatedPercentage)).toBe(56);
          }
          if (currentState === 9) {
            expect(Math.round(calculatedPercentage)).toBe(100);
          }

          // Verify percentage increases monotonically
          const nextPercentage = ((currentState + 1) / totalStates) * 100;
          if (currentState < 9) {
            expect(nextPercentage).toBeGreaterThan(calculatedPercentage);
          }
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property test: Step indicator consistency
   * 
   * Verifies that the step indicator always shows the correct format
   * and matches the current state value.
   */
  it('Property 4 (step indicator): Step text format is consistent for all states', { timeout: 120000 }, () => {
    fc.assert(
      fc.property(
        fc.integer({ min: 1, max: 9 }),
        (currentState) => {
          const mockStateMetadata: StateMetadata = {
            state_number: currentState,
            name: `State ${currentState}`,
            agent: 'test_agent',
            description: `Description for state ${currentState}`,
            required_fields: [],
          };

          const completedStates = Array.from(
            { length: currentState - 1 },
            (_, i) => i + 1
          );

          const { unmount } = render(
            <OnboardingProgressBar
              currentState={currentState}
              totalStates={9}
              completionPercentage={(currentState / 9) * 100}
              stateMetadata={mockStateMetadata}
              completedStates={completedStates}
            />
          );

          // Verify step text format
          const stepText = screen.getByText(/Progress: Step \d+ of 9/);
          expect(stepText).toBeInTheDocument();
          expect(stepText.textContent).toBe(`Progress: Step ${currentState} of 9`);

          // Verify the numbers in the text match the props
          expect(stepText.textContent).toContain(String(currentState));
          expect(stepText.textContent).toContain('9');

          unmount();
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property 6: State list rendering
   * 
   * For any onboarding progress state, the state list should display:
   * - Completed states (state number < current state) with checkmarks
   * - Current state highlighted with a distinct style
   * - Upcoming states (state number > current state) grayed out
   * 
   * Validates: Requirements US-4.2, US-4.3, US-4.4, US-4.5
   */
  it('Property 6: State list rendering - completed, current, and upcoming states are styled correctly', { timeout: 120000 }, () => {
    fc.assert(
      fc.property(
        // Generate random current state from 1 to 9
        fc.integer({ min: 1, max: 9 }),
        (currentState) => {
          // Calculate completed states (all states before current)
          const completedStates = Array.from(
            { length: currentState - 1 },
            (_, i) => i + 1
          );

          const mockStateMetadata: StateMetadata = {
            state_number: currentState,
            name: `State ${currentState}`,
            agent: 'test_agent',
            description: `Description for state ${currentState}`,
            required_fields: [],
          };

          const { unmount } = render(
            <OnboardingProgressBar
              currentState={currentState}
              totalStates={9}
              completionPercentage={(currentState / 9) * 100}
              stateMetadata={mockStateMetadata}
              completedStates={completedStates}
            />
          );

          // Property 1: Completed states have checkmarks
          const completedLabels = screen.queryAllByLabelText('Completed');
          expect(completedLabels).toHaveLength(currentState - 1);

          // Property 2: Current state is highlighted
          const currentLabel = screen.getByLabelText('Current step');
          expect(currentLabel).toBeInTheDocument();

          // Verify current state has the correct styling (blue background)
          const currentStateElement = currentLabel.closest('.bg-blue-600');
          expect(currentStateElement).toBeInTheDocument();

          // Property 3: Upcoming states are grayed out
          const upcomingLabels = screen.queryAllByLabelText('Upcoming step');
          const expectedUpcomingCount = 9 - currentState;
          expect(upcomingLabels).toHaveLength(expectedUpcomingCount);

          // Verify upcoming states have gray styling
          upcomingLabels.forEach((label) => {
            const upcomingElement = label.closest('.bg-gray-300');
            expect(upcomingElement).toBeInTheDocument();
          });

          // Property 4: Total states rendered equals 9
          const allStateElements = screen.getAllByLabelText(/Step \d+:/);
          expect(allStateElements).toHaveLength(9);

          // Property 5: Verify state ordering is correct
          // Completed states should come before current, current before upcoming
          if (currentState > 1) {
            // There should be completed states
            expect(completedLabels.length).toBeGreaterThan(0);
          }
          if (currentState < 9) {
            // There should be upcoming states
            expect(upcomingLabels.length).toBeGreaterThan(0);
          }

          unmount();
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property 6 (extended): Verify checkmark icons for completed states
   * 
   * This test specifically checks that completed states display
   * the checkmark SVG icon correctly.
   */
  it('Property 6 (checkmarks): Completed states display checkmark icons', { timeout: 120000 }, () => {
    fc.assert(
      fc.property(
        fc.integer({ min: 2, max: 9 }), // Start from 2 to ensure at least 1 completed state
        (currentState) => {
          const completedStates = Array.from(
            { length: currentState - 1 },
            (_, i) => i + 1
          );

          const mockStateMetadata: StateMetadata = {
            state_number: currentState,
            name: `State ${currentState}`,
            agent: 'test_agent',
            description: `Description for state ${currentState}`,
            required_fields: [],
          };

          const { unmount } = render(
            <OnboardingProgressBar
              currentState={currentState}
              totalStates={9}
              completionPercentage={(currentState / 9) * 100}
              stateMetadata={mockStateMetadata}
              completedStates={completedStates}
            />
          );

          // Verify completed states have green checkmark styling
          const completedLabels = screen.getAllByLabelText('Completed');
          expect(completedLabels.length).toBe(currentState - 1);

          completedLabels.forEach((label) => {
            // Check for green background
            const greenElement = label.closest('.bg-green-500');
            expect(greenElement).toBeInTheDocument();

            // Check for SVG checkmark path
            const svg = label.querySelector('svg');
            expect(svg).toBeInTheDocument();
            
            const path = svg?.querySelector('path');
            expect(path).toBeInTheDocument();
            expect(path?.getAttribute('d')).toBe('M5 13l4 4L19 7');
          });

          unmount();
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property 6 (styling): Verify distinct styling for each state status
   * 
   * Tests that completed, current, and upcoming states have
   * visually distinct styling classes.
   */
  it('Property 6 (styling): Each state status has distinct visual styling', { timeout: 120000 }, () => {
    fc.assert(
      fc.property(
        fc.integer({ min: 2, max: 8 }), // 2-8 to ensure all three types exist
        (currentState) => {
          const completedStates = Array.from(
            { length: currentState - 1 },
            (_, i) => i + 1
          );

          const mockStateMetadata: StateMetadata = {
            state_number: currentState,
            name: `State ${currentState}`,
            agent: 'test_agent',
            description: `Description for state ${currentState}`,
            required_fields: [],
          };

          const { unmount } = render(
            <OnboardingProgressBar
              currentState={currentState}
              totalStates={9}
              completionPercentage={(currentState / 9) * 100}
              stateMetadata={mockStateMetadata}
              completedStates={completedStates}
            />
          );

          // Get all state containers
          const allStates = screen.getAllByLabelText(/Step \d+:/);

          // Verify completed states have green styling
          const completedStateElements = allStates.filter((_, index) => index < currentState - 1);
          completedStateElements.forEach((element) => {
            expect(element).toHaveClass('bg-green-50');
            expect(element).toHaveClass('border-green-200');
          });

          // Verify current state has blue styling
          const currentStateElement = allStates[currentState - 1];
          expect(currentStateElement).toHaveClass('bg-blue-100');
          expect(currentStateElement).toHaveClass('border-blue-500');

          // Verify upcoming states have gray styling
          const upcomingStateElements = allStates.filter((_, index) => index > currentState - 1);
          upcomingStateElements.forEach((element) => {
            expect(element).toHaveClass('bg-gray-50');
            expect(element).toHaveClass('border-gray-200');
          });

          unmount();
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property 5: State metadata display
   * 
   * For any onboarding state, the state name and description displayed in the UI
   * should match the STATE_METADATA returned from the backend
   * GET /api/v1/onboarding/progress endpoint.
   * 
   * Validates: Requirements US-2.7
   */
  it('Property 5: State metadata display - displayed name and description match backend metadata', { timeout: 120000 }, () => {
    fc.assert(
      fc.property(
        // Generate random state number
        fc.integer({ min: 1, max: 9 }),
        // Generate random state name and description with non-whitespace characters
        fc.string({ minLength: 5, maxLength: 50 }).filter(s => s.trim().length >= 5),
        fc.string({ minLength: 10, maxLength: 100 }).filter(s => s.trim().length >= 10),
        (currentState, stateName, stateDescription) => {
          // Create state metadata with generated values
          const mockStateMetadata: StateMetadata = {
            state_number: currentState,
            name: stateName,
            agent: 'test_agent',
            description: stateDescription,
            required_fields: [],
          };

          const completedStates = Array.from(
            { length: currentState - 1 },
            (_, i) => i + 1
          );

          const { unmount, container } = render(
            <OnboardingProgressBar
              currentState={currentState}
              totalStates={9}
              completionPercentage={(currentState / 9) * 100}
              stateMetadata={mockStateMetadata}
              completedStates={completedStates}
            />
          );

          // Property 1: Displayed state name matches backend metadata
          // Use getByText with exact match function to avoid normalization issues
          const displayedName = screen.getByText((content, element) => {
            return element?.textContent === stateName;
          });
          expect(displayedName).toBeInTheDocument();
          expect(displayedName.textContent).toBe(stateName);

          // Property 2: Displayed description matches backend metadata
          const displayedDescription = screen.getByText((content, element) => {
            return element?.textContent === stateDescription;
          });
          expect(displayedDescription).toBeInTheDocument();
          expect(displayedDescription.textContent).toBe(stateDescription);

          // Property 3: Metadata is displayed in the current state info section
          // Verify the metadata is within the blue info box
          const nameElement = displayedName.closest('.bg-blue-50');
          expect(nameElement).toBeInTheDocument();

          const descriptionElement = displayedDescription.closest('.bg-blue-50');
          expect(descriptionElement).toBeInTheDocument();

          // Property 4: Both name and description are in the same container
          expect(nameElement).toBe(descriptionElement);

          unmount();
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property 5 (null handling): Verify behavior when stateMetadata is null
   * 
   * Tests that the component handles null metadata gracefully
   * without crashing or displaying incorrect information.
   */
  it('Property 5 (null handling): Component handles null stateMetadata gracefully', { timeout: 120000 }, () => {
    fc.assert(
      fc.property(
        fc.integer({ min: 1, max: 9 }),
        (currentState) => {
          const completedStates = Array.from(
            { length: currentState - 1 },
            (_, i) => i + 1
          );

          const { unmount } = render(
            <OnboardingProgressBar
              currentState={currentState}
              totalStates={9}
              completionPercentage={(currentState / 9) * 100}
              stateMetadata={null}
              completedStates={completedStates}
            />
          );

          // Verify component renders without crashing
          const stepText = screen.getByText(`Progress: Step ${currentState} of 9`);
          expect(stepText).toBeInTheDocument();

          // Verify the current state info section is not rendered
          const infoSection = document.querySelector('.bg-blue-50');
          expect(infoSection).not.toBeInTheDocument();

          unmount();
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property 5 (consistency): Verify metadata consistency across re-renders
   * 
   * Tests that when metadata changes, the displayed information
   * updates correctly to match the new metadata.
   */
  it('Property 5 (consistency): Metadata updates are reflected in the UI', { timeout: 120000 }, () => {
    fc.assert(
      fc.property(
        fc.integer({ min: 1, max: 9 }),
        fc.string({ minLength: 5, maxLength: 50 }).filter(s => s.trim().length >= 5),
        fc.string({ minLength: 10, maxLength: 100 }).filter(s => s.trim().length >= 10),
        fc.string({ minLength: 5, maxLength: 50 }).filter(s => s.trim().length >= 5),
        fc.string({ minLength: 10, maxLength: 100 }).filter(s => s.trim().length >= 10),
        (currentState, name1, desc1, name2, desc2) => {
          // Ensure names and descriptions are different
          fc.pre(name1 !== name2 && desc1 !== desc2);

          const metadata1: StateMetadata = {
            state_number: currentState,
            name: name1,
            agent: 'test_agent',
            description: desc1,
            required_fields: [],
          };

          const metadata2: StateMetadata = {
            state_number: currentState,
            name: name2,
            agent: 'test_agent',
            description: desc2,
            required_fields: [],
          };

          const completedStates = Array.from(
            { length: currentState - 1 },
            (_, i) => i + 1
          );

          // Render with first metadata
          const { rerender, unmount } = render(
            <OnboardingProgressBar
              currentState={currentState}
              totalStates={9}
              completionPercentage={(currentState / 9) * 100}
              stateMetadata={metadata1}
              completedStates={completedStates}
            />
          );

          // Verify first metadata is displayed using exact text match
          const displayedName1 = screen.getByText((content, element) => {
            return element?.textContent === name1;
          });
          expect(displayedName1).toBeInTheDocument();
          
          const displayedDesc1 = screen.getByText((content, element) => {
            return element?.textContent === desc1;
          });
          expect(displayedDesc1).toBeInTheDocument();

          // Re-render with second metadata
          rerender(
            <OnboardingProgressBar
              currentState={currentState}
              totalStates={9}
              completionPercentage={(currentState / 9) * 100}
              stateMetadata={metadata2}
              completedStates={completedStates}
            />
          );

          // Verify second metadata is displayed
          const displayedName2 = screen.getByText((content, element) => {
            return element?.textContent === name2;
          });
          expect(displayedName2).toBeInTheDocument();
          
          const displayedDesc2 = screen.getByText((content, element) => {
            return element?.textContent === desc2;
          });
          expect(displayedDesc2).toBeInTheDocument();

          // Verify first metadata is no longer displayed
          const name1Query = screen.queryByText((content, element) => {
            return element?.textContent === name1;
          });
          expect(name1Query).not.toBeInTheDocument();
          
          const desc1Query = screen.queryByText((content, element) => {
            return element?.textContent === desc1;
          });
          expect(desc1Query).not.toBeInTheDocument();

          unmount();
        }
      ),
      { numRuns: 50 } // Fewer runs due to re-render complexity
    );
  });
});
