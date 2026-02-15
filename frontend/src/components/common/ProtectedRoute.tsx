import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { useUser } from '../../contexts/UserContext';
import { LoadingSpinner } from './LoadingSpinner';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requireOnboardingComplete?: boolean;
}

/**
 * ProtectedRoute component that ensures user is authenticated before accessing protected pages
 * Redirects to login page if user is not authenticated
 * Checks if onboarding is completed based on requireOnboardingComplete prop
 */
export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ 
  children, 
  requireOnboardingComplete = true 
}) => {
  const { isAuthenticated, loading: authLoading } = useAuth();
  const { onboardingCompleted, loading: userLoading } = useUser();
  const location = useLocation();

  // Show loading state while checking authentication or user status
  if (authLoading || userLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner message="Loading..." size="lg" />
      </div>
    );
  }

  // Redirect to login if not authenticated
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  // If onboarding is required and not complete, redirect to onboarding
  if (requireOnboardingComplete && !onboardingCompleted) {
    return <Navigate to="/onboarding" replace />;
  }

  // If onboarding is complete and user is accessing /onboarding, redirect to dashboard
  if (onboardingCompleted && location.pathname === '/onboarding') {
    return <Navigate to="/dashboard" replace />;
  }

  return <>{children}</>;
};
