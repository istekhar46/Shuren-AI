import React from 'react';
import type { OnboardingWorkoutPlan } from '../../types/onboarding.types';

interface WorkoutPlanPreviewProps {
  plan: OnboardingWorkoutPlan;
}

/**
 * WorkoutPlanPreview Component
 * 
 * Displays workout plan details in a structured, readable format:
 * - Plan summary (frequency, location, duration)
 * - Equipment list
 * - Day-by-day breakdown with exercises
 * - Sets, reps, and rest periods for each exercise
 * 
 * Requirements: US-3, AC-3.1
 */
export const WorkoutPlanPreview: React.FC<WorkoutPlanPreviewProps> = ({ plan }) => {
  return (
    <div className="space-y-6">
      {/* Plan Summary */}
      <div className="bg-gradient-to-r from-green-50 to-blue-50 rounded-lg p-5 border border-green-200">
        <h3 className="text-lg font-bold text-gray-900 mb-3">Plan Overview</h3>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="flex items-center space-x-2">
            <span className="text-2xl">📅</span>
            <div>
              <p className="text-xs text-gray-600">Frequency</p>
              <p className="text-sm font-semibold text-gray-900">
                {plan.frequency} days/week
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <span className="text-2xl">📍</span>
            <div>
              <p className="text-xs text-gray-600">Location</p>
              <p className="text-sm font-semibold text-gray-900 capitalize">
                {plan.location}
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <span className="text-2xl">⏱️</span>
            <div>
              <p className="text-xs text-gray-600">Duration</p>
              <p className="text-sm font-semibold text-gray-900">
                {plan.duration_minutes} minutes
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Equipment List */}
      {plan.equipment && plan.equipment.length > 0 && (
        <div className="bg-gray-50 rounded-lg p-5 border border-gray-200">
          <h3 className="text-md font-bold text-gray-900 mb-3 flex items-center">
            <span className="text-xl mr-2">🏋️</span>
            Equipment Needed
          </h3>
          <div className="flex flex-wrap gap-2">
            {plan.equipment.map((item, index) => (
              <span
                key={index}
                className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800"
              >
                {item}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Workout Days */}
      <div className="space-y-4">
        <h3 className="text-lg font-bold text-gray-900 flex items-center">
          <span className="text-xl mr-2">💪</span>
          Workout Schedule
        </h3>
        {plan.days.map((day) => (
          <div
            key={day.day_number}
            className="bg-white rounded-lg border-2 border-gray-200 overflow-hidden hover:border-blue-300 transition-colors duration-200"
          >
            {/* Day Header */}
            <div className="bg-gradient-to-r from-blue-600 to-blue-700 px-5 py-3">
              <h4 className="text-lg font-bold text-white">
                Day {day.day_number}: {day.name}
              </h4>
            </div>

            {/* Exercises */}
            <div className="p-5 space-y-4">
              {day.exercises.map((exercise, exerciseIndex) => (
                <div
                  key={exerciseIndex}
                  className="bg-gray-50 rounded-lg p-4 border border-gray-200"
                >
                  {/* Exercise Name */}
                  <h5 className="text-md font-semibold text-gray-900 mb-3">
                    {exerciseIndex + 1}. {exercise.name}
                  </h5>

                  {/* Exercise Details */}
                  <div className="grid grid-cols-3 gap-3 mb-3">
                    <div className="text-center">
                      <p className="text-xs text-gray-600 mb-1">Sets</p>
                      <p className="text-lg font-bold text-blue-600">
                        {exercise.sets}
                      </p>
                    </div>
                    <div className="text-center">
                      <p className="text-xs text-gray-600 mb-1">Reps</p>
                      <p className="text-lg font-bold text-blue-600">
                        {exercise.reps}
                      </p>
                    </div>
                    <div className="text-center">
                      <p className="text-xs text-gray-600 mb-1">Rest</p>
                      <p className="text-lg font-bold text-blue-600">
                        {exercise.rest_seconds}s
                      </p>
                    </div>
                  </div>

                  {/* Exercise Notes */}
                  {exercise.notes && (
                    <div className="bg-yellow-50 border-l-4 border-yellow-400 p-3 rounded">
                      <p className="text-xs font-medium text-yellow-800 mb-1">
                        💡 Note:
                      </p>
                      <p className="text-sm text-yellow-900">{exercise.notes}</p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Summary Footer */}
      <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
        <p className="text-sm text-blue-900">
          <span className="font-semibold">Total:</span> {plan.days.length} workout days with{' '}
          {plan.days.reduce((total, day) => total + day.exercises.length, 0)} exercises
        </p>
      </div>
    </div>
  );
};
