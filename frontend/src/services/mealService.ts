import api from './api';
import type { MealPlanResponse, MealScheduleResponse } from '../types/meal.types';
import type { TodayMealsResponse, NextMealResponse } from '../types/mealTemplate.types';

export const mealService = {
  /**
   * Get user's meal plan
   * @returns User's meal plan with nutritional targets, or null if not configured
   */
  async getMealPlan(): Promise<MealPlanResponse | null> {
    const response = await api.get<MealPlanResponse | null>('/meals/plan');
    return response.data;
  },

  /**
   * Update user's meal plan
   * @param updates - Fields to update in the meal plan
   * @returns Updated meal plan
   */
  async updateMealPlan(updates: Record<string, any>): Promise<MealPlanResponse> {
    const response = await api.patch<MealPlanResponse>('/meals/plan', updates);
    return response.data;
  },

  /**
   * Get user's meal schedule
   * @returns Meal schedule with all scheduled meals
   */
  async getMealSchedule(): Promise<MealScheduleResponse> {
    const response = await api.get<MealScheduleResponse>('/meals/schedule');
    return response.data;
  },

  /**
   * Update user's meal schedule
   * @param updates - Fields to update in the meal schedule
   * @returns Updated meal schedule
   */
  async updateMealSchedule(updates: Record<string, any>): Promise<MealScheduleResponse> {
    const response = await api.patch<MealScheduleResponse>('/meals/schedule', updates);
    return response.data;
  },

  /**
   * Get today's meals
   * @returns Today's meals with nutritional information
   */
  async getTodayMeals(): Promise<TodayMealsResponse> {
    const response = await api.get<TodayMealsResponse>('/meals/today');
    return response.data;
  },

  /**
   * Get next upcoming meal
   * @returns Next meal details with time until meal
   */
  async getNextMeal(): Promise<NextMealResponse> {
    const response = await api.get<NextMealResponse>('/meals/next');
    return response.data;
  },

  /**
   * Search for dishes by query
   * @param query - Search query string
   * @returns Array of matching dishes
   */
  async searchDishes(_query: string): Promise<any[]> {
    // TODO: Implement when backend endpoint is available
    // For now, return empty array to prevent build errors
    console.warn('searchDishes not yet implemented in backend');
    return [];
  },

  /**
   * Generate shopping list for date range
   * @param startDate - Start date (YYYY-MM-DD)
   * @param endDate - End date (YYYY-MM-DD)
   * @returns Shopping list with ingredients
   */
  async generateShoppingList(_startDate: string, _endDate: string): Promise<any> {
    // TODO: Implement when backend endpoint is available
    // For now, return empty shopping list to prevent build errors
    console.warn('generateShoppingList not yet implemented in backend');
    return {
      items: [],
      generatedAt: new Date().toISOString(),
    };
  },
};
