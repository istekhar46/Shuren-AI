import { describe, it, expect, vi, beforeEach } from 'vitest';
import { dishService } from '../../src/services/dishService';
import api from '../../src/services/api';
import type { DishSummaryResponse, DishResponse, DishSearchFilters } from '../../src/types/api';

// Mock the api module
vi.mock('../../src/services/api');

describe('dishService Unit Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('listDishes', () => {
    it('should call GET /dishes/ without filters', async () => {
      const mockDishes: DishSummaryResponse[] = [
        {
          id: 'dish-1',
          name: 'Grilled Chicken Salad',
          name_hindi: 'ग्रिल्ड चिकन सलाद',
          meal_type: 'lunch',
          cuisine_type: 'continental',
          calories: 350,
          protein_g: 35,
          carbs_g: 20,
          fats_g: 15,
          prep_time_minutes: 15,
          cook_time_minutes: 20,
          total_time_minutes: 35,
          difficulty_level: 'easy',
          is_vegetarian: false,
          is_vegan: false,
        },
      ];

      vi.mocked(api.get).mockResolvedValue({
        data: mockDishes,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      });

      const result = await dishService.listDishes();

      expect(api.get).toHaveBeenCalledWith('/dishes/', {
        params: undefined,
      });
      expect(api.get).toHaveBeenCalledTimes(1);
      expect(result).toEqual(mockDishes);
      expect(result).toHaveLength(1);
    });

    it('should call GET /dishes/ with filters', async () => {
      const filters: DishSearchFilters = {
        meal_type: 'breakfast',
        diet_type: 'vegetarian',
        limit: 10,
      };

      const mockDishes: DishSummaryResponse[] = [
        {
          id: 'dish-2',
          name: 'Oatmeal Bowl',
          name_hindi: 'ओटमील बाउल',
          meal_type: 'breakfast',
          cuisine_type: 'continental',
          calories: 250,
          protein_g: 10,
          carbs_g: 40,
          fats_g: 5,
          prep_time_minutes: 5,
          cook_time_minutes: 10,
          total_time_minutes: 15,
          difficulty_level: 'easy',
          is_vegetarian: true,
          is_vegan: true,
        },
      ];

      vi.mocked(api.get).mockResolvedValue({
        data: mockDishes,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      });

      const result = await dishService.listDishes(filters);

      expect(api.get).toHaveBeenCalledWith('/dishes/', {
        params: filters,
      });
      expect(result).toEqual(mockDishes);
      expect(result[0].is_vegetarian).toBe(true);
    });

    it('should return empty array when no dishes found', async () => {
      vi.mocked(api.get).mockResolvedValue({
        data: [],
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      });

      const result = await dishService.listDishes();

      expect(result).toEqual([]);
      expect(result).toHaveLength(0);
    });

    it('should throw error when API call fails', async () => {
      const mockError = new Error('Network error');
      vi.mocked(api.get).mockRejectedValue(mockError);

      await expect(dishService.listDishes()).rejects.toThrow('Network error');
      expect(api.get).toHaveBeenCalledWith('/dishes/', {
        params: undefined,
      });
    });

    it('should throw error when user is not authenticated (401)', async () => {
      const mockError = {
        response: {
          status: 401,
          data: { detail: 'Not authenticated' },
        },
      };
      vi.mocked(api.get).mockRejectedValue(mockError);

      await expect(dishService.listDishes()).rejects.toThrow();
      expect(api.get).toHaveBeenCalledWith('/dishes/', {
        params: undefined,
      });
    });
  });

  describe('searchDishes', () => {
    it('should call GET /dishes/search with filters', async () => {
      const filters: DishSearchFilters = {
        max_prep_time: 30,
        max_calories: 500,
        diet_type: 'vegetarian',
      };

      const mockDishes: DishSummaryResponse[] = [
        {
          id: 'dish-3',
          name: 'Veggie Stir Fry',
          name_hindi: 'वेजी स्टिर फ्राई',
          meal_type: 'dinner',
          cuisine_type: 'asian',
          calories: 400,
          protein_g: 15,
          carbs_g: 50,
          fats_g: 12,
          prep_time_minutes: 10,
          cook_time_minutes: 15,
          total_time_minutes: 25,
          difficulty_level: 'medium',
          is_vegetarian: true,
          is_vegan: true,
        },
      ];

      vi.mocked(api.get).mockResolvedValue({
        data: mockDishes,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      });

      const result = await dishService.searchDishes(filters);

      expect(api.get).toHaveBeenCalledWith('/dishes/search', {
        params: filters,
      });
      expect(api.get).toHaveBeenCalledTimes(1);
      expect(result).toEqual(mockDishes);
      expect(result[0].total_time_minutes).toBeLessThanOrEqual(30);
      expect(result[0].calories).toBeLessThanOrEqual(500);
    });

    it('should search with multiple filter criteria', async () => {
      const filters: DishSearchFilters = {
        meal_type: 'lunch',
        max_prep_time: 20,
        max_calories: 600,
        limit: 5,
        offset: 0,
      };

      const mockDishes: DishSummaryResponse[] = [];

      vi.mocked(api.get).mockResolvedValue({
        data: mockDishes,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      });

      const result = await dishService.searchDishes(filters);

      expect(api.get).toHaveBeenCalledWith('/dishes/search', {
        params: filters,
      });
      expect(result).toEqual([]);
    });

    it('should throw error when API call fails', async () => {
      const mockError = new Error('Network error');
      vi.mocked(api.get).mockRejectedValue(mockError);

      await expect(
        dishService.searchDishes({ max_calories: 500 })
      ).rejects.toThrow('Network error');
    });

    it('should throw error when validation fails (422)', async () => {
      const mockError = {
        response: {
          status: 422,
          data: { detail: 'Invalid filter parameters' },
        },
      };
      vi.mocked(api.get).mockRejectedValue(mockError);

      await expect(
        dishService.searchDishes({ max_calories: -100 } as any)
      ).rejects.toThrow();
    });

    it('should handle pagination with offset and limit', async () => {
      const filters: DishSearchFilters = {
        limit: 20,
        offset: 40,
      };

      const mockDishes: DishSummaryResponse[] = Array(20)
        .fill(null)
        .map((_, i) => ({
          id: `dish-${i + 40}`,
          name: `Dish ${i + 40}`,
          name_hindi: `डिश ${i + 40}`,
          meal_type: 'lunch',
          cuisine_type: 'indian',
          calories: 400,
          protein_g: 20,
          carbs_g: 40,
          fats_g: 10,
          prep_time_minutes: 15,
          cook_time_minutes: 20,
          total_time_minutes: 35,
          difficulty_level: 'medium',
          is_vegetarian: true,
          is_vegan: false,
        }));

      vi.mocked(api.get).mockResolvedValue({
        data: mockDishes,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      });

      const result = await dishService.searchDishes(filters);

      expect(result).toHaveLength(20);
      expect(api.get).toHaveBeenCalledWith('/dishes/search', {
        params: filters,
      });
    });
  });

  describe('getDishDetails', () => {
    it('should call GET /dishes/{dishId} and return dish details', async () => {
      const dishId = 'dish-uuid-123';
      const mockDish: DishResponse = {
        id: dishId,
        name: 'Grilled Chicken Salad',
        name_hindi: 'ग्रिल्ड चिकन सलाद',
        description: 'A healthy grilled chicken salad with fresh vegetables',
        meal_type: 'lunch',
        dish_category: 'main_course',
        cuisine_type: 'continental',
        calories: 350,
        protein_g: 35,
        carbs_g: 20,
        fats_g: 15,
        fiber_g: 5,
        serving_size_g: 300,
        prep_time_minutes: 15,
        cook_time_minutes: 20,
        total_time_minutes: 35,
        difficulty_level: 'easy',
        is_vegetarian: false,
        is_vegan: false,
        is_gluten_free: true,
        is_dairy_free: true,
        is_nut_free: true,
        contains_allergens: [],
        is_active: true,
        popularity_score: 85,
        ingredients: [
          {
            ingredient_id: 'ing-1',
            name: 'Chicken Breast',
            name_hindi: 'चिकन ब्रेस्ट',
            quantity: 200,
            unit: 'g',
            is_optional: false,
          },
          {
            ingredient_id: 'ing-2',
            name: 'Mixed Greens',
            name_hindi: 'मिक्स्ड ग्रीन्स',
            quantity: 100,
            unit: 'g',
            is_optional: false,
          },
        ],
      };

      vi.mocked(api.get).mockResolvedValue({
        data: mockDish,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      });

      const result = await dishService.getDishDetails(dishId);

      expect(api.get).toHaveBeenCalledWith(`/dishes/${dishId}`);
      expect(api.get).toHaveBeenCalledTimes(1);
      expect(result).toEqual(mockDish);
      expect(result.id).toBe(dishId);
      expect(result.ingredients).toHaveLength(2);
    });

    it('should return dish with allergen information', async () => {
      const dishId = 'dish-uuid-456';
      const mockDish: DishResponse = {
        id: dishId,
        name: 'Peanut Butter Toast',
        name_hindi: 'पीनट बटर टोस्ट',
        description: 'Whole wheat toast with peanut butter',
        meal_type: 'breakfast',
        dish_category: 'snack',
        cuisine_type: 'continental',
        calories: 300,
        protein_g: 12,
        carbs_g: 35,
        fats_g: 14,
        fiber_g: 4,
        serving_size_g: 100,
        prep_time_minutes: 5,
        cook_time_minutes: 5,
        total_time_minutes: 10,
        difficulty_level: 'easy',
        is_vegetarian: true,
        is_vegan: true,
        is_gluten_free: false,
        is_dairy_free: true,
        is_nut_free: false,
        contains_allergens: ['peanuts', 'gluten'],
        is_active: true,
        popularity_score: 70,
        ingredients: [],
      };

      vi.mocked(api.get).mockResolvedValue({
        data: mockDish,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      });

      const result = await dishService.getDishDetails(dishId);

      expect(result.contains_allergens).toContain('peanuts');
      expect(result.is_nut_free).toBe(false);
    });

    it('should throw error when dish not found (404)', async () => {
      const mockError = {
        response: {
          status: 404,
          data: { detail: 'Dish not found' },
        },
      };
      vi.mocked(api.get).mockRejectedValue(mockError);

      await expect(dishService.getDishDetails('invalid-id')).rejects.toThrow();
      expect(api.get).toHaveBeenCalledWith('/dishes/invalid-id');
    });

    it('should throw error when API call fails', async () => {
      const mockError = new Error('Network error');
      vi.mocked(api.get).mockRejectedValue(mockError);

      await expect(dishService.getDishDetails('dish-123')).rejects.toThrow('Network error');
      expect(api.get).toHaveBeenCalledWith('/dishes/dish-123');
    });

    it('should throw error when user is not authenticated (401)', async () => {
      const mockError = {
        response: {
          status: 401,
          data: { detail: 'Not authenticated' },
        },
      };
      vi.mocked(api.get).mockRejectedValue(mockError);

      await expect(dishService.getDishDetails('dish-123')).rejects.toThrow();
    });
  });
});
