/**
 * Shopping List Type Definitions
 * 
 * These types define the structure of shopping list-related responses
 * for the Shuren API. They align with the backend FastAPI endpoints.
 */

/**
 * Shopping list response
 * Returned by GET /shopping-list/
 * Contains ingredients grouped by category for a specified number of weeks
 */
export interface ShoppingListResponse {
  week_number: number;
  start_date: string;
  end_date: string;
  categories: IngredientCategory[];
  total_items: number;
}

/**
 * Ingredient category grouping
 * Groups ingredients by category (e.g., vegetables, grains, proteins)
 */
export interface IngredientCategory {
  category: string;
  ingredients: ShoppingListIngredient[];
}

/**
 * Shopping list ingredient
 * Represents a single ingredient with aggregated quantities
 */
export interface ShoppingListIngredient {
  ingredient_id: string;
  name: string;
  name_hindi: string;
  category: string;
  total_quantity: number;
  unit: string;
  is_optional: boolean;
  used_in_dishes: string[];
}
