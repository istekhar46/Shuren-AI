import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { workoutService } from '../services/workoutService';
import type { WorkoutPlanResponse, WorkoutDayResponse, WorkoutScheduleResponse } from '../types/workout.types';
import { WorkoutSchedule } from '../components/workouts/WorkoutSchedule';
import { TodayWorkout } from '../components/workouts/TodayWorkout';
import { FullWorkoutPlan } from '../components/workouts/FullWorkoutPlan';

type ViewMode = 'today' | 'schedule' | 'plan';

export const WorkoutsPage = () => {
  const navigate = useNavigate();
  const [viewMode, setViewMode] = useState<ViewMode>('today');
  const [todayWorkout, setTodayWorkout] = useState<WorkoutDayResponse | null>(null);
  const [schedule, setSchedule] = useState<WorkoutScheduleResponse[]>([]);
  const [fullPlan, setFullPlan] = useState<WorkoutPlanResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadWorkoutData();
  }, []);

  const loadWorkoutData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [today, scheduleData, planData] = await Promise.all([
        workoutService.getTodayWorkout(),
        workoutService.getSchedule(),
        workoutService.getWorkoutPlan(),
      ]);
      setTodayWorkout(today);
      setSchedule(scheduleData);
      setFullPlan(planData);
    } catch (err) {
      setError('Failed to load workout data. Please try again.');
      console.error('Error loading workouts:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleRequestDemo = (exerciseName: string) => {
    navigate('/chat', {
      state: {
        prefillMessage: `Can you show me how to do ${exerciseName}?`,
        agentType: 'workout_planning',
      },
    });
  };

  if (loading) {
    return (
      <div className="p-6 text-center py-8" style={{ color: 'var(--color-text-muted)' }}>
        Loading workouts...
      </div>
    );
  }

  const toggleBtnClass = (active: boolean) =>
    `px-4 py-2 rounded-md text-sm font-medium transition-all ${
      active
        ? 'text-white'
        : ''
    }`;

  return (
    <div style={{ background: 'var(--color-bg-primary)', minHeight: '100vh', width: '100%' }}>
      <div className="p-6 max-w-6xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold" style={{ color: 'var(--color-text-primary)' }}>Workouts</h1>

        <div className="flex gap-2">
          {(['today', 'schedule', 'plan'] as ViewMode[]).map((mode) => (
            <button
              key={mode}
              onClick={() => setViewMode(mode)}
              className={toggleBtnClass(viewMode === mode)}
              style={
                viewMode === mode
                  ? { background: 'var(--gradient-accent)' }
                  : { background: 'var(--color-bg-surface)', color: 'var(--color-text-muted)', border: '1px solid var(--color-border)' }
              }
            >
              {mode === 'today' ? 'Today' : mode === 'schedule' ? 'Schedule' : 'Full Plan'}
            </button>
          ))}
        </div>
      </div>

      {error && (
        <div
          className="px-4 py-3 rounded-md mb-4"
          style={{ background: 'rgba(239,68,68,0.12)', border: '1px solid rgba(239,68,68,0.25)', color: '#f87171' }}
        >
          {error}
          <button
            onClick={() => setError(null)}
            className="float-right hover:opacity-80"
            style={{ color: '#f87171' }}
          >
            ×
          </button>
        </div>
      )}

      {viewMode === 'today' && (
        <div>
          {todayWorkout ? (
            <TodayWorkout workout={todayWorkout} onRequestDemo={handleRequestDemo} />
          ) : (
            <div className="ds-card text-center">
              <p style={{ color: 'var(--color-text-muted)' }}>No workout scheduled for today. Enjoy your rest day!</p>
            </div>
          )}
        </div>
      )}

      {viewMode === 'schedule' && <WorkoutSchedule schedule={schedule} />}

      {viewMode === 'plan' && <FullWorkoutPlan plan={fullPlan} onRequestDemo={handleRequestDemo} />}
      </div>
    </div>
  );
};
