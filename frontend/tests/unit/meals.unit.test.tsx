import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { MealPlanView } from '../../src/components/meals/MealPlanView';
import { DishBrowser } from '../../src/components/meals/DishBrowser';
import { ShoppingList } from '../../src/components/meals/ShoppingList';
import { MealDetails } from '../../src/components/meals/MealDetails';
import { MealsPage } from '../../src/pages/MealsPage';
import { mealService } from '../../src/services/mealService';
import type { Meal, Dish, ShoppingList as ShoppingListType } from '../../src/types';

// Mock the meal service
vi.mock('../../src/services/mealService', () => ({
  mealService: {
    getMealPlan: vi.fn(),
    getMealDetails: vi.fn(),
    searchDishes: vi.fn(),
    generateShoppingList: vi.fn(),
  },
}));

// Mock react-router-dom navigate
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe('Meal Components Unit Tests', () => {
  const mockMeals: Meal[] = [
    {
      id: '1',
      mealType: 'breakfast',
      dish: {
        id: 'd1',
        name: 'Oatmeal with Berries',
        description: 'Healthy breakfast',
        ingredients: [
          { id: 'i1', name: 'Oats', quantity: 50, unit: 'g', category: 'Grains' },
          { id: 'i2', name: 'Blueberries', quantity: 100, unit: 'g', category: 'Fruits' },
        ],
        instructions: ['Cook oats', 'Add berries'],
        macros: { calories: 300, protein: 10, carbs: 50, fats: 5 },
        prepTime: 5,
        cookTime: 10,
      },
      scheduledTime: '08:00',
      date: '2024-01-15',
    },
    {
      id: '2',
      mealType: 'lunch',
      dish: {
        id: 'd2',
        name: 'Grilled Chicken Salad',
        description: 'Protein-rich lunch',
        ingredients: [
          { id: 'i3', name: 'Chicken Breast', quantity: 150, unit: 'g', category: 'Protein' },
          { id: 'i4', name: 'Mixed Greens', quantity: 100, unit: 'g', category: 'Vegetables' },
        ],
        instructions: ['Grill chicken', 'Toss salad'],
        macros: { calories: 400, protein: 35, carbs: 20, fats: 15 },
        prepTime: 10,
        cookTime: 15,
      },
      scheduledTime: '12:30',
      date: '2024-01-15',
    },
  ];

  const mockDishes: Dish[] = [
    {
      id: 'd1',
      name: 'Oatmeal with Berries',
      description: 'Healthy breakfast',
      ingredients: [
        { id: 'i1', name: 'Oats', quantity: 50, unit: 'g', category: 'Grains' },
      ],
      instructions: ['Cook oats'],
      macros: { calories: 300, protein: 10, carbs: 50, fats: 5 },
      prepTime: 5,
      cookTime: 10,
    },
    {
      id: 'd2',
      name: 'Grilled Chicken',
      description: 'Protein-rich meal',
      ingredients: [
        { id: 'i2', name: 'Chicken', quantity: 150, unit: 'g', category: 'Protein' },
      ],
      instructions: ['Grill chicken'],
      macros: { calories: 250, protein: 40, carbs: 0, fats: 10 },
      prepTime: 5,
      cookTime: 20,
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    mockNavigate.mockClear();
  });

  describe('MealPlanView', () => {
    it('should display empty state when no meals', () => {
      const onMealClick = vi.fn();
      render(<MealPlanView meals={[]} onMealClick={onMealClick} />);

      expect(screen.getByText(/No meals scheduled/i)).toBeInTheDocument();
    });

    it('should render all meals grouped by date', () => {
      const onMealClick = vi.fn();
      render(<MealPlanView meals={mockMeals} onMealClick={onMealClick} />);

      expect(screen.getByText('Oatmeal with Berries')).toBeInTheDocument();
      expect(screen.getByText('Grilled Chicken Salad')).toBeInTheDocument();
    });

    it('should display meal type and scheduled time', () => {
      const onMealClick = vi.fn();
      render(<MealPlanView meals={mockMeals} onMealClick={onMealClick} />);

      // Meal types are lowercase in the component
      expect(screen.getByText('breakfast')).toBeInTheDocument();
      expect(screen.getByText('lunch')).toBeInTheDocument();
      expect(screen.getByText('08:00')).toBeInTheDocument();
      expect(screen.getByText('12:30')).toBeInTheDocument();
    });

    it('should display macros for each meal', () => {
      const onMealClick = vi.fn();
      render(<MealPlanView meals={mockMeals} onMealClick={onMealClick} />);

      expect(screen.getByText('300 cal')).toBeInTheDocument();
      expect(screen.getByText('P: 10g')).toBeInTheDocument();
      expect(screen.getByText('C: 50g')).toBeInTheDocument();
    });

    it('should call onMealClick when meal is clicked', async () => {
      const onMealClick = vi.fn();
      const user = userEvent.setup();
      render(<MealPlanView meals={mockMeals} onMealClick={onMealClick} />);

      const mealButton = screen.getByText('Oatmeal with Berries').closest('button');
      await user.click(mealButton!);

      expect(onMealClick).toHaveBeenCalledWith(mockMeals[0]);
    });

    it('should group meals by date correctly', () => {
      const mealsMultipleDays: Meal[] = [
        { ...mockMeals[0], date: '2024-01-15' },
        { ...mockMeals[1], date: '2024-01-16' },
      ];
      const onMealClick = vi.fn();
      render(<MealPlanView meals={mealsMultipleDays} onMealClick={onMealClick} />);

      // Should show two different days
      const dayHeaders = screen.getAllByRole('heading', { level: 3 });
      expect(dayHeaders.length).toBeGreaterThanOrEqual(2);
    });
  });

  describe('DishBrowser', () => {
    it('should render search input', () => {
      render(<DishBrowser />);

      expect(screen.getByPlaceholderText(/Search for dishes/i)).toBeInTheDocument();
    });

    it('should display empty state initially', () => {
      render(<DishBrowser />);

      expect(screen.getByText(/Search for dishes to browse/i)).toBeInTheDocument();
    });

    it('should search dishes when typing', async () => {
      vi.mocked(mealService.searchDishes).mockResolvedValue(mockDishes);
      const user = userEvent.setup();
      render(<DishBrowser />);

      const searchInput = screen.getByPlaceholderText(/Search for dishes/i);
      await user.type(searchInput, 'chicken');

      await waitFor(() => {
        expect(mealService.searchDishes).toHaveBeenCalledWith('chicken');
      });
    });

    it('should display search results', async () => {
      vi.mocked(mealService.searchDishes).mockResolvedValue(mockDishes);
      const user = userEvent.setup();
      render(<DishBrowser />);

      const searchInput = screen.getByPlaceholderText(/Search for dishes/i);
      await user.type(searchInput, 'oat');

      await waitFor(() => {
        expect(screen.getByText('Oatmeal with Berries')).toBeInTheDocument();
        expect(screen.getByText('Grilled Chicken')).toBeInTheDocument();
      });
    });

    it('should display dish macros and timing', async () => {
      vi.mocked(mealService.searchDishes).mockResolvedValue([mockDishes[0]]);
      const user = userEvent.setup();
      render(<DishBrowser />);

      const searchInput = screen.getByPlaceholderText(/Search for dishes/i);
      await user.type(searchInput, 'oat');

      await waitFor(() => {
        expect(screen.getByText('300 cal')).toBeInTheDocument();
        expect(screen.getByText('P: 10g')).toBeInTheDocument();
        expect(screen.getByText(/Prep: 5m/i)).toBeInTheDocument();
        expect(screen.getByText(/Cook: 10m/i)).toBeInTheDocument();
      });
    });

    it('should call onDishSelect when dish is clicked', async () => {
      const onDishSelect = vi.fn();
      vi.mocked(mealService.searchDishes).mockResolvedValue([mockDishes[0]]);
      const user = userEvent.setup();
      render(<DishBrowser onDishSelect={onDishSelect} />);

      const searchInput = screen.getByPlaceholderText(/Search for dishes/i);
      await user.type(searchInput, 'oat');

      await waitFor(() => {
        expect(screen.getByText('Oatmeal with Berries')).toBeInTheDocument();
      });

      const dishButton = screen.getByText('Oatmeal with Berries').closest('button');
      await user.click(dishButton!);

      expect(onDishSelect).toHaveBeenCalledWith(mockDishes[0]);
    });

    it('should display error message on search failure', async () => {
      vi.mocked(mealService.searchDishes).mockRejectedValue(new Error('Search failed'));
      const user = userEvent.setup();
      render(<DishBrowser />);

      const searchInput = screen.getByPlaceholderText(/Search for dishes/i);
      await user.type(searchInput, 'test');

      await waitFor(() => {
        expect(screen.getByText(/Failed to search dishes/i)).toBeInTheDocument();
      });
    });

    it('should display no results message when search returns empty', async () => {
      vi.mocked(mealService.searchDishes).mockResolvedValue([]);
      const user = userEvent.setup();
      render(<DishBrowser />);

      const searchInput = screen.getByPlaceholderText(/Search for dishes/i);
      await user.type(searchInput, 'nonexistent');

      await waitFor(() => {
        expect(screen.getByText(/No dishes found for "nonexistent"/i)).toBeInTheDocument();
      });
    });

    it('should show loading state while searching', async () => {
      vi.mocked(mealService.searchDishes).mockImplementation(
        () => new Promise((resolve) => setTimeout(() => resolve(mockDishes), 100))
      );
      const user = userEvent.setup();
      render(<DishBrowser />);

      const searchInput = screen.getByPlaceholderText(/Search for dishes/i);
      await user.type(searchInput, 'test');

      // Should show loading spinner
      await waitFor(() => {
        const spinner = document.querySelector('.animate-spin');
        expect(spinner).toBeInTheDocument();
      });
    });
  });

  describe('ShoppingList', () => {
    const mockShoppingList: ShoppingListType = {
      items: [
        {
          ingredient: { id: 'i1', name: 'Oats', quantity: 50, unit: 'g', category: 'Grains' },
          totalQuantity: 150,
          meals: ['m1', 'm2'],
        },
        {
          ingredient: { id: 'i2', name: 'Chicken', quantity: 150, unit: 'g', category: 'Protein' },
          totalQuantity: 300,
          meals: ['m3'],
        },
      ],
      generatedAt: '2024-01-15T10:00:00Z',
    };

    it('should generate shopping list on mount', async () => {
      vi.mocked(mealService.generateShoppingList).mockResolvedValue(mockShoppingList);
      render(<ShoppingList startDate="2024-01-15" endDate="2024-01-22" />);

      await waitFor(() => {
        expect(mealService.generateShoppingList).toHaveBeenCalledWith('2024-01-15', '2024-01-22');
      });
    });

    it('should display shopping list items grouped by category', async () => {
      vi.mocked(mealService.generateShoppingList).mockResolvedValue(mockShoppingList);
      render(<ShoppingList startDate="2024-01-15" endDate="2024-01-22" />);

      await waitFor(() => {
        expect(screen.getByText('Grains')).toBeInTheDocument();
        expect(screen.getByText('Protein')).toBeInTheDocument();
        expect(screen.getByText('Oats')).toBeInTheDocument();
        expect(screen.getByText('Chicken')).toBeInTheDocument();
      });
    });

    it('should display total quantity for each ingredient', async () => {
      vi.mocked(mealService.generateShoppingList).mockResolvedValue(mockShoppingList);
      render(<ShoppingList startDate="2024-01-15" endDate="2024-01-22" />);

      await waitFor(() => {
        expect(screen.getByText(/150\.00/)).toBeInTheDocument();
        expect(screen.getByText(/300\.00/)).toBeInTheDocument();
      });
    });

    it('should show meal count for ingredients used in multiple meals', async () => {
      vi.mocked(mealService.generateShoppingList).mockResolvedValue(mockShoppingList);
      render(<ShoppingList startDate="2024-01-15" endDate="2024-01-22" />);

      await waitFor(() => {
        expect(screen.getByText(/used in 2 meals/i)).toBeInTheDocument();
      });
    });

    it('should display summary with total items and categories', async () => {
      vi.mocked(mealService.generateShoppingList).mockResolvedValue(mockShoppingList);
      render(<ShoppingList startDate="2024-01-15" endDate="2024-01-22" />);

      await waitFor(() => {
        expect(screen.getByText(/Total: 2 items across 2 categories/i)).toBeInTheDocument();
      });
    });

    it('should display error message on generation failure', async () => {
      vi.mocked(mealService.generateShoppingList).mockRejectedValue(new Error('Failed'));
      render(<ShoppingList startDate="2024-01-15" endDate="2024-01-22" />);

      await waitFor(() => {
        expect(screen.getByText(/Failed to generate shopping list/i)).toBeInTheDocument();
      });
    });

    it('should show loading state while generating', async () => {
      vi.mocked(mealService.generateShoppingList).mockImplementation(
        () => new Promise((resolve) => setTimeout(() => resolve(mockShoppingList), 100))
      );
      render(<ShoppingList startDate="2024-01-15" endDate="2024-01-22" />);

      // Should show loading spinner
      const spinner = document.querySelector('.animate-spin');
      expect(spinner).toBeInTheDocument();
    });

    it('should display empty state when no items', async () => {
      vi.mocked(mealService.generateShoppingList).mockResolvedValue({
        items: [],
        generatedAt: '2024-01-15T10:00:00Z',
      });
      render(<ShoppingList startDate="2024-01-15" endDate="2024-01-22" />);

      await waitFor(() => {
        expect(screen.getByText(/No ingredients needed/i)).toBeInTheDocument();
      });
    });

    it('should render print button', async () => {
      vi.mocked(mealService.generateShoppingList).mockResolvedValue(mockShoppingList);
      render(<ShoppingList startDate="2024-01-15" endDate="2024-01-22" />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /print/i })).toBeInTheDocument();
      });
    });
  });

  describe('MealDetails', () => {
    it('should not render when meal is null', () => {
      const onClose = vi.fn();
      const { container } = render(<MealDetails meal={null} onClose={onClose} />);

      expect(container.firstChild).toBeNull();
    });

    it('should render meal details when meal is provided', () => {
      const onClose = vi.fn();
      render(
        <BrowserRouter>
          <MealDetails meal={mockMeals[0]} onClose={onClose} />
        </BrowserRouter>
      );

      expect(screen.getByText('Oatmeal with Berries')).toBeInTheDocument();
      // Use getAllByText since "Breakfast" appears in both the header and description
      const breakfastElements = screen.getAllByText(/Breakfast/i);
      expect(breakfastElements.length).toBeGreaterThan(0);
    });

    it('should display nutrition information', () => {
      const onClose = vi.fn();
      render(
        <BrowserRouter>
          <MealDetails meal={mockMeals[0]} onClose={onClose} />
        </BrowserRouter>
      );

      expect(screen.getByText('300')).toBeInTheDocument(); // Calories
      expect(screen.getByText('10g')).toBeInTheDocument(); // Protein
      expect(screen.getByText('50g')).toBeInTheDocument(); // Carbs
      expect(screen.getByText('5g')).toBeInTheDocument(); // Fats
    });

    it('should display ingredients list', () => {
      const onClose = vi.fn();
      render(
        <BrowserRouter>
          <MealDetails meal={mockMeals[0]} onClose={onClose} />
        </BrowserRouter>
      );

      expect(screen.getByText(/50 g Oats/)).toBeInTheDocument();
      expect(screen.getByText(/100 g Blueberries/)).toBeInTheDocument();
    });

    it('should display cooking instructions', () => {
      const onClose = vi.fn();
      render(
        <BrowserRouter>
          <MealDetails meal={mockMeals[0]} onClose={onClose} />
        </BrowserRouter>
      );

      expect(screen.getByText('Cook oats')).toBeInTheDocument();
      expect(screen.getByText('Add berries')).toBeInTheDocument();
    });

    it('should display prep and cook time', () => {
      const onClose = vi.fn();
      render(
        <BrowserRouter>
          <MealDetails meal={mockMeals[0]} onClose={onClose} />
        </BrowserRouter>
      );

      expect(screen.getByText(/Prep: 5 min/i)).toBeInTheDocument();
      expect(screen.getByText(/Cook: 10 min/i)).toBeInTheDocument();
    });

    it('should call onClose when close button is clicked', async () => {
      const onClose = vi.fn();
      const user = userEvent.setup();
      render(
        <BrowserRouter>
          <MealDetails meal={mockMeals[0]} onClose={onClose} />
        </BrowserRouter>
      );

      const closeButtons = screen.getAllByRole('button', { name: /close/i });
      await user.click(closeButtons[0]);

      expect(onClose).toHaveBeenCalledTimes(1);
    });

    it('should navigate to chat when request substitution is clicked', async () => {
      const onClose = vi.fn();
      const user = userEvent.setup();
      render(
        <BrowserRouter>
          <MealDetails meal={mockMeals[0]} onClose={onClose} />
        </BrowserRouter>
      );

      const substitutionButton = screen.getByRole('button', { name: /request substitution/i });
      await user.click(substitutionButton);

      expect(mockNavigate).toHaveBeenCalledWith('/chat', {
        state: expect.objectContaining({
          agentType: 'diet_planning',
          prefillMessage: expect.stringContaining('Oatmeal with Berries'),
        }),
      });
    });
  });

  describe('MealsPage Integration', () => {
    beforeEach(() => {
      vi.clearAllMocks();
    });

    it('should render all view mode tabs', () => {
      vi.mocked(mealService.getMealPlan).mockResolvedValue([]);
      render(
        <BrowserRouter>
          <MealsPage />
        </BrowserRouter>
      );

      expect(screen.getByRole('button', { name: /meal plan/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /browse dishes/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /shopping list/i })).toBeInTheDocument();
    });

    it('should load meal plan on mount', async () => {
      vi.mocked(mealService.getMealPlan).mockResolvedValue(mockMeals);
      render(
        <BrowserRouter>
          <MealsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(mealService.getMealPlan).toHaveBeenCalled();
      });
    });

    it('should switch to browse dishes view', async () => {
      vi.mocked(mealService.getMealPlan).mockResolvedValue([]);
      const user = userEvent.setup();
      render(
        <BrowserRouter>
          <MealsPage />
        </BrowserRouter>
      );

      const browseDishesTab = screen.getByRole('button', { name: /browse dishes/i });
      await user.click(browseDishesTab);

      expect(screen.getByPlaceholderText(/Search for dishes/i)).toBeInTheDocument();
    });

    it('should switch to shopping list view', async () => {
      vi.mocked(mealService.getMealPlan).mockResolvedValue([]);
      vi.mocked(mealService.generateShoppingList).mockResolvedValue({
        items: [],
        generatedAt: '2024-01-15T10:00:00Z',
      });
      const user = userEvent.setup();
      render(
        <BrowserRouter>
          <MealsPage />
        </BrowserRouter>
      );

      const shoppingListTab = screen.getByRole('button', { name: /shopping list/i });
      await user.click(shoppingListTab);

      // Use getAllByText since "Shopping List" appears in both the tab and the heading
      await waitFor(() => {
        const shoppingListElements = screen.getAllByText('Shopping List');
        expect(shoppingListElements.length).toBeGreaterThan(1);
      });
    });

    it('should display date range selector for meal plan view', () => {
      vi.mocked(mealService.getMealPlan).mockResolvedValue([]);
      render(
        <BrowserRouter>
          <MealsPage />
        </BrowserRouter>
      );

      expect(screen.getByLabelText(/from:/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/to:/i)).toBeInTheDocument();
    });

    it('should refresh meal plan when refresh button is clicked', async () => {
      vi.mocked(mealService.getMealPlan).mockResolvedValue(mockMeals);
      const user = userEvent.setup();
      render(
        <BrowserRouter>
          <MealsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(mealService.getMealPlan).toHaveBeenCalledTimes(1);
      });

      const refreshButton = screen.getByRole('button', { name: /refresh/i });
      await user.click(refreshButton);

      await waitFor(() => {
        expect(mealService.getMealPlan).toHaveBeenCalledTimes(2);
      });
    });

    it('should display error message on meal plan load failure', async () => {
      vi.mocked(mealService.getMealPlan).mockRejectedValue(new Error('Failed'));
      render(
        <BrowserRouter>
          <MealsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/Failed to load meal plan/i)).toBeInTheDocument();
      });
    });

    it('should open meal details when meal is clicked', async () => {
      vi.mocked(mealService.getMealPlan).mockResolvedValue(mockMeals);
      const user = userEvent.setup();
      render(
        <BrowserRouter>
          <MealsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Oatmeal with Berries')).toBeInTheDocument();
      });

      const mealButton = screen.getByText('Oatmeal with Berries').closest('button');
      await user.click(mealButton!);

      // Meal details modal should open
      await waitFor(() => {
        expect(screen.getAllByText('Oatmeal with Berries')).toHaveLength(2); // One in list, one in modal
      });
    });
  });
});
