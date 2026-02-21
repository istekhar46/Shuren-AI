import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { workoutService } from '../services/workoutService';
import type { WorkoutDayResponse, WorkoutScheduleResponse } from '../types/workout.types';
import { WorkoutSchedule } from '../components/workouts/WorkoutSchedule';
import { TodayWorkout } from '../components/workouts/TodayWorkout';

type ViewMode = 'today' | 'schedule';

export const WorkoutsPage = () => {
  const navigate = useNavigate();
  const [viewMode, setViewMode] = useState<ViewMode>('today');
  const [todayWorkout, setTodayWorkout] = useState<WorkoutDayResponse | null>(null);
  const [schedule, setSchedule] = useState<WorkoutScheduleResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadWorkoutData();
  }, []);

  const loadWorkoutData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Backend supports: getTodayWorkout() and getSchedule()
      const [today, scheduleData] = await Promise.all([
        workoutService.getTodayWorkout(),
        workoutService.getSchedule(),
      ]);

      setTodayWorkout(today);
      setSchedule(scheduleData);
    } catch (err) {
      setError('Failed to load workout data. Please try again.');
      console.error('Error loading workouts:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleRequestDemo = (exerciseName: string) => {
    // Navigate to chat with pre-filled message
    navigate('/chat', {
      state: {
        prefillMessage: `Can you show me how to do ${exerciseName}?`,
        agentType: 'workout_planning',
      },
    });
  };

  if (loading) {
    return (
      <div className="workouts-page p-6">
        <div className="text-center py-8">Loading workouts...</div>
      </div>
    );
  }

  return (
    <div className="workouts-page p-6 max-w-6xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Workouts</h1>
        
        <div className="flex gap-2">
          <button
            onClick={() => setViewMode('today')}
            className={`px-4 py-2 rounded-md ${
              viewMode === 'today'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            Today
          </button>
          <button
            onClick={() => setViewMode('schedule')}
            className={`px-4 py-2 rounded-md ${
              viewMode === 'schedule'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            Schedule
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-300 text-red-700 px-4 py-3 rounded-md mb-4">
          {error}
          <button
            onClick={() => setError(null)}
            className="float-right text-red-700 hover:text-red-900"
          >
            ×
          </button>
        </div>
      )}

      {viewMode === 'today' && (
        <div>
          {todayWorkout ? (
            <TodayWorkout
              workout={todayWorkout}
              onRequestDemo={handleRequestDemo}
            />
          ) : (
            <div className="bg-white rounded-lg shadow p-6 text-center">
              <p className="text-gray-600">No workout scheduled for today. Enjoy your rest day!</p>
            </div>
          )}
        </div>
      )}

      {viewMode === 'schedule' && (
        <WorkoutSchedule schedule={schedule} />
      )}
    </div>
  );
};
