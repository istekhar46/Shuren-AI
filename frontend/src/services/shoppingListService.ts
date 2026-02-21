import api from './api';
import type { ShoppingListResponse } from '../types/api';

/**
 * Shopping List Service
 * 
 * Handles shopping list generation based on meal templates.
 * Aggregates ingredients from meal plans and organizes them by category.
 * All operations require authentication.
 */
export const shoppingListService = {
  /**
   * Get shopping list for specified number of weeks
   * 
   * Generates a shopping list by aggregating all ingredients needed
   * for the meal templates over the specified number of weeks.
   * Ingredients are organized by category and quantities are totaled.
   * 
   * @param {number} [weeks=1] - Number of weeks to generate shopping list for (default: 1)
   * @returns {Promise<ShoppingListResponse>} Shopping list with categorized ingredients
   * @throws {Error} If the request fails or user is not authenticated
   * 
   * @example
   * // Get shopping list for 1 week
   * const list = await shoppingListService.getShoppingList();
   * console.log(list.categories); // Array of ingredient categories
   * console.log(list.total_items); // Total number of unique ingredients
   * 
   * @example
   * // Get shopping list for 2 weeks
   * const twoWeekList = await shoppingListService.getShoppingList(2);
   * console.log(twoWeekList.start_date); // '2024-02-10'
   * console.log(twoWeekList.end_date); // '2024-02-24'
   */
  async getShoppingList(weeks: number = 1): Promise<ShoppingListResponse> {
    const response = await api.get<ShoppingListResponse>('/shopping-list/', {
      params: { weeks },
    });
    return response.data;
  },
};
