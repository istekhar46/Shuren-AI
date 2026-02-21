/**
 * Response Validation Utilities
 * 
 * Provides Zod schemas for validating API response data.
 * These schemas ensure type safety at runtime by validating
 * responses from the backend match expected structures.
 */

import { z } from 'zod';

// ============================================================================
// Authentication Schemas
// ============================================================================

/**
 * Schema for token response from authentication endpoints
 * Used by POST /auth/login and POST /auth/register
 */
export const TokenResponseSchema = z.object({
  access_token: z.string().min(1),
  token_type: z.string(),
  user_id: z.string().uuid(),
});

/**
 * Schema for user information response
 * Used by GET /auth/me
 */
export const UserResponseSchema = z.object({
  id: z.string().uuid(),
  email: z.string().email(),
  full_name: z.string(),
  oauth_provider: z.string().nullable(),
  is_active: z.boolean(),
  created_at: z.string(),
});

// ============================================================================
// Onboarding Schemas
// ============================================================================

/**
 * Schema for onboarding state response
 * Used by GET /onboarding/state
 */
export const OnboardingStateResponseSchema = z.object({
  id: z.string().uuid(),
  user_id: z.string().uuid(),
  current_step: z.number().int().min(0),
  is_complete: z.boolean(),
  step_data: z.record(z.string(), z.any()),
});

/**
 * Schema for onboarding step response
 * Used by POST /onboarding/step
 */
export const OnboardingStepResponseSchema = z.object({
  current_step: z.number().int().min(0),
  is_complete: z.boolean(),
  message: z.string(),
});

// ============================================================================
// Profile Schemas
// ============================================================================

/**
 * Schema for fitness goal
 */
export const FitnessGoalSchema = z.object({
  id: z.string().uuid(),
  goal_type: z.string(),
  target_value: z.number().nullable(),
  target_date: z.string().nullable(),
  priority: z.number().int(),
});

/**
 * Schema for physical constraint
 */
export const PhysicalConstraintSchema = z.object({
  id: z.string().uuid(),
  constraint_type: z.string(),
  description: z.string(),
  severity: z.string(),
});

/**
 * Schema for dietary preferences
 */
export const DietaryPreferencesSchema = z.object({
  id: z.string().uuid(),
  diet_type: z.string(),
  allergies: z.array(z.string()),
  dislikes: z.array(z.string()),
  preferences: z.record(z.string(), z.any()),
});

/**
 * Schema for meal plan
 */
export const MealPlanSchema = z.object({
  id: z.string().uuid(),
  meals_per_day: z.number().int().positive(),
  daily_calories_target: z.number().positive(),
  daily_calories_min: z.number().positive(),
  daily_calories_max: z.number().positive(),
  protein_grams_target: z.number().nonnegative(),
  carbs_grams_target: z.number().nonnegative(),
  fats_grams_target: z.number().nonnegative(),
  protein_percentage: z.number().min(0).max(100),
  carbs_percentage: z.number().min(0).max(100),
  fats_percentage: z.number().min(0).max(100),
  plan_rationale: z.string(),
  is_locked: z.boolean(),
  created_at: z.string(),
  updated_at: z.string(),
});

/**
 * Schema for meal schedule
 */
export const MealScheduleSchema = z.object({
  id: z.string().uuid(),
  meal_number: z.number().int().positive(),
  meal_name: z.string(),
  scheduled_time: z.string(),
  notification_offset_minutes: z.number().int(),
  earliest_time: z.string(),
  latest_time: z.string(),
  is_active: z.boolean(),
});

/**
 * Schema for workout schedule
 */
export const WorkoutScheduleSchema = z.object({
  id: z.string().uuid(),
  day_of_week: z.number().int().min(0).max(6),
  scheduled_time: z.string(),
  enable_notifications: z.boolean(),
});

/**
 * Schema for hydration preferences
 */
export const HydrationPreferencesSchema = z.object({
  id: z.string().uuid(),
  daily_water_target_ml: z.number().int().positive(),
  reminder_interval_minutes: z.number().int().positive(),
  enable_reminders: z.boolean(),
});

