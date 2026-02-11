import type { WorkoutDayResponse } from '../../types/workout.types';

interface TodayWorkoutProps {
  workout: WorkoutDayResponse | null;
  onRequestDemo: (exerciseName: string) => void;
}

export const TodayWorkout = ({ workout, onRequestDemo }: TodayWorkoutProps) => {
  if (!workout) {
    return (
      <div className="today-workout">
        <h2 className="text-xl font-semibold mb-4">Today's Workout</h2>
        <div className="text-center text-gray-500 py-8">
          No workout scheduled for today
        </div>
      </div>
    );
  }

  return (
    <div className="today-workout">
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-2xl font-bold mb-2">{workout.day_name}</h2>
        <div className="text-sm text-gray-600 mb-4">
          Day {workout.day_number} • {workout.workout_type} • {workout.estimated_duration_minutes || 'N/A'} min
        </div>
        
        {workout.description && (
          <p className="text-gray-700 mb-4">{workout.description}</p>
        )}

        <div className="mb-4">
          <span className="text-sm font-medium text-gray-600">Target Muscles: </span>
          <span className="text-sm text-gray-900">{workout.muscle_groups.join(', ')}</span>
        </div>

        <div className="space-y-6 mt-6">
          {workout.exercises.map((exercise) => (
            <div key={exercise.id.toString()} className="border rounded-lg p-4">
              <div className="flex justify-between items-start mb-3">
                <div>
                  <div className="text-sm text-gray-500 mb-1">Exercise {exercise.exercise_order}</div>
                  <h3 className="font-semibold text-lg">{exercise.exercise_library.exercise_name}</h3>
                  <div className="text-sm text-gray-600">
                    {exercise.exercise_library.primary_muscle_group}
                    {exercise.exercise_library.secondary_muscle_groups.length > 0 && 
                      ` • ${exercise.exercise_library.secondary_muscle_groups.join(', ')}`
                    }
                  </div>
                  <div className="text-xs text-gray-500 mt-1">
                    {exercise.exercise_library.difficulty_level} • {exercise.exercise_library.exercise_type}
                  </div>
                </div>
                <button
                  onClick={() => onRequestDemo(exercise.exercise_library.exercise_name)}
                  className="text-sm text-blue-600 hover:text-blue-700"
                >
                  Request Demo
                </button>
              </div>

              {exercise.exercise_library.description && (
                <p className="text-sm text-gray-700 mb-3">{exercise.exercise_library.description}</p>
              )}

              {exercise.exercise_library.gif_url && (
                <div className="mb-3">
                  <img 
                    src={exercise.exercise_library.gif_url} 
                    alt={exercise.exercise_library.exercise_name}
                    className="rounded-lg max-w-xs"
                  />
                </div>
              )}

              <div className="bg-gray-50 rounded p-3 mb-3">
                <div className="text-sm font-medium mb-2">Target:</div>
                <div className="text-sm text-gray-700">
                  {exercise.sets} sets × {' '}
                  {exercise.reps_target ? (
                    `${exercise.reps_target} reps`
                  ) : exercise.reps_min && exercise.reps_max ? (
                    `${exercise.reps_min}-${exercise.reps_max} reps`
                  ) : (
                    'N/A reps'
                  )}
                  {exercise.weight_kg && ` @ ${exercise.weight_kg} kg`}
                  {' • '}
                  Rest: {exercise.rest_seconds}s
                </div>
              </div>

              {exercise.notes && (
                <div className="text-sm text-gray-600 italic">
                  Note: {exercise.notes}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
