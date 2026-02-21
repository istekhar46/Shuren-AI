import type { AgentType } from '../../types';

interface AgentSelectorProps {
  value: AgentType;
  onChange: (agentType: AgentType) => void;
  disabled?: boolean;
}

const agentOptions: { value: AgentType; label: string; description: string }[] = [
  {
    value: 'general_assistant',
    label: 'General Assistant',
    description: 'General questions and motivation',
  },
  {
    value: 'workout_planning',
    label: 'Workout Planning',
    description: 'Exercise plans and training guidance',
  },
  {
    value: 'diet_planning',
    label: 'Diet Planning',
    description: 'Meal plans and nutrition advice',
  },
  {
    value: 'supplement_guidance',
    label: 'Supplement Guidance',
    description: 'Supplement information and recommendations',
  },
  {
    value: 'tracking_adjustment',
    label: 'Tracking & Adjustment',
    description: 'Progress tracking and plan adjustments',
  },
  {
    value: 'scheduling_reminder',
    label: 'Scheduling & Reminder',
    description: 'Schedule management and reminders',
  },
];

export const AgentSelector = ({ value, onChange, disabled }: AgentSelectorProps) => {
  return (
    <div className="w-full">
      <label htmlFor="agent-select" className="block text-sm font-medium text-gray-700 mb-2">
        Select AI Agent
      </label>
      <select
        id="agent-select"
        value={value}
        onChange={(e) => onChange(e.target.value as AgentType)}
        disabled={disabled}
        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
      >
        {agentOptions.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label} - {option.description}
          </option>
        ))}
      </select>
    </div>
  );
};
