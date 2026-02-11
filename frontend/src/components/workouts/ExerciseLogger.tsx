import { useState } from 'react';
import type { Exercise, ExerciseSet } from '../../types';

interface ExerciseLoggerProps {
  exercise: Exercise;
  sessionId: string;
  onLogSet: (exerciseId: string, setNumber: number, reps: number, weight?: number) => void;
}

export const ExerciseLogger = ({ exercise, sessionId: _sessionId, onLogSet }: ExerciseLoggerProps) => {
  const [activeSet, setActiveSet] = useState<number | null>(null);
  const [reps, setReps] = useState<string>('');
  const [weight, setWeight] = useState<string>('');

  const handleLogSet = (set: ExerciseSet) => {
    setActiveSet(set.setNumber);
    setReps(set.targetReps.toString());
    setWeight(set.targetWeight?.toString() || '');
  };

  const handleSubmit = () => {
    if (activeSet && reps) {
      onLogSet(
        exercise.id,
        activeSet,
        parseInt(reps),
        weight ? parseFloat(weight) : undefined
      );
      setActiveSet(null);
      setReps('');
      setWeight('');
    }
  };

  const handleCancel = () => {
    setActiveSet(null);
    setReps('');
    setWeight('');
  };

  return (
    <div className="exercise-logger border rounded-lg p-4">
      <h3 className="font-semibold text-lg mb-2">{exercise.name}</h3>
      <div className="text-sm text-gray-600 mb-4">{exercise.muscleGroup}</div>

      <div className="space-y-3">
        {exercise.sets.map((set) => (
          <div key={set.setNumber}>
            {activeSet === set.setNumber ? (
              <div className="bg-blue-50 p-3 rounded-lg">
                <div className="font-medium mb-2">Log Set {set.setNumber}</div>
                
                <div className="space-y-2">
                  <div>
                    <label className="block text-sm font-medium mb-1">
                      Reps Completed
                    </label>
                    <input
                      type="number"
                      value={reps}
                      onChange={(e) => setReps(e.target.value)}
                      className="w-full px-3 py-2 border rounded-md"
                      placeholder={`Target: ${set.targetReps}`}
                      min="0"
                    />
                  </div>

                  {set.targetWeight !== undefined && (
                    <div>
                      <label className="block text-sm font-medium mb-1">
                        Weight (lbs)
                      </label>
                      <input
                        type="number"
                        value={weight}
                        onChange={(e) => setWeight(e.target.value)}
                        className="w-full px-3 py-2 border rounded-md"
                        placeholder={`Target: ${set.targetWeight}`}
                        min="0"
                        step="0.5"
                      />
                    </div>
                  )}

                  <div className="flex gap-2 mt-3">
                    <button
                      onClick={handleSubmit}
                      className="flex-1 bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
                    >
                      Save
                    </button>
                    <button
                      onClick={handleCancel}
                      className="flex-1 bg-gray-200 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-300"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              </div>
            ) : (
              <div
                className={`flex items-center justify-between p-3 rounded-lg ${
                  set.completed ? 'bg-green-50' : 'bg-gray-50'
                }`}
              >
                <div className="flex-1">
                  <div className="font-medium">Set {set.setNumber}</div>
                  <div className="text-sm text-gray-600">
                    Target: {set.targetReps} reps
                    {set.targetWeight && ` @ ${set.targetWeight} lbs`}
                  </div>
                  {set.completed && (
                    <div className="text-sm text-green-600 mt-1">
                      ✓ Completed: {set.actualReps} reps
                      {set.actualWeight && ` @ ${set.actualWeight} lbs`}
                    </div>
                  )}
                </div>

                {!set.completed && (
                  <button
                    onClick={() => handleLogSet(set)}
                    className="text-sm text-blue-600 hover:text-blue-700 font-medium"
                  >
                    Log Set
                  </button>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