/**
 * Schema for lifestyle baseline
 */
export const LifestyleBaselineSchema = z.object({
  id: z.string().uuid(),
  energy_level: z.number().int().min(1).max(10),
  stress_level: z.number().int().min(1).max(10),
  sleep_hours: z.number().nonnegative(),
  notes: z.string().nullable(),
});

/**
 * Schema for user profile response
 * Used by GET /profiles/me and PATCH /profiles/me
 */
export const UserProfileResponseSchema = z.object({
  id: z.string().uuid(),
  user_id: z.string().uuid(),
  is_locked: z.boolean(),
  fitness_level: z.string(),
  fitness_goals: z.array(FitnessGoalSchema),
  physical_constraints: z.array(PhysicalConstraintSchema),
  dietary_preferences: DietaryPreferencesSchema.nullable(),
  meal_plan: MealPlanSchema.nullable(),
  meal_schedules: z.array(MealScheduleSchema),
  workout_schedules: z.array(WorkoutScheduleSchema),
  hydration_preferences: HydrationPreferencesSchema.nullable(),
  lifestyle_baseline: LifestyleBaselineSchema.nullable(),
});

// ============================================================================
// Chat Schemas
// ============================================================================

/**
 * Schema for individual message in chat history
 */
export const MessageDictSchema = z.object({
  role: z.string(),
  content: z.string(),
  agent_type: z.string().nullable(),
  created_at: z.string(),
});

/**
 * Schema for chat response
 * Used by POST /chat/chat
 */
export const ChatResponseSchema = z.object({
  response: z.string(),
  agent_type: z.string(),
  conversation_id: z.string().uuid(),
  tools_used: z.array(z.string()),
});

/**
 * Schema for chat history response
 * Used by GET /chat/history
 */
export const ChatHistoryResponseSchema = z.object({
  messages: z.array(MessageDictSchema),
  total: z.number().int().nonnegative(),
});

// ============================================================================
// Meal Schemas
// ============================================================================

/**
 * Schema for meal plan response
 * Used by GET /meals/plan
 */
export const MealPlanResponseSchema = z.object({
  id: z.string().uuid(),
  meals_per_day: z.number().int().positive(),
  daily_calories_target: z.number().positive(),
  daily_calories_min: z.number().positive(),
  daily_calories_max: z.number().positive(),
  protein_grams_target: z.number().nonnegative(),
  carbs_grams_target: z.number().nonnegative(),
  fats_grams_target: z.number().nonnegative(),
  protein_percentage: z.number().min(0).max(100),
  carbs_percentage: z.number().min(0).max(100),
  fats_percentage: z.number().min(0).max(100),
  plan_rationale: z.string(),
  is_locked: z.boolean(),
  created_at: z.string(),
  updated_at: z.string(),
});

/**
 * Schema for meal schedule item
 */
export const MealScheduleItemResponseSchema = z.object({
  id: z.string().uuid(),
  meal_number: z.number().int().positive(),
  meal_name: z.string(),
  scheduled_time: z.string(),
  notification_offset_minutes: z.number().int(),
  earliest_time: z.string(),
  latest_time: z.string(),
  is_active: z.boolean(),
});

/**
 * Schema for meal schedule response
 * Used by GET /meals/schedule
 */
export const MealScheduleResponseSchema = z.object({
  meals: z.array(MealScheduleItemResponseSchema),
});

// ============================================================================
// Dish Schemas
// ============================================================================

/**
 * Schema for dish ingredient
 */
export const DishIngredientSchema = z.object({
  id: z.string().uuid(),
  ingredient_id: z.string().uuid(),
  ingredient_name: z.string(),
  ingredient_name_hindi: z.string(),
  quantity: z.number().positive(),
  unit: z.string(),
  is_optional: z.boolean(),
  preparation_notes: z.string().nullable(),
});

/**
 * Schema for dish summary response
 * Used by GET /dishes/ and GET /dishes/search
 */
