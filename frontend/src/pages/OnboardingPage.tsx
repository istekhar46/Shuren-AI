import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

/**
 * @deprecated This form-based onboarding flow has been replaced by OnboardingChatPage.
 * This component now redirects to the new agent-based conversational onboarding.
 * 
 * The old 12-step form flow has been replaced with a 9-state conversational flow
 * powered by specialized AI agents.
 * 
 * Migration: All users are automatically redirected to /onboarding-chat
 */
export const OnboardingPage = () => {
  const navigate = useNavigate();

  useEffect(() => {
    // Redirect to new onboarding chat page
    navigate('/onboarding-chat', { replace: true });
  }, [navigate]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
        <p className="text-gray-600">Redirecting to onboarding...</p>
      </div>
    </div>
  );
};
