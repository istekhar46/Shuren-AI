import type { WorkoutSession } from '../../types';

interface WorkoutHistoryProps {
  sessions: WorkoutSession[];
  onSelectSession: (session: WorkoutSession) => void;
}

export const WorkoutHistory = ({ sessions, onSelectSession }: WorkoutHistoryProps) => {
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
      weekday: 'short', 
      month: 'short', 
      day: 'numeric',
      year: 'numeric'
    });
  };

  const formatDuration = (minutes?: number) => {
    if (!minutes) return 'N/A';
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    if (hours > 0) {
      return `${hours}h ${mins}m`;
    }
    return `${mins}m`;
  };

  const completedSessions = sessions.filter(s => s.completed);

  return (
    <div className="workout-history">
      <h2 className="text-xl font-semibold mb-4">Workout History</h2>

      {completedSessions.length === 0 ? (
        <div className="text-center text-gray-500 py-8">
          No completed workouts yet
        </div>
      ) : (
        <div className="space-y-3">
          {completedSessions.map((session) => {
            const totalSets = session.exercises.reduce(
              (sum, ex) => sum + ex.sets.length,
              0
            );
            const completedSets = session.exercises.reduce(
              (sum, ex) => sum + ex.sets.filter(s => s.completed).length,
              0
            );

            return (
              <div
                key={session.id}
                onClick={() => onSelectSession(session)}
                className="border rounded-lg p-4 cursor-pointer hover:bg-gray-50 transition-colors"
              >
                <div className="flex justify-between items-start mb-2">
                  <div>
                    <div className="font-semibold">{formatDate(session.date)}</div>
                    <div className="text-sm text-gray-600">
                      {session.exercises.length} exercises • {completedSets}/{totalSets} sets
                    </div>
                  </div>
                  <div className="text-sm text-green-600 font-medium">
                    ✓ Completed
                  </div>
                </div>

                {session.duration && (
                  <div className="text-sm text-gray-600">
                    Duration: {formatDuration(session.duration)}
                  </div>
                )}

                <div className="mt-2 flex flex-wrap gap-2">
                  {session.exercises.map((exercise) => (
                    <span
                      key={exercise.id}
                      className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded"
                    >
                      {exercise.name}
                    </span>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
