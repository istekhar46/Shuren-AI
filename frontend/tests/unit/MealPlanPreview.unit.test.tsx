import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MealPlanPreview } from '../../src/components/onboarding/MealPlanPreview';
import type { MealPlan } from '../../src/types/onboarding.types';

describe('MealPlanPreview', () => {
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

  describe('Plan Summary', () => {
    it('displays diet type correctly', () => {
      render(<MealPlanPreview plan={mockMealPlan} />);
      
      expect(screen.getByText('Diet Type')).toBeInTheDocument();
      expect(screen.getByText('balanced')).toBeInTheDocument();
    });

    it('displays daily calories correctly', () => {
      render(<MealPlanPreview plan={mockMealPlan} />);
      
      expect(screen.getByText('Daily Calories')).toBeInTheDocument();
      expect(screen.getByText(/2200 kcal/)).toBeInTheDocument();
    });

    it('displays meal frequency correctly', () => {
      render(<MealPlanPreview plan={mockMealPlan} />);
      
      expect(screen.getByText('Meal Frequency')).toBeInTheDocument();
      expect(screen.getByText('4 meals/day')).toBeInTheDocument();
    });

    it('renders plan overview section', () => {
      render(<MealPlanPreview plan={mockMealPlan} />);
      
      expect(screen.getByText('Plan Overview')).toBeInTheDocument();
    });
  });

  describe('Macro Breakdown', () => {
    it('displays macro breakdown heading', () => {
      render(<MealPlanPreview plan={mockMealPlan} />);
      
      expect(screen.getByText('Macro Breakdown')).toBeInTheDocument();
    });

    it('displays protein macros correctly', () => {
      render(<MealPlanPreview plan={mockMealPlan} />);
      
      const proteinLabels = screen.getAllByText('Protein');
      expect(proteinLabels.length).toBeGreaterThan(0);
      const proteinValues = screen.getAllByText(/165g/);
      expect(proteinValues.length).toBeGreaterThan(0);
    });

    it('displays carbs macros correctly', () => {
      render(<MealPlanPreview plan={mockMealPlan} />);
      
      const carbsLabels = screen.getAllByText('Carbs');
      expect(carbsLabels.length).toBeGreaterThan(0);
      const carbsValues = screen.getAllByText(/220g/);
      expect(carbsValues.length).toBeGreaterThan(0);
    });

    it('displays fats macros correctly', () => {
      render(<MealPlanPreview plan={mockMealPlan} />);
      
      const fatsLabels = screen.getAllByText('Fats');
      expect(fatsLabels.length).toBeGreaterThan(0);
      const fatsValues = screen.getAllByText(/73g/);
      expect(fatsValues.length).toBeGreaterThan(0);
    });

    it('calculates macro percentages correctly', () => {
      render(<MealPlanPreview plan={mockMealPlan} />);
      
      // Protein: 165g * 4 = 660 cal
      // Carbs: 220g * 4 = 880 cal
      // Fats: 73g * 9 = 657 cal
      // Total: 2197 cal
      // Protein %: 660/2197 = 30%
      // Carbs %: 880/2197 = 40%
      // Fats %: 657/2197 = 30%
      
      const thirtyPercent = screen.getAllByText(/30%/);
      expect(thirtyPercent.length).toBeGreaterThan(0);
      const fortyPercent = screen.getAllByText(/40%/);
      expect(fortyPercent.length).toBeGreaterThan(0);
    });

    it('displays macro summary cards', () => {
      render(<MealPlanPreview plan={mockMealPlan} />);
      
      // Check for the large macro values in summary cards
      const proteinCard = screen.getAllByText('165g');
      const carbsCard = screen.getAllByText('220g');
      const fatsCard = screen.getAllByText('73g');
      
      expect(proteinCard.length).toBeGreaterThan(0);
      expect(carbsCard.length).toBeGreaterThan(0);
      expect(fatsCard.length).toBeGreaterThan(0);
    });

    it('renders macro bars with proper styling', () => {
      const { container } = render(<MealPlanPreview plan={mockMealPlan} />);
      
      // Check for progress bar elements
      const proteinBar = container.querySelector('.bg-blue-600');
      expect(proteinBar).toBeInTheDocument();
    });
  });

  describe('Sample Meals', () => {
    it('displays sample meals heading', () => {
      render(<MealPlanPreview plan={mockMealPlan} />);
      
      expect(screen.getByText('Sample Meals')).toBeInTheDocument();
    });

    it('renders all sample meals', () => {
      render(<MealPlanPreview plan={mockMealPlan} />);
      
      expect(screen.getByText(/Meal 1: Breakfast/)).toBeInTheDocument();
      expect(screen.getByText(/Meal 2: Lunch/)).toBeInTheDocument();
    });

    it('displays meal numbers correctly', () => {
      render(<MealPlanPreview plan={mockMealPlan} />);
      
      expect(screen.getByText(/Meal 1:/)).toBeInTheDocument();
      expect(screen.getByText(/Meal 2:/)).toBeInTheDocument();
    });

    it('displays meal names correctly', () => {
      render(<MealPlanPreview plan={mockMealPlan} />);
      
      expect(screen.getByText(/Breakfast/)).toBeInTheDocument();
      expect(screen.getByText(/Lunch/)).toBeInTheDocument();
    });

    it('displays meal calories', () => {
      render(<MealPlanPreview plan={mockMealPlan} />);
      
      expect(screen.getByText(/450 kcal/)).toBeInTheDocument();
      expect(screen.getByText(/600 kcal/)).toBeInTheDocument();
    });

    it('displays meal macros', () => {
      render(<MealPlanPreview plan={mockMealPlan} />);
      
      // Breakfast macros
      expect(screen.getByText('30g')).toBeInTheDocument(); // Protein
      expect(screen.getByText('55g')).toBeInTheDocument(); // Carbs
      expect(screen.getByText('12g')).toBeInTheDocument(); // Fats
      
      // Lunch macros
      expect(screen.getByText('50g')).toBeInTheDocument(); // Protein
      expect(screen.getByText('65g')).toBeInTheDocument(); // Carbs
      expect(screen.getByText('15g')).toBeInTheDocument(); // Fats
    });

    it('displays all foods for each meal', () => {
      render(<MealPlanPreview plan={mockMealPlan} />);
      
      // Breakfast foods
      expect(screen.getByText('Oatmeal')).toBeInTheDocument();
      expect(screen.getByText('Protein powder')).toBeInTheDocument();
      expect(screen.getByText('Berries')).toBeInTheDocument();
      
      // Lunch foods
      expect(screen.getByText('Grilled chicken')).toBeInTheDocument();
      expect(screen.getByText('Rice')).toBeInTheDocument();
      expect(screen.getByText('Vegetables')).toBeInTheDocument();
    });

    it('displays foods label', () => {
      render(<MealPlanPreview plan={mockMealPlan} />);
      
      const foodsLabels = screen.getAllByText('Foods:');
      expect(foodsLabels.length).toBe(2); // One for each meal
    });
  });

  describe('Meal Timing Tip', () => {
    it('displays meal timing tip', () => {
      render(<MealPlanPreview plan={mockMealPlan} />);
      
      expect(screen.getByText(/💡 Tip:/)).toBeInTheDocument();
      expect(screen.getByText(/Space your meals evenly throughout the day/)).toBeInTheDocument();
    });

    it('mentions workout schedule in tip', () => {
      render(<MealPlanPreview plan={mockMealPlan} />);
      
      expect(screen.getByText(/workout schedule/)).toBeInTheDocument();
    });
  });

  describe('Summary Footer', () => {
    it('displays total meals', () => {
      render(<MealPlanPreview plan={mockMealPlan} />);
      
      expect(screen.getByText(/4 meals providing/)).toBeInTheDocument();
    });

    it('displays total calories', () => {
      render(<MealPlanPreview plan={mockMealPlan} />);
      
      expect(screen.getByText(/2200 calories per day/)).toBeInTheDocument();
    });

    it('displays Total label', () => {
      render(<MealPlanPreview plan={mockMealPlan} />);
      
      const totalLabels = screen.getAllByText(/Total:/);
      expect(totalLabels.length).toBeGreaterThan(0);
    });
  });

  describe('Edge Cases', () => {
    it('handles single meal plan', () => {
      const singleMealPlan: MealPlan = {
        diet_type: 'intermittent fasting',
        meal_frequency: 1,
        daily_calories: 2000,
        macros: {
          protein_g: 150,
          carbs_g: 200,
          fats_g: 67,
        },
        sample_meals: [
          {
            meal_number: 1,
            name: 'OMAD',
            calories: 2000,
            protein_g: 150,
            carbs_g: 200,
            fats_g: 67,
            foods: ['Large mixed meal'],
          },
        ],
      };
      
      render(<MealPlanPreview plan={singleMealPlan} />);
      
      expect(screen.getByText(/1 meals providing/)).toBeInTheDocument();
      expect(screen.getByText(/OMAD/)).toBeInTheDocument();
    });

    it('handles many meals per day', () => {
      const manyMealsPlan: MealPlan = {
        diet_type: 'bodybuilding',
        meal_frequency: 6,
        daily_calories: 3000,
        macros: {
          protein_g: 250,
          carbs_g: 300,
          fats_g: 100,
        },
        sample_meals: [
          {
            meal_number: 1,
            name: 'Meal 1',
            calories: 500,
            protein_g: 40,
            carbs_g: 50,
            fats_g: 15,
            foods: ['Food 1'],
          },
          {
            meal_number: 2,
            name: 'Meal 2',
            calories: 500,
            protein_g: 40,
            carbs_g: 50,
            fats_g: 15,
            foods: ['Food 2'],
          },
          {
            meal_number: 3,
            name: 'Meal 3',
            calories: 500,
            protein_g: 40,
            carbs_g: 50,
            fats_g: 15,
            foods: ['Food 3'],
          },
        ],
      };
      
      render(<MealPlanPreview plan={manyMealsPlan} />);
      
      expect(screen.getByText(/6 meals providing/)).toBeInTheDocument();
      expect(screen.getByText(/Meal 1/)).toBeInTheDocument();
      expect(screen.getByText(/Meal 3/)).toBeInTheDocument();
    });

    it('handles long food names', () => {
      const longFoodPlan: MealPlan = {
        diet_type: 'balanced',
        meal_frequency: 1,
        daily_calories: 2000,
        macros: {
          protein_g: 150,
          carbs_g: 200,
          fats_g: 67,
        },
        sample_meals: [
          {
            meal_number: 1,
            name: 'Breakfast',
            calories: 2000,
            protein_g: 150,
            carbs_g: 200,
            fats_g: 67,
            foods: [
              'Organic steel-cut oats with almond butter and mixed berries',
              'Grass-fed whey protein isolate shake with banana',
            ],
          },
        ],
      };
      
      render(<MealPlanPreview plan={longFoodPlan} />);
      
      expect(screen.getByText(/Organic steel-cut oats/)).toBeInTheDocument();
      expect(screen.getByText(/Grass-fed whey protein/)).toBeInTheDocument();
    });

    it('handles various diet types', () => {
      const veganPlan: MealPlan = {
        ...mockMealPlan,
        diet_type: 'vegan',
      };
      
      render(<MealPlanPreview plan={veganPlan} />);
      
      expect(screen.getByText('vegan')).toBeInTheDocument();
    });

    it('handles high calorie plans', () => {
      const highCaloriePlan: MealPlan = {
        ...mockMealPlan,
        daily_calories: 4000,
      };
      
      render(<MealPlanPreview plan={highCaloriePlan} />);
      
      const fourThousand = screen.getAllByText(/4000/);
      expect(fourThousand.length).toBeGreaterThan(0);
    });

    it('handles low calorie plans', () => {
      const lowCaloriePlan: MealPlan = {
        ...mockMealPlan,
        daily_calories: 1200,
      };
      
      render(<MealPlanPreview plan={lowCaloriePlan} />);
      
      const twelveHundred = screen.getAllByText(/1200/);
      expect(twelveHundred.length).toBeGreaterThan(0);
    });
  });

  describe('Responsive Design', () => {
    it('renders with proper grid layout classes', () => {
      const { container } = render(<MealPlanPreview plan={mockMealPlan} />);
      
      // Check for responsive grid classes
      const gridElement = container.querySelector('.grid-cols-1');
      expect(gridElement).toBeInTheDocument();
    });

    it('renders with proper spacing classes', () => {
      const { container } = render(<MealPlanPreview plan={mockMealPlan} />);
      
      // Check for spacing classes
      const spacingElement = container.querySelector('.space-y-6');
      expect(spacingElement).toBeInTheDocument();
    });

    it('renders macro summary with 3-column grid', () => {
      const { container } = render(<MealPlanPreview plan={mockMealPlan} />);
      
      // Check for 3-column grid for macro summary
      const gridCols3 = container.querySelector('.grid-cols-3');
      expect(gridCols3).toBeInTheDocument();
    });
  });
});
