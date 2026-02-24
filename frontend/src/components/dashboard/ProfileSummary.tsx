import React from 'react';
import type { UserProfile } from '../../types';
import '../../pages/DashboardPage.css';

interface ProfileSummaryProps {
  profile: UserProfile;
}

export const ProfileSummary: React.FC<ProfileSummaryProps> = ({ profile }) => {
  const fitnessLevel = profile?.fitnessLevel || 'beginner';
  const levelLabel = fitnessLevel.charAt(0).toUpperCase() + fitnessLevel.slice(1);

  const goals = profile?.goals || [];
  const formatGoal = (type: string) => type.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());

  const energyLevel = profile?.lifestyleBaseline?.energyLevel;
  const energyLabel = energyLevel
    ? energyLevel.charAt(0).toUpperCase() + energyLevel.slice(1)
    : 'Not set';

  return (
    <div className="ds-card" style={{ height: '100%' }}>
      <div className="flex items-start gap-4 mb-5">
        {/* Avatar */}
        <div
          className="flex-shrink-0 w-12 h-12 rounded-xl flex items-center justify-center text-xl font-bold text-white"
          style={{ background: 'var(--gradient-accent)' }}
        >
          {(profile.email?.[0] || 'U').toUpperCase()}
        </div>
        <div className="min-w-0">
          <h2 className="text-lg font-semibold truncate" style={{ color: 'var(--color-text-primary)' }}>
            {profile.email?.split('@')[0] || 'User'}
          </h2>
          <div className="flex items-center gap-2 mt-1">
            <span className={`dash-badge dash-badge--${fitnessLevel}`}>{levelLabel}</span>
            <span className="text-xs" style={{ color: 'var(--color-text-faint)' }}>
              {profile.isLocked ? '🔒 Locked' : '🔓 Unlocked'}
            </span>
          </div>
        </div>
      </div>

      {/* Energy Level */}
      <div className="flex justify-between items-center mb-4 pb-4" style={{ borderBottom: '1px solid var(--color-border)' }}>
        <span className="text-sm" style={{ color: 'var(--color-text-muted)' }}>Energy Level</span>
        <span className="text-sm font-medium" style={{ color: 'var(--color-text-primary)' }}>
          {energyLevel === 'high' ? '⚡' : energyLevel === 'medium' ? '✨' : '💤'} {energyLabel}
        </span>
      </div>

      {/* Goals */}
      <div className="dash-section-title">Goals</div>
      {goals.length > 0 ? (
        <div className="flex flex-wrap gap-2">
          {goals.map((goal, i) => (
            <span key={i} className="dash-chip">{formatGoal(goal.type)}</span>
          ))}
        </div>
      ) : (
        <p className="text-sm" style={{ color: 'var(--color-text-faint)' }}>No goals set yet</p>
      )}
    </div>
  );
};