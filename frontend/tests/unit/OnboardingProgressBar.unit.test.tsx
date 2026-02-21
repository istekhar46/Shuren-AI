import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { OnboardingProgressBar } from '../../src/components/onboarding/OnboardingProgressBar';
import type { StateMetadata } from '../../src/types/onboarding.types';

describe('OnboardingProgressBar', () => {
  const mockStateMetadata: StateMetadata = {
    state_number: 3,
    name: 'Workout Preferences & Constraints',
    agent: 'workout_planning',
    description: 'Tell us about your workout preferences and any physical constraints',
    required_fields: ['equipment_access', 'physical_constraints'],
  };

  it('renders progress bar with correct percentage', () => {
    render(
      <OnboardingProgressBar
        currentState={3}
        totalStates={9}
        completionPercentage={33.33}
        stateMetadata={mockStateMetadata}
        completedStates={[1, 2]}
      />
    );

    // Check step indicator (text is split across elements, rendered twice for desktop/mobile)
    const progressLabels = screen.getAllByText('Progress');
    expect(progressLabels.length).toBeGreaterThan(0);
    const stepIndicators = screen.getAllByText(/Step 3 of 9/);
    expect(stepIndicators.length).toBeGreaterThan(0);
    
    // Check percentage display (rendered twice for desktop/mobile)
    const percentages = screen.getAllByText('33%');
    expect(percentages.length).toBeGreaterThan(0);
  });

  it('displays current state name and description', () => {
    render(
      <OnboardingProgressBar
        currentState={3}
        totalStates={9}
        completionPercentage={33.33}
        stateMetadata={mockStateMetadata}
        completedStates={[1, 2]}
      />
    );

    // State name and description rendered twice for desktop/mobile
    const stateNames = screen.getAllByText('Workout Preferences & Constraints');
    expect(stateNames.length).toBeGreaterThan(0);
    const descriptions = screen.getAllByText('Tell us about your workout preferences and any physical constraints');
    expect(descriptions.length).toBeGreaterThan(0);
  });

  it('shows checkmarks for completed states', () => {
    render(
      <OnboardingProgressBar
        currentState={3}
        totalStates={9}
        completionPercentage={33.33}
        stateMetadata={mockStateMetadata}
        completedStates={[1, 2]}
      />
    );

    // Check for completed state labels (rendered twice for desktop/mobile)
    const completedLabels = screen.getAllByLabelText(/Completed/);
    expect(completedLabels.length).toBeGreaterThanOrEqual(2);
  });

  it('highlights current state', () => {
    render(
      <OnboardingProgressBar
        currentState={3}
        totalStates={9}
        completionPercentage={33.33}
        stateMetadata={mockStateMetadata}
        completedStates={[1, 2]}
      />
    );

    // Check for current state indicator (rendered twice for desktop/mobile)
    const currentLabels = screen.getAllByLabelText(/Current step/);
    expect(currentLabels.length).toBeGreaterThan(0);
  });

  it('shows upcoming states as grayed out', () => {
    render(
      <OnboardingProgressBar
        currentState={3}
        totalStates={9}
        completionPercentage={33.33}
        stateMetadata={mockStateMetadata}
        completedStates={[1, 2]}
      />
    );

    // Check for upcoming state indicators (states 4-9 = 6 upcoming states, rendered twice for desktop/mobile)
    const upcomingLabels = screen.getAllByLabelText(/Upcoming step/);
    expect(upcomingLabels.length).toBeGreaterThanOrEqual(6);
  });

  it('renders all 9 states in the list', () => {
    // Use state 1 metadata to avoid duplicate text in current state info
    const state1Metadata: StateMetadata = {
      state_number: 1,
      name: 'Fitness Level Assessment',
      agent: 'onboarding',
      description: 'Tell us about your current fitness level',
      required_fields: ['fitness_level'],
    };

    render(
      <OnboardingProgressBar
        currentState={1}
        totalStates={9}
        completionPercentage={11.11}
        stateMetadata={state1Metadata}
        completedStates={[]}
      />
    );

    // Check that all state names are present in the list (rendered twice for desktop/mobile)
    expect(screen.getAllByText(/Fitness Level Assessment/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Primary Fitness Goals/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Workout Preferences & Constraints/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Diet Preferences & Restrictions/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Fixed Meal Plan Selection/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Meal Timing Schedule/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Workout Schedule/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Hydration Schedule/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Supplement Preferences/).length).toBeGreaterThan(0);
  });

  it('handles null stateMetadata gracefully', () => {
    render(
      <OnboardingProgressBar
        currentState={1}
        totalStates={9}
        completionPercentage={11.11}
        stateMetadata={null}
        completedStates={[]}
      />
    );

    // Should still render progress bar and state list (rendered twice for desktop/mobile)
    const progressLabels = screen.getAllByText('Progress');
    expect(progressLabels.length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Fitness Level Assessment/).length).toBeGreaterThan(0);
  });

  it('calculates progress percentage correctly for different states', () => {
    const { rerender } = render(
      <OnboardingProgressBar
        currentState={1}
        totalStates={9}
        completionPercentage={11.11}
        stateMetadata={mockStateMetadata}
        completedStates={[]}
      />
    );

    expect(screen.getAllByText('11%').length).toBeGreaterThan(0);

    // Test state 5 (middle)
    rerender(
      <OnboardingProgressBar
        currentState={5}
        totalStates={9}
        completionPercentage={55.56}
        stateMetadata={mockStateMetadata}
        completedStates={[1, 2, 3, 4]}
      />
    );

    expect(screen.getAllByText('56%').length).toBeGreaterThan(0);

    // Test state 9 (complete)
    rerender(
      <OnboardingProgressBar
        currentState={9}
        totalStates={9}
        completionPercentage={100}
        stateMetadata={mockStateMetadata}
        completedStates={[1, 2, 3, 4, 5, 6, 7, 8]}
      />
    );

    expect(screen.getAllByText('100%').length).toBeGreaterThan(0);
  });

  it('has proper ARIA labels for accessibility', () => {
    render(
      <OnboardingProgressBar
        currentState={3}
        totalStates={9}
        completionPercentage={33.33}
        stateMetadata={mockStateMetadata}
        completedStates={[1, 2]}
      />
    );

    // Check progress bar has proper ARIA attributes (rendered twice for desktop/mobile)
    const progressBars = screen.getAllByRole('progressbar');
    expect(progressBars.length).toBeGreaterThanOrEqual(2); // Desktop and mobile versions
    
    // Check first progress bar attributes
    const firstProgressBar = progressBars[0];
    expect(firstProgressBar).toHaveAttribute('aria-valuenow', '33');
    expect(firstProgressBar).toHaveAttribute('aria-valuemin', '0');
    expect(firstProgressBar).toHaveAttribute('aria-valuemax', '100');
    expect(firstProgressBar).toHaveAttribute('aria-label', 'Onboarding progress: 33% complete');
  });
});
