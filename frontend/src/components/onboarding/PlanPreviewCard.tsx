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

export const PlanPreviewCard: React.FC<PlanPreviewCardProps> = ({
  plan,
  planType,
  onApprove,
  onModify,
  onClose,
}) => {
  const [showModifyInput, setShowModifyInput] = useState(false);
  const [modifyFeedback, setModifyFeedback] = useState('');

  React.useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        if (showModifyInput) handleCancelModification();
        else onClose();
      }
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [showModifyInput, onClose]);

  const handleApprove = () => onApprove();

  const handleModifyClick = () => setShowModifyInput(true);

  const handleSubmitModification = () => {
    if (modifyFeedback.trim()) {
      onModify(modifyFeedback);
      setModifyFeedback('');
      setShowModifyInput(false);
    }
  };

  const handleCancelModification = () => {
    setShowModifyInput(false);
    setModifyFeedback('');
  };

  return (
    <>
      {/* Overlay */}
      <div
        className="fixed inset-0 z-40 transition-opacity duration-300"
        style={{ background: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(4px)' }}
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Modal Panel */}
      <div
        className="fixed inset-x-0 bottom-0 md:inset-y-0 md:right-0 md:left-auto md:w-[600px] lg:w-[700px] z-50 shadow-2xl transform transition-transform duration-300 ease-out flex flex-col"
        style={{ background: 'var(--color-bg-primary)', borderLeft: '1px solid var(--color-border)' }}
        role="dialog"
        aria-modal="true"
        aria-labelledby="plan-preview-title"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4" style={{ borderBottom: '1px solid var(--color-border)', background: 'var(--color-bg-surface)' }}>
          <h2 id="plan-preview-title" className="text-xl font-bold" style={{ color: 'var(--color-text-primary)' }}>
            {planType === 'workout' ? (
              <><span role="img" aria-label="workout">🏋️</span> Your Workout Plan</>
            ) : (
              <><span role="img" aria-label="meal">🥗</span> Your Meal Plan</>
            )}
          </h2>
          <button
            onClick={onClose}
            className="p-2 rounded-full transition-colors"
            style={{ color: 'var(--color-text-muted)' }}
            aria-label="Close plan preview"
          >
            <svg className="w-6 h-6" fill="none" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" viewBox="0 0 24 24" stroke="currentColor">
              <path d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Scrollable Content */}
        <div className="flex-1 overflow-y-auto px-6 py-4" style={{ color: 'var(--color-text-primary)' }}>
          {planType === 'workout' ? (
            <WorkoutPlanPreview plan={plan as OnboardingWorkoutPlan} />
          ) : (
            <MealPlanPreview plan={plan as OnboardingMealPlan} />
          )}
        </div>

        {/* Action Buttons */}
        <div className="px-6 py-4" style={{ borderTop: '1px solid var(--color-border)', background: 'var(--color-bg-surface)' }}>
          {!showModifyInput ? (
            <div className="flex flex-col sm:flex-row gap-3">
              <button
                onClick={handleApprove}
                className="flex-1 font-semibold py-3 px-6 rounded-lg transition-all duration-200 text-white"
                style={{ background: '#34d399' }}
                aria-label="Approve this plan"
              >
                <span role="img" aria-label="checkmark">✓</span> Approve Plan
              </button>
              <button
                onClick={handleModifyClick}
                className="ds-btn-primary flex-1 font-semibold py-3 px-6"
                aria-label="Request changes to this plan"
              >
                <span role="img" aria-label="edit">✎</span> Request Changes
              </button>
            </div>
          ) : (
            <div className="space-y-3">
              <label htmlFor="modify-feedback" className="block text-sm font-medium" style={{ color: 'var(--color-text-muted)' }}>
                What would you like to change?
              </label>
              <textarea
                id="modify-feedback"
                value={modifyFeedback}
                onChange={(e) => setModifyFeedback(e.target.value)}
                placeholder="E.g., 'Can we reduce the workout frequency to 3 days per week?'"
                className="w-full px-4 py-3 rounded-lg resize-none focus:ring-2 focus:ring-[var(--color-violet)] focus:border-transparent"
                style={{ background: 'var(--color-bg-surface)', border: '1px solid var(--color-border)', color: 'var(--color-text-primary)' }}
                rows={4}
                autoFocus
              />
              <div className="flex gap-3">
                <button
                  onClick={handleSubmitModification}
                  disabled={!modifyFeedback.trim()}
                  className="ds-btn-primary flex-1 font-semibold py-3 px-6 disabled:opacity-40 disabled:cursor-not-allowed"
                  aria-label="Send modification feedback"
                >
                  Send Feedback
                </button>
                <button
                  onClick={handleCancelModification}
                  className="ds-btn-ghost flex-1 font-semibold py-3 px-6"
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
