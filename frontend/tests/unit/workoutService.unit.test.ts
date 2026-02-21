import { describe, it, expect, vi, beforeEach } from 'vitest';
import { workoutService } from '../../src/services/workoutService';
import api from '../../src/services/api';
import type { 
  WorkoutPlanResponse, 
  WorkoutDayResponse, 
  WorkoutScheduleResponse 
} from '../../src/types/workout.types';

// Mock the api module
vi.mock('../../src/services/api');

describe('workoutService Unit Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('getWorkoutPlan', () => {
    it('should call GET /workouts/plan and return workout plan', async () => {
      const mockWorkoutPlan: WorkoutPlanResponse = {
        id: 'plan-uuid-123',
        plan_name: 'Beginner Full Body',
        plan_description: 'A comprehensive full body workout plan for beginners',
        duration_weeks: 12,
        days_per_week: 3,
        plan_rationale: 'Balanced approach for building strength and endurance',
        is_locked: false,
        workout_days: [],
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      };

      vi.mocked(api.get).mockResolvedValue({
        data: mockWorkoutPlan,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      });

      const result = await workoutService.getWorkoutPlan();

      expect(api.get).toHaveBeenCalledWith('/workouts/plan');
      expect(api.get).toHaveBeenCalledTimes(1);
      expect(result).toEqual(mockWorkoutPlan);
      expect(result.days_per_week).toBe(3);
    });

    it('should throw error when API call fails', async () => {
      const mockError = new Error('Network error');
      vi.mocked(api.get).mockRejectedValue(mockError);

      await expect(workoutService.getWorkoutPlan()).rejects.toThrow('Network error');
    });
  });

  describe('getWorkoutDay', () => {
    it('should call GET /workouts/plan/day/{dayNumber} and return workout day', async () => {
      const mockWorkoutDay: WorkoutDayResponse = {
        id: 'day-uuid-123',
        day_number: 1,
        day_name: 'Push Day',
        muscle_groups: ['chest', 'shoulders', 'triceps'],
        workout_type: 'strength',
        description: 'Focus on pushing movements',
        estimated_duration_minutes: 60,
        exercises: [
          {
            id: 'exercise-1',
            exercise_order: 1,
            sets: 3,
            reps_target: 10,
            weight_kg: 20,
            rest_seconds: 90,
            exercise: {
              id: 'ex-lib-1',
              exercise_name: 'Bench Press',
              exercise_type: 'compound',
              primary_muscle_group: 'chest',
              gif_url: 'https://example.com/bench-press.gif',
            },
          },
        ],
      };

      vi.mocked(api.get).mockResolvedValue({
        data: mockWorkoutDay,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      });

      const result = await workoutService.getWorkoutDay(1);

      expect(api.get).toHaveBeenCalledWith('/workouts/plan/day/1');
      expect(api.get).toHaveBeenCalledTimes(1);
      expect(result).toEqual(mockWorkoutDay);
      expect(result.day_number).toBe(1);
      expect(result.exercises).toHaveLength(1);
    });

    it('should throw error when day not found (404)', async () => {
      const mockError = {
        response: {
          status: 404,
          data: { detail: 'Workout day not found' },
        },
      };
      vi.mocked(api.get).mockRejectedValue(mockError);

      await expect(workoutService.getWorkoutDay(99)).rejects.toThrow();
    });
  });

  describe('getTodayWorkout', () => {
    it('should call GET /workouts/today and return today\'s workout', async () => {
      const mockTodayWorkout = {
        id: 'session-123',
        workout_day: {
          day_name: 'Push Day',
          exercises: [],
        },
        scheduled_time: '18:00:00',
      };

      vi.mocked(api.get).mockResolvedValue({
        data: mockTodayWorkout,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      });

      const result = await workoutService.getTodayWorkout();

      expect(api.get).toHaveBeenCalledWith('/workouts/today');
      expect(result).toEqual(mockTodayWorkout);
    });

    it('should return null when no workout scheduled today', async () => {
      vi.mocked(api.get).mockResolvedValue({
        data: null,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      });

      const result = await workoutService.getTodayWorkout();

      expect(result).toBeNull();
    });
  });

  describe('getWeekWorkouts', () => {
    it('should call GET /workouts/week and return week workouts', async () => {
      const mockWeekWorkouts: WorkoutDayResponse[] = [
        {
          id: 'day-1',
          day_number: 1,
          day_name: 'Push Day',
          muscle_groups: ['chest', 'shoulders'],
          workout_type: 'strength',
          description: 'Push movements',
          estimated_duration_minutes: 60,
          exercises: [],
        },
        {
          id: 'day-2',
          day_number: 3,
          day_name: 'Pull Day',
          muscle_groups: ['back', 'biceps'],
          workout_type: 'strength',
          description: 'Pull movements',
          estimated_duration_minutes: 60,
          exercises: [],
        },
      ];

      vi.mocked(api.get).mockResolvedValue({
        data: mockWeekWorkouts,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      });

      const result = await workoutService.getWeekWorkouts();

      expect(api.get).toHaveBeenCalledWith('/workouts/week');
      expect(result).toEqual(mockWeekWorkouts);
      expect(result).toHaveLength(2);
    });
  });

  describe('getSchedule', () => {
    it('should call GET /workouts/schedule and return workout schedule', async () => {
      const mockSchedule: WorkoutScheduleResponse[] = [
        {
          id: 'schedule-1',
          day_of_week: 1,
          scheduled_time: '18:00:00',
          enable_notifications: true,
        },
        {
          id: 'schedule-2',
          day_of_week: 3,
          scheduled_time: '18:00:00',
          enable_notifications: true,
        },
      ];

      vi.mocked(api.get).mockResolvedValue({
        data: mockSchedule,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      });

      const result = await workoutService.getSchedule();

      expect(api.get).toHaveBeenCalledWith('/workouts/schedule');
      expect(result).toEqual(mockSchedule);
      expect(result).toHaveLength(2);
    });
  });

  describe('updateWorkoutPlan', () => {
    it('should call PATCH /workouts/plan with updates', async () => {
      const updates = {
        days_per_week: 4,
        duration_weeks: 16,
      };

      const mockUpdatedPlan: WorkoutPlanResponse = {
        id: 'plan-uuid-123',
        plan_name: 'Intermediate Full Body',
        plan_description: 'Updated workout plan',
        duration_weeks: 16,
        days_per_week: 4,
        plan_rationale: 'Increased frequency for better results',
        is_locked: false,
        workout_days: [],
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-02T00:00:00Z',
      };

      vi.mocked(api.patch).mockResolvedValue({
        data: mockUpdatedPlan,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      });

      const result = await workoutService.updateWorkoutPlan(updates);

      expect(api.patch).toHaveBeenCalledWith('/workouts/plan', updates);
      expect(result).toEqual(mockUpdatedPlan);
      expect(result.days_per_week).toBe(4);
    });
  });

  describe('updateWorkoutSchedule', () => {
    it('should call PATCH /workouts/schedule with updates', async () => {
      const updates = {
        schedules: [
          {
            day_of_week: 1,
            scheduled_time: '19:00:00',
          },
        ],
      };

      const mockUpdatedSchedule: WorkoutScheduleResponse[] = [
        {
          id: 'schedule-1',
          day_of_week: 1,
          scheduled_time: '19:00:00',
          enable_notifications: true,
        },
      ];

      vi.mocked(api.patch).mockResolvedValue({
        data: mockUpdatedSchedule,
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {} as any,
      });

      const result = await workoutService.updateWorkoutSchedule(updates);

      expect(api.patch).toHaveBeenCalledWith('/workouts/schedule', updates);
      expect(result).toEqual(mockUpdatedSchedule);
      expect(result[0].scheduled_time).toBe('19:00:00');
    });
  });

  describe('Deprecated - logSet', () => {
    it('should throw error with helpful message', async () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      await expect(
        workoutService.logSet({ exercise_id: 'ex-1', sets: 3 } as any)
      ).rejects.toThrow(
        'logSet() is no longer supported. The backend does not have a workout logging endpoint.'
      );

      expect(consoleErrorSpy).toHaveBeenCalledWith(
        'logSet() has been removed. Workout logging is not supported by the backend.'
      );

      consoleErrorSpy.mockRestore();
    });
  });

  describe('Deprecated - completeWorkout', () => {
    it('should throw error with helpful message', async () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      await expect(workoutService.completeWorkout('session-123')).rejects.toThrow(
        'completeWorkout() is no longer supported. The backend does not have a workout completion endpoint.'
      );

      expect(consoleErrorSpy).toHaveBeenCalledWith(
        'completeWorkout() has been removed. Workout completion is not supported by the backend.'
      );

      consoleErrorSpy.mockRestore();
    });
  });

  describe('Deprecated - getHistory', () => {
    it('should throw error with helpful message', async () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      await expect(workoutService.getHistory(10)).rejects.toThrow(
        'getHistory() is no longer supported. The backend does not have a workout history endpoint.'
      );

      expect(consoleErrorSpy).toHaveBeenCalledWith(
        'getHistory() has been removed. Workout history is not supported by the backend.'
      );

      consoleErrorSpy.mockRestore();
    });
  });
});
