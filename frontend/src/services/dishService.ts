import api from './api';
import type { DishSummaryResponse, DishResponse, DishSearchFilters } from '../types/api';

/**
 * Dish Service
 * 
 * Handles dish-related operations including listing, searching, and retrieving
 * detailed dish information with ingredients and nutritional data.
 * All operations require authentication.
 */
export const dishService = {
  /**
   * List dishes with optional filters
   * 
   * Retrieves a list of dishes from the database with optional filtering
   * by meal type, diet type, and other criteria.
   * 
   * @param {DishSearchFilters} [filters] - Optional search filters
   * @returns {Promise<DishSummaryResponse[]>} Array of dish summaries
   * @throws {Error} If the request fails or user is not authenticated
   * 
   * @example
   * const dishes = await dishService.listDishes({ meal_type: 'breakfast', limit: 10 });
   * console.log(dishes); // Array of breakfast dishes
   */
  async listDishes(filters?: DishSearchFilters): Promise<DishSummaryResponse[]> {
    const response = await api.get<DishSummaryResponse[]>('/dishes/', {
      params: filters,
    });
    return response.data;
  },

  /**
   * Search dishes with advanced filters
   * 
   * Performs an advanced search for dishes with filters including
   * prep time, calories, meal type, diet type, and more.
   * 
   * @param {DishSearchFilters} filters - Search filters including prep time and calories
   * @returns {Promise<DishSummaryResponse[]>} Array of dish summaries matching criteria
   * @throws {Error} If the request fails or user is not authenticated
   * 
   * @example
   * const quickMeals = await dishService.searchDishes({
   *   max_prep_time: 30,
   *   max_calories: 500,
   *   diet_type: 'vegetarian'
   * });
   */
  async searchDishes(filters: DishSearchFilters): Promise<DishSummaryResponse[]> {
    const response = await api.get<DishSummaryResponse[]>('/dishes/search', {
      params: filters,
    });
    return response.data;
  },

  /**
   * Get detailed dish information with ingredients
   * 
   * Retrieves complete dish details including ingredients, nutritional
   * information, preparation instructions, and allergen information.
   * 
   * @param {string} dishId - Dish UUID
   * @returns {Promise<DishResponse>} Complete dish details with ingredients
   * @throws {Error} If the request fails, dish not found, or user is not authenticated
   * 
   * @example
   * const dish = await dishService.getDishDetails('dish-uuid-123');
   * console.log(dish.name); // 'Grilled Chicken Salad'
   * console.log(dish.ingredients); // Array of ingredients with quantities
   */
  async getDishDetails(dishId: string): Promise<DishResponse> {
    const response = await api.get<DishResponse>(`/dishes/${dishId}`);
    return response.data;
  },
};
