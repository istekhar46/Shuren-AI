import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { WorkoutScheduleSummary } from './WorkoutScheduleSummary';
import type { UserProfile } from '../../types';

describe('WorkoutScheduleSummary', () => {
  const mockProfile: UserProfile = {
    id: '123',
    email: 'test@example.com',
    fitnessLevel: 'intermediate',
    goals: [{ type: 'muscle_gain' }],
    physicalConstraints: [],
    dietaryPreferences: {
      dietType: 'omnivore',
      allergies: [],
      dislikes: []
    },
    mealPlan: {
      dailyCalories: 2500,
      macros: { protein: 180, carbs: 250, fats: 70 },
      mealsPerDay: 4
    },
    mealSchedule: [],
    workoutSchedule: {
      daysPerWeek: 4,
      preferredDays: ['monday', 'tuesday', 'thursday', 'friday'],
      preferredTime: '18:00',
      sessionDuration: 60
    },
    hydrationPreferences: {
      dailyGoal: 3.0,
      reminderInterval: 60
    },
    lifestyleBaseline: {
      energyLevel: 'high',
      stressLevel: 'medium',
      sleepQuality: 'good'
    },
    notificationPreferences: {
      workoutReminders: true,
      mealReminders: true,
      hydrationReminders: true,
      motivationalMessages: true
    },
    isLocked: true,
    createdAt: '2024-01-01T00:00:00Z',
    updatedAt: '2024-01-01T00:00:00Z'
  };

  it('renders workout schedule heading', () => {
    render(<WorkoutScheduleSummary profile={mockProfile} />);
    expect(screen.getByText('Workout Schedule')).toBeInTheDocument();
  });

  it('displays days per week', () => {
    render(<WorkoutScheduleSummary profile={mockProfile} />);
    expect(screen.getByText('Days Per Week:')).toBeInTheDocument();
    expect(screen.getByText('4')).toBeInTheDocument();
  });

  it('displays preferred days section heading', () => {
    render(<WorkoutScheduleSummary profile={mockProfile} />);
    expect(screen.getByText('Preferred Days:')).toBeInTheDocument();
  });

  it('displays formatted preferred days', () => {
    render(<WorkoutScheduleSummary profile={mockProfile} />);
    expect(screen.getByText('Monday, Tuesday, Thursday, Friday')).toBeInTheDocument();
  });

  it('displays preferred time', () => {
    render(<WorkoutScheduleSummary profile={mockProfile} />);
    expect(screen.getByText('Preferred Time:')).toBeInTheDocument();
    expect(screen.getByText('6:00 PM')).toBeInTheDocument();
  });

  it('displays session duration', () => {
    render(<WorkoutScheduleSummary profile={mockProfile} />);
    expect(screen.getByText('Session Duration:')).toBeInTheDocument();
    expect(screen.getByText('60 minutes')).toBeInTheDocument();
  });

  it('formats morning time correctly (AM)', () => {
    const morningProfile = {
      ...mockProfile,
      workoutSchedule: { ...mockProfile.workoutSchedule, preferredTime: '07:30' }
    };
    render(<WorkoutScheduleSummary profile={morningProfile} />);
    expect(screen.getByText('7:30 AM')).toBeInTheDocument();
  });

  it('formats noon time correctly', () => {
    const noonProfile = {
      ...mockProfile,
      workoutSchedule: { ...mockProfile.workoutSchedule, preferredTime: '12:00' }
    };
    render(<WorkoutScheduleSummary profile={noonProfile} />);
    expect(screen.getByText('12:00 PM')).toBeInTheDocument();
  });

  it('formats midnight time correctly', () => {
    const midnightProfile = {
      ...mockProfile,
      workoutSchedule: { ...mockProfile.workoutSchedule, preferredTime: '00:00' }
    };
    render(<WorkoutScheduleSummary profile={midnightProfile} />);
    expect(screen.getByText('12:00 AM')).toBeInTheDocument();
  });

  it('displays different days per week correctly', () => {
    const threeDaysProfile = {
      ...mockProfile,
      workoutSchedule: { ...mockProfile.workoutSchedule, daysPerWeek: 3 }
    };
    render(<WorkoutScheduleSummary profile={threeDaysProfile} />);
    expect(screen.getByText('3')).toBeInTheDocument();
  });

  it('displays different session duration correctly', () => {
    const longerSessionProfile = {
      ...mockProfile,
      workoutSchedule: { ...mockProfile.workoutSchedule, sessionDuration: 90 }
    };
    render(<WorkoutScheduleSummary profile={longerSessionProfile} />);
    expect(screen.getByText('90 minutes')).toBeInTheDocument();
  });

  it('formats single preferred day correctly', () => {
    const oneDayProfile = {
      ...mockProfile,
      workoutSchedule: {
        ...mockProfile.workoutSchedule,
        preferredDays: ['wednesday']
      }
    };
    render(<WorkoutScheduleSummary profile={oneDayProfile} />);
    expect(screen.getByText('Wednesday')).toBeInTheDocument();
  });

  it('formats multiple preferred days with proper capitalization', () => {
    const weekendProfile = {
      ...mockProfile,
      workoutSchedule: {
        ...mockProfile.workoutSchedule,
        preferredDays: ['saturday', 'sunday']
      }
    };
    render(<WorkoutScheduleSummary profile={weekendProfile} />);
    expect(screen.getByText('Saturday, Sunday')).toBeInTheDocument();
  });
});
