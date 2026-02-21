import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { AgentHeader } from '../../src/components/onboarding/AgentHeader';
import { AgentType } from '../../src/types/onboarding.types';

/**
 * AgentHeader Component Unit Tests
 * 
 * Tests the agent context header that displays current agent information
 * and onboarding progress at the top of the chat interface.
 * 
 * Requirements: US-2, AC-2.1, AC-2.2, AC-2.3, AC-2.4
 */
describe('AgentHeader Component Tests', () => {
  const defaultProps = {
    agentType: AgentType.FITNESS_ASSESSMENT,
    agentDescription: 'Tell us about your current fitness level',
    currentState: 1,
    totalStates: 9,
    stateName: 'Fitness Level Assessment',
  };

  describe('Agent Information Display', () => {
    it('should render agent name based on agent type', () => {
      render(<AgentHeader {...defaultProps} />);
      
      expect(screen.getByText('Fitness Assessment Agent')).toBeInTheDocument();
    });

    it('should render agent description', () => {
      render(<AgentHeader {...defaultProps} />);
      
      expect(screen.getByText('Tell us about your current fitness level')).toBeInTheDocument();
    });

    it('should render correct agent icon for each agent type', () => {
      const agentTypes = [
        { type: AgentType.FITNESS_ASSESSMENT, icon: '💪', name: 'Fitness Assessment Agent' },
        { type: AgentType.GOAL_SETTING, icon: '🎯', name: 'Goal Setting Agent' },
        { type: AgentType.WORKOUT_PLANNING, icon: '🏋️', name: 'Workout Planning Agent' },
        { type: AgentType.DIET_PLANNING, icon: '🥗', name: 'Diet Planning Agent' },
        { type: AgentType.SCHEDULING, icon: '📅', name: 'Scheduling Agent' },
      ];

      agentTypes.forEach(({ type, icon, name }) => {
        const { unmount } = render(
          <AgentHeader
            {...defaultProps}
            agentType={type}
            agentDescription="Test description"
          />
        );

        expect(screen.getByText(name)).toBeInTheDocument();
        expect(screen.getByLabelText(`${name} icon`)).toHaveTextContent(icon);

        unmount();
      });
    });
  });

  describe('State Progress Display', () => {
    it('should display current state and total states', () => {
      render(<AgentHeader {...defaultProps} />);
      
      // Component renders step indicator twice (desktop + mobile)
      const stepIndicators = screen.getAllByText(/Step 1 of 9/);
      expect(stepIndicators.length).toBeGreaterThan(0);
      expect(stepIndicators[0]).toBeInTheDocument();
    });

    it('should display state name', () => {
      render(<AgentHeader {...defaultProps} />);
      
      expect(screen.getByText('Fitness Level Assessment')).toBeInTheDocument();
    });

    it('should update when state changes', () => {
      const { rerender } = render(<AgentHeader {...defaultProps} />);
      
      let stepIndicators = screen.getAllByText(/Step 1 of 9/);
      expect(stepIndicators.length).toBeGreaterThan(0);

      rerender(
        <AgentHeader
          {...defaultProps}
          currentState={5}
          stateName="Fixed Meal Plan Selection"
        />
      );

      stepIndicators = screen.getAllByText(/Step 5 of 9/);
      expect(stepIndicators.length).toBeGreaterThan(0);
      expect(screen.getByText('Fixed Meal Plan Selection')).toBeInTheDocument();
    });
  });

  describe('Color Themes', () => {
    it('should apply correct color theme for each agent type', () => {
      const agentColors = [
        { type: AgentType.FITNESS_ASSESSMENT, colorClass: 'bg-purple-600' },
        { type: AgentType.GOAL_SETTING, colorClass: 'bg-blue-600' },
        { type: AgentType.WORKOUT_PLANNING, colorClass: 'bg-green-600' },
        { type: AgentType.DIET_PLANNING, colorClass: 'bg-orange-600' },
        { type: AgentType.SCHEDULING, colorClass: 'bg-indigo-600' },
      ];

      agentColors.forEach(({ type, colorClass }) => {
        const { container, unmount } = render(
          <AgentHeader {...defaultProps} agentType={type} />
        );

        const header = container.querySelector(`.${colorClass}`);
        expect(header).toBeInTheDocument();

        unmount();
      });
    });
  });

  describe('Responsive Design', () => {
    it('should render desktop state indicator with hidden class on mobile', () => {
      render(<AgentHeader {...defaultProps} />);
      
      // Desktop indicator should have 'hidden sm:flex' classes
      // Find the parent div that contains the hidden class
      const stepIndicators = screen.getAllByText(/Step 1 of 9/);
      const desktopIndicator = stepIndicators[0].closest('.hidden');
      expect(desktopIndicator).toBeInTheDocument();
      expect(desktopIndicator?.className).toContain('sm:flex');
    });

    it('should render mobile state indicator with sm:hidden class', () => {
      render(<AgentHeader {...defaultProps} />);
      
      // Mobile indicator should have 'sm:hidden' class
      const mobileIndicators = screen.getAllByText(/Step 1 of 9/);
      const mobileIndicator = mobileIndicators.find(el => 
        el.closest('div')?.className.includes('sm:hidden')
      );
      expect(mobileIndicator).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have proper ARIA role for banner', () => {
      const { container } = render(<AgentHeader {...defaultProps} />);
      
      const banner = container.querySelector('[role="banner"]');
      expect(banner).toBeInTheDocument();
      expect(banner).toHaveAttribute('aria-label', 'Current onboarding agent');
    });

    it('should have descriptive aria-label for agent icon', () => {
      render(<AgentHeader {...defaultProps} />);
      
      const icon = screen.getByLabelText('Fitness Assessment Agent icon');
      expect(icon).toBeInTheDocument();
      expect(icon).toHaveAttribute('role', 'img');
    });

    it('should be keyboard accessible', () => {
      const { container } = render(<AgentHeader {...defaultProps} />);
      
      // Header should be in the tab order (no tabindex=-1)
      const header = container.querySelector('[role="banner"]');
      expect(header).not.toHaveAttribute('tabindex', '-1');
    });
  });

  describe('Sticky Positioning', () => {
    it('should have sticky positioning classes', () => {
      const { container } = render(<AgentHeader {...defaultProps} />);
      
      const header = container.querySelector('[role="banner"]');
      expect(header?.className).toContain('sticky');
      expect(header?.className).toContain('top-0');
      expect(header?.className).toContain('z-10');
    });
  });

  describe('Transitions', () => {
    it('should have transition classes for smooth agent changes', () => {
      const { container } = render(<AgentHeader {...defaultProps} />);
      
      const header = container.querySelector('[role="banner"]');
      expect(header?.className).toContain('transition-all');
      expect(header?.className).toContain('duration-300');
    });

    it('should smoothly transition between agents', () => {
      const { container, rerender } = render(<AgentHeader {...defaultProps} />);
      
      expect(screen.getByText('Fitness Assessment Agent')).toBeInTheDocument();

      rerender(
        <AgentHeader
          {...defaultProps}
          agentType={AgentType.GOAL_SETTING}
          agentDescription="What are your primary fitness goals?"
          stateName="Primary Fitness Goals"
          currentState={2}
        />
      );

      expect(screen.getByText('Goal Setting Agent')).toBeInTheDocument();
      expect(screen.getByText('What are your primary fitness goals?')).toBeInTheDocument();
      
      // Transition classes should still be present
      const header = container.querySelector('[role="banner"]');
      expect(header?.className).toContain('transition-all');
    });
  });

  describe('Edge Cases', () => {
    it('should handle state 9 (last state) correctly', () => {
      render(
        <AgentHeader
          {...defaultProps}
          currentState={9}
          stateName="Supplement Preferences"
        />
      );
      
      const stepIndicators = screen.getAllByText(/Step 9 of 9/);
      expect(stepIndicators.length).toBeGreaterThan(0);
      expect(screen.getByText('Supplement Preferences')).toBeInTheDocument();
    });

    it('should handle long agent descriptions', () => {
      const longDescription = 'This is a very long description that should still render properly without breaking the layout or causing overflow issues in the component.';
      
      render(
        <AgentHeader
          {...defaultProps}
          agentDescription={longDescription}
        />
      );
      
      expect(screen.getByText(longDescription)).toBeInTheDocument();
    });

    it('should handle long state names', () => {
      const longStateName = 'Very Long State Name That Should Still Display Properly';
      
      render(
        <AgentHeader
          {...defaultProps}
          stateName={longStateName}
        />
      );
      
      expect(screen.getByText(longStateName)).toBeInTheDocument();
    });
  });
});
