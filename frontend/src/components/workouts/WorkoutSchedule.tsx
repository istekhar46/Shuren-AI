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
    <div className="workout-schedule animate-fade-in">
      <div className="ds-card p-8">
        <h2 className="text-3xl font-bold mb-6" style={{ color: 'var(--color-text-primary)' }}>Weekly Workout Schedule</h2>
        
        {schedule.length === 0 ? (
          <div className="text-center py-12" style={{ color: 'var(--color-text-muted)' }}>
            No workout schedule configured yet
          </div>
        ) : (
          <div className="space-y-4">
            {schedule.map((item) => (
              <div
                key={item.id.toString()}
                className="flex items-center justify-between p-5 rounded-xl border transition-all"
                style={{ 
                  background: 'var(--color-bg-primary)', 
                  borderColor: 'var(--color-border)',
                }}
              >
                <div className="flex items-center gap-4">
                  <div className="w-32">
                    <div className="font-semibold text-lg" style={{ color: 'var(--color-text-primary)' }}>
                      {dayNames[item.day_of_week]}
                    </div>
                  </div>
                  <div className="font-medium" style={{ color: 'var(--color-text-muted)' }}>
                    {formatTime(item.scheduled_time.toString())}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {item.enable_notifications ? (
                    <span className="text-sm flex items-center gap-1 font-medium" style={{ color: 'var(--color-emerald)' }}>
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                      </svg>
                      Reminders On
                    </span>
                  ) : (
                    <span className="text-sm font-medium" style={{ color: 'var(--color-text-faint)' }}>Reminders Off</span>
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
