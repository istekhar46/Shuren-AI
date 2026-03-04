import React from 'react';
import { Dumbbell } from 'lucide-react';
import type { WorkoutPlanResponse } from '../../types/workout.types';
import { TodayWorkout } from './TodayWorkout';

interface FullWorkoutPlanProps {
  plan: WorkoutPlanResponse | null;
  onRequestDemo: (exerciseName: string) => void;
}

export const FullWorkoutPlan: React.FC<FullWorkoutPlanProps> = ({ plan, onRequestDemo }) => {
  if (!plan) {
    return (
      <div className="flex flex-col items-center justify-center py-16 px-4 text-center rounded-2xl border border-[var(--color-border)] bg-[var(--color-bg-surface)]">
        <div className="w-16 h-16 mb-4 rounded-full bg-blue-500/10 flex items-center justify-center">
          <svg className="w-8 h-8 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        </div>
        <p className="text-lg font-medium text-[var(--color-text-primary)]">No full workout plan found.</p>
        <p className="mt-2 text-sm text-[var(--color-text-muted)]">Generate a plan to get started on your fitness journey.</p>
      </div>
    );
  }

  if (!plan.workout_days || plan.workout_days.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 px-4 text-center rounded-2xl border border-[var(--color-border)] bg-[var(--color-bg-surface)]">
        <div className="w-16 h-16 mb-4 rounded-full bg-purple-500/10 flex items-center justify-center">
          <svg className="w-8 h-8 text-purple-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 002-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
          </svg>
        </div>
        <p className="text-lg font-medium text-[var(--color-text-primary)]">Your workout plan has no days configured yet.</p>
        <p className="mt-2 text-sm text-[var(--color-text-muted)]">Update your current plan to add exercise days.</p>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header Card */}
      <div className="ds-card relative overflow-hidden p-8">
        <div className="hidden sm:block absolute right-8 top-8 opacity-5 pointer-events-none" style={{ color: 'var(--color-text-primary)' }}>
          <Dumbbell size={160} strokeWidth={1} />
        </div>

        <div className="relative z-10 flex flex-col md:flex-row gap-6 md:items-start justify-between">
          <div className="flex-1">
            <div 
              className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wider mb-4"
              style={{ background: 'var(--color-bg-primary)', border: '1px solid var(--color-border)', color: 'var(--color-violet)' }}
            >
              Active Program
            </div>
            
            <h2 className="text-3xl md:text-5xl font-black mb-4" style={{ color: 'var(--color-text-primary)' }}>
              {plan.plan_name}
            </h2>
            
            <div className="flex flex-wrap items-center gap-4 text-sm font-medium mb-6" style={{ color: 'var(--color-text-muted)' }}>
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg" style={{ background: 'var(--color-bg-primary)', border: '1px solid var(--color-border)' }}>
                <svg className="w-4 h-4" style={{ color: 'var(--color-violet)' }} fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
                {plan.duration_weeks} Weeks
              </div>
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg" style={{ background: 'var(--color-bg-primary)', border: '1px solid var(--color-border)' }}>
                <svg className="w-4 h-4" style={{ color: 'var(--color-pink)' }} fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
                {plan.days_per_week} Days/Week
              </div>
            </div>
            
            {plan.plan_description && (
              <p className="text-lg leading-relaxed max-w-3xl" style={{ color: 'var(--color-text-muted)' }}>
                {plan.plan_description}
              </p>
            )}
            
            {plan.plan_rationale && (
              <div className="mt-6 flex items-start gap-3 p-4 rounded-xl" style={{ background: 'var(--color-bg-primary)', border: '1px solid var(--color-border)' }}>
                <svg className="w-5 h-5 mt-0.5 shrink-0" style={{ color: 'var(--color-violet)' }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <div>
                  <h4 className="text-sm font-bold uppercase tracking-wider mb-1" style={{ color: 'var(--color-text-primary)' }}>Coach Note</h4>
                  <p className="text-sm leading-relaxed" style={{ color: 'var(--color-text-muted)' }}>
                    {plan.plan_rationale}
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Simple List View */}
      <div className="space-y-6">
        {plan.workout_days.map((day) => (
          <div key={day.id.toString()} className="ds-card overflow-hidden" style={{ padding: 0 }}>
             {/* Day Header - Flat Design */}
             <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 md:px-6 border-b" style={{ borderColor: 'var(--color-border)', background: 'var(--color-bg-primary)' }}>
               <div className="flex items-center gap-4">
                 <div className="flex items-center justify-center w-12 h-12 rounded-xl font-bold text-lg shrink-0" style={{ background: 'var(--color-bg-surface)', border: '1px solid var(--color-border)', color: 'var(--color-text-primary)' }}>
                   {day.day_number}
                 </div>
                 <div>
                   <h3 className="text-xl font-bold mb-1" style={{ color: 'var(--color-text-primary)' }}>
                     {day.day_name}
                   </h3>
                   <div className="flex flex-wrap items-center gap-2">
                     <span className="px-2 py-0.5 rounded text-xs font-semibold" style={{ background: 'var(--color-bg-surface)', border: '1px solid var(--color-border)', color: 'var(--color-violet)' }}>
                       {day.workout_type}
                     </span>
                     {day.estimated_duration_minutes && (
                       <span className="text-xs font-medium" style={{ color: 'var(--color-text-muted)' }}>
                         • {day.estimated_duration_minutes} min
                       </span>
                     )}
                   </div>
                 </div>
               </div>
             </div>
             
             {/* Day Exercises List */}
             <div className="bg-transparent">
               <TodayWorkout 
                 workout={day} 
                 onRequestDemo={onRequestDemo} 
                 hideHeader={true}
               />
             </div>
          </div>
        ))}
      </div>
    </div>
  );
};
