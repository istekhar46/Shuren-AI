import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mealTemplateService } from '../../src/services/mealTemplateService';
import api from '../../src/services/api';
import type {
  TodayMealsResponse,
  NextMealResponse,
  MealTemplateResponse,
} from '../../src/types/api';

// Mock the api module
vi.mock('../../src/services/api');

describe('mealTemplateService Unit Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('getTodayMealsWithDishes', () => {
    it('should call GET /meal-templates/today and return today meals', async () => {
      const mockTodayMeals: TodayMealsResponse = {
        date: '2024-02-10',
        day_of_week: 6,
        day_name: 'Saturday',
        meals: [
          {
            meal_name: 'Breakfast',
            scheduled_time: '08:00:00',
            day_of_week: 6,
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
        total_calories: 1800,
        total_protein_g: 120,
        total_carbs_g: 200,
        total_fats_g: 60,
      };

      vi.mocked(api.get).mockResolvedValue({
        data: mockTodayMeals,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      });

      const result = await mealTemplateService.getTodayMealsWithDishes();

      expect(api.get).toHaveBeenCalledWith('/meal-templates/today');
      expect(api.get).toHaveBeenCalledTimes(1);
      expect(result).toEqual(mockTodayMeals);
      expect(result.meals).toHaveLength(1);
      expect(result.total_calories).toBe(1800);
    });

    it('should return multiple meals for the day', async () => {
      const mockTodayMeals: TodayMealsResponse = {
        date: '2024-02-10',
        day_of_week: 6,
        day_name: 'Saturday',
        meals: [
          {
            meal_name: 'Breakfast',
            scheduled_time: '08:00:00',
            day_of_week: 6,
            primary_dish: {
              id: 'dish-1',
              name: 'Oatmeal',
              name_hindi: 'ओटमील',
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
          {
            meal_name: 'Lunch',
            scheduled_time: '13:00:00',
            day_of_week: 6,
            primary_dish: {
              id: 'dish-2',
              name: 'Grilled Chicken',
              name_hindi: 'ग्रिल्ड चिकन',
              meal_type: 'lunch',
              cuisine_type: 'continental',
              calories: 500,
              protein_g: 45,
              carbs_g: 30,
              fats_g: 20,
              prep_time_minutes: 15,
              cook_time_minutes: 25,
              total_time_minutes: 40,
              difficulty_level: 'medium',
              is_vegetarian: false,
              is_vegan: false,
            },
            alternative_dishes: [],
          },
        ],
        total_calories: 2000,
        total_protein_g: 150,
        total_carbs_g: 220,
        total_fats_g: 70,
      };

      vi.mocked(api.get).mockResolvedValue({
        data: mockTodayMeals,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      });

      const result = await mealTemplateService.getTodayMealsWithDishes();

      expect(result.meals).toHaveLength(2);
      expect(result.meals[0].meal_name).toBe('Breakfast');
      expect(result.meals[1].meal_name).toBe('Lunch');
    });

    it('should throw error when API call fails', async () => {
      const mockError = new Error('Network error');
      vi.mocked(api.get).mockRejectedValue(mockError);

      await expect(mealTemplateService.getTodayMealsWithDishes()).rejects.toThrow(
        'Network error'
      );
      expect(api.get).toHaveBeenCalledWith('/meal-templates/today');
    });

    it('should throw error when user is not authenticated (401)', async () => {
      const mockError = {
        response: {
          status: 401,
          data: { detail: 'Not authenticated' },
        },
      };
      vi.mocked(api.get).mockRejectedValue(mockError);

      await expect(mealTemplateService.getTodayMealsWithDishes()).rejects.toThrow();
    });
  });

  describe('getNextMealWithDishes', () => {
    it('should call GET /meal-templates/next and return next meal', async () => {
      const mockNextMeal: NextMealResponse = {
        meal_name: 'Lunch',
        scheduled_time: '13:00:00',
        time_until_meal_minutes: 45,
        primary_dish: {
          id: 'dish-3',
          name: 'Chicken Salad',
          name_hindi: 'चिकन सलाद',
          meal_type: 'lunch',
          cuisine_type: 'continental',
          calories: 400,
          protein_g: 35,
          carbs_g: 25,
          fats_g: 18,
          prep_time_minutes: 10,
          cook_time_minutes: 15,
          total_time_minutes: 25,
          difficulty_level: 'easy',
          is_vegetarian: false,
          is_vegan: false,
        },
        alternative_dishes: [
          {
            id: 'dish-4',
            name: 'Veggie Wrap',
            name_hindi: 'वेजी रैप',
            meal_type: 'lunch',
            cuisine_type: 'continental',
            calories: 350,
            protein_g: 15,
            carbs_g: 45,
            fats_g: 12,
            prep_time_minutes: 8,
            cook_time_minutes: 10,
            total_time_minutes: 18,
            difficulty_level: 'easy',
            is_vegetarian: true,
            is_vegan: false,
          },
        ],
      };

      vi.mocked(api.get).mockResolvedValue({
        data: mockNextMeal,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      });

      const result = await mealTemplateService.getNextMealWithDishes();

      expect(api.get).toHaveBeenCalledWith('/meal-templates/next');
      expect(api.get).toHaveBeenCalledTimes(1);
      expect(result).toEqual(mockNextMeal);
      expect(result.meal_name).toBe('Lunch');
      expect(result.time_until_meal_minutes).toBe(45);
      expect(result.alternative_dishes).toHaveLength(1);
    });

    it('should return next meal without alternatives', async () => {
      const mockNextMeal: NextMealResponse = {
        meal_name: 'Dinner',
        scheduled_time: '19:00:00',
        time_until_meal_minutes: 120,
        primary_dish: {
          id: 'dish-5',
          name: 'Grilled Fish',
          name_hindi: 'ग्रिल्ड फिश',
          meal_type: 'dinner',
          cuisine_type: 'continental',
          calories: 450,
          protein_g: 40,
          carbs_g: 20,
          fats_g: 22,
          prep_time_minutes: 12,
          cook_time_minutes: 18,
          total_time_minutes: 30,
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

      const result = await mealTemplateService.getNextMealWithDishes();

      expect(result.alternative_dishes).toHaveLength(0);
      expect(result.time_until_meal_minutes).toBe(120);
    });

    it('should throw error when API call fails', async () => {
      const mockError = new Error('Network error');
      vi.mocked(api.get).mockRejectedValue(mockError);

      await expect(mealTemplateService.getNextMealWithDishes()).rejects.toThrow(
        'Network error'
      );
    });

    it('should throw error when no upcoming meals (404)', async () => {
      const mockError = {
        response: {
          status: 404,
          data: { detail: 'No upcoming meals found' },
        },
      };
      vi.mocked(api.get).mockRejectedValue(mockError);

      await expect(mealTemplateService.getNextMealWithDishes()).rejects.toThrow();
    });
  });

  describe('getMealTemplate', () => {
    it('should call GET /meal-templates/template without week number', async () => {
      const mockTemplate: MealTemplateResponse = {
        id: 'template-1',
        week_number: 1,
        is_active: true,
        days: [],
        created_at: '2024-02-01T00:00:00Z',
        updated_at: '2024-02-01T00:00:00Z',
      };

      vi.mocked(api.get).mockResolvedValue({
        data: mockTemplate,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      });

      const result = await mealTemplateService.getMealTemplate();

      expect(api.get).toHaveBeenCalledWith('/meal-templates/template', {
        params: {},
      });
      expect(api.get).toHaveBeenCalledTimes(1);
      expect(result).toEqual(mockTemplate);
      expect(result.is_active).toBe(true);
    });

    it('should call GET /meal-templates/template with week number', async () => {
      const mockTemplate: MealTemplateResponse = {
        id: 'template-2',
        week_number: 2,
        is_active: false,
        days: [],
        created_at: '2024-02-08T00:00:00Z',
        updated_at: '2024-02-08T00:00:00Z',
      };

      vi.mocked(api.get).mockResolvedValue({
        data: mockTemplate,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      });

      const result = await mealTemplateService.getMealTemplate(2);

      expect(api.get).toHaveBeenCalledWith('/meal-templates/template', {
        params: { week_number: 2 },
      });
      expect(result.week_number).toBe(2);
    });

    it('should throw error when API call fails', async () => {
      const mockError = new Error('Network error');
      vi.mocked(api.get).mockRejectedValue(mockError);

      await expect(mealTemplateService.getMealTemplate()).rejects.toThrow('Network error');
    });

    it('should throw error when template not found (404)', async () => {
      const mockError = {
        response: {
          status: 404,
          data: { detail: 'Template not found' },
        },
      };
      vi.mocked(api.get).mockRejectedValue(mockError);

      await expect(mealTemplateService.getMealTemplate(5)).rejects.toThrow();
    });
  });

  describe('regenerateMealTemplate', () => {
    it('should call POST /meal-templates/template/regenerate without parameters', async () => {
      const mockTemplate: MealTemplateResponse = {
        id: 'template-new',
        week_number: 1,
        is_active: true,
        days: [],
        created_at: '2024-02-10T00:00:00Z',
        updated_at: '2024-02-10T00:00:00Z',
      };

      vi.mocked(api.post).mockResolvedValue({
        data: mockTemplate,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      });

      const result = await mealTemplateService.regenerateMealTemplate();

      expect(api.post).toHaveBeenCalledWith('/meal-templates/template/regenerate', {});
      expect(api.post).toHaveBeenCalledTimes(1);
      expect(result).toEqual(mockTemplate);
    });

    it('should call POST with preferences only', async () => {
      const mockTemplate: MealTemplateResponse = {
        id: 'template-pref',
        week_number: 1,
        is_active: true,
        days: [],
        created_at: '2024-02-10T00:00:00Z',
        updated_at: '2024-02-10T00:00:00Z',
      };

      vi.mocked(api.post).mockResolvedValue({
        data: mockTemplate,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      });

      const result = await mealTemplateService.regenerateMealTemplate(
        'I want more variety and quick meals'
      );

      expect(api.post).toHaveBeenCalledWith('/meal-templates/template/regenerate', {
        preferences: 'I want more variety and quick meals',
      });
      expect(result).toEqual(mockTemplate);
    });

    it('should call POST with week number only', async () => {
      const mockTemplate: MealTemplateResponse = {
        id: 'template-week',
        week_number: 3,
        is_active: false,
        days: [],
        created_at: '2024-02-10T00:00:00Z',
        updated_at: '2024-02-10T00:00:00Z',
      };

      vi.mocked(api.post).mockResolvedValue({
        data: mockTemplate,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      });

      const result = await mealTemplateService.regenerateMealTemplate(undefined, 3);

      expect(api.post).toHaveBeenCalledWith('/meal-templates/template/regenerate', {
        week_number: 3,
      });
      expect(result.week_number).toBe(3);
    });

    it('should call POST with both preferences and week number', async () => {
      const mockTemplate: MealTemplateResponse = {
        id: 'template-both',
        week_number: 2,
        is_active: true,
        days: [],
        created_at: '2024-02-10T00:00:00Z',
        updated_at: '2024-02-10T00:00:00Z',
      };

      vi.mocked(api.post).mockResolvedValue({
        data: mockTemplate,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      });

      const result = await mealTemplateService.regenerateMealTemplate(
        'More protein-rich meals',
        2
      );

      expect(api.post).toHaveBeenCalledWith('/meal-templates/template/regenerate', {
        preferences: 'More protein-rich meals',
        week_number: 2,
      });
      expect(result).toEqual(mockTemplate);
    });

    it('should throw error when API call fails', async () => {
      const mockError = new Error('Network error');
      vi.mocked(api.post).mockRejectedValue(mockError);

      await expect(mealTemplateService.regenerateMealTemplate()).rejects.toThrow(
        'Network error'
      );
    });

    it('should throw error when user is not authenticated (401)', async () => {
      const mockError = {
        response: {
          status: 401,
          data: { detail: 'Not authenticated' },
        },
      };
      vi.mocked(api.post).mockRejectedValue(mockError);

      await expect(mealTemplateService.regenerateMealTemplate()).rejects.toThrow();
    });

    it('should throw error when validation fails (422)', async () => {
      const mockError = {
        response: {
          status: 422,
          data: { detail: 'Invalid week number' },
        },
      };
      vi.mocked(api.post).mockRejectedValue(mockError);

      await expect(mealTemplateService.regenerateMealTemplate(undefined, 10)).rejects.toThrow();
    });
  });
});
