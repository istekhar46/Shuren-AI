/**
 * Dish Type Definitions
 * 
 * These types define the structure of dish-related requests and responses
 * for the Shuren API. They align with the backend FastAPI endpoints.
 */

/**
 * Dish search filters
 * Used as query parameters for GET /dishes/search
 * Allows filtering dishes by various criteria
 */
export interface DishSearchFilters {
  meal_type?: string;
  diet_type?: string;
  max_prep_time?: number;
  max_calories?: number;
  limit?: number;
  offset?: number;
}

/**
 * Dish summary response
 * Returned by GET /dishes/ and GET /dishes/search
 * Contains basic dish information without full details
 */
export interface DishSummaryResponse {
  id: string;
  name: string;
  name_hindi: string;
  meal_type: string;
  cuisine_type: string;
  calories: number;
  protein_g: number;
  carbs_g: number;
  fats_g: number;
  prep_time_minutes: number;
  cook_time_minutes: number;
  total_time_minutes: number;
  difficulty_level: string;
  is_vegetarian: boolean;
  is_vegan: boolean;
}

/**
 * Complete dish response
 * Returned by GET /dishes/{dish_id}
 * Extends DishSummaryResponse with full details and ingredients
 */
export interface DishResponse extends DishSummaryResponse {
  description: string;
  dish_category: string;
  serving_size_g: number;
  fiber_g: number;
  is_gluten_free: boolean;
  is_dairy_free: boolean;
  is_nut_free: boolean;
  contains_allergens: string[];
  is_active: boolean;
  popularity_score: number;
  ingredients: DishIngredient[];
}

/**
 * Dish ingredient definition
 * Represents an ingredient used in a dish
 */
export interface DishIngredient {
  id: string;
  ingredient_id: string;
  ingredient_name: string;
  ingredient_name_hindi: string;
  quantity: number;
  unit: string;
  is_optional: boolean;
  preparation_notes: string | null;
}
