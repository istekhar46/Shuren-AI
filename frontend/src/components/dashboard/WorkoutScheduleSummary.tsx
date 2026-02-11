import React from 'react';
import type { UserProfile } from '../../types';

interface WorkoutScheduleSummaryProps {
  profile: UserProfile;
}

export const WorkoutScheduleSummary: React.FC<WorkoutScheduleSummaryProps> = ({ profile }) => {
  const { workoutSchedule } = profile;

  const formatTime = (time: string | undefined) => {
    if (!time || typeof time !== 'string') return 'Not set';
    const [hours, minutes] = time.split(':');
    const hour = parseInt(hours, 10);
    const ampm = hour >= 12 ? 'PM' : 'AM';
    const displayHour = hour % 12 || 12;
    return `${displayHour}:${minutes} ${ampm}`;
  };

  const formatDays = (days: string[] | undefined) => {
    if (!days || !Array.isArray(days) || days.length === 0) return 'Not set';
    return days.map(day => day.charAt(0).toUpperCase() + day.slice(1)).join(', ');
  };

  // Handle case where workout schedule is not set
  if (!workoutSchedule) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Workout Schedule</h2>
        <p className="text-sm text-gray-500">No workout schedule configured yet.</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-xl font-semibold text-gray-900 mb-4">Workout Schedule</h2>
      
      <div className="space-y-3">
        <div className="flex justify-between items-center">
          <span className="text-sm font-medium text-gray-600">Days Per Week:</span>
          <span className="text-sm text-gray-900 font-semibold">{workoutSchedule.daysPerWeek || 0}</span>
        </div>

        <div className="border-t pt-3">
          <p className="text-sm font-medium text-gray-600 mb-2">Preferred Days:</p>
          <p className="text-sm text-gray-900">{formatDays(workoutSchedule.preferredDays)}</p>
        </div>

        <div className="border-t pt-3">
          <div className="flex justify-between items-center">
            <span className="text-sm font-medium text-gray-600">Preferred Time:</span>
            <span className="text-sm text-gray-900">{formatTime(workoutSchedule.preferredTime)}</span>
          </div>
        </div>

        <div className="border-t pt-3">
          <div className="flex justify-between items-center">
            <span className="text-sm font-medium text-gray-600">Session Duration:</span>
            <span className="text-sm text-gray-900">{workoutSchedule.sessionDuration || 0} minutes</span>
          </div>
        </div>
      </div>
    </div>
  );
};
