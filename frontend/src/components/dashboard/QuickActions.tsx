import React from 'react';
import { useNavigate } from 'react-router-dom';
import '../../pages/DashboardPage.css';

const actions = [
  {
    title: 'Chat with AI',
    description: 'Get personalized guidance from your coach',
    icon: '💬',
    accent: 'violet',
    iconBg: 'rgba(167,139,250,0.12)',
    path: '/chat',
  },
  {
    title: 'Meal Plans',
    description: 'View meals, browse dishes, shop lists',
    icon: '🍽️',
    accent: 'coral',
    iconBg: 'rgba(251,146,60,0.12)',
    path: '/meals',
  },
  {
    title: 'Workouts',
    description: 'Track exercises and follow your plan',
    icon: '💪',
    accent: 'emerald',
    iconBg: 'rgba(52,211,153,0.12)',
    path: '/workouts',
  },
];

export const QuickActions: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="ds-card" style={{ height: '100%' }}>
      <h2 className="text-lg font-semibold mb-4" style={{ color: 'var(--color-text-primary)' }}>⚡ Quick Actions</h2>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {actions.map((action) => (
          <button
            key={action.title}
            onClick={() => navigate(action.path)}
            className={`dash-action dash-action--${action.accent}`}
          >
            <div className="dash-action-icon" style={{ background: action.iconBg }}>
              {action.icon}
            </div>
            <div className="min-w-0">
              <h3 className="font-semibold text-sm" style={{ color: 'var(--color-text-primary)' }}>
                {action.title}
              </h3>
              <p className="text-xs mt-0.5 truncate" style={{ color: 'var(--color-text-muted)' }}>
                {action.description}
              </p>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
};
