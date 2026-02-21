import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mealService } from '../../src/services/mealService';
import api from '../../src/services/api';
import type { MealPlanResponse, MealScheduleResponse } from '../../src/types/meal.types';
import type { TodayMealsResponse, NextMealResponse } from '../../src/types/mealTemplate.types';

// Mock the api module
vi.mock('../../src/services/api');

describe('mealService Unit Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('getMealPlan', () => {
    it('should call GET /meals/plan and return meal plan', async () => {
      const mockMealPlan: MealPlanResponse = {
        id: 'plan-uuid-123',
        meals_per_day: 3,
        daily_calories_target: 2000,
        daily_calories_min: 1800,
        daily_calories_max: 2200,
        protein_grams_target: 150,
        carbs_grams_target: 200,
        fats_grams_target: 67,
        protein_percentage: 30,
        carbs_percentage: 40,
        fats_percentage: 30,
        plan_rationale: 'Balanced macros for muscle gain',
        is_locked: false,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      };

      vi.mocked(api.get).mockResolvedValue({
        data: mockMealPlan,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      });

      const result = await mealService.getMealPlan();

      expect(api.get).toHaveBeenCalledWith('/meals/plan');
      expect(api.get).toHaveBeenCalledTimes(1);
      expect(result).toEqual(mockMealPlan);
      expect(result.meals_per_day).toBe(3);
    });

    it('should throw error when API call fails', async () => {
      const mockError = new Error('Network error');
      vi.mocked(api.get).mockRejectedValue(mockError);

      await expect(mealService.getMealPlan()).rejects.toThrow('Network error');
      expect(api.get).toHaveBeenCalledWith('/meals/plan');
    });

    it('should throw error when user is not authenticated (401)', async () => {
      const mockError = {
        response: {
          status: 401,
          data: { detail: 'Not authenticated' },
        },
      };
      vi.mocked(api.get).mockRejectedValue(mockError);

      await expect(mealService.getMealPlan()).rejects.toThrow();
    });
  });

  describe('updateMealPlan', () => {
    it('should call PATCH /meals/plan with updates', async () => {
      const updates = {
        daily_calories_target: 2200,
        protein_percentage: 35,
      };

      const mockUpdatedPlan: MealPlanResponse = {
        id: 'plan-uuid-123',
        meals_per_day: 3,
        daily_calories_target: 2200,
        daily_calories_min: 2000,
        daily_calories_max: 2400,
        protein_grams_target: 165,
        carbs_grams_target: 180,
        fats_grams_target: 73,
        protein_percentage: 35,
        carbs_percentage: 35,
        fats_percentage: 30,
        plan_rationale: 'Updated for higher protein intake',
        is_locked: false,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-02T00:00:00Z',
      };

      vi.mocked(api.patch).mockResolvedValue({
        data: mockUpdatedPlan,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      });

      const result = await mealService.updateMealPlan(updates);

      expect(api.patch).toHaveBeenCalledWith('/meals/plan', updates);
      expect(api.patch).toHaveBeenCalledTimes(1);
      expect(result).toEqual(mockUpdatedPlan);
      expect(result.daily_calories_target).toBe(2200);
      expect(result.protein_percentage).toBe(35);
    });

    it('should throw error when validation fails (422)', async () => {
      const mockError = {
        response: {
          status: 422,
          data: { detail: 'Invalid update parameters' },
        },
      };
      vi.mocked(api.patch).mockRejectedValue(mockError);

      await expect(
        mealService.updateMealPlan({ invalid_field: 'value' })
      ).rejects.toThrow();
    });
  });

  describe('getMealSchedule', () => {
    it('should call GET /meals/schedule and return meal schedule', async () => {
      const mockSchedule: MealScheduleResponse = {
        meals: [
          {
            id: 'schedule-1',
            meal_number: 1,
            meal_name: 'Breakfast',
            scheduled_time: '08:00:00',
            notification_offset_minutes: 15,
            earliest_time: '07:00:00',
            latest_time: '10:00:00',
            is_active: true,
          },
          {
            id: 'schedule-2',
            meal_number: 2,
            meal_name: 'Lunch',
            scheduled_time: '13:00:00',
            notification_offset_minutes: 15,
            earliest_time: '12:00:00',
            latest_time: '15:00:00',
            is_active: true,
          },
        ],
      };

      vi.mocked(api.get).mockResolvedValue({
        data: mockSchedule,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      });

      const result = await mealService.getMealSchedule();

      expect(api.get).toHaveBeenCalledWith('/meals/schedule');
      expect(api.get).toHaveBeenCalledTimes(1);
      expect(result).toEqual(mockSchedule);
      expect(result.meals).toHaveLength(2);
    });

    it('should throw error when API call fails', async () => {
      const mockError = new Error('Network error');
      vi.mocked(api.get).mockRejectedValue(mockError);

      await expect(mealService.getMealSchedule()).rejects.toThrow('Network error');
    });
  });

  describe('updateMealSchedule', () => {
    it('should call PATCH /meals/schedule with updates', async () => {
      const updates = {
        meals: [
          {
            meal_number: 1,
            scheduled_time: '07:30:00',
          },
        ],
      };

      const mockUpdatedSchedule: MealScheduleResponse = {
        meals: [
          {
            id: 'schedule-1',
            meal_number: 1,
            meal_name: 'Breakfast',
            scheduled_time: '07:30:00',
            notification_offset_minutes: 15,
            earliest_time: '07:00:00',
            latest_time: '10:00:00',
            is_active: true,
          },
        ],
      };

      vi.mocked(api.patch).mockResolvedValue({
        data: mockUpdatedSchedule,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      });

      const result = await mealService.updateMealSchedule(updates);

      expect(api.patch).toHaveBeenCalledWith('/meals/schedule', updates);
      expect(result).toEqual(mockUpdatedSchedule);
      expect(result.meals[0].scheduled_time).toBe('07:30:00');
    });
  });

  describe('getTodayMeals', () => {
    it('should call GET /meals/today and return today\'s meals', async () => {
      const mockTodayMeals: TodayMealsResponse = {
        date: '2024-01-15',
        day_of_week: 1,
        day_name: 'Monday',
        meals: [
          {
            meal_name: 'Breakfast',
            scheduled_time: '08:00:00',
            day_of_week: 1,
            primary_dish: {
              id: 'dish-1',
              name: 'Oatmeal Bowl',
              name_hindi: 'ओटमील बाउल',
              meal_type: 'breakfast',
              cuisine_type: 'continental',
              calories: 300,
              protein_g: 12,
              carbs_g: 45,
              fats_g: 8,
              prep_time_minutes: 5,
              cook_time_minutes: 10,
              total_time_minutes: 15,
              difficulty_level: 'easy',
              is_vegetarian: true,
              is_vegan: true,
            },
            alternative_dishes: [],
          },
        ],
        total_calories: 300,
        total_protein_g: 12,
        total_carbs_g: 45,
        total_fats_g: 8,
      };

      vi.mocked(api.get).mockResolvedValue({
        data: mockTodayMeals,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      });

      const result = await mealService.getTodayMeals();

      expect(api.get).toHaveBeenCalledWith('/meals/today');
      expect(api.get).toHaveBeenCalledTimes(1);
      expect(result).toEqual(mockTodayMeals);
      expect(result.meals).toHaveLength(1);
      expect(result.day_name).toBe('Monday');
    });

    it('should throw error when API call fails', async () => {
      const mockError = new Error('Network error');
      vi.mocked(api.get).mockRejectedValue(mockError);

      await expect(mealService.getTodayMeals()).rejects.toThrow('Network error');
    });
  });

  describe('getNextMeal', () => {
    it('should call GET /meals/next and return next meal', async () => {
      const mockNextMeal: NextMealResponse = {
        meal_name: 'Lunch',
        scheduled_time: '13:00:00',
        time_until_meal_minutes: 120,
        primary_dish: {
          id: 'dish-2',
          name: 'Grilled Chicken Salad',
          name_hindi: 'ग्रिल्ड चिकन सलाद',
          meal_type: 'lunch',
          cuisine_type: 'continental',
          calories: 450,
          protein_g: 40,
          carbs_g: 30,
          fats_g: 18,
          prep_time_minutes: 15,
          cook_time_minutes: 20,
          total_time_minutes: 35,
          difficulty_level: 'medium',
          is_vegetarian: false,
          is_vegan: false,
        },
        alternative_dishes: [],
      };

      vi.mocked(api.get).mockResolvedValue({
        data: mockNextMeal,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      });

      const result = await mealService.getNextMeal();

      expect(api.get).toHaveBeenCalledWith('/meals/next');
      expect(api.get).toHaveBeenCalledTimes(1);
      expect(result).toEqual(mockNextMeal);
      expect(result.meal_name).toBe('Lunch');
      expect(result.time_until_meal_minutes).toBe(120);
    });

    it('should throw error when API call fails', async () => {
      const mockError = new Error('Network error');
      vi.mocked(api.get).mockRejectedValue(mockError);

      await expect(mealService.getNextMeal()).rejects.toThrow('Network error');
    });
  });

  describe('Backward Compatibility - getMealPlanWithDates', () => {
    it('should call getMealPlan and log deprecation warning', async () => {
      const consoleWarnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
      
      const mockMealPlan: MealPlanResponse = {
        id: 'plan-uuid-123',
        meals_per_day: 3,
        daily_calories_target: 2000,
        daily_calories_min: 1800,
        daily_calories_max: 2200,
        protein_grams_target: 150,
        carbs_grams_target: 200,
        fats_grams_target: 67,
        protein_percentage: 30,
        carbs_percentage: 40,
        fats_percentage: 30,
        plan_rationale: 'Balanced macros',
        is_locked: false,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      };

      vi.mocked(api.get).mockResolvedValue({
        data: mockMealPlan,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      });

      const result = await mealService.getMealPlanWithDates('2024-01-01', '2024-01-07');

      expect(consoleWarnSpy).toHaveBeenCalledWith(
        'getMealPlanWithDates() is deprecated. Date filtering is not supported. Use getMealPlan() instead.'
      );
      expect(api.get).toHaveBeenCalledWith('/meals/plan');
      expect(result).toEqual(mockMealPlan);

      consoleWarnSpy.mockRestore();
    });

    it('should not log warning when no dates provided', async () => {
      const consoleWarnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
      
      const mockMealPlan: MealPlanResponse = {
        id: 'plan-uuid-123',
        meals_per_day: 3,
        daily_calories_target: 2000,
        daily_calories_min: 1800,
        daily_calories_max: 2200,
        protein_grams_target: 150,
        carbs_grams_target: 200,
        fats_grams_target: 67,
        protein_percentage: 30,
        carbs_percentage: 40,
        fats_percentage: 30,
        plan_rationale: 'Balanced macros',
        is_locked: false,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      };

      vi.mocked(api.get).mockResolvedValue({
        data: mockMealPlan,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      });

      await mealService.getMealPlanWithDates();

      expect(consoleWarnSpy).not.toHaveBeenCalled();

      consoleWarnSpy.mockRestore();
    });
  });

  describe('Backward Compatibility - getMealDetails', () => {
    it('should throw error with helpful message', async () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      await expect(mealService.getMealDetails('meal-123')).rejects.toThrow(
        'getMealDetails() is no longer supported. Use getTodayMeals() or getNextMeal() instead.'
      );

      expect(consoleErrorSpy).toHaveBeenCalledWith(
        'getMealDetails() has been removed. Individual meal endpoints are not available.'
      );

      consoleErrorSpy.mockRestore();
    });
  });

  describe('Backward Compatibility - searchDishes', () => {
    it('should throw error with helpful message', async () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      await expect(mealService.searchDishes('chicken')).rejects.toThrow(
        'searchDishes() has been moved to dishService. Use dishService.searchDishes() instead.'
      );

      expect(consoleErrorSpy).toHaveBeenCalledWith(
        'searchDishes() has been moved to dishService. Import dishService instead.'
      );

      consoleErrorSpy.mockRestore();
    });
  });

  describe('Backward Compatibility - generateShoppingList', () => {
    it('should throw error with helpful message', async () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      await expect(
        mealService.generateShoppingList('2024-01-01', '2024-01-07')
      ).rejects.toThrow(
        'generateShoppingList() has been moved to shoppingListService. Use shoppingListService.getShoppingList(weeks) instead.'
      );

      expect(consoleErrorSpy).toHaveBeenCalledWith(
        'generateShoppingList() has been moved to shoppingListService. Import shoppingListService instead.'
      );

      consoleErrorSpy.mockRestore();
    });
  });
});
