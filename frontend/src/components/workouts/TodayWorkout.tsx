import type { WorkoutDayResponse } from '../../types/workout.types';

interface TodayWorkoutProps {
  workout: WorkoutDayResponse | null;
  onRequestDemo: (exerciseName: string) => void;
  hideHeader?: boolean;
}

export const TodayWorkout = ({ workout, onRequestDemo, hideHeader = false }: TodayWorkoutProps) => {
  if (!workout) {
    return (
      <div className="flex flex-col items-center justify-center py-16 px-4 text-center rounded-2xl border border-[var(--color-border)] bg-[var(--color-bg-surface)]">
        <div className="w-16 h-16 mb-4 rounded-full bg-cyan-500/10 flex items-center justify-center">
          <svg className="w-8 h-8 text-cyan-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <h2 className="text-xl font-bold mb-2 text-[var(--color-text-primary)]">Today's Workout</h2>
        <p className="text-sm text-[var(--color-text-muted)]">No workout scheduled for today.</p>
        <p className="text-sm mt-1 text-[var(--color-text-muted)]">Enjoy your recovery!</p>
      </div>
    );
  }

  return (
    <div className="animate-fade-in">
      <div className={hideHeader ? "" : "ds-card p-8"}>
        {!hideHeader && (
          <div className="mb-8 border-b pb-6" style={{ borderColor: 'var(--color-border)' }}>
            <h2 className="text-3xl font-bold mb-4" style={{ color: 'var(--color-text-primary)' }}>
              {workout.day_name}
            </h2>
            
            <div className="flex items-center gap-3 mb-4">
              <span className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-semibold" style={{ background: 'var(--color-bg-primary)', border: '1px solid var(--color-border)', color: 'var(--color-violet)' }}>
                Day {workout.day_number}
              </span>
              <span className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-semibold" style={{ background: 'var(--color-bg-primary)', border: '1px solid var(--color-border)', color: 'var(--color-pink)' }}>
                {workout.workout_type}
              </span>
              {workout.estimated_duration_minutes && (
                <span className="text-sm font-medium" style={{ color: 'var(--color-text-muted)' }}>
                  • {workout.estimated_duration_minutes} min
                </span>
              )}
            </div>
            
            {workout.description && (
              <p className="leading-relaxed mb-4" style={{ color: 'var(--color-text-muted)' }}>{workout.description}</p>
            )}

            {(workout.muscle_groups || []).length > 0 && (
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-sm font-medium" style={{ color: 'var(--color-text-muted)' }}>Target Muscles:</span>
                {(workout.muscle_groups || []).map((muscle, i) => (
                  <span key={i} className="text-xs font-medium px-2 py-0.5 rounded" style={{ background: 'var(--color-bg-primary)', border: '1px solid var(--color-border)', color: 'var(--color-text-secondary)' }}>
                    {muscle}
                  </span>
                ))}
              </div>
            )}
          </div>
        )}

        <div className="flex flex-col p-4">
          {workout.exercises.map((exercise, index) => (
            <div 
              key={exercise.id.toString()} 
              className={`py-6 flex flex-col md:flex-row gap-6 ${index !== 0 ? 'border-t' : ''}`}
              style={{ borderColor: 'var(--color-border)' }}
            >
              <div className="flex-1">
                <div className="flex items-start justify-between gap-4 mb-2">
                  <div className="flex items-center gap-3">
                    <span className="font-bold text-lg min-w-[24px]" style={{ color: 'var(--color-violet)' }}>
                      {exercise.exercise_order}.
                    </span>
                    <h3 className="font-bold text-xl" style={{ color: 'var(--color-text-primary)' }}>
                      {exercise.exercise_library.exercise_name}
                    </h3>
                  </div>
                  
                  <button
                    onClick={() => onRequestDemo(exercise.exercise_library.exercise_name)}
                    className="shrink-0 p-2 transition-colors rounded-lg border hover-scale"
                    title="View Demonstration"
                    style={{ 
                      color: 'var(--color-text-muted)', 
                      background: 'var(--color-bg-primary)', 
                      borderColor: 'var(--color-border)' 
                    }}
                  >
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </button>
                </div>

                <div className="flex flex-wrap gap-2 text-xs mb-3 ml-9">
                  <span style={{ color: 'var(--color-text-muted)' }}>
                    {exercise.exercise_library.primary_muscle_group}
                  </span>
                  {(exercise.exercise_library.secondary_muscle_groups || []).length > 0 && 
                    <span style={{ color: 'var(--color-text-faint)' }}>
                      • {(exercise.exercise_library.secondary_muscle_groups || []).join(', ')}
                    </span>
                  }
                  <span style={{ color: 'var(--color-text-faint)' }}>•</span>
                  <span className="uppercase tracking-wider" style={{ color: 'var(--color-emerald)' }}>
                    {exercise.exercise_library.exercise_type}
                  </span>
                </div>

                {exercise.exercise_library.description && (
                  <p className="text-sm mb-4 ml-9" style={{ color: 'var(--color-text-muted)' }}>
                    {exercise.exercise_library.description}
                  </p>
                )}

                {/* Minimal Stats Row */}
                <div className="flex flex-wrap gap-x-6 gap-y-2 ml-9 text-sm">
                  <div className="flex items-baseline gap-1.5">
                    <span className="font-medium uppercase text-xs" style={{ color: 'var(--color-text-faint)' }}>Sets</span>
                    <span className="font-bold" style={{ color: 'var(--color-text-primary)' }}>{exercise.sets}</span>
                  </div>
                  
                  <div className="flex items-baseline gap-1.5">
                    <span className="font-medium uppercase text-xs" style={{ color: 'var(--color-text-faint)' }}>Reps</span>
                    <span className="font-bold" style={{ color: 'var(--color-text-primary)' }}>
                      {exercise.reps_target ? (
                        exercise.reps_target
                      ) : exercise.reps_min && exercise.reps_max ? (
                        `${exercise.reps_min}-${exercise.reps_max}`
                      ) : (
                        '--'
                      )}
                    </span>
                  </div>

                  {exercise.weight_kg && (
                    <div className="flex items-baseline gap-1.5">
                      <span className="font-medium uppercase text-xs" style={{ color: 'var(--color-text-faint)' }}>Weight</span>
                      <span className="font-bold" style={{ color: 'var(--color-text-primary)' }}>{exercise.weight_kg}kg</span>
                    </div>
                  )}

                  <div className="flex items-baseline gap-1.5">
                    <span className="font-medium uppercase text-xs" style={{ color: 'var(--color-text-faint)' }}>Rest</span>
                    <span className="font-bold" style={{ color: 'var(--color-violet)' }}>{exercise.rest_seconds}s</span>
                  </div>
                </div>

                {exercise.notes && (
                  <div className="mt-4 ml-9 flex gap-2 items-start text-sm p-3 rounded-lg border" style={{ color: 'var(--color-amber)', background: 'rgba(245, 158, 11, 0.1)', borderColor: 'rgba(245, 158, 11, 0.2)' }}>
                    <svg className="w-4 h-4 mt-0.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <span className="italic">{exercise.notes}</span>
                  </div>
                )}
              </div>

              {exercise.exercise_library.gif_url && (
                <div className="shrink-0 w-full md:w-48 lg:w-56 rounded-lg overflow-hidden border aspect-video flex justify-center items-center" style={{ borderColor: 'var(--color-border)', background: 'var(--color-bg-primary)' }}>
                  <img 
                    src={exercise.exercise_library.gif_url} 
                    alt={exercise.exercise_library.exercise_name}
                    className="w-full h-full object-cover mix-blend-screen opacity-90"
                  />
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
