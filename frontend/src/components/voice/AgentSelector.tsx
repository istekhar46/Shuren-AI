import React from 'react';
import type { AgentType } from '../../types';

interface AgentSelectorProps {
  value: AgentType;
  onChange: (agentType: AgentType) => void;
  disabled?: boolean;
}

const agentOptions: { value: AgentType; label: string }[] = [
  { value: 'workout_planning', label: 'Workout Planning' },
  { value: 'diet_planning', label: 'Diet Planning' },
  { value: 'supplement_guidance', label: 'Supplement Guidance' },
  { value: 'tracking_adjustment', label: 'Tracking & Adjustment' },
  { value: 'scheduling_reminder', label: 'Scheduling & Reminder' },
  { value: 'general_assistant', label: 'General Assistant' },
];

export const AgentSelector: React.FC<AgentSelectorProps> = ({
  value,
  onChange,
  disabled = false,
}) => {
  return (
    <div className="flex flex-col gap-2">
      <label htmlFor="agent-select" className="text-sm font-medium">
        Select Agent:
      </label>
      <select
        id="agent-select"
        value={value}
        onChange={(e) => onChange(e.target.value as AgentType)}
        disabled={disabled}
        className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
      >
        {agentOptions.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </div>
  );
};
