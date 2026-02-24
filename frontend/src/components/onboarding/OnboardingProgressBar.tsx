import React, { useState } from 'react';
import type { StateMetadata } from '../../types/onboarding.types';

interface OnboardingProgressBarProps {
  currentState: number;
  totalStates: number;
  completionPercentage: number;
  stateMetadata: StateMetadata | null;
  completedStates: number[];
}

export const OnboardingProgressBar: React.FC<OnboardingProgressBarProps> = ({
  currentState,
  totalStates,
  completionPercentage,
  stateMetadata,
  completedStates,
}) => {
  const [isCollapsed, setIsCollapsed] = useState(false);

  const allStates = [
    { number: 1, name: 'Fitness Assessment', agent: 'fitness_assessment' },
    { number: 2, name: 'Workout Planning', agent: 'workout_planning' },
    { number: 3, name: 'Diet Planning', agent: 'diet_planning' },
    { number: 4, name: 'Scheduling', agent: 'scheduling' },
  ];

  const getStateStatus = (stateNumber: number): 'completed' | 'current' | 'upcoming' => {
    if (stateNumber < 1 || stateNumber > 4) return 'upcoming';
    if (completedStates.includes(stateNumber)) return 'completed';
    if (stateNumber === currentState) return 'current';
    return 'upcoming';
  };

  const stateStyle = (status: 'completed' | 'current' | 'upcoming') => {
    if (status === 'current') return { background: 'rgba(167,139,250,0.12)', border: '2px solid var(--color-violet)' };
    if (status === 'completed') return { background: 'rgba(52,211,153,0.08)', border: '1px solid rgba(52,211,153,0.3)' };
    return { background: 'var(--color-bg-surface)', border: '1px solid var(--color-border)' };
  };

  const stateTextColor = (status: 'completed' | 'current' | 'upcoming') => {
    if (status === 'current') return 'var(--color-violet)';
    if (status === 'completed') return '#34d399';
    return 'var(--color-text-faint)';
  };

  const StatusIcon = ({ status }: { status: 'completed' | 'current' | 'upcoming' }) => {
    if (status === 'completed') {
      return (
        <div className="w-6 h-6 rounded-full flex items-center justify-center" style={{ background: '#34d399' }}>
          <svg className="w-4 h-4 text-white" fill="none" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" viewBox="0 0 24 24" stroke="currentColor">
            <path d="M5 13l4 4L19 7" />
          </svg>
        </div>
      );
    }
    if (status === 'current') {
      return (
        <div className="w-6 h-6 rounded-full flex items-center justify-center animate-pulse" style={{ background: 'var(--color-violet)' }}>
          <svg className="w-4 h-4 text-white" fill="none" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" viewBox="0 0 24 24" stroke="currentColor">
            <path d="M9 5l7 7-7 7" />
          </svg>
        </div>
      );
    }
    return <div className="w-6 h-6 rounded-full" style={{ background: 'rgba(255,255,255,0.08)', border: '1px solid var(--color-border)' }} />;
  };

  return (
    <>
      {/* Desktop Sidebar */}
      <div className="hidden lg:block lg:w-80 lg:flex-shrink-0">
        <div className="h-full ds-card overflow-y-auto" style={{ borderRadius: 'var(--radius-lg)' }}>
          {/* Progress Header */}
          <div className="mb-4">
            <div className="flex justify-between items-center mb-2">
              <h2 className="text-lg font-semibold" style={{ color: 'var(--color-text-primary)' }}>Progress</h2>
              <span className="text-sm font-medium" style={{ color: 'var(--color-violet)' }}>{Math.round(completionPercentage)}%</span>
            </div>
            <div className="w-full h-3 rounded-full overflow-hidden" style={{ background: 'rgba(255,255,255,0.06)' }}
              role="progressbar" aria-valuenow={Math.round(completionPercentage)} aria-valuemin={0} aria-valuemax={100}
              aria-label={`Onboarding progress: ${Math.round(completionPercentage)}% complete`}
            >
              <div className="h-full rounded-full transition-all duration-500 ease-out" style={{ width: `${completionPercentage}%`, background: 'var(--gradient-accent)' }} />
            </div>
            <p className="text-xs mt-2" style={{ color: 'var(--color-text-faint)' }}>Step {currentState} of {totalStates}</p>
          </div>

          {/* Current State Info */}
          {stateMetadata && (
            <div className="mb-6 p-4 rounded-lg transition-all duration-300" style={{ background: 'rgba(167,139,250,0.08)', border: '1px solid rgba(167,139,250,0.2)' }}>
              <h3 className="text-md font-semibold mb-1" style={{ color: 'var(--color-violet)' }}>{stateMetadata.name}</h3>
              <p className="text-sm" style={{ color: 'var(--color-text-muted)' }}>{stateMetadata.description}</p>
            </div>
          )}

          {/* State List */}
          <div className="space-y-2">
            <h3 className="text-sm font-medium mb-3" style={{ color: 'var(--color-text-muted)' }}>All Steps</h3>
            {allStates.map((state) => {
              const status = getStateStatus(state.number);
              return (
                <div key={state.number} className="flex items-center p-3 rounded-lg transition-all duration-300" style={stateStyle(status)}
                  aria-label={`Step ${state.number}: ${state.name} - ${status}`}>
                  <div className="flex-shrink-0 mr-3"><StatusIcon status={status} /></div>
                  <p className="text-sm font-medium" style={{ color: stateTextColor(status) }}>{state.number}. {state.name}</p>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Mobile Collapsible */}
      <div className="lg:hidden mb-4">
        <div className="ds-card overflow-hidden">
          <button
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="w-full px-4 py-3 flex items-center justify-between transition-colors duration-200"
            style={{ background: 'rgba(167,139,250,0.08)' }}
            aria-expanded={!isCollapsed} aria-controls="mobile-progress-content"
          >
            <div className="flex items-center space-x-3">
              <span className="text-lg font-semibold" style={{ color: 'var(--color-text-primary)' }}>Progress</span>
              <span className="text-sm font-medium" style={{ color: 'var(--color-violet)' }}>{Math.round(completionPercentage)}%</span>
            </div>
            <svg className={`w-5 h-5 transition-transform duration-300 ${isCollapsed ? '' : 'rotate-180'}`} style={{ color: 'var(--color-text-muted)' }}
              fill="none" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" viewBox="0 0 24 24" stroke="currentColor">
              <path d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          <div className="px-4 py-2">
            <div className="w-full h-2 rounded-full overflow-hidden" style={{ background: 'rgba(255,255,255,0.06)' }}
              role="progressbar" aria-valuenow={Math.round(completionPercentage)} aria-valuemin={0} aria-valuemax={100}
              aria-label={`Onboarding progress: ${Math.round(completionPercentage)}% complete`}
            >
              <div className="h-full rounded-full transition-all duration-500 ease-out" style={{ width: `${completionPercentage}%`, background: 'var(--gradient-accent)' }} />
            </div>
            <p className="text-xs mt-1" style={{ color: 'var(--color-text-faint)' }}>Step {currentState} of {totalStates}</p>
          </div>

          <div id="mobile-progress-content"
            className={`transition-all duration-300 ease-in-out overflow-hidden ${isCollapsed ? 'max-h-0' : 'max-h-[600px]'}`}>
            <div className="px-4 pb-4">
              {stateMetadata && (
                <div className="mb-4 p-3 rounded-lg" style={{ background: 'rgba(167,139,250,0.08)', border: '1px solid rgba(167,139,250,0.2)' }}>
                  <h3 className="text-sm font-semibold mb-1" style={{ color: 'var(--color-violet)' }}>{stateMetadata.name}</h3>
                  <p className="text-xs" style={{ color: 'var(--color-text-muted)' }}>{stateMetadata.description}</p>
                </div>
              )}
              <div className="space-y-2">
                <h3 className="text-xs font-medium mb-2" style={{ color: 'var(--color-text-muted)' }}>All Steps</h3>
                {allStates.map((state) => {
                  const status = getStateStatus(state.number);
                  return (
                    <div key={state.number} className="flex items-center p-2 rounded-lg transition-all duration-300" style={stateStyle(status)}
                      aria-label={`Step ${state.number}: ${state.name} - ${status}`}>
                      <div className="flex-shrink-0 mr-2"><StatusIcon status={status} /></div>
                      <p className="text-xs font-medium" style={{ color: stateTextColor(status) }}>{state.number}. {state.name}</p>
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