export const DishSummaryResponseSchema = z.object({
  id: z.string().uuid(),
  name: z.string(),
  name_hindi: z.string(),
  meal_type: z.string(),
  cuisine_type: z.string(),
  calories: z.number().nonnegative(),
  protein_g: z.number().nonnegative(),
  carbs_g: z.number().nonnegative(),
  fats_g: z.number().nonnegative(),
  prep_time_minutes: z.number().int().nonnegative(),
  cook_time_minutes: z.number().int().nonnegative(),
  total_time_minutes: z.number().int().nonnegative(),
  difficulty_level: z.string(),
  is_vegetarian: z.boolean(),
  is_vegan: z.boolean(),
});

/**
 * Schema for complete dish response
 * Used by GET /dishes/{dish_id}
 */
export const DishResponseSchema = DishSummaryResponseSchema.extend({
  description: z.string(),
  dish_category: z.string(),
  serving_size_g: z.number().positive(),
  fiber_g: z.number().nonnegative(),
  is_gluten_free: z.boolean(),
  is_dairy_free: z.boolean(),
  is_nut_free: z.boolean(),
  contains_allergens: z.array(z.string()),
  is_active: z.boolean(),
  popularity_score: z.number().nonnegative(),
  ingredients: z.array(DishIngredientSchema),
});

// ============================================================================
// Meal Template Schemas
// ============================================================================

/**
 * Schema for meal slot
 */
export const MealSlotSchema = z.object({
  meal_name: z.string(),
  scheduled_time: z.string(),
  day_of_week: z.number().int().min(0).max(6),
  primary_dish: DishSummaryResponseSchema,
  alternative_dishes: z.array(DishSummaryResponseSchema),
});

/**
 * Schema for today's meals response
 * Used by GET /meal-templates/today
 */
export const TodayMealsResponseSchema = z.object({
  date: z.string(),
  day_of_week: z.number().int().min(0).max(6),
  day_name: z.string(),
  meals: z.array(MealSlotSchema),
  total_calories: z.number().nonnegative(),
  total_protein_g: z.number().nonnegative(),
  total_carbs_g: z.number().nonnegative(),
  total_fats_g: z.number().nonnegative(),
});

/**
 * Schema for next meal response
 * Used by GET /meal-templates/next
 */
export const NextMealResponseSchema = z.object({
  meal_name: z.string(),
  scheduled_time: z.string(),
  time_until_meal_minutes: z.number().int(),
  primary_dish: DishSummaryResponseSchema,
  alternative_dishes: z.array(DishSummaryResponseSchema),
});

/**
 * Schema for day meals
 */
export const DayMealsSchema = z.object({
  day_of_week: z.number().int().min(0).max(6),
  day_name: z.string(),
  meals: z.array(MealSlotSchema),
});

/**
 * Schema for meal template response
 * Used by GET /meal-templates/template
 */
export const MealTemplateResponseSchema = z.object({
  id: z.string().uuid(),
  week_number: z.number().int().positive(),
  is_active: z.boolean(),
  days: z.array(DayMealsSchema),
  created_at: z.string(),
  updated_at: z.string(),
});

// ============================================================================
// Shopping List Schemas
// ============================================================================

/**
 * Schema for shopping list ingredient
 */
export const ShoppingListIngredientSchema = z.object({
  ingredient_id: z.string().uuid(),
  name: z.string(),
  name_hindi: z.string(),
  category: z.string(),
  total_quantity: z.number().positive(),
  unit: z.string(),
  is_optional: z.boolean(),
  used_in_dishes: z.array(z.string()),
});

/**
 * Schema for ingredient category
 */
export const IngredientCategorySchema = z.object({
  category: z.string(),
  ingredients: z.array(ShoppingListIngredientSchema),
});

/**
 * Schema for shopping list response
 * Used by GET /shopping-list/
 */
export const ShoppingListResponseSchema = z.object({
  week_number: z.number().int().positive(),
  start_date: z.string(),
  end_date: z.string(),
  categories: z.array(IngredientCategorySchema),
  total_items: z.number().int().nonnegative(),
});

