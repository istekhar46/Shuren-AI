import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MealPlanSummary } from './MealPlanSummary';
import type { UserProfile } from '../../types';

describe('MealPlanSummary', () => {
  const mockProfile: UserProfile = {
    id: '123',
    email: 'test@example.com',
    fitnessLevel: 'intermediate',
    goals: [{ type: 'fat_loss' }],
    physicalConstraints: [],
    dietaryPreferences: {
      dietType: 'omnivore',
      allergies: [],
      dislikes: []
    },
    mealPlan: {
      dailyCalories: 2000,
      macros: {
        protein: 150,
        carbs: 200,
        fats: 65
      },
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

  it('renders meal plan summary heading', () => {
    render(<MealPlanSummary profile={mockProfile} />);
    expect(screen.getByText('Meal Plan Summary')).toBeInTheDocument();
  });

  it('displays daily calories', () => {
    render(<MealPlanSummary profile={mockProfile} />);
    expect(screen.getByText('Daily Calories:')).toBeInTheDocument();
    expect(screen.getByText('2000 kcal')).toBeInTheDocument();
  });

  it('displays macros section heading', () => {
    render(<MealPlanSummary profile={mockProfile} />);
    expect(screen.getByText('Macros:')).toBeInTheDocument();
  });

  it('displays protein macros', () => {
    render(<MealPlanSummary profile={mockProfile} />);
    expect(screen.getByText('Protein:')).toBeInTheDocument();
    expect(screen.getByText('150g')).toBeInTheDocument();
  });

  it('displays carbs macros', () => {
    render(<MealPlanSummary profile={mockProfile} />);
    expect(screen.getByText('Carbs:')).toBeInTheDocument();
    expect(screen.getByText('200g')).toBeInTheDocument();
  });

  it('displays fats macros', () => {
    render(<MealPlanSummary profile={mockProfile} />);
    expect(screen.getByText('Fats:')).toBeInTheDocument();
    expect(screen.getByText('65g')).toBeInTheDocument();
  });

  it('displays meals per day', () => {
    render(<MealPlanSummary profile={mockProfile} />);
    expect(screen.getByText('Meals Per Day:')).toBeInTheDocument();
    expect(screen.getByText('3')).toBeInTheDocument();
  });

  it('displays different calorie values correctly', () => {
    const highCalorieProfile = {
      ...mockProfile,
      mealPlan: { ...mockProfile.mealPlan, dailyCalories: 3500 }
    };
    render(<MealPlanSummary profile={highCalorieProfile} />);
    expect(screen.getByText('3500 kcal')).toBeInTheDocument();
  });

  it('displays different macro values correctly', () => {
    const differentMacrosProfile = {
      ...mockProfile,
      mealPlan: {
        ...mockProfile.mealPlan,
        macros: { protein: 180, carbs: 250, fats: 70 }
      }
    };
    render(<MealPlanSummary profile={differentMacrosProfile} />);
    expect(screen.getByText('180g')).toBeInTheDocument();
    expect(screen.getByText('250g')).toBeInTheDocument();
    expect(screen.getByText('70g')).toBeInTheDocument();
  });

  it('displays different meals per day correctly', () => {
    const fiveMealsProfile = {
      ...mockProfile,
      mealPlan: { ...mockProfile.mealPlan, mealsPerDay: 5 }
    };
    render(<MealPlanSummary profile={fiveMealsProfile} />);
    expect(screen.getByText('5')).toBeInTheDocument();
  });
});
