import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import logo from '../../assets/logo.png';

interface HeaderProps {
  onboardingCompleted: boolean;
}

interface NavItem {
  path: string;
  label: string;
  requiresOnboarding: boolean;
}

export const Header: React.FC<HeaderProps> = ({ onboardingCompleted }) => {
  const { isAuthenticated, user, logout } = useAuth();
  const location = useLocation();

  const navItems: NavItem[] = [
    { path: '/dashboard', label: 'Dashboard', requiresOnboarding: true },
    { path: '/chat', label: 'Chat', requiresOnboarding: true },
    { path: '/voice', label: 'Voice', requiresOnboarding: true },
    { path: '/meals', label: 'Meals', requiresOnboarding: true },
    { path: '/workouts', label: 'Workouts', requiresOnboarding: true },
    { path: '/onboarding', label: 'Onboarding', requiresOnboarding: false },
  ];

  const isActive = (path: string) => location.pathname === path;
  const isDisabled = (item: NavItem) => item.requiresOnboarding && !onboardingCompleted;

  const navLinkClass = (item: NavItem) => {
    const base = 'px-3 py-2 rounded-md text-sm font-medium transition-colors';
    if (isDisabled(item)) {
      return `${base} opacity-40 cursor-not-allowed` ;
    }
    return isActive(item.path)
      ? `${base} bg-[rgba(167,139,250,0.15)] text-[var(--color-violet)]`
      : `${base} text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] hover:bg-[rgba(255,255,255,0.05)]`;
  };

  return (
    <header
      className="border-b shadow-sm"
      style={{ background: 'var(--color-bg-primary)', borderColor: 'var(--color-border)' }}
    >
      <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <div className="flex items-center">
            <Link to="/dashboard" className="flex items-center no-underline">
              <img src={logo} alt="Shuren" className="h-8 object-contain" />
            </Link>
          </div>

          {/* Desktop Nav */}
          {isAuthenticated && (
            <div className="hidden md:flex items-center space-x-1">
              {navItems.map((item) => {
                if (isDisabled(item)) {
                  return (
                    <div key={item.path} className="relative group" title="Complete onboarding to unlock">
                      <span className={navLinkClass(item)}>{item.label}</span>
                      <div
                        className="absolute hidden group-hover:block bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 text-xs text-white rounded-md whitespace-nowrap z-10"
                        style={{ background: 'var(--color-bg-elevated)' }}
                      >
                        Complete onboarding to unlock
                      </div>
                    </div>
                  );
                }
                return (
                  <Link key={item.path} to={item.path} className={navLinkClass(item)}>
                    {item.label}
                  </Link>
                );
              })}
            </div>
          )}

          {/* User Menu */}
          {isAuthenticated && (
            <div className="flex items-center space-x-4">
              <span className="text-sm hidden sm:block" style={{ color: 'var(--color-text-muted)' }}>
                {user?.email}
              </span>
              <button
                onClick={logout}
                className="ds-btn-ghost text-sm"
              >
                Logout
              </button>
            </div>
          )}
        </div>

        {/* Mobile Nav */}
        {isAuthenticated && (
          <div className="md:hidden pb-3 space-y-1">
            {navItems.map((item) => {
              if (isDisabled(item)) {
                return (
                  <div key={item.path} className="relative group" title="Complete onboarding to unlock">
                    <span className={`block ${navLinkClass(item)}`}>{item.label}</span>
                  </div>
                );
              }
              return (
                <Link key={item.path} to={item.path} className={`block ${navLinkClass(item)}`}>
                  {item.label}
                </Link>
              );
            })}
          </div>
        )}
      </nav>
    </header>
  );
};
