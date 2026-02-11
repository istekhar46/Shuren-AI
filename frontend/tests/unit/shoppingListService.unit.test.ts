import { describe, it, expect, vi, beforeEach } from 'vitest';
import { shoppingListService } from '../../src/services/shoppingListService';
import api from '../../src/services/api';
import type { ShoppingListResponse } from '../../src/types/api';

// Mock the api module
vi.mock('../../src/services/api');

describe('shoppingListService Unit Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('getShoppingList', () => {
    it('should call GET /shopping-list/ with default weeks parameter', async () => {
      const mockShoppingList: ShoppingListResponse = {
        week_number: 1,
        start_date: '2024-02-10',
        end_date: '2024-02-17',
        categories: [
          {
            category: 'Vegetables',
            ingredients: [
              {
                ingredient_id: 'ing-1',
                name: 'Tomatoes',
                name_hindi: 'टमाटर',
                category: 'Vegetables',
                total_quantity: 500,
                unit: 'g',
                is_optional: false,
                used_in_dishes: ['Salad', 'Curry'],
              },
            ],
          },
        ],
        total_items: 1,
      };

      vi.mocked(api.get).mockResolvedValue({
        data: mockShoppingList,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      });

      const result = await shoppingListService.getShoppingList();

      expect(api.get).toHaveBeenCalledWith('/shopping-list/', {
        params: { weeks: 1 },
      });
      expect(api.get).toHaveBeenCalledTimes(1);
      expect(result).toEqual(mockShoppingList);
      expect(result.total_items).toBe(1);
    });

    it('should call GET /shopping-list/ with specified weeks parameter', async () => {
      const mockShoppingList: ShoppingListResponse = {
        week_number: 1,
        start_date: '2024-02-10',
        end_date: '2024-02-24',
        categories: [
          {
            category: 'Proteins',
            ingredients: [
              {
                ingredient_id: 'ing-2',
                name: 'Chicken Breast',
                name_hindi: 'चिकन ब्रेस्ट',
                category: 'Proteins',
                total_quantity: 1000,
                unit: 'g',
                is_optional: false,
                used_in_dishes: ['Grilled Chicken', 'Chicken Salad'],
              },
            ],
          },
        ],
        total_items: 1,
      };

      vi.mocked(api.get).mockResolvedValue({
        data: mockShoppingList,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      });

      const result = await shoppingListService.getShoppingList(2);

      expect(api.get).toHaveBeenCalledWith('/shopping-list/', {
        params: { weeks: 2 },
      });
      expect(result.start_date).toBe('2024-02-10');
      expect(result.end_date).toBe('2024-02-24');
    });

    it('should return shopping list with multiple categories', async () => {
      const mockShoppingList: ShoppingListResponse = {
        week_number: 1,
        start_date: '2024-02-10',
        end_date: '2024-02-17',
        categories: [
          {
            category: 'Vegetables',
            ingredients: [
              {
                ingredient_id: 'ing-1',
                name: 'Tomatoes',
                name_hindi: 'टमाटर',
                category: 'Vegetables',
                total_quantity: 500,
                unit: 'g',
                is_optional: false,
                used_in_dishes: ['Salad'],
              },
              {
                ingredient_id: 'ing-2',
                name: 'Onions',
                name_hindi: 'प्याज',
                category: 'Vegetables',
                total_quantity: 300,
                unit: 'g',
                is_optional: false,
                used_in_dishes: ['Curry', 'Stir Fry'],
              },
            ],
          },
          {
            category: 'Grains',
            ingredients: [
              {
                ingredient_id: 'ing-3',
                name: 'Rice',
                name_hindi: 'चावल',
                category: 'Grains',
                total_quantity: 1000,
                unit: 'g',
                is_optional: false,
                used_in_dishes: ['Fried Rice', 'Biryani'],
              },
            ],
          },
        ],
        total_items: 3,
      };

      vi.mocked(api.get).mockResolvedValue({
        data: mockShoppingList,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      });

      const result = await shoppingListService.getShoppingList();

      expect(result.categories).toHaveLength(2);
      expect(result.categories[0].category).toBe('Vegetables');
      expect(result.categories[0].ingredients).toHaveLength(2);
      expect(result.categories[1].category).toBe('Grains');
      expect(result.total_items).toBe(3);
    });

    it('should return empty shopping list when no ingredients needed', async () => {
      const mockShoppingList: ShoppingListResponse = {
        week_number: 1,
        start_date: '2024-02-10',
        end_date: '2024-02-17',
        categories: [],
        total_items: 0,
      };

      vi.mocked(api.get).mockResolvedValue({
        data: mockShoppingList,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      });

      const result = await shoppingListService.getShoppingList();

      expect(result.categories).toEqual([]);
      expect(result.total_items).toBe(0);
    });

    it('should handle optional ingredients', async () => {
      const mockShoppingList: ShoppingListResponse = {
        week_number: 1,
        start_date: '2024-02-10',
        end_date: '2024-02-17',
        categories: [
          {
            category: 'Spices',
            ingredients: [
              {
                ingredient_id: 'ing-4',
                name: 'Coriander',
                name_hindi: 'धनिया',
                category: 'Spices',
                total_quantity: 50,
                unit: 'g',
                is_optional: true,
                used_in_dishes: ['Curry'],
              },
            ],
          },
        ],
        total_items: 1,
      };

      vi.mocked(api.get).mockResolvedValue({
        data: mockShoppingList,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      });

      const result = await shoppingListService.getShoppingList();

      expect(result.categories[0].ingredients[0].is_optional).toBe(true);
    });

    it('should throw error when API call fails', async () => {
      const mockError = new Error('Network error');
      vi.mocked(api.get).mockRejectedValue(mockError);

      await expect(shoppingListService.getShoppingList()).rejects.toThrow('Network error');
      expect(api.get).toHaveBeenCalledWith('/shopping-list/', {
        params: { weeks: 1 },
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

      await expect(shoppingListService.getShoppingList()).rejects.toThrow();
    });

    it('should throw error when meal template not found (404)', async () => {
      const mockError = {
        response: {
          status: 404,
          data: { detail: 'Meal template not found' },
        },
      };
      vi.mocked(api.get).mockRejectedValue(mockError);

      await expect(shoppingListService.getShoppingList()).rejects.toThrow();
    });

    it('should throw error when validation fails (422)', async () => {
      const mockError = {
        response: {
          status: 422,
          data: { detail: 'Invalid weeks parameter' },
        },
      };
      vi.mocked(api.get).mockRejectedValue(mockError);

      await expect(shoppingListService.getShoppingList(-1)).rejects.toThrow();
    });

    it('should handle large shopping lists with many items', async () => {
      const mockShoppingList: ShoppingListResponse = {
        week_number: 1,
        start_date: '2024-02-10',
        end_date: '2024-03-10',
        categories: Array(10)
          .fill(null)
          .map((_, i) => ({
            category: `Category ${i}`,
            ingredients: Array(5)
              .fill(null)
              .map((_, j) => ({
                ingredient_id: `ing-${i}-${j}`,
                name: `Ingredient ${i}-${j}`,
                name_hindi: `सामग्री ${i}-${j}`,
                category: `Category ${i}`,
                total_quantity: 100 * (j + 1),
                unit: 'g',
                is_optional: false,
                used_in_dishes: ['Dish 1', 'Dish 2'],
              })),
          })),
        total_items: 50,
      };

      vi.mocked(api.get).mockResolvedValue({
        data: mockShoppingList,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      });

      const result = await shoppingListService.getShoppingList(4);

      expect(result.categories).toHaveLength(10);
      expect(result.total_items).toBe(50);
      expect(api.get).toHaveBeenCalledWith('/shopping-list/', {
        params: { weeks: 4 },
      });
    });
  });
});
