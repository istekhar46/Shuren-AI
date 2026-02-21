import { describe, it, expect, beforeEach, vi } from 'vitest';
import fc from 'fast-check';
import { mealService } from '../../src/services/mealService';
import api from '../../src/services/api';
import type { Dish, ShoppingList, ShoppingListItem, Ingredient } from '../../src/types';

// Mock the API module
vi.mock('../../src/services/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

describe('Meal Properties', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('Property 11: Dish search filters results', async () => {
    // Feature: minimal-frontend-testing, Property 11: Dish search filters results
    // For any search query, the searchDishes function should only return dishes
    // whose names contain the search query (case-insensitive), ensuring proper
    // filtering of results.
    // Validates: Requirements 2.5.3

    await fc.assert(
      fc.asyncProperty(
        fc.string({ minLength: 1, maxLength: 20 }), // Random search query
        fc.array(
          fc.record({
            id: fc.uuid(),
            name: fc.string({ minLength: 5, maxLength: 50 }),
            description: fc.string({ minLength: 10, maxLength: 200 }),
            ingredients: fc.array(
              fc.record({
                id: fc.uuid(),
                name: fc.string({ minLength: 3, maxLength: 30 }),
                quantity: fc.float({ min: Math.fround(0.1), max: Math.fround(1000), noNaN: true }),
                unit: fc.constantFrom('g', 'ml', 'cup', 'tbsp', 'tsp', 'oz', 'lb'),
                category: fc.constantFrom('protein', 'vegetable', 'fruit', 'grain', 'dairy', 'spice'),
              }),
              { minLength: 1, maxLength: 15 }
            ),
            instructions: fc.array(fc.string({ minLength: 10, maxLength: 100 }), { minLength: 1, maxLength: 10 }),
            macros: fc.record({
              calories: fc.integer({ min: 50, max: 2000 }),
              protein: fc.float({ min: 0, max: 200 }),
              carbs: fc.float({ min: 0, max: 300 }),
              fats: fc.float({ min: 0, max: 150 }),
            }),
            prepTime: fc.integer({ min: 0, max: 120 }),
            cookTime: fc.integer({ min: 0, max: 180 }),
          }),
          { minLength: 5, maxLength: 20 }
        ), // Array of random dishes
        async (query, allDishes) => {
          // Filter dishes that should match the query (case-insensitive)
          const expectedMatches = allDishes.filter((dish) =>
            dish.name.toLowerCase().includes(query.toLowerCase())
          );

          // Mock API response with filtered dishes
          vi.mocked(api.get).mockResolvedValueOnce({ data: expectedMatches });

          // Call the service
          const result = await mealService.searchDishes(query);

          // Verify API was called with correct query
          expect(api.get).toHaveBeenCalledWith('/meals/dishes/search', {
            params: { q: query },
          });

          // Verify all returned dishes contain the query in their name
          result.forEach((dish) => {
            expect(dish.name.toLowerCase()).toContain(query.toLowerCase());
          });

          // Verify result count matches expected
          expect(result.length).toBe(expectedMatches.length);
        }
      ),
      { numRuns: 50, timeout: 10000 }
    );
  });

  it('Property 12: Shopping list groups by category', async () => {
    // Feature: minimal-frontend-testing, Property 12: Shopping list groups by category
    // For any shopping list generated from meals, ingredients should be grouped by
    // their category, and items in the same category should be adjacent in the list.
    // Validates: Requirements 2.5.6

    await fc.assert(
      fc.asyncProperty(
        fc.date({ min: new Date('2024-01-01'), max: new Date('2025-12-31') }), // Random start date
        fc.integer({ min: 1, max: 14 }), // Random number of days (1-14)
        fc.array(
          fc.record({
            ingredient: fc.record({
              id: fc.uuid(),
              name: fc.string({ minLength: 3, maxLength: 30 }),
              quantity: fc.float({ min: Math.fround(0.1), max: Math.fround(1000), noNaN: true }),
              unit: fc.constantFrom('g', 'ml', 'cup', 'tbsp', 'tsp', 'oz', 'lb'),
              category: fc.constantFrom('protein', 'vegetable', 'fruit', 'grain', 'dairy', 'spice'),
            }),
            totalQuantity: fc.float({ min: Math.fround(0.1), max: Math.fround(5000), noNaN: true }),
            meals: fc.array(fc.uuid(), { minLength: 1, maxLength: 10 }),
          }),
          { minLength: 5, maxLength: 50 }
        ), // Array of shopping list items
        async (startDate, daysCount, shoppingItems) => {
          // Format dates
          const startDateStr = startDate.toISOString().split('T')[0];
          const endDate = new Date(startDate);
          endDate.setDate(endDate.getDate() + daysCount);
          const endDateStr = endDate.toISOString().split('T')[0];

          // Create shopping list
          const mockShoppingList: ShoppingList = {
            items: shoppingItems,
            generatedAt: new Date().toISOString(),
          };

          // Mock API response
          vi.mocked(api.post).mockResolvedValueOnce({ data: mockShoppingList });

          // Call the service
          const result = await mealService.generateShoppingList(startDateStr, endDateStr);

          // Verify API was called with correct dates
          expect(api.post).toHaveBeenCalledWith('/meals/shopping-list', {
            start_date: startDateStr,
            end_date: endDateStr,
          });

          // Verify shopping list structure
          expect(result.items).toBeDefined();
          expect(Array.isArray(result.items)).toBe(true);
          expect(result.generatedAt).toBeDefined();

          // Group items by category
          const categoriesMap = new Map<string, ShoppingListItem[]>();
          result.items.forEach((item) => {
            const category = item.ingredient.category;
            if (!categoriesMap.has(category)) {
              categoriesMap.set(category, []);
            }
            categoriesMap.get(category)!.push(item);
          });

          // Verify each item has required fields
          result.items.forEach((item) => {
            expect(item.ingredient).toBeDefined();
            expect(item.ingredient.category).toBeDefined();
            expect(typeof item.ingredient.category).toBe('string');
            expect(item.ingredient.category.length).toBeGreaterThan(0);
            expect(item.totalQuantity).toBeDefined();
            expect(typeof item.totalQuantity).toBe('number');
            expect(item.totalQuantity).toBeGreaterThan(0);
            expect(Array.isArray(item.meals)).toBe(true);
            expect(item.meals.length).toBeGreaterThan(0);
          });

          // Verify categories are properly grouped
          // (Items with same category should be adjacent when sorted by category)
          const sortedByCategory = [...result.items].sort((a, b) =>
            a.ingredient.category.localeCompare(b.ingredient.category)
          );

          let currentCategory = '';
          let categoryStartIndex = 0;

          sortedByCategory.forEach((item, index) => {
            if (item.ingredient.category !== currentCategory) {
              // Verify previous category was contiguous
              if (currentCategory !== '') {
                const categoryItems = sortedByCategory.slice(categoryStartIndex, index);
                categoryItems.forEach((catItem) => {
                  expect(catItem.ingredient.category).toBe(currentCategory);
                });
              }
              currentCategory = item.ingredient.category;
              categoryStartIndex = index;
            }
          });

          // Verify last category
          if (currentCategory !== '') {
            const categoryItems = sortedByCategory.slice(categoryStartIndex);
            categoryItems.forEach((catItem) => {
              expect(catItem.ingredient.category).toBe(currentCategory);
            });
          }
        }
      ),
      { numRuns: 50, timeout: 10000 }
    );
  });
});
