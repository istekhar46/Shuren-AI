import React from 'react';
import type { UserProfile } from '../../types';

interface ProfileSummaryProps {
  profile: UserProfile;
}

export const ProfileSummary: React.FC<ProfileSummaryProps> = ({ profile }) => {
  const formatFitnessLevel = (level: string | undefined) => {
    if (!level || typeof level !== 'string' || level.length === 0) return 'Not set';
    return level.charAt(0).toUpperCase() + level.slice(1);
  };

  const formatEnergyLevel = (level: string | undefined) => {
    if (!level || typeof level !== 'string' || level.length === 0) return 'Not set';
    return level.charAt(0).toUpperCase() + level.slice(1);
  };

  const formatGoals = (goals: UserProfile['goals'] | undefined) => {
    if (!goals || !Array.isArray(goals) || goals.length === 0) return 'No goals set';
    return goals.map((goal) => goal.type.replace('_', ' ')).join(', ');
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-xl font-semibold text-gray-900 mb-4">Profile Summary</h2>
      
      <div className="space-y-3">
        <div className="flex justify-between items-center">
          <span className="text-sm font-medium text-gray-600">Email:</span>
          <span className="text-sm text-gray-900">{profile.email || 'Not available'}</span>
        </div>

        <div className="flex justify-between items-center">
          <span className="text-sm font-medium text-gray-600">Fitness Level:</span>
          <span className="text-sm text-gray-900">{formatFitnessLevel(profile?.fitnessLevel)}</span>
        </div>

        <div className="flex justify-between items-center">
          <span className="text-sm font-medium text-gray-600">Goals:</span>
          <span className="text-sm text-gray-900 capitalize">{formatGoals(profile?.goals)}</span>
        </div>

        <div className="flex justify-between items-center">
          <span className="text-sm font-medium text-gray-600">Energy Level:</span>
          <span className="text-sm text-gray-900">{formatEnergyLevel(profile.lifestyleBaseline?.energyLevel)}</span>
        </div>

        <div className="flex justify-between items-center">
          <span className="text-sm font-medium text-gray-600">Profile Status:</span>
          <span className={`text-sm font-medium ${profile.isLocked ? 'text-green-600' : 'text-yellow-600'}`}>
            {profile.isLocked ? 'Locked' : 'Unlocked'}
          </span>
        </div>
      </div>
    </div>
  );
};