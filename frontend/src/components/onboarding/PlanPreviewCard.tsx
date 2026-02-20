import React, { useState } from 'react';
import type { OnboardingWorkoutPlan, OnboardingMealPlan } from '../../types/onboarding.types';
import { WorkoutPlanPreview } from './WorkoutPlanPreview';
import { MealPlanPreview } from './MealPlanPreview';

interface PlanPreviewCardProps {
  plan: OnboardingWorkoutPlan | OnboardingMealPlan;
  planType: 'workout' | 'meal';
  onApprove: () => void;
  onModify: (feedback: string) => void;
  onClose: () => void;
}

/**
 * PlanPreviewCard Component
 * 
 * Displays workout or meal plans in a modal/slide-in panel for user review.
 * Allows users to approve the plan or request modifications.
 * 
 * Requirements: US-3, AC-3.1, AC-3.2, AC-3.3, AC-3.4, AC-3.5, AC-3.6
 */
export const PlanPreviewCard: React.FC<PlanPreviewCardProps> = ({
  plan,
  planType,
  onApprove,
  onModify,
  onClose,
}) => {
  const [showModifyInput, setShowModifyInput] = useState(false);
  const [modifyFeedback, setModifyFeedback] = useState('');

  /**
   * Handle keyboard events for accessibility
   */
  React.useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Close on Escape key
      if (event.key === 'Escape') {
        if (showModifyInput) {
          handleCancelModification();
        } else {
          onClose();
        }
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [showModifyInput, onClose]);

  /**
   * Handle approve button click
   */
  const handleApprove = () => {
    onApprove();
  };

  /**
   * Handle modify button click
   */
  const handleModifyClick = () => {
    setShowModifyInput(true);
  };

  /**
   * Handle submit modification feedback
   */
  const handleSubmitModification = () => {
    if (modifyFeedback.trim()) {
      onModify(modifyFeedback);
      setModifyFeedback('');
      setShowModifyInput(false);
    }
  };

  /**
   * Handle cancel modification
   */
  const handleCancelModification = () => {
    setShowModifyInput(false);
    setModifyFeedback('');
  };

  return (
    <>
      {/* Overlay */}
      <div
        className="fixed inset-0 bg-black bg-opacity-50 z-40 transition-opacity duration-300"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Modal/Slide-in Panel */}
      <div
        className="fixed inset-x-0 bottom-0 md:inset-y-0 md:right-0 md:left-auto md:w-[600px] lg:w-[700px] bg-white z-50 shadow-2xl transform transition-transform duration-300 ease-out flex flex-col"
        role="dialog"
        aria-modal="true"
        aria-labelledby="plan-preview-title"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 bg-gray-50">
          <h2
            id="plan-preview-title"
            className="text-xl font-bold text-gray-900"
          >
            {planType === 'workout' ? (
              <>
                <span role="img" aria-label="workout">🏋️</span> Your Workout Plan
              </>
            ) : (
              <>
                <span role="img" aria-label="meal">🥗</span> Your Meal Plan
              </>
            )}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors p-2 rounded-full hover:bg-gray-200"
            aria-label="Close plan preview"
          >
            <svg
              className="w-6 h-6"
              fill="none"
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Scrollable Content */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          {planType === 'workout' ? (
            <WorkoutPlanPreview plan={plan as OnboardingWorkoutPlan} />
          ) : (
            <MealPlanPreview plan={plan as OnboardingMealPlan} />
          )}
        </div>

        {/* Action Buttons */}
        <div className="px-6 py-4 border-t border-gray-200 bg-gray-50">
          {!showModifyInput ? (
            <div className="flex flex-col sm:flex-row gap-3">
              <button
                onClick={handleApprove}
                className="flex-1 bg-green-600 hover:bg-green-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2"
                aria-label="Approve this plan"
              >
                <span role="img" aria-label="checkmark">✓</span> Approve Plan
              </button>
              <button
                onClick={handleModifyClick}
                className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                aria-label="Request changes to this plan"
              >
                <span role="img" aria-label="edit">✎</span> Request Changes
              </button>
            </div>
          ) : (
            <div className="space-y-3">
              <label htmlFor="modify-feedback" className="block text-sm font-medium text-gray-700">
                What would you like to change?
              </label>
              <textarea
                id="modify-feedback"
                value={modifyFeedback}
                onChange={(e) => setModifyFeedback(e.target.value)}
                placeholder="E.g., 'Can we reduce the workout frequency to 3 days per week?' or 'I'd prefer more protein in my meals'"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                rows={4}
                autoFocus
              />
              <div className="flex gap-3">
                <button
                  onClick={handleSubmitModification}
                  disabled={!modifyFeedback.trim()}
                  className="flex-1 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-white font-semibold py-3 px-6 rounded-lg transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                  aria-label="Send modification feedback"
                >
                  Send Feedback
                </button>
                <button
                  onClick={handleCancelModification}
                  className="flex-1 bg-gray-300 hover:bg-gray-400 text-gray-800 font-semibold py-3 px-6 rounded-lg transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2"
                  aria-label="Cancel modification request"
                >
                  Cancel
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  );
};
