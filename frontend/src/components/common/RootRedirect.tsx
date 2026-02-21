import { Navigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { useUser } from '../../contexts/UserContext';
import { LoadingSpinner } from './LoadingSpinner';

/**
 * RootRedirect component that handles root path (/) navigation
 * Redirects based on authentication and onboarding status:
 * - Not authenticated -> /login
 * - Authenticated but onboarding incomplete -> /onboarding
 * - Authenticated and onboarding complete -> /dashboard
 */
export const RootRedirect = () => {
  const { isAuthenticated, loading: authLoading } = useAuth();
  const { onboardingCompleted, loading: userLoading } = useUser();

  // Show loading state while checking authentication or user status
  if (authLoading || userLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner message="Loading..." size="lg" />
      </div>
    );
  }

  // Not authenticated -> login
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  // Authenticated but onboarding incomplete -> onboarding
  if (!onboardingCompleted) {
    return <Navigate to="/onboarding" replace />;
  }

  // Authenticated and onboarding complete -> dashboard
  return <Navigate to="/dashboard" replace />;
};
