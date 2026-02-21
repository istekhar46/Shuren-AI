import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useUser } from '../contexts/UserContext';
import { ProfileSummary } from '../components/dashboard/ProfileSummary';
import { MealPlanSummary } from '../components/dashboard/MealPlanSummary';
import { WorkoutScheduleSummary } from '../components/dashboard/WorkoutScheduleSummary';
import { QuickActions } from '../components/dashboard/QuickActions';

export const DashboardPage: React.FC = () => {
  const { user, logout } = useAuth();
  const { profile, refreshProfile, loading, error } = useUser();
  const navigate = useNavigate();

  useEffect(() => {
    // Fetch profile on mount
    refreshProfile().catch((err) => {
      console.error('Failed to load profile:', err);
    });
  }, [refreshProfile]);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  if (loading && !profile) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading your dashboard...</p>
        </div>
      </div>
    );
  }

  if (error && !profile) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 mb-4">{error}</p>
          <button
            onClick={() => refreshProfile()}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-600">No profile found. Please complete onboarding.</p>
          <button
            onClick={() => navigate('/onboarding')}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            Start Onboarding
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="container mx-auto px-4 py-4">
          <div className="flex justify-between items-center">
            <h1 className="text-2xl font-bold text-gray-900">Shuren AI Dashboard</h1>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-600">Welcome, {user?.email}</span>
              <button
                onClick={handleLogout}
                className="px-4 py-2 text-sm bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Profile Summary */}
          <ProfileSummary profile={profile} />

          {/* Meal Plan Summary */}
          <MealPlanSummary profile={profile} />

          {/* Workout Schedule Summary */}
          <WorkoutScheduleSummary profile={profile} />

          {/* Quick Actions */}
          <QuickActions />
        </div>
      </main>
    </div>
  );
};
