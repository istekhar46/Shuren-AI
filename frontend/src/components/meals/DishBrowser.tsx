import { useState, useEffect } from 'react';
import type { Dish } from '../../types';
import { mealService } from '../../services/mealService';

interface DishBrowserProps {
  onDishSelect?: (dish: Dish) => void;
}

export const DishBrowser = ({ onDishSelect }: DishBrowserProps) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [dishes, setDishes] = useState<Dish[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedDish, setSelectedDish] = useState<Dish | null>(null);

  useEffect(() => {
    // Debounce search
    const timer = setTimeout(() => {
      if (searchQuery.trim()) {
        handleSearch();
      } else {
        setDishes([]);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [searchQuery]);

  const handleSearch = async () => {
    try {
      setLoading(true);
      setError(null);
      const results = await mealService.searchDishes(searchQuery);
      setDishes(results);
    } catch (err) {
      setError('Failed to search dishes. Please try again.');
      console.error('Dish search error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDishClick = (dish: Dish) => {
    setSelectedDish(dish);
    if (onDishSelect) {
      onDishSelect(dish);
    }
  };

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-2xl font-semibold text-gray-900 mb-4">Browse Dishes</h2>
        
        {/* Search Input */}
        <div className="relative">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search for dishes..."
            className="w-full px-4 py-3 pl-10 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <svg
            className="absolute left-3 top-3.5 w-5 h-5 text-gray-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
          {error}
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
        </div>
      )}

      {/* Results */}
      {!loading && dishes.length > 0 && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {dishes.map((dish) => (
            <button
              key={dish.id}
              onClick={() => handleDishClick(dish)}
              className={`text-left p-4 rounded-lg border transition-all ${
                selectedDish?.id === dish.id
                  ? 'border-blue-500 bg-blue-50 shadow-md'
                  : 'border-gray-200 hover:border-blue-300 hover:shadow-md'
              }`}
            >
              <h3 className="font-semibold text-gray-900 mb-2">{dish.name}</h3>
              <p className="text-sm text-gray-600 mb-3 line-clamp-2">{dish.description}</p>
              
              <div className="flex flex-wrap gap-2 text-xs text-gray-600 mb-3">
                <span className="bg-gray-100 px-2 py-1 rounded">{dish.macros.calories} cal</span>
                <span className="bg-gray-100 px-2 py-1 rounded">P: {dish.macros.protein}g</span>
                <span className="bg-gray-100 px-2 py-1 rounded">C: {dish.macros.carbs}g</span>
                <span className="bg-gray-100 px-2 py-1 rounded">F: {dish.macros.fats}g</span>
              </div>

              <div className="flex gap-3 text-xs text-gray-500">
                <span>⏱️ Prep: {dish.prepTime}m</span>
                <span>🔥 Cook: {dish.cookTime}m</span>
              </div>
            </button>
          ))}
        </div>
      )}

      {/* No Results */}
      {!loading && searchQuery && dishes.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          <p>No dishes found for "{searchQuery}"</p>
          <p className="text-sm mt-2">Try a different search term</p>
        </div>
      )}

      {/* Empty State */}
      {!loading && !searchQuery && dishes.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          <svg
            className="w-16 h-16 mx-auto mb-4 text-gray-300"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
          <p>Search for dishes to browse available options</p>
        </div>
      )}
    </div>
  );
};
