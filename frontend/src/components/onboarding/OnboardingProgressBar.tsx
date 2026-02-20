import React, { useState } from 'react';
import type { StateMetadata } from '../../types/onboarding.types';

interface OnboardingProgressBarProps {
  currentState: number;
  totalStates: number;
  completionPercentage: number;
  stateMetadata: StateMetadata | null;
  completedStates: number[];
}

/**
 * OnboardingProgressBar Component
 * 
 * Displays visual progress through onboarding states with:
 * - Progress bar showing completion percentage
 * - "Step X of Y" indicator
 * - Current state name and description
 * - List of all states with status indicators (completed, current, upcoming)
 * - Responsive design: sidebar on desktop, collapsible on mobile
 * 
 * Requirements: US-4, AC-4.1, AC-4.2, AC-4.3, AC-4.4, AC-4.5
 */
export const OnboardingProgressBar: React.FC<OnboardingProgressBarProps> = ({
  currentState,
  totalStates,
  completionPercentage,
  stateMetadata,
  completedStates,
}) => {
  const [isCollapsed, setIsCollapsed] = useState(false);

  // Define all 9 onboarding states with their names
  const allStates = [
    { number: 1, name: 'Fitness Level Assessment' },
    { number: 2, name: 'Primary Fitness Goals' },
    { number: 3, name: 'Workout Preferences & Constraints' },
    { number: 4, name: 'Diet Preferences & Restrictions' },
    { number: 5, name: 'Fixed Meal Plan Selection' },
    { number: 6, name: 'Meal Timing Schedule' },
    { number: 7, name: 'Workout Schedule' },
    { number: 8, name: 'Hydration Schedule' },
    { number: 9, name: 'Supplement Preferences' },
  ];

  /**
   * Determine the status of a state
   * @param stateNumber - The state number to check
   * @returns 'completed' | 'current' | 'upcoming'
   */
  const getStateStatus = (stateNumber: number): 'completed' | 'current' | 'upcoming' => {
    if (completedStates.includes(stateNumber)) {
      return 'completed';
    }
    if (stateNumber === currentState) {
      return 'current';
    }
    return 'upcoming';
  };

  return (
    <>
      {/* Desktop Sidebar (>= 1024px) */}
      <div className="hidden lg:block lg:w-80 lg:flex-shrink-0">
        <div className="h-full bg-white rounded-lg shadow-md p-6 overflow-y-auto">
          {/* Progress Header */}
          <div className="mb-4">
            <div className="flex justify-between items-center mb-2">
              <h2 className="text-lg font-semibold text-gray-800">
                Progress
              </h2>
              <span className="text-sm font-medium text-blue-600">
                {Math.round(completionPercentage)}%
              </span>
            </div>

            {/* Progress Bar */}
            <div 
              className="w-full bg-gray-200 rounded-full h-3 overflow-hidden"
              role="progressbar"
              aria-valuenow={Math.round(completionPercentage)}
              aria-valuemin={0}
              aria-valuemax={100}
              aria-label={`Onboarding progress: ${Math.round(completionPercentage)}% complete`}
            >
              <div
                className="bg-blue-600 h-full rounded-full transition-all duration-500 ease-out"
                style={{ width: `${completionPercentage}%` }}
              />
            </div>

            <p className="text-xs text-gray-600 mt-2">
              Step {currentState} of {totalStates}
            </p>
          </div>

          {/* Current State Info */}
          {stateMetadata && (
            <div className="mb-6 p-4 bg-blue-50 rounded-lg border border-blue-200 transition-all duration-300">
              <h3 className="text-md font-semibold text-blue-900 mb-1">
                {stateMetadata.name}
              </h3>
              <p className="text-sm text-blue-700">
                {stateMetadata.description}
              </p>
            </div>
          )}

          {/* State List */}
          <div className="space-y-2">
            <h3 className="text-sm font-medium text-gray-700 mb-3">All Steps</h3>
            {allStates.map((state) => {
              const status = getStateStatus(state.number);
              
              return (
                <div
                  key={state.number}
                  className={`flex items-center p-3 rounded-lg transition-all duration-300 ${
                    status === 'current'
                      ? 'bg-blue-100 border-2 border-blue-500 scale-105'
                      : status === 'completed'
                      ? 'bg-green-50 border border-green-200'
                      : 'bg-gray-50 border border-gray-200'
                  }`}
                  aria-label={`Step ${state.number}: ${state.name} - ${status}`}
                >
                  {/* Status Icon */}
                  <div className="flex-shrink-0 mr-3">
                    {status === 'completed' && (
                      <div 
                        className="w-6 h-6 bg-green-500 rounded-full flex items-center justify-center transition-transform duration-300 hover:scale-110"
                        aria-label="Completed"
                      >
                        <svg
                          className="w-4 h-4 text-white"
                          fill="none"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth="2"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                        >
                          <path d="M5 13l4 4L19 7" />
                        </svg>
                      </div>
                    )}
                    {status === 'current' && (
                      <div 
                        className="w-6 h-6 bg-blue-600 rounded-full flex items-center justify-center animate-pulse"
                        aria-label="Current step"
                      >
                        <svg
                          className="w-4 h-4 text-white"
                          fill="none"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth="2"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                        >
                          <path d="M9 5l7 7-7 7" />
                        </svg>
                      </div>
                    )}
                    {status === 'upcoming' && (
                      <div 
                        className="w-6 h-6 bg-gray-300 rounded-full transition-colors duration-300"
                        aria-label="Upcoming step"
                      />
                    )}
                  </div>

                  {/* State Name */}
                  <div className="flex-grow">
                    <p
                      className={`text-sm font-medium transition-colors duration-300 ${
                        status === 'current'
                          ? 'text-blue-900'
                          : status === 'completed'
                          ? 'text-green-900'
                          : 'text-gray-500'
                      }`}
                    >
                      {state.number}. {state.name}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Mobile Collapsible (< 1024px) */}
      <div className="lg:hidden mb-4">
        <div className="bg-white rounded-lg shadow-md overflow-hidden">
          {/* Collapsible Header */}
          <button
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="w-full px-4 py-3 flex items-center justify-between bg-blue-50 hover:bg-blue-100 transition-colors duration-200"
            aria-expanded={!isCollapsed}
            aria-controls="mobile-progress-content"
          >
            <div className="flex items-center space-x-3">
              <span className="text-lg font-semibold text-gray-800">
                Progress
              </span>
              <span className="text-sm font-medium text-blue-600">
                {Math.round(completionPercentage)}%
              </span>
            </div>
            <svg
              className={`w-5 h-5 text-gray-600 transition-transform duration-300 ${
                isCollapsed ? '' : 'rotate-180'
              }`}
              fill="none"
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          {/* Progress Bar (Always Visible) */}
          <div className="px-4 py-2 bg-white">
            <div 
              className="w-full bg-gray-200 rounded-full h-2 overflow-hidden"
              role="progressbar"
              aria-valuenow={Math.round(completionPercentage)}
              aria-valuemin={0}
              aria-valuemax={100}
              aria-label={`Onboarding progress: ${Math.round(completionPercentage)}% complete`}
            >
              <div
                className="bg-blue-600 h-full rounded-full transition-all duration-500 ease-out"
                style={{ width: `${completionPercentage}%` }}
              />
            </div>
            <p className="text-xs text-gray-600 mt-1">
              Step {currentState} of {totalStates}
            </p>
          </div>

          {/* Collapsible Content */}
          <div
            id="mobile-progress-content"
            className={`transition-all duration-300 ease-in-out overflow-hidden ${
              isCollapsed ? 'max-h-0' : 'max-h-[600px]'
            }`}
          >
            <div className="px-4 pb-4">
              {/* Current State Info */}
              {stateMetadata && (
                <div className="mb-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
                  <h3 className="text-sm font-semibold text-blue-900 mb-1">
                    {stateMetadata.name}
                  </h3>
                  <p className="text-xs text-blue-700">
                    {stateMetadata.description}
                  </p>
                </div>
              )}

              {/* State List */}
              <div className="space-y-2">
                <h3 className="text-xs font-medium text-gray-700 mb-2">All Steps</h3>
                {allStates.map((state) => {
                  const status = getStateStatus(state.number);
                  
                  return (
                    <div
                      key={state.number}
                      className={`flex items-center p-2 rounded-lg transition-all duration-300 ${
                        status === 'current'
                          ? 'bg-blue-100 border-2 border-blue-500'
                          : status === 'completed'
                          ? 'bg-green-50 border border-green-200'
                          : 'bg-gray-50 border border-gray-200'
                      }`}
                      aria-label={`Step ${state.number}: ${state.name} - ${status}`}
                    >
                      {/* Status Icon */}
                      <div className="flex-shrink-0 mr-2">
                        {status === 'completed' && (
                          <div 
                            className="w-5 h-5 bg-green-500 rounded-full flex items-center justify-center"
                            aria-label="Completed"
                          >
                            <svg
                              className="w-3 h-3 text-white"
                              fill="none"
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth="2"
                              viewBox="0 0 24 24"
                              stroke="currentColor"
                            >
                              <path d="M5 13l4 4L19 7" />
                            </svg>
                          </div>
                        )}
                        {status === 'current' && (
                          <div 
                            className="w-5 h-5 bg-blue-600 rounded-full flex items-center justify-center"
                            aria-label="Current step"
                          >
                            <svg
                              className="w-3 h-3 text-white"
                              fill="none"
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth="2"
                              viewBox="0 0 24 24"
                              stroke="currentColor"
                            >
                              <path d="M9 5l7 7-7 7" />
                            </svg>
                          </div>
                        )}
                        {status === 'upcoming' && (
                          <div 
                            className="w-5 h-5 bg-gray-300 rounded-full"
                            aria-label="Upcoming step"
                          />
                        )}
                      </div>

                      {/* State Name */}
                      <div className="flex-grow">
                        <p
                          className={`text-xs font-medium ${
                            status === 'current'
                              ? 'text-blue-900'
                              : status === 'completed'
                              ? 'text-green-900'
                              : 'text-gray-500'
                          }`}
                        >
                          {state.number}. {state.name}
                        </p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};
