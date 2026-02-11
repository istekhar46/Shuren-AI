import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

export const Header: React.FC = () => {
  const { isAuthenticated, user, logout } = useAuth();
  const location = useLocation();

  const isActive = (path: string) => {
    return location.pathname === path;
  };

  const navLinkClass = (path: string) => {
    const baseClass = 'px-3 py-2 rounded-md text-sm font-medium transition-colors';
    return isActive(path)
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
              <Link to="/dashboard" className={navLinkClass('/dashboard')}>
                Dashboard
              </Link>
              <Link to="/chat" className={navLinkClass('/chat')}>
                Chat
              </Link>
              <Link to="/voice" className={navLinkClass('/voice')}>
                Voice
              </Link>
              <Link to="/meals" className={navLinkClass('/meals')}>
                Meals
              </Link>
              <Link to="/workouts" className={navLinkClass('/workouts')}>
                Workouts
              </Link>
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
            <Link
              to="/dashboard"
              className={`block ${navLinkClass('/dashboard')}`}
            >
              Dashboard
            </Link>
            <Link
              to="/chat"
              className={`block ${navLinkClass('/chat')}`}
            >
              Chat
            </Link>
            <Link
              to="/voice"
              className={`block ${navLinkClass('/voice')}`}
            >
              Voice
            </Link>
            <Link
              to="/meals"
              className={`block ${navLinkClass('/meals')}`}
            >
              Meals
            </Link>
            <Link
              to="/workouts"
              className={`block ${navLinkClass('/workouts')}`}
            >
              Workouts
            </Link>
          </div>
        )}
      </nav>
    </header>
  );
};
