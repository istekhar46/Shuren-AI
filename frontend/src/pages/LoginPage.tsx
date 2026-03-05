import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import logo from '../assets/logo.png';
import { handleApiError } from '../utils/errorHandling';
import { GoogleSignInButton } from '../components/auth/GoogleSignInButton';
import type { TokenResponse } from '../types/auth.types';

/* ── Shared input style helper ── */
const inputClass = (hasError: boolean) =>
  `mt-1 appearance-none relative block w-full px-3 py-2.5 rounded-md sm:text-sm transition-colors
   focus:outline-none focus:ring-2 focus:ring-[var(--color-violet)] focus:border-transparent
   ${hasError
      ? 'border border-red-500/60'
      : 'border border-[var(--color-border)]'
   }`.replace(/\n\s+/g, ' ')
  + ' bg-[var(--color-bg-surface)] text-[var(--color-text-primary)] placeholder-[var(--color-text-faint)]';

export const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const { login } = useAuth();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [googleError, setGoogleError] = useState('');
  const [validationErrors, setValidationErrors] = useState<{
    email?: string;
    password?: string;
  }>({});

  const validateForm = (): boolean => {
    const errors: { email?: string; password?: string } = {};
    if (!email) errors.email = 'Email is required';
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) errors.email = 'Invalid email format';
    if (!password) errors.password = 'Password is required';
    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setValidationErrors({});
    if (!validateForm()) return;
    setLoading(true);
    try {
      await login(email, password);
      navigate('/dashboard');
    } catch (err) {
      const appError = handleApiError(err);
      setError(appError.message);
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleSuccess = async (response: TokenResponse) => {
    try {
      setGoogleError('');
      localStorage.setItem('auth_token', response.access_token);
      const { authService } = await import('../services/authService');
      const userData = await authService.getCurrentUser();
      localStorage.setItem('auth_user', JSON.stringify(userData));
      const destination = userData.onboarding_completed ? '/dashboard' : '/onboarding';
      window.location.href = destination;
    } catch (err) {
      const appError = handleApiError(err);
      setGoogleError(appError.message);
    }
  };

  const handleGoogleError = (error: Error) => {
    setGoogleError(error.message);
  };

  return (
    <div
      className="min-h-screen flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8"
      style={{ background: 'var(--color-bg-primary)' }}
    >
      <div className="max-w-md w-full space-y-8">
        {/* Header */}
        <div>
          <div className="flex justify-center mb-4">
            <img src={logo} alt="Shuren" className="h-12 object-contain" />
          </div>
          <h2 className="text-center text-3xl font-bold" style={{ color: 'var(--color-text-primary)' }}>
            Sign in to your account
          </h2>
          <p className="mt-2 text-center text-sm" style={{ color: 'var(--color-text-muted)' }}>
            Or{' '}
            <Link to="/register" style={{ color: 'var(--color-violet)' }} className="font-medium hover:underline">
              create a new account
            </Link>
          </p>
        </div>

        {/* Form */}
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          {error && (
            <div className="rounded-md p-4" style={{ background: 'rgba(239,68,68,0.12)', border: '1px solid rgba(239,68,68,0.25)' }}>
              <h3 className="text-sm font-medium" style={{ color: '#f87171' }}>{error}</h3>
            </div>
          )}

          <div className="space-y-4">
            <div>
              <label htmlFor="email" className="sr-only">Email address</label>
              <input
                id="email" name="email" type="email" autoComplete="email" required
                value={email} onChange={(e) => setEmail(e.target.value)}
                className={inputClass(!!validationErrors.email)}
                placeholder="Email address"
              />
              {validationErrors.email && (
                <p className="mt-1 text-sm" style={{ color: '#f87171' }}>{validationErrors.email}</p>
              )}
            </div>
            <div>
              <label htmlFor="password" className="sr-only">Password</label>
              <input
                id="password" name="password" type="password" autoComplete="current-password" required
                value={password} onChange={(e) => setPassword(e.target.value)}
                className={inputClass(!!validationErrors.password)}
                placeholder="Password"
              />
              {validationErrors.password && (
                <p className="mt-1 text-sm" style={{ color: '#f87171' }}>{validationErrors.password}</p>
              )}
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className={`ds-btn-primary w-full justify-center py-2.5 ${loading ? 'opacity-60 cursor-not-allowed' : ''}`}
          >
            {loading ? 'Signing in...' : 'Sign in'}
          </button>
        </form>

        {/* OR Divider */}
        <div className="relative">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full" style={{ borderTop: '1px solid var(--color-border)' }} />
          </div>
          <div className="relative flex justify-center text-sm">
            <span className="px-2" style={{ background: 'var(--color-bg-primary)', color: 'var(--color-text-muted)' }}>OR</span>
          </div>
        </div>

        {/* Google Sign-In */}
        <div className="mt-6">
          {googleError && (
            <div className="rounded-md p-4 mb-4" style={{ background: 'rgba(239,68,68,0.12)', border: '1px solid rgba(239,68,68,0.25)' }}>
              <h3 className="text-sm font-medium" style={{ color: '#f87171' }}>{googleError}</h3>
            </div>
          )}
          <div className="flex justify-center">
            <GoogleSignInButton
              onSuccess={handleGoogleSuccess}
              onError={handleGoogleError}
              disabled={loading}
            />
          </div>
        </div>
      </div>
    </div>
  );
};
