import type { WorkoutScheduleResponse } from '../../types/workout.types';

interface WorkoutScheduleProps {
  schedule: WorkoutScheduleResponse[];
}

export const WorkoutSchedule = ({ schedule }: WorkoutScheduleProps) => {
  const dayNames = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

  const formatTime = (time: string) => {
    // time is in HH:MM:SS format
    const [hours, minutes] = time.split(':');
    const hour = parseInt(hours, 10);
    const ampm = hour >= 12 ? 'PM' : 'AM';
    const displayHour = hour % 12 || 12;
    return `${displayHour}:${minutes} ${ampm}`;
  };

  return (
    <div className="workout-schedule">
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Weekly Workout Schedule</h2>
        
        {schedule.length === 0 ? (
          <div className="text-center text-gray-500 py-8">
            No workout schedule configured yet
          </div>
        ) : (
          <div className="space-y-3">
            {schedule.map((item) => (
              <div
                key={item.id.toString()}
                className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50"
              >
                <div className="flex items-center gap-4">
                  <div className="w-32">
                    <div className="font-medium text-gray-900">
                      {dayNames[item.day_of_week]}
                    </div>
                  </div>
                  <div className="text-gray-600">
                    {formatTime(item.scheduled_time.toString())}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {item.enable_notifications ? (
                    <span className="text-sm text-green-600 flex items-center gap-1">
                      <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M10 2a6 6 0 00-6 6v3.586l-.707.707A1 1 0 004 14h12a1 1 0 00.707-1.707L16 11.586V8a6 6 0 00-6-6zM10 18a3 3 0 01-3-3h6a3 3 0 01-3 3z" />
                      </svg>
                      Reminders On
                    </span>
                  ) : (
                    <span className="text-sm text-gray-400">Reminders Off</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
