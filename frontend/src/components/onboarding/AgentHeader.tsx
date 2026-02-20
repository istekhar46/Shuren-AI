import React from 'react';
import { AgentType as OnboardingAgentType } from '../../types/onboarding.types';

interface AgentHeaderProps {
  agentType: OnboardingAgentType;
  agentDescription: string;
  currentState: number;
  totalStates: number;
  stateName: string;
}

/**
 * AgentHeader Component
 * 
 * Displays current agent context and state information at the top of the onboarding chat.
 * Shows which specialized agent the user is talking to and what information is being collected.
 * 
 * Requirements: US-2, AC-2.1, AC-2.2, AC-2.3, AC-2.4
 */
export const AgentHeader: React.FC<AgentHeaderProps> = ({
  agentType,
  agentDescription,
  currentState,
  totalStates,
  stateName,
}) => {
  /**
   * Get agent display name from agent type
   */
  const getAgentName = (type: OnboardingAgentType): string => {
    const agentNames: Record<OnboardingAgentType, string> = {
      [OnboardingAgentType.FITNESS_ASSESSMENT]: 'Fitness Assessment Agent',
      [OnboardingAgentType.GOAL_SETTING]: 'Goal Setting Agent',
      [OnboardingAgentType.WORKOUT_PLANNING]: 'Workout Planning Agent',
      [OnboardingAgentType.DIET_PLANNING]: 'Diet Planning Agent',
      [OnboardingAgentType.SCHEDULING]: 'Scheduling Agent',
    };
    return agentNames[type];
  };

  /**
   * Get agent icon emoji based on agent type
   */
  const getAgentIcon = (type: OnboardingAgentType): string => {
    const agentIcons: Record<OnboardingAgentType, string> = {
      [OnboardingAgentType.FITNESS_ASSESSMENT]: '💪',
      [OnboardingAgentType.GOAL_SETTING]: '🎯',
      [OnboardingAgentType.WORKOUT_PLANNING]: '🏋️',
      [OnboardingAgentType.DIET_PLANNING]: '🥗',
      [OnboardingAgentType.SCHEDULING]: '📅',
    };
    return agentIcons[type];
  };

  /**
   * Get agent color theme based on agent type
   */
  const getAgentColorClass = (type: OnboardingAgentType): string => {
    const agentColors: Record<OnboardingAgentType, string> = {
      [OnboardingAgentType.FITNESS_ASSESSMENT]: 'bg-purple-600',
      [OnboardingAgentType.GOAL_SETTING]: 'bg-blue-600',
      [OnboardingAgentType.WORKOUT_PLANNING]: 'bg-green-600',
      [OnboardingAgentType.DIET_PLANNING]: 'bg-orange-600',
      [OnboardingAgentType.SCHEDULING]: 'bg-indigo-600',
    };
    return agentColors[type];
  };

  const agentName = getAgentName(agentType);
  const agentIcon = getAgentIcon(agentType);
  const colorClass = getAgentColorClass(agentType);

  return (
    <div 
      className={`sticky top-0 z-10 ${colorClass} text-white shadow-lg transition-all duration-300`}
      role="banner"
      aria-label="Current onboarding agent"
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div className="flex items-center justify-between">
          {/* Agent Info */}
          <div className="flex items-center space-x-4">
            {/* Agent Icon */}
            <div 
              className="text-4xl flex-shrink-0"
              role="img"
              aria-label={`${agentName} icon`}
            >
              {agentIcon}
            </div>

            {/* Agent Details */}
            <div className="flex-grow">
              <h1 className="text-xl sm:text-2xl font-bold">
                {agentName}
              </h1>
              <p className="text-sm sm:text-base text-white/90 mt-1">
                {agentDescription}
              </p>
            </div>
          </div>

          {/* State Indicator */}
          <div className="hidden sm:flex items-center space-x-2 bg-white/20 rounded-lg px-4 py-2">
            <div className="text-right">
              <p className="text-xs text-white/80 font-medium">
                Step {currentState} of {totalStates}
              </p>
              <p className="text-sm font-semibold">
                {stateName}
              </p>
            </div>
          </div>
        </div>

        {/* Mobile State Indicator */}
        <div className="sm:hidden mt-3 bg-white/20 rounded-lg px-3 py-2">
          <p className="text-xs text-white/80 font-medium">
            Step {currentState} of {totalStates}: {stateName}
          </p>
        </div>
      </div>
    </div>
  );
};
