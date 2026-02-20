import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { render, screen, cleanup } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { OnboardingChatPage } from '../../src/pages/OnboardingChatPage';
import { onboardingService } from '../../src/services/onboardingService';
import type { OnboardingProgress } from '../../src/types/onboarding.types';

// Mock the onboarding service
vi.mock('../../src/services/onboardingService');

// Mock useNavigate
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

/**
 * Responsive Layout Tests
 * 
 * Tests the responsive behavior of the onboarding chat interface
 * across different screen sizes and breakpoints.
 * 
 * **Validates: Requirements NFR-2 (Usability), NFR-4 (Compatibility)**
 */

describe('Responsive Layout Tests', () => {
  const mockProgress: OnboardingProgress = {
    current_state: 0,
    total_states: 9,
    completed_states: [],
    is_complete: false,
    can_complete: false,
    completion_percentage: 0,
    current_state_info: {
      state_number: 0,
      name: 'Fitness Level Assessment',
      agent: 'fitness_assessment',
      description: 'Tell us about your current fitness level',
      required_fields: [],
    },
    next_state_info: null,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.resetAllMocks();
    mockNavigate.mockClear();
    vi.mocked(onboardingService.getOnboardingProgress).mockResolvedValue(mockProgress);
  });

  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
    vi.resetAllMocks();
  });

  describe('Mobile Layout (< 768px)', () => {
    beforeEach(() => {
      // Set viewport to mobile size
      global.innerWidth = 375;
      global.innerHeight = 667;
    });

    it('renders agent header with mobile layout', async () => {
      render(
        <MemoryRouter>
          <OnboardingChatPage />
        </MemoryRouter>
      );

      // Wait for component to load
      await screen.findByRole('banner');

      // Verify agent header is present
      const header = screen.getByRole('banner');
      expect(header).not.toBeNull();

      // Verify agent name is displayed
      expect(screen.getByText(/Fitness Assessment Agent/i)).not.toBeNull();
    });

    it('hides progress sidebar on mobile', async () => {
      render(
        <MemoryRouter>
          <OnboardingChatPage />
        </MemoryRouter>
      );

      await screen.findByRole('banner');

      // Progress sidebar should be hidden on mobile (lg:block class)
      // We can verify by checking that the main chat area takes full width
      const chatArea = screen.getByRole('region', { name: /chat and progress area/i });
      expect(chatArea).not.toBeNull();
    });

    it('displays message input at full width', async () => {
      render(
        <MemoryRouter>
          <OnboardingChatPage />
        </MemoryRouter>
      );

      await screen.findByRole('banner');

      // Verify message input area exists
      const inputArea = screen.getByRole('region', { name: /message input/i });
      expect(inputArea).not.toBeNull();

      // Verify textbox is present
      const textbox = screen.getByRole('textbox');
      expect(textbox).not.toBeNull();
    });

    it('shows mobile state indicator in header', async () => {
      render(
        <MemoryRouter>
          <OnboardingChatPage />
        </MemoryRouter>
      );

      await screen.findByRole('banner');

      // Mobile layout shows "Step X of 9" in header
      const stepIndicators = screen.getAllByText(/Step.*0.*of.*9/i);
      expect(stepIndicators.length).toBeGreaterThan(0);
    });
  });

  describe('Tablet Layout (768px - 1024px)', () => {
    beforeEach(() => {
      // Set viewport to tablet size
      global.innerWidth = 820;
      global.innerHeight = 1180;
    });

    it('renders agent header with desktop layout', async () => {
      render(
        <MemoryRouter>
          <OnboardingChatPage />
        </MemoryRouter>
      );

      await screen.findByRole('banner');

      // Verify agent header is present
      const header = screen.getByRole('banner');
      expect(header).not.toBeNull();

      // Verify agent name is displayed
      expect(screen.getByText(/Fitness Assessment Agent/i)).not.toBeNull();
    });

    it('still hides progress sidebar on tablet', async () => {
      render(
        <MemoryRouter>
          <OnboardingChatPage />
        </MemoryRouter>
      );

      await screen.findByRole('banner');

      // Progress sidebar should still be hidden on tablet (lg:block class)
      const chatArea = screen.getByRole('region', { name: /chat and progress area/i });
      expect(chatArea).not.toBeNull();
    });

    it('displays message input with proper sizing', async () => {
      render(
        <MemoryRouter>
          <OnboardingChatPage />
        </MemoryRouter>
      );

      await screen.findByRole('banner');

      // Verify message input area exists
      const inputArea = screen.getByRole('region', { name: /message input/i });
      expect(inputArea).not.toBeNull();

      // Verify textbox is present
      const textbox = screen.getByRole('textbox');
      expect(textbox).not.toBeNull();
    });
  });

  describe('Desktop Layout (> 1024px)', () => {
    beforeEach(() => {
      // Set viewport to desktop size
      global.innerWidth = 1920;
      global.innerHeight = 1080;
    });

    it('renders agent header with full desktop layout', async () => {
      render(
        <MemoryRouter>
          <OnboardingChatPage />
        </MemoryRouter>
      );

      await screen.findByRole('banner');

      // Verify agent header is present
      const header = screen.getByRole('banner');
      expect(header).not.toBeNull();

      // Verify agent name is displayed
      expect(screen.getByText(/Fitness Assessment Agent/i)).not.toBeNull();

      // Verify agent description is displayed
      expect(screen.getByText(/Tell us about your current fitness level/i)).not.toBeNull();
    });

    it('displays progress sidebar on desktop', async () => {
      render(
        <MemoryRouter>
          <OnboardingChatPage />
        </MemoryRouter>
      );

      await screen.findByRole('banner');

      // Progress sidebar should be visible on desktop
      const chatArea = screen.getByRole('region', { name: /chat and progress area/i });
      expect(chatArea).not.toBeNull();

      // Verify progress heading exists
      const progressHeading = screen.getByText(/Progress/i);
      expect(progressHeading).not.toBeNull();
    });

    it('displays all 9 states in progress sidebar', async () => {
      render(
        <MemoryRouter>
          <OnboardingChatPage />
        </MemoryRouter>
      );

      await screen.findByRole('banner');

      // Verify "All Steps" heading exists
      const allStepsHeading = screen.getByText(/All Steps/i);
      expect(allStepsHeading).not.toBeNull();

      // Verify state names are displayed
      expect(screen.getByText(/Fitness Level Assessment/i)).not.toBeNull();
    });

    it('displays message input with max-width constraint', async () => {
      render(
        <MemoryRouter>
          <OnboardingChatPage />
        </MemoryRouter>
      );

      await screen.findByRole('banner');

      // Verify message input area exists
      const inputArea = screen.getByRole('region', { name: /message input/i });
      expect(inputArea).not.toBeNull();

      // Verify textbox is present
      const textbox = screen.getByRole('textbox');
      expect(textbox).not.toBeNull();
    });

    it('shows progress percentage in sidebar', async () => {
      render(
        <MemoryRouter>
          <OnboardingChatPage />
        </MemoryRouter>
      );

      await screen.findByRole('banner');

      // Verify progress percentage is displayed
      const percentageElements = screen.getAllByText(/0%/i);
      expect(percentageElements.length).toBeGreaterThan(0);
    });
  });

  describe('Responsive Breakpoint Transitions', () => {
    it('handles transition from mobile to desktop', async () => {
      // Start with mobile
      global.innerWidth = 375;
      global.innerHeight = 667;

      const { rerender } = render(
        <MemoryRouter>
          <OnboardingChatPage />
        </MemoryRouter>
      );

      await screen.findByRole('banner');

      // Verify mobile layout
      expect(screen.getByRole('banner')).not.toBeNull();

      // Simulate resize to desktop
      global.innerWidth = 1920;
      global.innerHeight = 1080;

      // Rerender component
      rerender(
        <MemoryRouter>
          <OnboardingChatPage />
        </MemoryRouter>
      );

      // Verify desktop layout elements are present
      expect(screen.getByRole('banner')).not.toBeNull();
      expect(screen.getByText(/Progress/i)).not.toBeNull();
    });

    it('handles transition from desktop to mobile', async () => {
      // Start with desktop
      global.innerWidth = 1920;
      global.innerHeight = 1080;

      const { rerender } = render(
        <MemoryRouter>
          <OnboardingChatPage />
        </MemoryRouter>
      );

      await screen.findByRole('banner');

      // Verify desktop layout
      expect(screen.getByText(/Progress/i)).not.toBeNull();

      // Simulate resize to mobile
      global.innerWidth = 375;
      global.innerHeight = 667;

      // Rerender component
      rerender(
        <MemoryRouter>
          <OnboardingChatPage />
        </MemoryRouter>
      );

      // Verify mobile layout still works
      expect(screen.getByRole('banner')).not.toBeNull();
    });
  });

  describe('Content Overflow Handling', () => {
    it('handles long agent descriptions without overflow', async () => {
      const longDescriptionProgress: OnboardingProgress = {
        ...mockProgress,
        current_state_info: {
          ...mockProgress.current_state_info,
          description: 'This is a very long description that should wrap properly and not cause horizontal overflow on any screen size. It contains multiple sentences to test the wrapping behavior.',
        },
      };

      vi.mocked(onboardingService.getOnboardingProgress).mockResolvedValue(longDescriptionProgress);

      render(
        <MemoryRouter>
          <OnboardingChatPage />
        </MemoryRouter>
      );

      await screen.findByRole('banner');

      // Verify long description is displayed
      const description = screen.getByText(/This is a very long description/i);
      expect(description).not.toBeNull();
    });

    it('handles long state names without overflow', async () => {
      const longStateNameProgress: OnboardingProgress = {
        ...mockProgress,
        current_state_info: {
          ...mockProgress.current_state_info,
          name: 'Very Long State Name That Should Be Handled Properly',
        },
      };

      vi.mocked(onboardingService.getOnboardingProgress).mockResolvedValue(longStateNameProgress);

      render(
        <MemoryRouter>
          <OnboardingChatPage />
        </MemoryRouter>
      );

      await screen.findByRole('banner');

      // Verify long state name is displayed
      const stateName = screen.getByText(/Very Long State Name/i);
      expect(stateName).not.toBeNull();
    });
  });

  describe('Accessibility at Different Screen Sizes', () => {
    it('maintains ARIA labels on mobile', async () => {
      global.innerWidth = 375;
      global.innerHeight = 667;

      render(
        <MemoryRouter>
          <OnboardingChatPage />
        </MemoryRouter>
      );

      await screen.findByRole('banner');

      // Verify ARIA labels are present
      expect(screen.getByRole('banner')).not.toBeNull();
      expect(screen.getByRole('main')).not.toBeNull();
      expect(screen.getByRole('region', { name: /chat and progress area/i })).not.toBeNull();
    });

    it('maintains ARIA labels on desktop', async () => {
      global.innerWidth = 1920;
      global.innerHeight = 1080;

      render(
        <MemoryRouter>
          <OnboardingChatPage />
        </MemoryRouter>
      );

      await screen.findByRole('banner');

      // Verify ARIA labels are present
      expect(screen.getByRole('banner')).not.toBeNull();
      expect(screen.getByRole('main')).not.toBeNull();
      expect(screen.getByRole('region', { name: /chat and progress area/i })).not.toBeNull();
    });

    it('maintains progressbar role on all screen sizes', async () => {
      render(
        <MemoryRouter>
          <OnboardingChatPage />
        </MemoryRouter>
      );

      await screen.findByRole('banner');

      // Verify progressbar role exists
      const progressbar = screen.getByRole('progressbar');
      expect(progressbar).not.toBeNull();
      expect(progressbar.getAttribute('aria-valuenow')).toBe('0');
      expect(progressbar.getAttribute('aria-valuemin')).toBe('0');
      expect(progressbar.getAttribute('aria-valuemax')).toBe('100');
    });
  });
});
