import api from './api';
import type { WorkoutSession, WorkoutLog } from '../types';
import type { 
  WorkoutPlanResponse, 
  WorkoutDayResponse, 
  WorkoutScheduleResponse 
} from '../types/workout.types';

export const workoutService = {
  /**
   * Get user's workout plan
   * @returns Complete workout plan with all workout days
   */
  async getWorkoutPlan(): Promise<WorkoutPlanResponse> {
    const response = await api.get<WorkoutPlanResponse>('/workouts/plan');
    return response.data;
  },

  /**
   * Get specific workout day details
   * @param dayNumber - Day number (1-7)
   * @returns Workout day with exercises
   */
  async getWorkoutDay(dayNumber: number): Promise<WorkoutDayResponse> {
    const response = await api.get<WorkoutDayResponse>(`/workouts/plan/day/${dayNumber}`);
    return response.data;
  },

  /**
   * Get today's workout
   * @returns Today's workout day or null if no workout scheduled
   */
  async getTodayWorkout(): Promise<WorkoutDayResponse | null> {
    const response = await api.get<WorkoutDayResponse | null>('/workouts/today');
    return response.data;
  },

  /**
   * Get workouts for the current week
   * @returns Array of workout days for the week
   */
  async getWeekWorkouts(): Promise<WorkoutDayResponse[]> {
    const response = await api.get<WorkoutDayResponse[]>('/workouts/week');
    return response.data;
  },

  /**
   * Get workout schedule
   * @returns Array of scheduled workout times
   */
  async getSchedule(): Promise<WorkoutScheduleResponse[]> {
    const response = await api.get<WorkoutScheduleResponse[]>('/workouts/schedule');
    return response.data;
  },

  /**
   * Update workout plan
   * @param updates - Fields to update in the workout plan
   * @returns Updated workout plan
   */
  async updateWorkoutPlan(updates: Record<string, any>): Promise<WorkoutPlanResponse> {
    const response = await api.patch<WorkoutPlanResponse>('/workouts/plan', updates);
    return response.data;
  },

  /**
   * Update workout schedule
   * @param updates - Fields to update in the workout schedule
   * @returns Updated workout schedule
   */
  async updateWorkoutSchedule(updates: Record<string, any>): Promise<WorkoutScheduleResponse[]> {
    const response = await api.patch<WorkoutScheduleResponse[]>('/workouts/schedule', updates);
    return response.data;
  },
};
