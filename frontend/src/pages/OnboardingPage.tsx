import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

/**
 * @deprecated Redirects to the new agent-based conversational onboarding.
 */
export const OnboardingPage = () => {
  const navigate = useNavigate();

  useEffect(() => {
    navigate('/onboarding-chat', { replace: true });
  }, [navigate]);

  return (
    <div
      className="min-h-screen flex items-center justify-center"
      style={{ background: 'var(--color-bg-primary)' }}
    >
      <div className="text-center">
        <div
          className="animate-spin rounded-full h-12 w-12 mx-auto mb-4"
          style={{ borderWidth: 3, borderColor: 'var(--color-violet)', borderTopColor: 'transparent' }}
        />
        <p style={{ color: 'var(--color-text-muted)' }}>Redirecting to onboarding...</p>
      </div>
    </div>
  );
};
