/**
 * Meal Template Type Definitions
 * 
 * These types define the structure of meal template-related requests and responses
 * for the Shuren API. They align with the backend FastAPI endpoints.
 */

import type { DishSummaryResponse } from './dish.types';

/**
 * Today's meals response
 * Returned by GET /meal-templates/today
 * Contains all meals for today with assigned dishes
 */
export interface TodayMealsResponse {
  date: string;
  day_of_week: number;
  day_name: string;
  meals: MealSlot[];
  total_calories: number;
  total_protein_g: number;
  total_carbs_g: number;
  total_fats_g: number;
}

/**
 * Meal slot definition
 * Represents a single meal with primary and alternative dishes
 */
export interface MealSlot {
  meal_name: string;
  scheduled_time: string;
  day_of_week: number;
  primary_dish: DishSummaryResponse;
  alternative_dishes: DishSummaryResponse[];
}

/**
 * Next meal response
 * Returned by GET /meal-templates/next
 * Contains the next upcoming meal with dishes
 */
export interface NextMealResponse {
  meal_name: string;
  scheduled_time: string;
  time_until_meal_minutes: number;
  primary_dish: DishSummaryResponse;
  alternative_dishes: DishSummaryResponse[];
}

/**
 * Meal template response
 * Returned by GET /meal-templates/template
 * Contains complete meal template for a week
 */
export interface MealTemplateResponse {
  id: string;
  week_number: number;
  is_active: boolean;
  days: DayMeals[];
  created_at: string;
  updated_at: string;
}

/**
 * Day meals definition
 * Represents all meals for a single day
 */
export interface DayMeals {
  day_of_week: number;
  day_name: string;
  meals: MealSlot[];
}

/**
 * Template regenerate request
 * Sent to POST /meal-templates/template/regenerate
 * Used to regenerate meal template with new preferences
 */
export interface TemplateRegenerateRequest {
  preferences?: string;
  week_number?: number;
}
