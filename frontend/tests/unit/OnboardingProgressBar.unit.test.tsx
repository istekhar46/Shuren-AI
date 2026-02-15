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

    // Check step indicator
    expect(screen.getByText('Progress: Step 3 of 9')).toBeInTheDocument();
    
    // Check percentage display
    expect(screen.getByText('33%')).toBeInTheDocument();
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

    expect(screen.getByText('Workout Preferences & Constraints')).toBeInTheDocument();
    expect(
      screen.getByText('Tell us about your workout preferences and any physical constraints')
    ).toBeInTheDocument();
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

    // Check for completed state labels
    const completedLabels = screen.getAllByLabelText(/Completed/);
    expect(completedLabels).toHaveLength(2);
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

    // Check for current state indicator
    const currentLabel = screen.getByLabelText(/Current step/);
    expect(currentLabel).toBeInTheDocument();
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

    // Check for upcoming state indicators (states 4-9 = 6 upcoming states)
    const upcomingLabels = screen.getAllByLabelText(/Upcoming step/);
    expect(upcomingLabels).toHaveLength(6);
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

    // Check that all state names are present in the list
    expect(screen.getAllByText(/Fitness Level Assessment/).length).toBeGreaterThan(0);
    expect(screen.getByText(/Primary Fitness Goals/)).toBeInTheDocument();
    expect(screen.getByText(/Workout Preferences & Constraints/)).toBeInTheDocument();
    expect(screen.getByText(/Diet Preferences & Restrictions/)).toBeInTheDocument();
    expect(screen.getByText(/Fixed Meal Plan Selection/)).toBeInTheDocument();
    expect(screen.getByText(/Meal Timing Schedule/)).toBeInTheDocument();
    expect(screen.getByText(/Workout Schedule/)).toBeInTheDocument();
    expect(screen.getByText(/Hydration Schedule/)).toBeInTheDocument();
    expect(screen.getByText(/Supplement Preferences/)).toBeInTheDocument();
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

    // Should still render progress bar and state list
    expect(screen.getByText('Progress: Step 1 of 9')).toBeInTheDocument();
    expect(screen.getByText(/Fitness Level Assessment/)).toBeInTheDocument();
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

    expect(screen.getByText('11%')).toBeInTheDocument();

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

    expect(screen.getByText('56%')).toBeInTheDocument();

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

    expect(screen.getByText('100%')).toBeInTheDocument();
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

    // Check progress bar has proper ARIA attributes
    const progressBar = screen.getByRole('progressbar');
    expect(progressBar).toHaveAttribute('aria-valuenow', '33');
    expect(progressBar).toHaveAttribute('aria-valuemin', '0');
    expect(progressBar).toHaveAttribute('aria-valuemax', '100');
    expect(progressBar).toHaveAttribute('aria-label', 'Onboarding progress: 33% complete');
  });
});
