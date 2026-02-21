import React from 'react';
import { useNavigate } from 'react-router-dom';

export const QuickActions: React.FC = () => {
  const navigate = useNavigate();

  const actions = [
    {
      title: 'Chat with AI',
      description: 'Get personalized guidance',
      icon: '💬',
      onClick: () => navigate('/chat'),
      color: 'bg-blue-50 hover:bg-blue-100 border-blue-200',
    },
    {
      title: 'Voice Session',
      description: 'Talk to your AI coach',
      icon: '🎤',
      onClick: () => navigate('/voice'),
      color: 'bg-purple-50 hover:bg-purple-100 border-purple-200',
    },
    {
      title: 'Meal Plans',
      description: 'View and manage meals',
      icon: '🍽️',
      onClick: () => navigate('/meals'),
      color: 'bg-green-50 hover:bg-green-100 border-green-200',
    },
    {
      title: 'Workouts',
      description: 'Track your exercises',
      icon: '💪',
      onClick: () => navigate('/workouts'),
      color: 'bg-orange-50 hover:bg-orange-100 border-orange-200',
    },
  ];

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-xl font-semibold text-gray-900 mb-4">Quick Actions</h2>
      
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {actions.map((action) => (
          <button
            key={action.title}
            onClick={action.onClick}
            className={`${action.color} border-2 rounded-lg p-4 text-left transition-colors duration-200`}
          >
            <div className="flex items-start space-x-3">
              <span className="text-2xl">{action.icon}</span>
              <div>
                <h3 className="font-semibold text-gray-900">{action.title}</h3>
                <p className="text-sm text-gray-600 mt-1">{action.description}</p>
              </div>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
};
