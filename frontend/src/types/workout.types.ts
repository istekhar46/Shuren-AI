/**
 * Workout Type Definitions
 * 
 * These types define the structure of workout-related requests and responses
 * for the Shuren API. They align with the backend FastAPI endpoints.
 */

/**
 * Exercise library entry
 * Contains exercise details from the exercise library
 */
export interface ExerciseLibrary {
  id: string;
  exercise_name: string;
  exercise_slug: string;
  exercise_type: string;
  primary_muscle_group: string;
  secondary_muscle_groups: string[];
  equipment_required: string[];
  difficulty_level: string;
  description: string;
  instructions: string;
  gif_url: string | null;
  is_compound: boolean;
  is_unilateral: boolean;
}

/**
 * Workout exercise definition
 * Represents a single exercise in a workout day
 */
export interface WorkoutExercise {
  id: string;
  exercise_order: number;
  sets: number;
  reps_min: number | null;
  reps_max: number | null;
  reps_target: number | null;
  weight_kg: number | null;
  weight_progression_type: string | null;
  rest_seconds: number;
  notes: string | null;
  exercise_library: ExerciseLibrary;
}

/**
 * Workout day response
 * Returned by GET /workouts/plan/day/{day_number} and GET /workouts/today
 * Contains exercises for a specific workout day
 */
export interface WorkoutDayResponse {
  id: string;
  day_number: number;
  day_name: string;
  muscle_groups: string[];
  workout_type: string;
  description: string | null;
  estimated_duration_minutes: number | null;
  exercises: WorkoutExercise[];
}

/**
 * Workout plan response
 * Returned by GET /workouts/plan
 * Contains complete workout plan with all workout days
 */
export interface WorkoutPlanResponse {
  id: string;
  plan_name: string;
  plan_description: string | null;
  duration_weeks: number;
  days_per_week: number;
  plan_rationale: string | null;
  is_locked: boolean;
  workout_days: WorkoutDayResponse[];
  created_at: string;
  updated_at: string;
}

/**
 * Workout schedule response
 * Returned by GET /workouts/schedule
 * Contains scheduled workout days and times
 */
export interface WorkoutScheduleResponse {
  id: string;
  day_of_week: number;
  scheduled_time: string;
  enable_notifications: boolean;
}
