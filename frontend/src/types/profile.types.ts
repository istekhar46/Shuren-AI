/**
 * Profile Type Definitions
 * 
 * These types define the structure of profile-related requests and responses
 * for the Shuren API. They align with the backend FastAPI endpoints.
 */

/**
 * Profile update request payload
 * Sent to PATCH /profiles/me
 * Used to update user profile fields with a reason
 */
export interface ProfileUpdateRequest {
  reason: string;
  updates: Record<string, any>;
}

/**
 * User profile response
 * Returned by GET /profiles/me
 * Contains complete user profile with all preferences and plans
 */
export interface UserProfileResponse {
  id: string;
  user_id: string;
  is_locked: boolean;
  fitness_level: string;
  fitness_goals: FitnessGoal[];
  physical_constraints: PhysicalConstraint[];
  dietary_preferences: DietaryPreferences | null;
  meal_plan: MealPlan | null;
  meal_schedules: MealSchedule[];
  workout_schedules: WorkoutSchedule[];
  hydration_preferences: HydrationPreferences | null;
  lifestyle_baseline: LifestyleBaseline | null;
}

/**
 * Fitness goal definition
 */
export interface FitnessGoal {
  id: string;
  goal_type: string;
  target_unit:string;
  target_value: number | null;
  target_date: string | null;
  priority: number;
  is_active:boolean;
}

/**
 * Physical constraint definition
 */
export interface PhysicalConstraint {
  id: string;
  constraint_type: string;
  description: string;
  severity: string;
}

/**
 * Dietary preferences
 */
export interface DietaryPreferences {
  id: string;
  diet_type: string;
  allergies: string[];
  dislikes: string[];
  preferred_cuisines:string[];
  // preferences: Record<string, any>;
  meals_per_day:number;
}

/**
 * Meal plan definition
 */
export interface MealPlan {
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
 * Meal schedule definition
 */
export interface MealSchedule {
  id: string;
  meal_number: number;
  meal_name: string;
  scheduled_time: string;
  notification_offset_minutes: number;
  earliest_time: string;
  latest_time: string;
  is_active: boolean;
}

/**
 * Workout schedule definition
 */
export interface WorkoutSchedule {
  id: string;
  day_of_week: number;
  scheduled_time: string;
  enable_notifications: boolean;
}

/**
 * Hydration preferences
 */
export interface HydrationPreferences {
  id: string;
  daily_water_target_ml: number;
  reminder_interval_minutes: number;
  enable_reminders: boolean;
}

/**
 * Lifestyle baseline tracking
 */
export interface LifestyleBaseline {
  id: string;
  energy_level: number;
  stress_level: number;
  sleep_hours: number;
  notes: string | null;
}
