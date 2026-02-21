import api from './api';
import type {
  TodayMealsResponse,
  NextMealResponse,
  MealTemplateResponse,
  TemplateRegenerateRequest,
} from '../types/api';

/**
 * Meal Template Service
 * 
 * Handles meal template operations including retrieving today's meals,
 * next meal, complete meal templates, and regenerating templates with
 * new dish assignments. All operations require authentication.
 */
export const mealTemplateService = {
  /**
   * Get today's meals with assigned dishes
   * 
   * Retrieves all meals scheduled for today with their assigned primary
   * and alternative dishes, including nutritional totals for the day.
   * 
   * @returns {Promise<TodayMealsResponse>} Today's meal plan with dishes and nutritional totals
   * @throws {Error} If the request fails or user is not authenticated
   * 
   * @example
   * const todayMeals = await mealTemplateService.getTodayMealsWithDishes();
   * console.log(todayMeals.meals); // Array of meal slots with dishes
   * console.log(todayMeals.total_calories); // Total calories for the day
   */
  async getTodayMealsWithDishes(): Promise<TodayMealsResponse> {
    const response = await api.get<TodayMealsResponse>('/meal-templates/today');
    return response.data;
  },

  /**
   * Get next upcoming meal with dishes
   * 
   * Retrieves the next scheduled meal with its assigned primary and
   * alternative dishes, including time until the meal.
   * 
   * @returns {Promise<NextMealResponse>} Next meal details with dishes and timing
   * @throws {Error} If the request fails or user is not authenticated
   * 
   * @example
   * const nextMeal = await mealTemplateService.getNextMealWithDishes();
   * console.log(nextMeal.meal_name); // 'Lunch'
   * console.log(nextMeal.time_until_meal_minutes); // 45
   * console.log(nextMeal.primary_dish); // Dish details
   */
  async getNextMealWithDishes(): Promise<NextMealResponse> {
    const response = await api.get<NextMealResponse>('/meal-templates/next');
    return response.data;
  },

  /**
   * Get meal template for a specific week
   * 
   * Retrieves the complete meal template for a week, including all days
   * and meals with assigned dishes. If no week number is specified,
   * returns the current active template.
   * 
   * @param {number} [weekNumber] - Week number (1-4), optional
   * @returns {Promise<MealTemplateResponse>} Complete meal template with all days and meals
   * @throws {Error} If the request fails or user is not authenticated
   * 
   * @example
   * // Get current week's template
   * const template = await mealTemplateService.getMealTemplate();
   * 
   * // Get specific week's template
   * const week2 = await mealTemplateService.getMealTemplate(2);
   * console.log(week2.days); // Array of 7 days with meals
   */
  async getMealTemplate(weekNumber?: number): Promise<MealTemplateResponse> {
    const response = await api.get<MealTemplateResponse>('/meal-templates/template', {
      params: weekNumber ? { week_number: weekNumber } : {},
    });
    return response.data;
  },

  /**
   * Regenerate meal template with new dishes
   * 
   * Generates a new meal template with different dish assignments based
   * on optional preferences. This creates a fresh template while maintaining
   * the meal structure and nutritional targets.
   * 
   * @param {string} [preferences] - Optional preferences for dish selection (e.g., 'more variety', 'quick meals')
   * @param {number} [weekNumber] - Optional week number to regenerate (1-4)
   * @returns {Promise<MealTemplateResponse>} Newly generated meal template
   * @throws {Error} If the request fails or user is not authenticated
   * 
   * @example
   * // Regenerate with preferences
   * const newTemplate = await mealTemplateService.regenerateMealTemplate(
   *   'I want more variety and quick meals',
   *   1
   * );
   * 
   * // Regenerate without preferences
   * const refreshed = await mealTemplateService.regenerateMealTemplate();
   */
  async regenerateMealTemplate(
    preferences?: string,
    weekNumber?: number
  ): Promise<MealTemplateResponse> {
    const payload: TemplateRegenerateRequest = {};
    if (preferences) payload.preferences = preferences;
    if (weekNumber) payload.week_number = weekNumber;

    const response = await api.post<MealTemplateResponse>(
      '/meal-templates/template/regenerate',
      payload
    );
    return response.data;
  },
};
