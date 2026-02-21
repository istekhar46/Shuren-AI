import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ProfileSummary } from './ProfileSummary';
import type { UserProfile } from '../../types';

describe('ProfileSummary', () => {
  const mockProfile: UserProfile = {
    id: '123',
    email: 'test@example.com',
    fitnessLevel: 'intermediate',
    goals: [
      { type: 'fat_loss', targetWeight: 75, targetDate: '2024-12-31' },
      { type: 'muscle_gain' }
    ],
    physicalConstraints: [],
    dietaryPreferences: {
      dietType: 'omnivore',
      allergies: [],
      dislikes: []
    },
    mealPlan: {
      dailyCalories: 2000,
      macros: { protein: 150, carbs: 200, fats: 65 },
      mealsPerDay: 3
    },
    mealSchedule: [],
    workoutSchedule: {
      daysPerWeek: 3,
      preferredDays: ['monday', 'wednesday', 'friday'],
      preferredTime: '18:00',
      sessionDuration: 60
    },
    hydrationPreferences: {
      dailyGoal: 2.5,
      reminderInterval: 60
    },
    lifestyleBaseline: {
      energyLevel: 'medium',
      stressLevel: 'low',
      sleepQuality: 'good'
    },
    notificationPreferences: {
      workoutReminders: true,
      mealReminders: true,
      hydrationReminders: true,
      motivationalMessages: false
    },
    isLocked: true,
    createdAt: '2024-01-01T00:00:00Z',
    updatedAt: '2024-01-01T00:00:00Z'
  };

  it('renders profile summary heading', () => {
    render(<ProfileSummary profile={mockProfile} />);
    expect(screen.getByText('Profile Summary')).toBeInTheDocument();
  });

  it('displays user email', () => {
    render(<ProfileSummary profile={mockProfile} />);
    expect(screen.getByText('Email:')).toBeInTheDocument();
    expect(screen.getByText('test@example.com')).toBeInTheDocument();
  });

  it('displays formatted fitness level', () => {
    render(<ProfileSummary profile={mockProfile} />);
    expect(screen.getByText('Fitness Level:')).toBeInTheDocument();
    expect(screen.getByText('Intermediate')).toBeInTheDocument();
  });

  it('displays formatted goals', () => {
    render(<ProfileSummary profile={mockProfile} />);
    expect(screen.getByText('Goals:')).toBeInTheDocument();
    expect(screen.getByText('fat loss, muscle gain')).toBeInTheDocument();
  });

  it('displays energy level', () => {
    render(<ProfileSummary profile={mockProfile} />);
    expect(screen.getByText('Energy Level:')).toBeInTheDocument();
    expect(screen.getByText('Medium')).toBeInTheDocument();
  });

  it('displays locked profile status', () => {
    render(<ProfileSummary profile={mockProfile} />);
    expect(screen.getByText('Profile Status:')).toBeInTheDocument();
    expect(screen.getByText('Locked')).toBeInTheDocument();
  });

  it('displays unlocked profile status when not locked', () => {
    const unlockedProfile = { ...mockProfile, isLocked: false };
    render(<ProfileSummary profile={unlockedProfile} />);
    expect(screen.getByText('Unlocked')).toBeInTheDocument();
  });

  it('formats beginner fitness level correctly', () => {
    const beginnerProfile = { ...mockProfile, fitnessLevel: 'beginner' as const };
    render(<ProfileSummary profile={beginnerProfile} />);
    expect(screen.getByText('Beginner')).toBeInTheDocument();
  });

  it('formats advanced fitness level correctly', () => {
    const advancedProfile = { ...mockProfile, fitnessLevel: 'advanced' as const };
    render(<ProfileSummary profile={advancedProfile} />);
    expect(screen.getByText('Advanced')).toBeInTheDocument();
  });

  it('formats low energy level correctly', () => {
    const lowEnergyProfile = {
      ...mockProfile,
      lifestyleBaseline: { ...mockProfile.lifestyleBaseline, energyLevel: 'low' as const }
    };
    render(<ProfileSummary profile={lowEnergyProfile} />);
    expect(screen.getByText('Low')).toBeInTheDocument();
  });

  it('formats high energy level correctly', () => {
    const highEnergyProfile = {
      ...mockProfile,
      lifestyleBaseline: { ...mockProfile.lifestyleBaseline, energyLevel: 'high' as const }
    };
    render(<ProfileSummary profile={highEnergyProfile} />);
    expect(screen.getByText('High')).toBeInTheDocument();
  });
});
