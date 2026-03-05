import React from 'react';
import { useNavigate } from 'react-router-dom';
import type { UserProfile } from '../../types';
import '../../pages/DashboardPage.css';

interface WorkoutScheduleSummaryProps {
  profile: UserProfile;
}

const ALL_DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
const DAY_ABBREV: Record<string, string> = {
  monday: 'Mon', tuesday: 'Tue', wednesday: 'Wed', thursday: 'Thu',
  friday: 'Fri', saturday: 'Sat', sunday: 'Sun',
};

export const WorkoutScheduleSummary: React.FC<WorkoutScheduleSummaryProps> = ({ profile }) => {
  const { workoutSchedule } = profile;
  const navigate = useNavigate();

  const formatTime = (time: string | undefined) => {
    if (!time) return 'Not set';
    const [hours, minutes] = time.split(':');
    const hour = parseInt(hours, 10);
    const ampm = hour >= 12 ? 'PM' : 'AM';
    return `${hour % 12 || 12}:${minutes} ${ampm}`;
  };

  const activeDays = new Set(
    (workoutSchedule?.preferredDays || []).map((d) => DAY_ABBREV[d.toLowerCase()] || d)
  );

  if (!workoutSchedule || workoutSchedule.daysPerWeek === 0) {
    return (
      <div className="ds-card flex flex-col" style={{ height: '100%' }}>
        <h2 className="text-lg font-semibold mb-4" style={{ color: 'var(--color-text-primary)' }}>🏋️ Workout Schedule</h2>
        <p className="text-sm flex-grow" style={{ color: 'var(--color-text-muted)' }}>No workout schedule configured yet.</p>
        <button 
          onClick={() => navigate('/workouts')} 
          className="ds-btn-secondary w-full mt-6"
        >
          View Full Workout Plan
        </button>
      </div>
    );
  }

  return (
    <div className="ds-card flex flex-col" style={{ height: '100%' }}>
      <h2 className="text-lg font-semibold mb-4" style={{ color: 'var(--color-text-primary)' }}>🏋️ Workout Schedule</h2>

      {/* Day Pills */}
      <div className="dash-section-title">Weekly Schedule</div>
      <div className="flex gap-2 mb-5">
        {ALL_DAYS.map((day) => (
          <div
            key={day}
            className={`dash-day-pill ${activeDays.has(day) ? 'dash-day-pill--active' : 'dash-day-pill--inactive'}`}
            title={day}
          >
            {day[0]}
          </div>
        ))}
      </div>

      {/* Stats */}
      <div className="space-y-3 flex-grow" style={{ borderTop: '1px solid var(--color-border)', paddingTop: '1rem', paddingBottom: '1rem' }}>
        {[
          { icon: '🕐', label: 'Preferred Time', value: formatTime(workoutSchedule.preferredTime) },
          { icon: '⏱️', label: 'Session Duration', value: `${workoutSchedule.sessionDuration || 0} minutes` },
          { icon: '📅', label: 'Days Per Week', value: `${workoutSchedule.daysPerWeek || 0} days` },
        ].map((row) => (
          <div key={row.label} className="flex justify-between items-center">
            <span className="text-sm" style={{ color: 'var(--color-text-muted)' }}>
              {row.icon} {row.label}
            </span>
            <span className="text-sm font-medium" style={{ color: 'var(--color-text-primary)' }}>{row.value}</span>
          </div>
        ))}
      </div>

      <button 
        onClick={() => navigate('/workouts')} 
        className="ds-btn-secondary w-full mt-auto"
      >
        View Full Workout Plan
      </button>
    </div>
  );
};
