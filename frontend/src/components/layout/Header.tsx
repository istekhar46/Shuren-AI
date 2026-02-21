import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

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

  const isActive = (path: string) => {
    return location.pathname === path;
  };

  const isDisabled = (item: NavItem) => {
    return item.requiresOnboarding && !onboardingCompleted;
  };

  const navLinkClass = (item: NavItem) => {
    const baseClass = 'px-3 py-2 rounded-md text-sm font-medium transition-colors';
    const disabled = isDisabled(item);
    
    if (disabled) {
      return `${baseClass} text-gray-400 cursor-not-allowed opacity-60`;
    }
    
    return isActive(item.path)
      ? `${baseClass} bg-blue-700 text-white`
      : `${baseClass} text-blue-100 hover:bg-blue-600 hover:text-white`;
  };

  return (
    <header className="bg-blue-600 shadow-md">
      <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo/Brand */}
          <div className="flex items-center">
            <Link to="/dashboard" className="text-white text-xl font-bold">
              Shuren AI
            </Link>
          </div>

          {/* Navigation Links */}
          {isAuthenticated && (
            <div className="hidden md:flex items-center space-x-4">
              {navItems.map((item) => {
                const disabled = isDisabled(item);
                
                if (disabled) {
                  return (
                    <div
                      key={item.path}
                      className="relative group"
                      title="Complete onboarding to unlock"
                    >
                      <span className={navLinkClass(item)}>
                        {item.label}
                      </span>
                      <div className="absolute hidden group-hover:block bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 text-xs text-white bg-gray-900 rounded-md whitespace-nowrap z-10">
                        Complete onboarding to unlock
                        <div className="absolute top-full left-1/2 transform -translate-x-1/2 -mt-1 border-4 border-transparent border-t-gray-900"></div>
                      </div>
                    </div>
                  );
                }
                
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={navLinkClass(item)}
                  >
                    {item.label}
                  </Link>
                );
              })}
            </div>
          )}

          {/* User Menu */}
          {isAuthenticated && (
            <div className="flex items-center space-x-4">
              <span className="text-blue-100 text-sm hidden sm:block">
                {user?.email}
              </span>
              <button
                onClick={logout}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-700 hover:bg-blue-800 rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-white"
              >
                Logout
              </button>
            </div>
          )}
        </div>

        {/* Mobile Navigation */}
        {isAuthenticated && (
          <div className="md:hidden pb-3 space-y-1">
            {navItems.map((item) => {
              const disabled = isDisabled(item);
              
              if (disabled) {
                return (
                  <div
                    key={item.path}
                    className="relative group"
                    title="Complete onboarding to unlock"
                  >
                    <span className={`block ${navLinkClass(item)}`}>
                      {item.label}
                    </span>
                    <div className="absolute hidden group-hover:block left-full top-0 ml-2 px-3 py-2 text-xs text-white bg-gray-900 rounded-md whitespace-nowrap z-10">
                      Complete onboarding to unlock
                      <div className="absolute top-1/2 right-full transform -translate-y-1/2 mr-1 border-4 border-transparent border-r-gray-900"></div>
                    </div>
                  </div>
                );
              }
              
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`block ${navLinkClass(item)}`}
                >
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
