import { useState, useEffect } from 'react';
import type { ShoppingList as ShoppingListType } from '../../types';
import { mealService } from '../../services/mealService';

interface ShoppingListProps {
  startDate: string;
  endDate: string;
}

export const ShoppingList = ({ startDate, endDate }: ShoppingListProps) => {
  const [shoppingList, setShoppingList] = useState<ShoppingListType | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (startDate && endDate) {
      generateList();
    }
  }, [startDate, endDate]);

  const generateList = async () => {
    try {
      setLoading(true);
      setError(null);
      const list = await mealService.generateShoppingList(startDate, endDate);
      setShoppingList(list);
    } catch (err) {
      setError('Failed to generate shopping list. Please try again.');
      console.error('Shopping list error:', err);
    } finally {
      setLoading(false);
    }
  };

  // Group items by category
  const itemsByCategory = shoppingList?.items.reduce((acc, item) => {
    const category = item.ingredient.category || 'Other';
    if (!acc[category]) {
      acc[category] = [];
    }
    acc[category].push(item);
    return acc;
  }, {} as Record<string, typeof shoppingList.items>);

  const categories = itemsByCategory ? Object.keys(itemsByCategory).sort() : [];

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
        {error}
        <button
          onClick={generateList}
          className="ml-4 text-sm underline hover:no-underline"
        >
          Try Again
        </button>
      </div>
    );
  }

  if (!shoppingList) {
    return (
      <div className="text-center py-8 text-gray-500">
        <p>Select a date range to generate your shopping list</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-semibold text-gray-900">Shopping List</h2>
          <p className="text-sm text-gray-500 mt-1">
            Generated on {new Date(shoppingList.generatedAt).toLocaleDateString()}
          </p>
        </div>
        <button
          onClick={() => window.print()}
          className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors flex items-center gap-2"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z"
            />
          </svg>
          Print
        </button>
      </div>

      {shoppingList.items.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          <p>No ingredients needed for the selected date range</p>
        </div>
      ) : itemsByCategory ? (
        <div className="space-y-6">
          {categories.map((category) => {
            const items = itemsByCategory[category];
            if (!items) return null;
            return (
              <div key={category} className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
                <h3 className="text-lg font-semibold text-gray-900 mb-3 pb-2 border-b border-gray-200">
                  {category}
                </h3>
                <ul className="space-y-2">
                  {items.map((item) => (
                    <li
                      key={item.ingredient.id}
                      className="flex items-start justify-between py-2 hover:bg-gray-50 px-2 rounded"
                    >
                      <div className="flex items-start gap-3 flex-1">
                        <input
                          type="checkbox"
                          className="mt-1 w-4 h-4 text-blue-500 rounded focus:ring-blue-500"
                        />
                        <div className="flex-1">
                          <span className="text-gray-900 font-medium">
                            {item.ingredient.name}
                          </span>
                          <div className="text-sm text-gray-500 mt-1">
                            {isNaN(item.totalQuantity) || !isFinite(item.totalQuantity) 
                              ? 'N/A' 
                              : item.totalQuantity.toFixed(2)} {item.ingredient.unit}
                            {item.meals.length > 1 && (
                              <span className="ml-2">
                                (used in {item.meals.length} meals)
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
            );
          })}
        </div>
      ) : null}

      {/* Summary */}
      {shoppingList.items.length > 0 && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center gap-2 text-blue-900">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <span className="font-medium">
              Total: {shoppingList.items.length} items across {categories.length} categories
            </span>
          </div>
        </div>
      )}
    </div>
  );
};
