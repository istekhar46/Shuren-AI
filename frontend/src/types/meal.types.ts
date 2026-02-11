/**
 * Meal Type Definitions
 * 
 * These types define the structure of meal-related requests and responses
 * for the Shuren API. They align with the backend FastAPI endpoints.
 */

/**
 * Meal plan response
 * Returned by GET /meals/plan
 * Contains the user's nutritional targets and macro distribution
 */
export interface MealPlanResponse {
  id: string;
  meals_per_day: number;
  daily_calories_target: number;
  daily_calories_min: number;
  daily_calories_max: number;
  protein_grams_target: number;
  carbs_grams_target: number;
  fats_grams_target: number;
  protein_percentage: number;
  carbs_percentage: number;
  fats_percentage: number;
  plan_rationale: string;
  is_locked: boolean;
  created_at: string;
  updated_at: string;
}

/**
 * Meal schedule response
 * Returned by GET /meals/schedule
 * Contains list of scheduled meals
 */
export interface MealScheduleResponse {
  meals: MealScheduleItemResponse[];
}

/**
 * Individual meal schedule item
 * Represents a single scheduled meal with timing and notification settings
 */
export interface MealScheduleItemResponse {
  id: string;
  meal_number: number;
  meal_name: string;
  scheduled_time: string;
  notification_offset_minutes: number;
  earliest_time: string;
  latest_time: string;
  is_active: boolean;
}
