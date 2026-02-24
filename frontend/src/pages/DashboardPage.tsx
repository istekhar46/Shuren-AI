import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useUser } from '../contexts/UserContext';
import { ProfileSummary } from '../components/dashboard/ProfileSummary';
import { MealPlanSummary } from '../components/dashboard/MealPlanSummary';
import { WorkoutScheduleSummary } from '../components/dashboard/WorkoutScheduleSummary';
import { QuickActions } from '../components/dashboard/QuickActions';
import './DashboardPage.css';

export const DashboardPage: React.FC = () => {
  const { user } = useAuth();
  const { profile, refreshProfile, loading, error } = useUser();
  const navigate = useNavigate();

  useEffect(() => {
    refreshProfile().catch((err) => {
      console.error('Failed to load profile:', err);
    });
  }, [refreshProfile]);

  /* ── Loading ── */
  if (loading && !profile) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="text-center">
          <div
            className="animate-spin rounded-full h-12 w-12 mx-auto"
            style={{ borderWidth: 3, borderColor: 'var(--color-violet)', borderTopColor: 'transparent' }}
          />
          <p className="mt-4" style={{ color: 'var(--color-text-muted)' }}>Loading your dashboard...</p>
        </div>
      </div>
    );
  }

  /* ── Error ── */
  if (error && !profile) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="text-center">
          <p className="mb-4" style={{ color: '#f87171' }}>{error}</p>
          <button onClick={() => refreshProfile()} className="ds-btn-primary">Retry</button>
        </div>
      </div>
    );
  }

  /* ── No profile ── */
  if (!profile) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="text-center">
          <p style={{ color: 'var(--color-text-muted)' }}>No profile found. Please complete onboarding.</p>
          <button onClick={() => navigate('/onboarding')} className="ds-btn-primary mt-4">Start Onboarding</button>
        </div>
      </div>
    );
  }

  /* ── Derived stats ── */
  const calories = profile.mealPlan?.dailyCalories || 0;
  const protein = profile.mealPlan?.macros?.protein || 0;
  const workoutDays = profile.workoutSchedule?.daysPerWeek || 0;
  const goalCount = profile.goals?.length || 0;

  const greeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 18) return 'Good afternoon';
    return 'Good evening';
  };

  const today = new Date().toLocaleDateString('en-US', {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
  });

  const stats = [
    { icon: '🔥', value: calories, unit: 'kcal', label: 'Daily Calories', accent: 'violet' },
    { icon: '💪', value: `${protein}g`, unit: '', label: 'Protein Target', accent: 'pink' },
    { icon: '🏋️', value: workoutDays, unit: 'days', label: 'Workout Days/Wk', accent: 'coral' },
    { icon: '🎯', value: goalCount, unit: goalCount === 1 ? 'goal' : 'goals', label: 'Active Goals', accent: 'emerald' },
  ];

  return (
    <div className="dash-grid">
      {/* ━━━ Hero Welcome Card ━━━ */}
      <div className="dash-hero dash-span-4">
        <div className="relative z-10">
          <p className="text-sm mb-1" style={{ color: 'var(--color-text-faint)' }}>{today}</p>
          <h1 className="text-2xl md:text-3xl font-bold mb-1" style={{ color: 'var(--color-text-primary)' }}>
            {greeting()}, <span className="ds-gradient-text">{user?.email?.split('@')[0] || 'there'}</span>
          </h1>
          <p style={{ color: 'var(--color-text-muted)' }}>Here's your fitness snapshot for today</p>
        </div>
      </div>

      {/* ━━━ Stat Metric Cards ━━━ */}
      {stats.map((s) => (
        <div key={s.label} className="dash-stat">
          <div className={`dash-stat-icon dash-stat-icon--${s.accent}`}>{s.icon}</div>
          <div className="dash-stat-value">
            {s.value}
            {s.unit && <span className="dash-stat-unit">{s.unit}</span>}
          </div>
          <div className="dash-stat-label">{s.label}</div>
        </div>
      ))}

      {/* ━━━ Profile + Meal Plan (side-by-side on desktop) ━━━ */}
      <div className="dash-span-2">
        <ProfileSummary profile={profile} />
      </div>
      <div className="dash-span-2">
        <MealPlanSummary profile={profile} />
      </div>

      {/* ━━━ Workout Schedule + Quick Actions (side-by-side on desktop) ━━━ */}
      <div className="dash-span-2">
        <WorkoutScheduleSummary profile={profile} />
      </div>
      <div className="dash-span-2">
        <QuickActions />
      </div>
    </div>
  );
};
