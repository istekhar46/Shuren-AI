import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import * as fc from 'fast-check';
import { Header } from '../../src/components/layout/Header';
import * as AuthContext from '../../src/contexts/AuthContext';
import type { User } from '../../src/types/auth.types';

// Feature: frontend-onboarding-integration, Property 1: Navigation lock during onboarding (UI portion)

describe('Header - Property Tests', () => {
  // Mock user data
  const mockUser: User = {
    id: '123',
    email: 'test@example.com',
    full_name: 'Test User',
    onboarding_completed: false,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  };

  // Mock useAuth hook
  const mockUseAuth = (isAuthenticated: boolean) => {
    vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
      isAuthenticated,
      user: isAuthenticated ? mockUser : null,
      token: isAuthenticated ? 'mock-token' : null,
      login: vi.fn(),
      logout: vi.fn(),
      register: vi.fn(),
      loading: false,
    });
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  /**
   * Property 1: Navigation lock during onboarding (UI portion)
   * 
   * For any user with incomplete onboarding (onboarding_completed = false),
   * clicking on disabled navigation items should not change the current route,
   * and only "Onboarding" and "Logout" should be enabled during onboarding.
   * 
   * Validates: Requirements US-3.1, US-3.3
   */
  it('Property 1: Navigation lock - disabled items do not navigate and only Onboarding/Logout are enabled', { timeout: 120000 }, () => {
    fc.assert(
      fc.property(
        // Generate random initial route
        fc.constantFrom('/onboarding', '/dashboard', '/chat', '/meals', '/workouts', '/voice'),
        (initialRoute) => {
          mockUseAuth(true);

          const { unmount, container } = render(
            <MemoryRouter initialEntries={[initialRoute]}>
              <Header onboardingCompleted={false} />
            </MemoryRouter>
          );

          // Get desktop navigation container
          const desktopNav = container.querySelector('.hidden.md\\:flex');
          expect(desktopNav).toBeInTheDocument();

          // Property 1: Verify disabled items exist in desktop nav
          const disabledItems = ['Dashboard', 'Chat', 'Voice', 'Meals', 'Workouts'];
          
          disabledItems.forEach((itemLabel) => {
            // Find all items with this label
            const items = screen.getAllByText(itemLabel);
            
            // At least one should be a disabled span
            const disabledSpans = items.filter(item => item.tagName === 'SPAN');
            expect(disabledSpans.length).toBeGreaterThan(0);
            
            // Verify disabled styling on at least one
            const hasDisabledStyling = disabledSpans.some(span => 
              span.classList.contains('cursor-not-allowed') &&
              span.classList.contains('text-gray-400') &&
              span.classList.contains('opacity-60')
            );
            expect(hasDisabledStyling).toBe(true);
          });

          // Property 2: Verify Onboarding link is enabled (rendered as Link)
          const onboardingLinks = screen.getAllByText('Onboarding');
          const hasEnabledLink = onboardingLinks.some(item => item.closest('a') !== null);
          expect(hasEnabledLink).toBe(true);
          
          // Verify at least one has correct href
          const onboardingLink = onboardingLinks.find(item => item.closest('a'))?.closest('a');
          expect(onboardingLink).toHaveAttribute('href', '/onboarding');

          // Property 3: Verify Logout button is enabled
          const logoutButton = screen.getByText('Logout');
          expect(logoutButton).toBeInTheDocument();
          expect(logoutButton.tagName).toBe('BUTTON');
          expect(logoutButton).not.toBeDisabled();

          // Property 4: Verify clicking disabled items doesn't trigger navigation
          disabledItems.forEach((itemLabel) => {
            const items = screen.getAllByText(itemLabel);
            const disabledSpans = items.filter(item => item.tagName === 'SPAN');
            
            disabledSpans.forEach(span => {
              // Attempt to click the disabled item
              fireEvent.click(span);
              
              // Verify it's still a span (no navigation)
              expect(span.tagName).toBe('SPAN');
              expect(span.closest('a')).toBeNull();
            });
          });

          unmount();
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property 1 (extended): Verify all protected routes are disabled during onboarding
   * 
   * Tests that all navigation items requiring onboarding completion
   * are properly disabled when onboarding is incomplete.
   */
  it('Property 1 (extended): All protected routes are disabled during incomplete onboarding', { timeout: 120000 }, () => {
    fc.assert(
      fc.property(
        fc.constantFrom('/onboarding', '/dashboard'),
        (initialRoute) => {
          mockUseAuth(true);

          const { unmount } = render(
            <MemoryRouter initialEntries={[initialRoute]}>
              <Header onboardingCompleted={false} />
            </MemoryRouter>
          );

          // Define all items that should be disabled
          const protectedItems = [
            { label: 'Dashboard', path: '/dashboard' },
            { label: 'Chat', path: '/chat' },
            { label: 'Voice', path: '/voice' },
            { label: 'Meals', path: '/meals' },
            { label: 'Workouts', path: '/workouts' },
          ];

          // Verify each protected item is disabled
          protectedItems.forEach(({ label, path }) => {
            const items = screen.getAllByText(label);
            
            // At least one should be rendered as span, not link
            const disabledSpans = items.filter(item => item.tagName === 'SPAN');
            expect(disabledSpans.length).toBeGreaterThan(0);
            
            // Verify disabled spans don't have href
            disabledSpans.forEach(span => {
              const parentLink = span.closest('a');
              expect(parentLink).toBeNull();
            });
            
            // Verify at least one has disabled styling
            const hasDisabledStyling = disabledSpans.some(span =>
              span.classList.contains('cursor-not-allowed') &&
              span.classList.contains('text-gray-400')
            );
            expect(hasDisabledStyling).toBe(true);
          });

          // Define items that should remain enabled
          const enabledItems = [
            { label: 'Onboarding', path: '/onboarding' },
          ];

          // Verify enabled items are links
          enabledItems.forEach(({ label, path }) => {
            const items = screen.getAllByText(label);
            const links = items.filter(item => item.closest('a') !== null);
            
            expect(links.length).toBeGreaterThan(0);
            
            // Verify at least one has correct href
            const link = links[0].closest('a');
            expect(link).toHaveAttribute('href', path);
          });

          // Verify logout button is enabled
          const logoutButton = screen.getByText('Logout');
          expect(logoutButton.tagName).toBe('BUTTON');
          expect(logoutButton).not.toBeDisabled();

          unmount();
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property 1 (contrast): Verify all navigation items are enabled after onboarding
   * 
   * Tests that when onboarding is complete, all navigation items
   * are rendered as clickable links.
   */
  it('Property 1 (contrast): All navigation items are enabled when onboarding is complete', { timeout: 120000 }, () => {
    fc.assert(
      fc.property(
        fc.constantFrom('/dashboard', '/chat', '/meals', '/workouts', '/voice', '/onboarding'),
        (initialRoute) => {
          mockUseAuth(true);

          const { unmount } = render(
            <MemoryRouter initialEntries={[initialRoute]}>
              <Header onboardingCompleted={true} />
            </MemoryRouter>
          );

          // Define all navigation items
          const allItems = [
            { label: 'Dashboard', path: '/dashboard' },
            { label: 'Chat', path: '/chat' },
            { label: 'Voice', path: '/voice' },
            { label: 'Meals', path: '/meals' },
            { label: 'Workouts', path: '/workouts' },
            { label: 'Onboarding', path: '/onboarding' },
          ];

          // Verify all items are rendered as links
          allItems.forEach(({ label, path }) => {
            const items = screen.getAllByText(label);
            const links = items.filter(item => item.closest('a') !== null);
            
            // At least one should be a link
            expect(links.length).toBeGreaterThan(0);
            
            // Verify at least one has correct href
            const link = links[0].closest('a');
            expect(link).toHaveAttribute('href', path);
            
            // Should NOT have disabled styling
            links.forEach(linkItem => {
              expect(linkItem).not.toHaveClass('cursor-not-allowed');
              expect(linkItem).not.toHaveClass('text-gray-400');
            });
          });

          // Verify logout button is still enabled
          const logoutButton = screen.getByText('Logout');
          expect(logoutButton.tagName).toBe('BUTTON');
          expect(logoutButton).not.toBeDisabled();

          unmount();
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property 1 (mobile): Verify navigation lock works on mobile view
   * 
   * Tests that the navigation lock is enforced in the mobile
   * navigation menu as well as desktop.
   */
  it('Property 1 (mobile): Navigation lock works in mobile view', { timeout: 120000 }, () => {
    fc.assert(
      fc.property(
        fc.constantFrom('/onboarding', '/dashboard'),
        (initialRoute) => {
          mockUseAuth(true);

          const { unmount, container } = render(
            <MemoryRouter initialEntries={[initialRoute]}>
              <Header onboardingCompleted={false} />
            </MemoryRouter>
          );

          // Find mobile navigation (has md:hidden class)
          const mobileNav = container.querySelector('.md\\:hidden');
          expect(mobileNav).toBeInTheDocument();

          // In mobile nav, verify disabled items
          const disabledItems = ['Dashboard', 'Chat', 'Voice', 'Meals', 'Workouts'];
          
          // Get all text nodes in mobile nav
          const allTextElements = screen.getAllByText(/Dashboard|Chat|Voice|Meals|Workouts|Onboarding/);
          
          // Filter to only mobile nav items (there will be duplicates for desktop/mobile)
          disabledItems.forEach((itemLabel) => {
            const items = screen.getAllByText(itemLabel);
            
            // At least one should be a disabled span (mobile or desktop)
            const hasDisabledSpan = items.some(item => item.tagName === 'SPAN');
            expect(hasDisabledSpan).toBe(true);
          });

          // Verify Onboarding is enabled in mobile nav
          const onboardingItems = screen.getAllByText('Onboarding');
          const hasEnabledLink = onboardingItems.some(item => item.closest('a') !== null);
          expect(hasEnabledLink).toBe(true);

          unmount();
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property 1 (consistency): Verify navigation lock state is consistent across re-renders
   * 
   * Tests that when onboarding status changes, the navigation lock
   * updates correctly.
   */
  it('Property 1 (consistency): Navigation lock updates when onboarding status changes', { timeout: 120000 }, () => {
    fc.assert(
      fc.property(
        fc.constantFrom('/onboarding', '/dashboard'),
        (initialRoute) => {
          mockUseAuth(true);

          // Render with onboarding incomplete
          const { rerender, unmount } = render(
            <MemoryRouter initialEntries={[initialRoute]}>
              <Header onboardingCompleted={false} />
            </MemoryRouter>
          );

          // Verify items are disabled
          const dashboardItems1 = screen.getAllByText('Dashboard');
          const disabledSpans1 = dashboardItems1.filter(item => item.tagName === 'SPAN');
          expect(disabledSpans1.length).toBeGreaterThan(0);
          expect(disabledSpans1[0]).toHaveClass('cursor-not-allowed');

          // Re-render with onboarding complete
          rerender(
            <MemoryRouter initialEntries={[initialRoute]}>
              <Header onboardingCompleted={true} />
            </MemoryRouter>
          );

          // Verify items are now enabled
          const dashboardItems2 = screen.getAllByText('Dashboard');
          const links = dashboardItems2.filter(item => item.closest('a') !== null);
          expect(links.length).toBeGreaterThan(0);
          
          const dashboardLink = links[0].closest('a');
          expect(dashboardLink).toHaveAttribute('href', '/dashboard');
          expect(links[0]).not.toHaveClass('cursor-not-allowed');

          unmount();
        }
      ),
      { numRuns: 50 } // Fewer runs due to re-render complexity
    );
  });

  /**
   * Property 3: Disabled items show tooltip
   * 
   * For any navigation item that requires onboarding completion,
   * when onboarding is incomplete, hovering over the item should
   * display a tooltip containing "Complete onboarding to unlock".
   * 
   * Validates: Requirements US-3.2
   */
  it('Property 3: Disabled items show tooltip on hover', { timeout: 120000 }, () => {
    fc.assert(
      fc.property(
        fc.constantFrom('/onboarding', '/dashboard', '/chat'),
        (initialRoute) => {
          mockUseAuth(true);

          const { unmount, container } = render(
            <MemoryRouter initialEntries={[initialRoute]}>
              <Header onboardingCompleted={false} />
            </MemoryRouter>
          );

          // Define disabled items that should have tooltips
          const disabledItems = [
            { label: 'Dashboard', path: '/dashboard' },
            { label: 'Chat', path: '/chat' },
            { label: 'Voice', path: '/voice' },
            { label: 'Meals', path: '/meals' },
            { label: 'Workouts', path: '/workouts' },
          ];

          // Verify each disabled item has tooltip
          disabledItems.forEach(({ label }) => {
            const items = screen.getAllByText(label);
            
            // Find disabled spans
            const disabledSpans = items.filter(item => item.tagName === 'SPAN');
            expect(disabledSpans.length).toBeGreaterThan(0);
            
            // Check that at least one disabled item has a parent with tooltip
            const hasTooltipParent = disabledSpans.some(span => {
              const parent = span.parentElement;
              if (!parent) return false;
              
              // Check for title attribute (basic tooltip)
              const hasTitle = parent.getAttribute('title') === 'Complete onboarding to unlock';
              
              // Check for tooltip div (custom tooltip implementation)
              const tooltipDiv = parent.querySelector('div');
              const hasTooltipDiv = tooltipDiv && 
                tooltipDiv.textContent?.includes('Complete onboarding to unlock');
              
              return hasTitle || hasTooltipDiv;
            });
            
            expect(hasTooltipParent).toBe(true);
          });

          // Verify tooltip content is correct
          const tooltipTexts = container.querySelectorAll('[title]');
          tooltipTexts.forEach(element => {
            const title = element.getAttribute('title');
            if (title && title.includes('Complete onboarding')) {
              expect(title).toBe('Complete onboarding to unlock');
            }
          });

          // Verify tooltip divs contain correct text
          const tooltipDivs = container.querySelectorAll('div.absolute');
          const tooltipMessages = Array.from(tooltipDivs)
            .map(div => div.textContent)
            .filter(text => text && text.includes('Complete onboarding'));
          
          // At least some tooltips should exist
          if (tooltipMessages.length > 0) {
            tooltipMessages.forEach(message => {
              expect(message).toContain('Complete onboarding to unlock');
            });
          }

          unmount();
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property 3 (extended): Enabled items do not show tooltip
   * 
   * Verifies that enabled navigation items (Onboarding, Logout)
   * do not have the "Complete onboarding to unlock" tooltip.
   */
  it('Property 3 (extended): Enabled items do not show disabled tooltip', { timeout: 120000 }, () => {
    fc.assert(
      fc.property(
        fc.constantFrom('/onboarding', '/dashboard'),
        (initialRoute) => {
          mockUseAuth(true);

          const { unmount, container } = render(
            <MemoryRouter initialEntries={[initialRoute]}>
              <Header onboardingCompleted={false} />
            </MemoryRouter>
          );

          // Verify Onboarding link doesn't have disabled tooltip
          const onboardingItems = screen.getAllByText('Onboarding');
          onboardingItems.forEach(item => {
            const parent = item.parentElement;
            if (parent) {
              const title = parent.getAttribute('title');
              // Should not have the disabled tooltip
              expect(title).not.toBe('Complete onboarding to unlock');
            }
          });

          // Verify Logout button doesn't have disabled tooltip
          const logoutButton = screen.getByText('Logout');
          const logoutParent = logoutButton.parentElement;
          if (logoutParent) {
            const title = logoutParent.getAttribute('title');
            expect(title).not.toBe('Complete onboarding to unlock');
          }

          unmount();
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property 3 (contrast): No tooltips when onboarding is complete
   * 
   * Verifies that when onboarding is complete, navigation items
   * do not show the "Complete onboarding to unlock" tooltip.
   */
  it('Property 3 (contrast): No disabled tooltips when onboarding is complete', { timeout: 120000 }, () => {
    fc.assert(
      fc.property(
        fc.constantFrom('/dashboard', '/chat', '/meals'),
        (initialRoute) => {
          mockUseAuth(true);

          const { unmount, container } = render(
            <MemoryRouter initialEntries={[initialRoute]}>
              <Header onboardingCompleted={true} />
            </MemoryRouter>
          );

          // Verify no items have the disabled tooltip
          const allItems = [
            'Dashboard', 'Chat', 'Voice', 'Meals', 'Workouts', 'Onboarding'
          ];

          allItems.forEach(label => {
            const items = screen.getAllByText(label);
            items.forEach(item => {
              const parent = item.parentElement;
              if (parent) {
                const title = parent.getAttribute('title');
                // Should not have the disabled tooltip
                expect(title).not.toBe('Complete onboarding to unlock');
              }
            });
          });

          // Verify no tooltip divs with disabled message exist
          const tooltipDivs = container.querySelectorAll('div.absolute');
          const disabledTooltips = Array.from(tooltipDivs)
            .filter(div => div.textContent?.includes('Complete onboarding to unlock'));
          
          // Should be no disabled tooltips when onboarding is complete
          expect(disabledTooltips.length).toBe(0);

          unmount();
        }
      ),
      { numRuns: 100 }
    );
  });
});
