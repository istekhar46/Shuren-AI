import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { WorkoutSchedule } from '../../src/components/workouts/WorkoutSchedule';
import { TodayWorkout } from '../../src/components/workouts/TodayWorkout';
import { ExerciseLogger } from '../../src/components/workouts/ExerciseLogger';
import { WorkoutsPage } from '../../src/pages/WorkoutsPage';
import { workoutService } from '../../src/services/workoutService';
import type { WorkoutSession, Exercise, ExerciseSet } from '../../src/types';

// Mock the workout service
vi.mock('../../src/services/workoutService', () => ({
  workoutService: {
    getSchedule: vi.fn(),
    getTodayWorkout: vi.fn(),
    logSet: vi.fn(),
    completeWorkout: vi.fn(),
    getHistory: vi.fn(),
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

describe('Workout Components Unit Tests', () => {
  const mockExercise: Exercise = {
    id: 'ex1',
    name: 'Bench Press',
    muscleGroup: 'Chest',
    sets: [
      { setNumber: 1, targetReps: 10, targetWeight: 135, actualReps: undefined, actualWeight: undefined, completed: false },
      { setNumber: 2, targetReps: 10, targetWeight: 135, actualReps: undefined, actualWeight: undefined, completed: false },
      { setNumber: 3, targetReps: 8, targetWeight: 145, actualReps: undefined, actualWeight: undefined, completed: false },
    ],
    instructions: ['Lie on bench', 'Lower bar to chest', 'Press up'],
  };

  const mockWorkoutSession: WorkoutSession = {
    id: 'session1',
    date: '2024-01-15',
    exercises: [mockExercise],
    completed: false,
  };

  const mockCompletedSession: WorkoutSession = {
    id: 'session2',
    date: '2024-01-14',
    exercises: [
      {
        ...mockExercise,
        sets: mockExercise.sets.map(set => ({ ...set, actualReps: set.targetReps, actualWeight: set.targetWeight, completed: true })),
      },
    ],
    completed: true,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    mockNavigate.mockClear();
    // Mock window.confirm and window.prompt
    global.confirm = vi.fn(() => true);
    global.prompt = vi.fn();
  });

  describe('WorkoutSchedule', () => {
    it('should display empty state when no sessions', () => {
      const onSelectSession = vi.fn();
      render(<WorkoutSchedule sessions={[]} onSelectSession={onSelectSession} />);

      expect(screen.getByText(/No workouts scheduled/i)).toBeInTheDocument();
    });

    it('should render workout sessions in calendar view', () => {
      const sessions = [mockWorkoutSession, mockCompletedSession];
      const onSelectSession = vi.fn();
      render(<WorkoutSchedule sessions={sessions} onSelectSession={onSelectSession} />);

      const exerciseTexts = screen.getAllByText(/1 exercises/);
      expect(exerciseTexts.length).toBeGreaterThan(0);
    });

    it('should display completed status for finished workouts', () => {
      const onSelectSession = vi.fn();
      render(<WorkoutSchedule sessions={[mockCompletedSession]} onSelectSession={onSelectSession} />);

      expect(screen.getByText(/✓ Done/i)).toBeInTheDocument();
    });

    it('should call onSelectSession when workout is clicked', async () => {
      const onSelectSession = vi.fn();
      const user = userEvent.setup();
      render(<WorkoutSchedule sessions={[mockWorkoutSession]} onSelectSession={onSelectSession} />);

      const workoutCard = screen.getByText(/1 exercises/).closest('div');
      await user.click(workoutCard!);

      expect(onSelectSession).toHaveBeenCalledWith(mockWorkoutSession);
    });

    it('should group sessions by week', () => {
      const sessions = [
        { ...mockWorkoutSession, date: '2024-01-15' },
        { ...mockWorkoutSession, id: 'session3', date: '2024-01-17' },
      ];
      const onSelectSession = vi.fn();
      render(<WorkoutSchedule sessions={sessions} onSelectSession={onSelectSession} />);

      expect(screen.getByText(/Week of/i)).toBeInTheDocument();
    });

    it('should display day of week for each session', () => {
      const onSelectSession = vi.fn();
      render(<WorkoutSchedule sessions={[mockWorkoutSession]} onSelectSession={onSelectSession} />);

      // Should show day abbreviations in header
      const sunElements = screen.getAllByText('Sun');
      const monElements = screen.getAllByText('Mon');
      expect(sunElements.length).toBeGreaterThan(0);
      expect(monElements.length).toBeGreaterThan(0);
    });

    it('should apply different styling for completed vs pending workouts', () => {
      const onSelectSession = vi.fn();
      const { container } = render(
        <WorkoutSchedule sessions={[mockWorkoutSession, mockCompletedSession]} onSelectSession={onSelectSession} />
      );

      const completedCard = screen.getByText(/✓ Done/i).closest('div')?.parentElement;
      expect(completedCard).toHaveClass('bg-green-50');
    });
  });

  describe('TodayWorkout', () => {
    it('should display empty state when no workout scheduled', () => {
      const onLogSet = vi.fn();
      const onRequestDemo = vi.fn();
      render(<TodayWorkout session={null} onLogSet={onLogSet} onRequestDemo={onRequestDemo} />);

      expect(screen.getByText(/No workout scheduled for today/i)).toBeInTheDocument();
    });

    it('should render workout session details', () => {
      const onLogSet = vi.fn();
      const onRequestDemo = vi.fn();
      render(<TodayWorkout session={mockWorkoutSession} onLogSet={onLogSet} onRequestDemo={onRequestDemo} />);

      expect(screen.getByText('Bench Press')).toBeInTheDocument();
      expect(screen.getByText('Chest')).toBeInTheDocument();
      expect(screen.getByText(/1 exercises/)).toBeInTheDocument();
    });

    it('should display exercise instructions', () => {
      const onLogSet = vi.fn();
      const onRequestDemo = vi.fn();
      render(<TodayWorkout session={mockWorkoutSession} onLogSet={onLogSet} onRequestDemo={onRequestDemo} />);

      expect(screen.getByText('Lie on bench')).toBeInTheDocument();
      expect(screen.getByText('Lower bar to chest')).toBeInTheDocument();
      expect(screen.getByText('Press up')).toBeInTheDocument();
    });

    it('should display all sets with target reps and weight', () => {
      const onLogSet = vi.fn();
      const onRequestDemo = vi.fn();
      render(<TodayWorkout session={mockWorkoutSession} onLogSet={onLogSet} onRequestDemo={onRequestDemo} />);

      expect(screen.getByText(/Set 1/)).toBeInTheDocument();
      expect(screen.getByText(/Set 2/)).toBeInTheDocument();
      expect(screen.getByText(/Set 3/)).toBeInTheDocument();
      const targetTexts = screen.getAllByText(/Target: 10 reps @ 135 lbs/);
      expect(targetTexts.length).toBeGreaterThan(0);
    });

    it('should show completed status for logged sets', () => {
      const onLogSet = vi.fn();
      const onRequestDemo = vi.fn();
      render(<TodayWorkout session={mockCompletedSession} onLogSet={onLogSet} onRequestDemo={onRequestDemo} />);

      const completedMarkers = screen.getAllByText(/✓/);
      expect(completedMarkers.length).toBeGreaterThan(0);
    });

    it('should call onRequestDemo when demo button is clicked', async () => {
      const onLogSet = vi.fn();
      const onRequestDemo = vi.fn();
      const user = userEvent.setup();
      render(<TodayWorkout session={mockWorkoutSession} onLogSet={onLogSet} onRequestDemo={onRequestDemo} />);

      const demoButton = screen.getByRole('button', { name: /Request Demo/i });
      await user.click(demoButton);

      expect(onRequestDemo).toHaveBeenCalledWith('Bench Press');
    });

    it('should call onLogSet when log set button is clicked and data entered', async () => {
      const onLogSet = vi.fn();
      const onRequestDemo = vi.fn();
      const user = userEvent.setup();
      
      // Mock prompt to return values
      vi.mocked(global.prompt)
        .mockReturnValueOnce('10') // reps
        .mockReturnValueOnce('135'); // weight

      render(<TodayWorkout session={mockWorkoutSession} onLogSet={onLogSet} onRequestDemo={onRequestDemo} />);

      const logButtons = screen.getAllByRole('button', { name: /Log Set/i });
      await user.click(logButtons[0]);

      expect(onLogSet).toHaveBeenCalledWith('ex1', 1, 10, 135);
    });

    it('should not show log button for completed sets', () => {
      const onLogSet = vi.fn();
      const onRequestDemo = vi.fn();
      render(<TodayWorkout session={mockCompletedSession} onLogSet={onLogSet} onRequestDemo={onRequestDemo} />);

      const logButtons = screen.queryAllByRole('button', { name: /Log Set/i });
      expect(logButtons).toHaveLength(0);
    });

    it('should display completed workout indicator', () => {
      const onLogSet = vi.fn();
      const onRequestDemo = vi.fn();
      render(<TodayWorkout session={mockCompletedSession} onLogSet={onLogSet} onRequestDemo={onRequestDemo} />);

      expect(screen.getByText(/✓ Completed/i)).toBeInTheDocument();
    });
  });

  describe('ExerciseLogger', () => {
    it('should render exercise details', () => {
      const onLogSet = vi.fn();
      render(<ExerciseLogger exercise={mockExercise} sessionId="session1" onLogSet={onLogSet} />);

      expect(screen.getByText('Bench Press')).toBeInTheDocument();
      expect(screen.getByText('Chest')).toBeInTheDocument();
    });

    it('should display all sets', () => {
      const onLogSet = vi.fn();
      render(<ExerciseLogger exercise={mockExercise} sessionId="session1" onLogSet={onLogSet} />);

      expect(screen.getByText(/Set 1/)).toBeInTheDocument();
      expect(screen.getByText(/Set 2/)).toBeInTheDocument();
      expect(screen.getByText(/Set 3/)).toBeInTheDocument();
    });

    it('should show log button for incomplete sets', () => {
      const onLogSet = vi.fn();
      render(<ExerciseLogger exercise={mockExercise} sessionId="session1" onLogSet={onLogSet} />);

      const logButtons = screen.getAllByRole('button', { name: /Log Set/i });
      expect(logButtons).toHaveLength(3);
    });

    it('should open logging form when log button is clicked', async () => {
      const onLogSet = vi.fn();
      const user = userEvent.setup();
      render(<ExerciseLogger exercise={mockExercise} sessionId="session1" onLogSet={onLogSet} />);

      const logButtons = screen.getAllByRole('button', { name: /Log Set/i });
      await user.click(logButtons[0]);

      expect(screen.getByPlaceholderText(/Target: 10/i)).toBeInTheDocument();
      expect(screen.getByPlaceholderText(/Target: 135/i)).toBeInTheDocument();
    });

    it('should populate form with target values as placeholders', async () => {
      const onLogSet = vi.fn();
      const user = userEvent.setup();
      render(<ExerciseLogger exercise={mockExercise} sessionId="session1" onLogSet={onLogSet} />);

      const logButtons = screen.getAllByRole('button', { name: /Log Set/i });
      await user.click(logButtons[0]);

      const repsInput = screen.getByPlaceholderText(/Target: 10/i);
      const weightInput = screen.getByPlaceholderText(/Target: 135/i);

      expect(repsInput).toHaveAttribute('placeholder', 'Target: 10');
      expect(weightInput).toHaveAttribute('placeholder', 'Target: 135');
    });

    it('should call onLogSet when save button is clicked', async () => {
      const onLogSet = vi.fn();
      const user = userEvent.setup();
      render(<ExerciseLogger exercise={mockExercise} sessionId="session1" onLogSet={onLogSet} />);

      const logButtons = screen.getAllByRole('button', { name: /Log Set/i });
      await user.click(logButtons[0]);

      const repsInput = screen.getByPlaceholderText(/Target: 10/i);
      const weightInput = screen.getByPlaceholderText(/Target: 135/i);

      await user.clear(repsInput);
      await user.type(repsInput, '10');
      await user.clear(weightInput);
      await user.type(weightInput, '135');

      const saveButton = screen.getByRole('button', { name: /Save/i });
      await user.click(saveButton);

      expect(onLogSet).toHaveBeenCalledWith('ex1', 1, 10, 135);
    });

    it('should close form when cancel button is clicked', async () => {
      const onLogSet = vi.fn();
      const user = userEvent.setup();
      render(<ExerciseLogger exercise={mockExercise} sessionId="session1" onLogSet={onLogSet} />);

      const logButtons = screen.getAllByRole('button', { name: /Log Set/i });
      await user.click(logButtons[0]);

      expect(screen.getByPlaceholderText(/Target: 10/i)).toBeInTheDocument();

      const cancelButton = screen.getByRole('button', { name: /Cancel/i });
      await user.click(cancelButton);

      expect(screen.queryByPlaceholderText(/Target: 10/i)).not.toBeInTheDocument();
    });

    it('should clear form after successful save', async () => {
      const onLogSet = vi.fn();
      const user = userEvent.setup();
      render(<ExerciseLogger exercise={mockExercise} sessionId="session1" onLogSet={onLogSet} />);

      const logButtons = screen.getAllByRole('button', { name: /Log Set/i });
      await user.click(logButtons[0]);

      const repsInput = screen.getByPlaceholderText(/Target: 10/i);
      await user.type(repsInput, '10');

      const saveButton = screen.getByRole('button', { name: /Save/i });
      await user.click(saveButton);

      expect(screen.queryByPlaceholderText(/Target: 10/i)).not.toBeInTheDocument();
    });

    it('should display completed sets with actual values', () => {
      const completedExercise: Exercise = {
        ...mockExercise,
        sets: [
          { setNumber: 1, targetReps: 10, targetWeight: 135, actualReps: 10, actualWeight: 135, completed: true },
        ],
      };
      const onLogSet = vi.fn();
      render(<ExerciseLogger exercise={completedExercise} sessionId="session1" onLogSet={onLogSet} />);

      expect(screen.getByText(/✓ Completed: 10 reps @ 135 lbs/i)).toBeInTheDocument();
    });

    it('should not show log button for completed sets', () => {
      const completedExercise: Exercise = {
        ...mockExercise,
        sets: [
          { setNumber: 1, targetReps: 10, targetWeight: 135, actualReps: 10, actualWeight: 135, completed: true },
        ],
      };
      const onLogSet = vi.fn();
      render(<ExerciseLogger exercise={completedExercise} sessionId="session1" onLogSet={onLogSet} />);

      const logButtons = screen.queryAllByRole('button', { name: /Log Set/i });
      expect(logButtons).toHaveLength(0);
    });
  });

  describe('WorkoutsPage Integration', () => {
    beforeEach(() => {
      vi.clearAllMocks();
    });

    it('should render all view mode tabs', async () => {
      vi.mocked(workoutService.getTodayWorkout).mockResolvedValue(null);
      vi.mocked(workoutService.getSchedule).mockResolvedValue([]);
      vi.mocked(workoutService.getHistory).mockResolvedValue([]);

      render(
        <BrowserRouter>
          <WorkoutsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /^Today$/i })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /^Schedule$/i })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /^History$/i })).toBeInTheDocument();
      });
    });

    it('should load workout data on mount', async () => {
      vi.mocked(workoutService.getTodayWorkout).mockResolvedValue(mockWorkoutSession);
      vi.mocked(workoutService.getSchedule).mockResolvedValue([mockWorkoutSession]);
      vi.mocked(workoutService.getHistory).mockResolvedValue([mockCompletedSession]);

      render(
        <BrowserRouter>
          <WorkoutsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(workoutService.getTodayWorkout).toHaveBeenCalled();
        expect(workoutService.getSchedule).toHaveBeenCalled();
        expect(workoutService.getHistory).toHaveBeenCalledWith(10);
      });
    });

    it('should display today workout by default', async () => {
      vi.mocked(workoutService.getTodayWorkout).mockResolvedValue(mockWorkoutSession);
      vi.mocked(workoutService.getSchedule).mockResolvedValue([]);
      vi.mocked(workoutService.getHistory).mockResolvedValue([]);

      render(
        <BrowserRouter>
          <WorkoutsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Bench Press')).toBeInTheDocument();
      });
    });

    it('should switch to schedule view', async () => {
      vi.mocked(workoutService.getTodayWorkout).mockResolvedValue(null);
      vi.mocked(workoutService.getSchedule).mockResolvedValue([mockWorkoutSession]);
      vi.mocked(workoutService.getHistory).mockResolvedValue([]);

      const user = userEvent.setup();
      render(
        <BrowserRouter>
          <WorkoutsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/No workout scheduled for today/i)).toBeInTheDocument();
      });

      const scheduleTab = screen.getByRole('button', { name: /^Schedule$/i });
      await user.click(scheduleTab);

      expect(screen.getByText(/Workout Schedule/i)).toBeInTheDocument();
    });

    it('should switch to history view', async () => {
      vi.mocked(workoutService.getTodayWorkout).mockResolvedValue(null);
      vi.mocked(workoutService.getSchedule).mockResolvedValue([]);
      vi.mocked(workoutService.getHistory).mockResolvedValue([mockCompletedSession]);

      const user = userEvent.setup();
      render(
        <BrowserRouter>
          <WorkoutsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(workoutService.getHistory).toHaveBeenCalled();
      });

      const historyTab = screen.getByRole('button', { name: /^History$/i });
      await user.click(historyTab);

      expect(screen.getByText(/Workout History/i)).toBeInTheDocument();
    });

    it('should log set successfully', async () => {
      vi.mocked(workoutService.getTodayWorkout).mockResolvedValue(mockWorkoutSession);
      vi.mocked(workoutService.getSchedule).mockResolvedValue([]);
      vi.mocked(workoutService.getHistory).mockResolvedValue([]);
      vi.mocked(workoutService.logSet).mockResolvedValue();

      // Mock prompt to return values
      vi.mocked(global.prompt)
        .mockReturnValueOnce('10') // reps
        .mockReturnValueOnce('135'); // weight

      const user = userEvent.setup();
      render(
        <BrowserRouter>
          <WorkoutsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Bench Press')).toBeInTheDocument();
      });

      const logButtons = screen.getAllByRole('button', { name: /Log Set/i });
      await user.click(logButtons[0]);

      await waitFor(() => {
        expect(workoutService.logSet).toHaveBeenCalledWith({
          sessionId: 'session1',
          exerciseId: 'ex1',
          setNumber: 1,
          reps: 10,
          weight: 135,
        });
      });
    });

    it('should complete workout successfully', async () => {
      const completedWorkout = {
        ...mockWorkoutSession,
        exercises: [
          {
            ...mockExercise,
            sets: mockExercise.sets.map(set => ({ ...set, actualReps: set.targetReps, actualWeight: set.targetWeight, completed: true })),
          },
        ],
      };

      vi.mocked(workoutService.getTodayWorkout).mockResolvedValue(completedWorkout);
      vi.mocked(workoutService.getSchedule).mockResolvedValue([]);
      vi.mocked(workoutService.getHistory).mockResolvedValue([]);
      vi.mocked(workoutService.completeWorkout).mockResolvedValue();

      // Mock window.alert
      global.alert = vi.fn();

      const user = userEvent.setup();
      render(
        <BrowserRouter>
          <WorkoutsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Bench Press')).toBeInTheDocument();
      });

      const completeButton = screen.getByRole('button', { name: /Mark Workout as Complete/i });
      await user.click(completeButton);

      await waitFor(() => {
        expect(workoutService.completeWorkout).toHaveBeenCalledWith('session1');
      });
    });

    it('should request demo and navigate to chat', async () => {
      vi.mocked(workoutService.getTodayWorkout).mockResolvedValue(mockWorkoutSession);
      vi.mocked(workoutService.getSchedule).mockResolvedValue([]);
      vi.mocked(workoutService.getHistory).mockResolvedValue([]);

      const user = userEvent.setup();
      render(
        <BrowserRouter>
          <WorkoutsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Bench Press')).toBeInTheDocument();
      });

      const demoButton = screen.getByRole('button', { name: /Request Demo/i });
      await user.click(demoButton);

      expect(mockNavigate).toHaveBeenCalledWith('/chat', {
        state: {
          prefillMessage: 'Can you show me how to do Bench Press?',
          agentType: 'workout_planning',
        },
      });
    });

    it('should display error message on load failure', async () => {
      vi.mocked(workoutService.getTodayWorkout).mockRejectedValue(new Error('Failed'));
      vi.mocked(workoutService.getSchedule).mockResolvedValue([]);
      vi.mocked(workoutService.getHistory).mockResolvedValue([]);

      render(
        <BrowserRouter>
          <WorkoutsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/Failed to load workout data/i)).toBeInTheDocument();
      });
    });

    it('should display error message on log set failure', async () => {
      vi.mocked(workoutService.getTodayWorkout).mockResolvedValue(mockWorkoutSession);
      vi.mocked(workoutService.getSchedule).mockResolvedValue([]);
      vi.mocked(workoutService.getHistory).mockResolvedValue([]);
      vi.mocked(workoutService.logSet).mockRejectedValue(new Error('Failed'));

      vi.mocked(global.prompt)
        .mockReturnValueOnce('10')
        .mockReturnValueOnce('135');

      const user = userEvent.setup();
      render(
        <BrowserRouter>
          <WorkoutsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Bench Press')).toBeInTheDocument();
      });

      const logButtons = screen.getAllByRole('button', { name: /Log Set/i });
      await user.click(logButtons[0]);

      await waitFor(() => {
        expect(screen.getByText(/Failed to log set/i)).toBeInTheDocument();
      });
    });

    it('should show confirmation when completing workout with incomplete sets', async () => {
      vi.mocked(workoutService.getTodayWorkout).mockResolvedValue(mockWorkoutSession);
      vi.mocked(workoutService.getSchedule).mockResolvedValue([]);
      vi.mocked(workoutService.getHistory).mockResolvedValue([]);

      const user = userEvent.setup();
      render(
        <BrowserRouter>
          <WorkoutsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Bench Press')).toBeInTheDocument();
      });

      const completeButton = screen.getByRole('button', { name: /Mark Workout as Complete/i });
      await user.click(completeButton);

      expect(global.confirm).toHaveBeenCalledWith(
        'Not all sets are logged. Are you sure you want to mark this workout as complete?'
      );
    });

    it('should not show complete button for already completed workout', async () => {
      vi.mocked(workoutService.getTodayWorkout).mockResolvedValue(mockCompletedSession);
      vi.mocked(workoutService.getSchedule).mockResolvedValue([]);
      vi.mocked(workoutService.getHistory).mockResolvedValue([]);

      render(
        <BrowserRouter>
          <WorkoutsPage />
        </BrowserRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Bench Press')).toBeInTheDocument();
      });

      const completeButton = screen.queryByRole('button', { name: /Mark Workout as Complete/i });
      expect(completeButton).not.toBeInTheDocument();
    });
  });
});
