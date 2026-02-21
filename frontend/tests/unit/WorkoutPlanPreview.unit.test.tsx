import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { WorkoutPlanPreview } from '../../src/components/onboarding/WorkoutPlanPreview';
import type { WorkoutPlan } from '../../src/types/onboarding.types';

describe('WorkoutPlanPreview', () => {
  const mockWorkoutPlan: WorkoutPlan = {
    frequency: 4,
    location: 'gym',
    duration_minutes: 60,
    equipment: ['dumbbells', 'barbell', 'bench'],
    days: [
      {
        day_number: 1,
        name: 'Upper Body',
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
        name: 'Lower Body',
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

  describe('Plan Summary', () => {
    it('displays frequency correctly', () => {
      render(<WorkoutPlanPreview plan={mockWorkoutPlan} />);
      
      expect(screen.getByText('Frequency')).toBeInTheDocument();
      expect(screen.getByText('4 days/week')).toBeInTheDocument();
    });

    it('displays location correctly', () => {
      render(<WorkoutPlanPreview plan={mockWorkoutPlan} />);
      
      expect(screen.getByText('Location')).toBeInTheDocument();
      expect(screen.getByText('gym')).toBeInTheDocument();
    });

    it('displays duration correctly', () => {
      render(<WorkoutPlanPreview plan={mockWorkoutPlan} />);
      
      expect(screen.getByText('Duration')).toBeInTheDocument();
      expect(screen.getByText('60 minutes')).toBeInTheDocument();
    });

    it('renders plan overview section', () => {
      render(<WorkoutPlanPreview plan={mockWorkoutPlan} />);
      
      expect(screen.getByText('Plan Overview')).toBeInTheDocument();
    });
  });

  describe('Equipment List', () => {
    it('displays all equipment items', () => {
      render(<WorkoutPlanPreview plan={mockWorkoutPlan} />);
      
      expect(screen.getByText('Equipment Needed')).toBeInTheDocument();
      expect(screen.getByText('dumbbells')).toBeInTheDocument();
      expect(screen.getByText('barbell')).toBeInTheDocument();
      expect(screen.getByText('bench')).toBeInTheDocument();
    });

    it('does not render equipment section when no equipment', () => {
      const planWithoutEquipment: WorkoutPlan = {
        ...mockWorkoutPlan,
        equipment: [],
      };
      
      render(<WorkoutPlanPreview plan={planWithoutEquipment} />);
      
      expect(screen.queryByText('Equipment Needed')).not.toBeInTheDocument();
    });

    it('renders equipment with proper styling', () => {
      render(<WorkoutPlanPreview plan={mockWorkoutPlan} />);
      
      const dumbbell = screen.getByText('dumbbells');
      expect(dumbbell).toHaveClass('bg-blue-100', 'text-blue-800');
    });
  });

  describe('Workout Days', () => {
    it('displays workout schedule heading', () => {
      render(<WorkoutPlanPreview plan={mockWorkoutPlan} />);
      
      expect(screen.getByText('Workout Schedule')).toBeInTheDocument();
    });

    it('renders all workout days', () => {
      render(<WorkoutPlanPreview plan={mockWorkoutPlan} />);
      
      expect(screen.getByText(/Day 1: Upper Body/)).toBeInTheDocument();
      expect(screen.getByText(/Day 2: Lower Body/)).toBeInTheDocument();
    });

    it('displays day numbers correctly', () => {
      render(<WorkoutPlanPreview plan={mockWorkoutPlan} />);
      
      expect(screen.getByText(/Day 1:/)).toBeInTheDocument();
      expect(screen.getByText(/Day 2:/)).toBeInTheDocument();
    });

    it('displays day names correctly', () => {
      render(<WorkoutPlanPreview plan={mockWorkoutPlan} />);
      
      expect(screen.getByText(/Upper Body/)).toBeInTheDocument();
      expect(screen.getByText(/Lower Body/)).toBeInTheDocument();
    });
  });

  describe('Exercises', () => {
    it('displays all exercises', () => {
      render(<WorkoutPlanPreview plan={mockWorkoutPlan} />);
      
      expect(screen.getByText(/Bench Press/)).toBeInTheDocument();
      expect(screen.getByText(/Dumbbell Rows/)).toBeInTheDocument();
      expect(screen.getByText(/Squats/)).toBeInTheDocument();
    });

    it('displays exercise numbers correctly', () => {
      render(<WorkoutPlanPreview plan={mockWorkoutPlan} />);
      
      // Each day has numbered exercises starting from 1
      const exerciseNumbers = screen.getAllByText(/1\./);
      expect(exerciseNumbers.length).toBeGreaterThan(0);
    });

    it('displays sets correctly', () => {
      render(<WorkoutPlanPreview plan={mockWorkoutPlan} />);
      
      const setsLabels = screen.getAllByText('Sets');
      expect(setsLabels.length).toBe(3); // 3 exercises
      
      // Check for specific set values
      const setValues = screen.getAllByText('3');
      expect(setValues.length).toBeGreaterThan(0);
    });

    it('displays reps correctly', () => {
      render(<WorkoutPlanPreview plan={mockWorkoutPlan} />);
      
      const repsLabels = screen.getAllByText('Reps');
      expect(repsLabels.length).toBe(3); // 3 exercises
      
      expect(screen.getByText('8-10')).toBeInTheDocument();
      expect(screen.getByText('10-12')).toBeInTheDocument();
      expect(screen.getByText('6-8')).toBeInTheDocument();
    });

    it('displays rest periods correctly', () => {
      render(<WorkoutPlanPreview plan={mockWorkoutPlan} />);
      
      const restLabels = screen.getAllByText('Rest');
      expect(restLabels.length).toBe(3); // 3 exercises
      
      expect(screen.getByText('90s')).toBeInTheDocument();
      expect(screen.getByText('60s')).toBeInTheDocument();
      expect(screen.getByText('120s')).toBeInTheDocument();
    });

    it('displays exercise notes when present', () => {
      render(<WorkoutPlanPreview plan={mockWorkoutPlan} />);
      
      expect(screen.getByText('Focus on form')).toBeInTheDocument();
      expect(screen.getByText('Keep chest up')).toBeInTheDocument();
    });

    it('does not display notes section when no notes', () => {
      render(<WorkoutPlanPreview plan={mockWorkoutPlan} />);
      
      // Dumbbell Rows has no notes, so it shouldn't have a note section
      // We can verify by checking that there are only 2 "💡 Note:" labels (for exercises with notes)
      const noteLabels = screen.getAllByText(/💡 Note:/);
      expect(noteLabels.length).toBe(2); // Only Bench Press and Squats have notes
    });

    it('renders note sections with proper styling', () => {
      render(<WorkoutPlanPreview plan={mockWorkoutPlan} />);
      
      const noteLabel = screen.getAllByText(/💡 Note:/)[0];
      expect(noteLabel).toHaveClass('text-yellow-800');
    });
  });

  describe('Summary Footer', () => {
    it('displays total workout days', () => {
      render(<WorkoutPlanPreview plan={mockWorkoutPlan} />);
      
      expect(screen.getByText(/2 workout days/)).toBeInTheDocument();
    });

    it('displays total exercises count', () => {
      render(<WorkoutPlanPreview plan={mockWorkoutPlan} />);
      
      expect(screen.getByText(/3 exercises/)).toBeInTheDocument();
    });

    it('calculates total exercises correctly', () => {
      render(<WorkoutPlanPreview plan={mockWorkoutPlan} />);
      
      // Day 1 has 2 exercises, Day 2 has 1 exercise = 3 total
      expect(screen.getByText(/Total:/)).toBeInTheDocument();
      expect(screen.getByText(/3 exercises/)).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('handles single workout day', () => {
      const singleDayPlan: WorkoutPlan = {
        frequency: 1,
        location: 'home',
        duration_minutes: 30,
        equipment: [],
        days: [
          {
            day_number: 1,
            name: 'Full Body',
            exercises: [
              {
                name: 'Push-ups',
                sets: 3,
                reps: '15',
                rest_seconds: 60,
              },
            ],
          },
        ],
      };
      
      render(<WorkoutPlanPreview plan={singleDayPlan} />);
      
      expect(screen.getByText(/1 workout days/)).toBeInTheDocument();
      expect(screen.getByText(/1 exercises/)).toBeInTheDocument();
    });

    it('handles multiple exercises per day', () => {
      const multiExercisePlan: WorkoutPlan = {
        frequency: 1,
        location: 'gym',
        duration_minutes: 90,
        equipment: ['dumbbells'],
        days: [
          {
            day_number: 1,
            name: 'Full Body',
            exercises: [
              { name: 'Exercise 1', sets: 3, reps: '10', rest_seconds: 60 },
              { name: 'Exercise 2', sets: 3, reps: '10', rest_seconds: 60 },
              { name: 'Exercise 3', sets: 3, reps: '10', rest_seconds: 60 },
              { name: 'Exercise 4', sets: 3, reps: '10', rest_seconds: 60 },
              { name: 'Exercise 5', sets: 3, reps: '10', rest_seconds: 60 },
            ],
          },
        ],
      };
      
      render(<WorkoutPlanPreview plan={multiExercisePlan} />);
      
      expect(screen.getByText(/5 exercises/)).toBeInTheDocument();
      expect(screen.getByText(/Exercise 1/)).toBeInTheDocument();
      expect(screen.getByText(/Exercise 5/)).toBeInTheDocument();
    });

    it('handles long exercise names', () => {
      const longNamePlan: WorkoutPlan = {
        frequency: 1,
        location: 'gym',
        duration_minutes: 60,
        equipment: [],
        days: [
          {
            day_number: 1,
            name: 'Day 1',
            exercises: [
              {
                name: 'Barbell Back Squat with Pause at Bottom Position',
                sets: 3,
                reps: '8-10',
                rest_seconds: 120,
              },
            ],
          },
        ],
      };
      
      render(<WorkoutPlanPreview plan={longNamePlan} />);
      
      expect(screen.getByText(/Barbell Back Squat with Pause at Bottom Position/)).toBeInTheDocument();
    });

    it('handles various rep formats', () => {
      const variousRepsPlan: WorkoutPlan = {
        frequency: 1,
        location: 'gym',
        duration_minutes: 60,
        equipment: [],
        days: [
          {
            day_number: 1,
            name: 'Day 1',
            exercises: [
              { name: 'Exercise 1', sets: 3, reps: '10', rest_seconds: 60 },
              { name: 'Exercise 2', sets: 3, reps: '8-12', rest_seconds: 60 },
              { name: 'Exercise 3', sets: 3, reps: 'AMRAP', rest_seconds: 60 },
            ],
          },
        ],
      };
      
      render(<WorkoutPlanPreview plan={variousRepsPlan} />);
      
      expect(screen.getByText('10')).toBeInTheDocument();
      expect(screen.getByText('8-12')).toBeInTheDocument();
      expect(screen.getByText('AMRAP')).toBeInTheDocument();
    });
  });

  describe('Responsive Design', () => {
    it('renders with proper grid layout classes', () => {
      const { container } = render(<WorkoutPlanPreview plan={mockWorkoutPlan} />);
      
      // Check for responsive grid classes
      const gridElement = container.querySelector('.grid-cols-1');
      expect(gridElement).toBeInTheDocument();
    });

    it('renders with proper spacing classes', () => {
      const { container } = render(<WorkoutPlanPreview plan={mockWorkoutPlan} />);
      
      // Check for spacing classes
      const spacingElement = container.querySelector('.space-y-6');
      expect(spacingElement).toBeInTheDocument();
    });
  });
});
