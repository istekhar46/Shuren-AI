import { useNavigate } from 'react-router-dom';
import type { Meal } from '../../types';

interface MealDetailsProps {
  meal: Meal | null;
  onClose: () => void;
}

export const MealDetails = ({ meal, onClose }: MealDetailsProps) => {
  const navigate = useNavigate();

  if (!meal) return null;

  const { dish } = meal;

  const handleRequestSubstitution = () => {
    // Navigate to chat with pre-filled message
    const message = `I would like to request a substitution for my ${meal.mealType} on ${meal.dayName}. The current dish is "${dish.name}". Can you suggest an alternative that fits my meal plan?`;
    navigate('/chat', { state: { prefillMessage: message, agentType: 'diet_planning' } });
  };

  return (
    <div className="fixed inset-0 bg-[#0a0a12]/80 backdrop-blur-sm flex items-center justify-center p-4 z-50">
      <div className="ds-card max-w-2xl w-full max-h-[90vh] overflow-y-auto !p-0 border-white/10 shadow-2xl">
        <div className="ds-card-glow" />
        
        {/* Header */}
        <div className="sticky top-0 bg-[#0a0a12]/60 backdrop-blur-md border-b border-white/10 p-6 flex items-start justify-between z-10">
          <div>
            <h2 className="text-2xl font-bold text-white tracking-tight">{dish.name}</h2>
            <p className="text-sm font-medium text-white/50 mt-1 uppercase tracking-wider">
              {meal.mealType} • {meal.scheduledTime}
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-full hover:bg-white/10 text-white/40 hover:text-white transition-all"
            aria-label="Close"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="p-8 space-y-8">
          {/* Label / Cuisine */}
          {dish.description && (
            <div className="ds-badge !lowercase first-letter:uppercase">
              <div className="ds-badge-dot" />
              {dish.description}
            </div>
          )}

          {/* Macros */}
          <div>
            <h3 className="text-sm font-bold text-white/40 uppercase tracking-widest mb-4">Nutrition Information</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-white/5 border border-white/5 rounded-xl p-4 text-center">
                <p className="text-2xl font-black text-white">{dish.macros.calories}</p>
                <p className="text-[10px] font-bold text-white/40 uppercase tracking-tighter">Calories</p>
              </div>
              <div className="bg-white/5 border border-white/5 rounded-xl p-4 text-center">
                <p className="text-2xl font-black text-violet-400">{dish.macros.protein}g</p>
                <p className="text-[10px] font-bold text-white/40 uppercase tracking-tighter">Protein</p>
              </div>
              <div className="bg-white/5 border border-white/5 rounded-xl p-4 text-center">
                <p className="text-2xl font-black text-pink-400">{dish.macros.carbs}g</p>
                <p className="text-[10px] font-bold text-white/40 uppercase tracking-tighter">Carbs</p>
              </div>
              <div className="bg-white/5 border border-white/5 rounded-xl p-4 text-center">
                <p className="text-2xl font-black text-coral-400">{dish.macros.fats}g</p>
                <p className="text-[10px] font-bold text-white/40 uppercase tracking-tighter">Fats</p>
              </div>
            </div>
          </div>

          {/* Time & Difficulty */}
          <div className="flex flex-wrap gap-6 text-sm text-white/60">
            <div className="flex items-center gap-2">
              <div className="p-2 bg-white/5 rounded-lg">
                <svg className="w-4 h-4 text-violet-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <span className="font-medium">Prep: {dish.prepTime} min</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="p-2 bg-white/5 rounded-lg">
                <svg className="w-4 h-4 text-pink-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 18.657A8 8 0 016.343 7.343S7 9 9 10c0-2 .5-5 2.986-7C14 5 16.09 5.777 17.656 7.343A7.975 7.975 0 0120 13a7.975 7.975 0 01-2.343 5.657z" />
                </svg>
              </div>
              <span className="font-medium">Cook: {dish.cookTime} min</span>
            </div>
          </div>


        </div>

        {/* Footer */}
        <div className="sticky bottom-0 bg-[#0a0a12]/80 backdrop-blur-md border-t border-white/10 p-6 flex justify-between items-center z-10">
          <button
            onClick={handleRequestSubstitution}
            className="ds-btn-primary !py-2.5"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
            </svg>
            Request Substitution
          </button>
          <button
            onClick={onClose}
            className="px-6 py-2.5 bg-white/5 hover:bg-white/10 text-white font-semibold rounded-xl border border-white/10 transition-all uppercase tracking-widest text-xs"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
