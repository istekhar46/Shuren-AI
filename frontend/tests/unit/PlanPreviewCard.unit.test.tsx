import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { PlanPreviewCard } from '../../src/components/onboarding/PlanPreviewCard';
import type { WorkoutPlan, MealPlan } from '../../src/types/onboarding.types';

describe('PlanPreviewCard', () => {
  const mockWorkoutPlan: WorkoutPlan = {
    frequency: 4,
    location: 'gym',
    duration_minutes: 60,
    equipment: ['dumbbells', 'barbell', 'bench'],
    days: [
      {
        day_number: 1,
        name: 'Monday - Upper Body',
        exercises: [
          {
            name: 'Bench Press',
            sets: 3,
            reps: '8-10',
            rest_seconds: 90,
            notes: 'Focus on form',
          },
          {
            name: 'Dumbbell Rows',
            sets: 3,
            reps: '10-12',
            rest_seconds: 60,
          },
        ],
      },
      {
        day_number: 2,
        name: 'Wednesday - Lower Body',
        exercises: [
          {
            name: 'Squats',
            sets: 4,
            reps: '6-8',
            rest_seconds: 120,
            notes: 'Keep chest up',
          },
        ],
      },
    ],
  };

  const mockMealPlan: MealPlan = {
    diet_type: 'balanced',
    meal_frequency: 4,
    daily_calories: 2200,
    macros: {
      protein_g: 165,
      carbs_g: 220,
      fats_g: 73,
    },
    sample_meals: [
      {
        meal_number: 1,
        name: 'Breakfast',
        calories: 450,
        protein_g: 30,
        carbs_g: 55,
        fats_g: 12,
        foods: ['Oatmeal', 'Protein powder', 'Berries'],
      },
      {
        meal_number: 2,
        name: 'Lunch',
        calories: 600,
        protein_g: 50,
        carbs_g: 65,
        fats_g: 15,
        foods: ['Grilled chicken', 'Rice', 'Vegetables'],
      },
    ],
  };

  const mockHandlers = {
    onApprove: vi.fn(),
    onModify: vi.fn(),
    onClose: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Rendering', () => {
    it('renders workout plan preview with correct title', () => {
      render(
        <PlanPreviewCard
          plan={mockWorkoutPlan}
          planType="workout"
          {...mockHandlers}
        />
      );

      expect(screen.getByText(/Your Workout Plan/)).toBeInTheDocument();
      expect(screen.getByLabelText('workout')).toBeInTheDocument();
    });

    it('renders meal plan preview with correct title', () => {
      render(
        <PlanPreviewCard
          plan={mockMealPlan}
          planType="meal"
          {...mockHandlers}
        />
      );

      expect(screen.getByText(/Your Meal Plan/)).toBeInTheDocument();
      expect(screen.getByLabelText('meal')).toBeInTheDocument();
    });

    it('renders WorkoutPlanPreview component for workout plans', () => {
      render(
        <PlanPreviewCard
          plan={mockWorkoutPlan}
          planType="workout"
          {...mockHandlers}
        />
      );

      // Check for workout-specific content
      expect(screen.getByText(/Bench Press/)).toBeInTheDocument();
      expect(screen.getByText(/Dumbbell Rows/)).toBeInTheDocument();
      expect(screen.getByText(/days\/week/)).toBeInTheDocument(); // Frequency text
    });

    it('renders MealPlanPreview component for meal plans', () => {
      render(
        <PlanPreviewCard
          plan={mockMealPlan}
          planType="meal"
          {...mockHandlers}
        />
      );

      // Check for meal-specific content
      const kcalElements = screen.getAllByText(/kcal/);
      expect(kcalElements.length).toBeGreaterThan(0); // Multiple kcal references
      expect(screen.getByText(/Breakfast/)).toBeInTheDocument();
      expect(screen.getByText(/balanced/)).toBeInTheDocument(); // Diet type
    });

    it('renders close button', () => {
      render(
        <PlanPreviewCard
          plan={mockWorkoutPlan}
          planType="workout"
          {...mockHandlers}
        />
      );

      expect(screen.getByLabelText('Close plan preview')).toBeInTheDocument();
    });

    it('renders approve and request changes buttons initially', () => {
      render(
        <PlanPreviewCard
          plan={mockWorkoutPlan}
          planType="workout"
          {...mockHandlers}
        />
      );

      expect(screen.getByLabelText('Approve this plan')).toBeInTheDocument();
      expect(screen.getByLabelText('Request changes to this plan')).toBeInTheDocument();
    });
  });

  describe('User Interactions', () => {
    it('calls onApprove when approve button is clicked', async () => {
      const user = userEvent.setup();
      render(
        <PlanPreviewCard
          plan={mockWorkoutPlan}
          planType="workout"
          {...mockHandlers}
        />
      );

      const approveButton = screen.getByLabelText('Approve this plan');
      await user.click(approveButton);

      expect(mockHandlers.onApprove).toHaveBeenCalledTimes(1);
    });

    it('calls onClose when close button is clicked', async () => {
      const user = userEvent.setup();
      render(
        <PlanPreviewCard
          plan={mockWorkoutPlan}
          planType="workout"
          {...mockHandlers}
        />
      );

      const closeButton = screen.getByLabelText('Close plan preview');
      await user.click(closeButton);

      expect(mockHandlers.onClose).toHaveBeenCalledTimes(1);
    });

    it('calls onClose when overlay is clicked', async () => {
      const user = userEvent.setup();
      render(
        <PlanPreviewCard
          plan={mockWorkoutPlan}
          planType="workout"
          {...mockHandlers}
        />
      );

      // Find overlay by aria-hidden attribute
      const overlay = document.querySelector('[aria-hidden="true"]');
      expect(overlay).toBeInTheDocument();
      
      if (overlay) {
        await user.click(overlay);
        expect(mockHandlers.onClose).toHaveBeenCalledTimes(1);
      }
    });

    it('shows modification input when request changes is clicked', async () => {
      const user = userEvent.setup();
      render(
        <PlanPreviewCard
          plan={mockWorkoutPlan}
          planType="workout"
          {...mockHandlers}
        />
      );

      const modifyButton = screen.getByLabelText('Request changes to this plan');
      await user.click(modifyButton);

      // Check that modification UI appears
      expect(screen.getByLabelText(/What would you like to change/)).toBeInTheDocument();
      expect(screen.getByPlaceholderText(/Can we reduce the workout frequency/)).toBeInTheDocument();
      expect(screen.getByLabelText('Send modification feedback')).toBeInTheDocument();
      expect(screen.getByLabelText('Cancel modification request')).toBeInTheDocument();
    });

    it('calls onModify with feedback when send feedback is clicked', async () => {
      const user = userEvent.setup();
      render(
        <PlanPreviewCard
          plan={mockWorkoutPlan}
          planType="workout"
          {...mockHandlers}
        />
      );

      // Click request changes
      const modifyButton = screen.getByLabelText('Request changes to this plan');
      await user.click(modifyButton);

      // Type feedback
      const textarea = screen.getByPlaceholderText(/Can we reduce the workout frequency/);
      await user.clear(textarea);
      await user.type(textarea, 'Please reduce to 3 days per week');

      // Submit feedback
      const sendButton = screen.getByLabelText('Send modification feedback');
      await user.click(sendButton);

      expect(mockHandlers.onModify).toHaveBeenCalledWith('Please reduce to 3 days per week');
    }, 10000);

    it('disables send feedback button when textarea is empty', async () => {
      const user = userEvent.setup();
      render(
        <PlanPreviewCard
          plan={mockWorkoutPlan}
          planType="workout"
          {...mockHandlers}
        />
      );

      // Click request changes
      const modifyButton = screen.getByLabelText('Request changes to this plan');
      await user.click(modifyButton);

      // Send button should be disabled
      const sendButton = screen.getByLabelText('Send modification feedback');
      expect(sendButton).toHaveAttribute('disabled');
    });

    it('cancels modification and returns to initial state', async () => {
      const user = userEvent.setup();
      render(
        <PlanPreviewCard
          plan={mockWorkoutPlan}
          planType="workout"
          {...mockHandlers}
        />
      );

      // Click request changes
      const modifyButton = screen.getByLabelText('Request changes to this plan');
      await user.click(modifyButton);

      // Type some feedback
      const textarea = screen.getByPlaceholderText(/Can we reduce the workout frequency/);
      await user.type(textarea, 'Some feedback');

      // Cancel
      const cancelButton = screen.getByLabelText('Cancel modification request');
      await user.click(cancelButton);

      // Should return to initial state
      await waitFor(() => {
        expect(screen.getByLabelText('Approve this plan')).toBeInTheDocument();
        expect(screen.getByLabelText('Request changes to this plan')).toBeInTheDocument();
        expect(screen.queryByLabelText(/What would you like to change/)).not.toBeInTheDocument();
      });
    }, 10000);

    it('clears feedback after successful submission', async () => {
      const user = userEvent.setup();
      render(
        <PlanPreviewCard
          plan={mockWorkoutPlan}
          planType="workout"
          {...mockHandlers}
        />
      );

      // Click request changes
      const modifyButton = screen.getByLabelText('Request changes to this plan');
      await user.click(modifyButton);

      // Type and submit feedback
      const textarea = screen.getByPlaceholderText(/Can we reduce the workout frequency/);
      await user.type(textarea, 'Test feedback');
      
      const sendButton = screen.getByLabelText('Send modification feedback');
      await user.click(sendButton);

      // Should return to initial state
      await waitFor(() => {
        expect(screen.getByLabelText('Approve this plan')).toBeInTheDocument();
      });
    }, 10000);
  });

  describe('Keyboard Navigation', () => {
    it('closes modal when Escape key is pressed', () => {
      render(
        <PlanPreviewCard
          plan={mockWorkoutPlan}
          planType="workout"
          {...mockHandlers}
        />
      );

      fireEvent.keyDown(document, { key: 'Escape' });

      expect(mockHandlers.onClose).toHaveBeenCalledTimes(1);
    });

    it('cancels modification when Escape is pressed in modify mode', async () => {
      const user = userEvent.setup();
      render(
        <PlanPreviewCard
          plan={mockWorkoutPlan}
          planType="workout"
          {...mockHandlers}
        />
      );

      // Enter modify mode
      const modifyButton = screen.getByLabelText('Request changes to this plan');
      await user.click(modifyButton);

      // Type some feedback
      const textarea = screen.getByPlaceholderText(/Can we reduce the workout frequency/);
      await user.type(textarea, 'Some feedback');

      // Press Escape
      fireEvent.keyDown(document, { key: 'Escape' });

      // Should cancel modification and return to initial state
      await waitFor(() => {
        expect(screen.getByLabelText('Approve this plan')).toBeInTheDocument();
      });
    });
  });

  describe('Accessibility', () => {
    it('has proper ARIA attributes for dialog', () => {
      render(
        <PlanPreviewCard
          plan={mockWorkoutPlan}
          planType="workout"
          {...mockHandlers}
        />
      );

      const dialog = screen.getByRole('dialog');
      expect(dialog).toHaveAttribute('aria-modal', 'true');
      expect(dialog).toHaveAttribute('aria-labelledby', 'plan-preview-title');
    });

    it('has proper heading with id for aria-labelledby', () => {
      render(
        <PlanPreviewCard
          plan={mockWorkoutPlan}
          planType="workout"
          {...mockHandlers}
        />
      );

      const heading = document.getElementById('plan-preview-title');
      expect(heading).toBeInTheDocument();
      expect(heading).toHaveTextContent(/Your Workout Plan/);
    });

    it('has descriptive aria-labels for all buttons', () => {
      render(
        <PlanPreviewCard
          plan={mockWorkoutPlan}
          planType="workout"
          {...mockHandlers}
        />
      );

      expect(screen.getByLabelText('Close plan preview')).toBeInTheDocument();
      expect(screen.getByLabelText('Approve this plan')).toBeInTheDocument();
      expect(screen.getByLabelText('Request changes to this plan')).toBeInTheDocument();
    });

    it('autofocuses textarea when modification mode is entered', async () => {
      const user = userEvent.setup();
      render(
        <PlanPreviewCard
          plan={mockWorkoutPlan}
          planType="workout"
          {...mockHandlers}
        />
      );

      const modifyButton = screen.getByLabelText('Request changes to this plan');
      await user.click(modifyButton);

      const textarea = screen.getByPlaceholderText(/Can we reduce the workout frequency/);
      // Check that textarea exists and is in the document (autoFocus is a React prop, not an HTML attribute)
      expect(textarea).toBeInTheDocument();
      expect(textarea).toHaveFocus();
    });
  });

  describe('Edge Cases', () => {
    it('does not call onModify with empty or whitespace-only feedback', async () => {
      const user = userEvent.setup();
      render(
        <PlanPreviewCard
          plan={mockWorkoutPlan}
          planType="workout"
          {...mockHandlers}
        />
      );

      // Enter modify mode
      const modifyButton = screen.getByLabelText('Request changes to this plan');
      await user.click(modifyButton);

      // Type only whitespace
      const textarea = screen.getByPlaceholderText(/Can we reduce the workout frequency/);
      await user.type(textarea, '   ');

      // Try to submit
      const sendButton = screen.getByLabelText('Send modification feedback');
      expect(sendButton).toBeDisabled();
      
      // Should not call onModify
      expect(mockHandlers.onModify).not.toHaveBeenCalled();
    });

    it('handles rapid button clicks gracefully', async () => {
      const user = userEvent.setup();
      render(
        <PlanPreviewCard
          plan={mockWorkoutPlan}
          planType="workout"
          {...mockHandlers}
        />
      );

      const approveButton = screen.getByLabelText('Approve this plan');
      
      // Click multiple times rapidly
      await user.click(approveButton);
      await user.click(approveButton);
      await user.click(approveButton);

      // Should be called 3 times (no debouncing in component)
      expect(mockHandlers.onApprove).toHaveBeenCalledTimes(3);
    });
  });
});