// ============================================================================
// Workout Schemas
// ============================================================================

/**
 * Schema for exercise library entry
 */
export const ExerciseLibrarySchema = z.object({
  id: z.string().uuid(),
  exercise_name: z.string(),
  exercise_type: z.string(),
  primary_muscle_group: z.string(),
  gif_url: z.string(),
});

/**
 * Schema for workout exercise
 */
export const WorkoutExerciseSchema = z.object({
  id: z.string().uuid(),
  exercise_order: z.number().int().positive(),
  sets: z.number().int().positive(),
  reps_target: z.number().int().positive(),
  weight_kg: z.number().nonnegative(),
  rest_seconds: z.number().int().nonnegative(),
  exercise: ExerciseLibrarySchema,
});

/**
 * Schema for workout day response
 * Used by GET /workouts/plan/day/{day_number}
 */
export const WorkoutDayResponseSchema = z.object({
  id: z.string().uuid(),
  day_number: z.number().int().positive(),
  day_name: z.string(),
  muscle_groups: z.array(z.string()),
  workout_type: z.string(),
  description: z.string(),
  estimated_duration_minutes: z.number().int().positive(),
  exercises: z.array(WorkoutExerciseSchema),
});

/**
 * Schema for workout plan response
 * Used by GET /workouts/plan
 */
export const WorkoutPlanResponseSchema = z.object({
  id: z.string().uuid(),
  plan_name: z.string(),
  plan_description: z.string(),
  duration_weeks: z.number().int().positive(),
  days_per_week: z.number().int().min(1).max(7),
  plan_rationale: z.string(),
  is_locked: z.boolean(),
  workout_days: z.array(WorkoutDayResponseSchema),
  created_at: z.string(),
  updated_at: z.string(),
});

/**
 * Schema for workout schedule response
 * Used by GET /workouts/schedule
 */
export const WorkoutScheduleResponseSchema = z.object({
  id: z.string().uuid(),
  day_of_week: z.number().int().min(0).max(6),
  scheduled_time: z.string(),
  enable_notifications: z.boolean(),
});

// ============================================================================
// Voice Session Schemas
// ============================================================================

/**
 * Schema for voice session response
 * Used by POST /voice-sessions/start
 */
export const VoiceSessionResponseSchema = z.object({
  room_name: z.string(),
  token: z.string(),
  livekit_url: z.string(),
  agent_type: z.string(),
  expires_at: z.string(),
});

/**
 * Schema for voice session status
 * Used by GET /voice-sessions/{room_name}/status
 */
export const VoiceSessionStatusSchema = z.object({
  room_name: z.string(),
  active: z.boolean(),
  participants: z.number().int().nonnegative(),
  agent_connected: z.boolean(),
  created_at: z.string().nullable(),
});

/**
 * Schema for session summary
 */
export const SessionSummarySchema = z.object({
  room_name: z.string(),
  agent_type: z.string(),
  participants: z.number().int().nonnegative(),
  created_at: z.string().nullable(),
});

/**
 * Schema for active sessions response
 * Used by GET /voice-sessions/active
 */
export const ActiveSessionsResponseSchema = z.object({
  sessions: z.array(SessionSummarySchema),
});

// ============================================================================
// Validation Helper Functions
// ============================================================================

/**
 * Validate response data against a Zod schema
 * @param schema - Zod schema to validate against
 * @param data - Data to validate
 * @returns Validated and typed data
 * @throws ZodError if validation fails
 */
export function validateResponse<T>(schema: z.ZodSchema<T>, data: unknown): T {
  return schema.parse(data);
}

/**
 * Safely validate response data against a Zod schema
 * @param schema - Zod schema to validate against
 * @param data - Data to validate
 * @returns Success result with data or error result with issues
 */
export function safeValidateResponse<T>(
  schema: z.ZodSchema<T>,
  data: unknown
): { success: true; data: T } | { success: false; error: z.ZodError } {
  const result = schema.safeParse(data);
  if (result.success) {
    return { success: true, data: result.data };
  }
  return { success: false, error: result.error };
}
