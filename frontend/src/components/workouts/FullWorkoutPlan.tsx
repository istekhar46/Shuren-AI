import React from 'react';
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
      <div className="relative overflow-hidden rounded-3xl p-8 border border-white/5 bg-slate-900/80 shadow-2xl backdrop-blur-xl">
        <div className="hidden sm:block absolute right-8 top-8 opacity-5 pointer-events-none text-white">
          <svg width="160" height="160" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round">
            <path d="M18 8h1a4 4 0 0 1 0 8h-1"></path>
            <path d="M2 8h16v9a4 4 0 0 1-4 4H6a4 4 0 0 1-4-4V8z"></path>
            <line x1="6" y1="1" x2="6" y2="4"></line>
            <line x1="10" y1="1" x2="10" y2="4"></line>
            <line x1="14" y1="1" x2="14" y2="4"></line>
          </svg>
        </div>

        <div className="relative z-10 flex flex-col md:flex-row gap-6 md:items-start justify-between">
          <div className="flex-1">
            <div className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wider mb-4 border border-sky-400/20 bg-sky-400/10 text-sky-400">
              Active Program
            </div>
            
            <h2 className="text-3xl md:text-5xl font-black mb-4 text-white">
              {plan.plan_name}
            </h2>
            
            <div className="flex flex-wrap items-center gap-4 text-sm font-medium mb-6 text-gray-300">
              <div className="flex items-center gap-2 bg-white/5 px-3 py-1.5 rounded-lg border border-white/5">
                <svg className="w-4 h-4 text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
                {plan.duration_weeks} Weeks
              </div>
              <div className="flex items-center gap-2 bg-white/5 px-3 py-1.5 rounded-lg border border-white/5">
                <svg className="w-4 h-4 text-purple-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
                {plan.days_per_week} Days/Week
              </div>
            </div>
            
            {plan.plan_description && (
              <p className="text-lg leading-relaxed max-w-3xl text-gray-300">
                {plan.plan_description}
              </p>
            )}
            
            {plan.plan_rationale && (
              <div className="mt-6 flex items-start gap-3 bg-blue-900/20 p-4 rounded-xl border border-blue-500/20">
                <svg className="w-5 h-5 text-blue-400 mt-0.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <div>
                  <h4 className="text-sm font-bold text-blue-300 uppercase tracking-wider mb-1">Coach Note</h4>
                  <p className="text-sm text-gray-300 leading-relaxed">
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
          <div key={day.id.toString()} className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-bg-surface)] overflow-hidden">
             {/* Day Header - Flat Design */}
             <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 md:px-6 border-b border-[var(--color-border)] bg-black/10">
               <div className="flex items-center gap-4">
                 <div className="flex items-center justify-center w-12 h-12 rounded-xl bg-slate-800 text-white font-bold text-lg shrink-0 border border-white/5">
                   {day.day_number}
                 </div>
                 <div>
                   <h3 className="text-xl font-bold text-white mb-1">
                     {day.day_name}
                   </h3>
                   <div className="flex flex-wrap items-center gap-2">
                     <span className="px-2 py-0.5 rounded text-xs font-semibold bg-white/5 border border-white/5 text-gray-300">
                       {day.workout_type}
                     </span>
                     {day.estimated_duration_minutes && (
                       <span className="text-xs text-gray-400 font-medium">
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
