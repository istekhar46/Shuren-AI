import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { lazy, Suspense } from 'react';
import { AuthProvider } from './contexts/AuthContext';
import { UserProvider } from './contexts/UserContext';
import { VoiceProvider } from './contexts/VoiceContext';
import { ProtectedRoute } from './components/common/ProtectedRoute';
import { MainLayout } from './components/layout/MainLayout';
import { LoadingSpinner } from './components/common/LoadingSpinner';
import './App.css';

// Eager load auth pages for faster initial load
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';

// Lazy load protected pages for code splitting
const DashboardPage = lazy(() => import('./pages/DashboardPage').then(m => ({ default: m.DashboardPage })));
const OnboardingPage = lazy(() => import('./pages/OnboardingPage').then(m => ({ default: m.OnboardingPage })));
const ChatPage = lazy(() => import('./pages/ChatPage').then(m => ({ default: m.ChatPage })));
const VoicePage = lazy(() => import('./pages/VoicePage').then(m => ({ default: m.VoicePage })));
const MealsPage = lazy(() => import('./pages/MealsPage').then(m => ({ default: m.MealsPage })));
const WorkoutsPage = lazy(() => import('./pages/WorkoutsPage').then(m => ({ default: m.WorkoutsPage })));

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <UserProvider>
          <VoiceProvider>
            <Routes>
              {/* Public routes */}
              <Route path="/" element={<Navigate to="/login" replace />} />
              <Route path="/login" element={<LoginPage />} />
              <Route path="/register" element={<RegisterPage />} />

              {/* Protected routes with layout and lazy loading */}
              <Route
                path="/dashboard"
                element={
                  <ProtectedRoute>
                    <MainLayout>
                      <Suspense fallback={<LoadingSpinner message="Loading dashboard..." />}>
                        <DashboardPage />
                      </Suspense>
                    </MainLayout>
                  </ProtectedRoute>
                }
              />
              <Route
                path="/onboarding"
                element={
                  <ProtectedRoute>
                    <MainLayout>
                      <Suspense fallback={<LoadingSpinner message="Loading onboarding..." />}>
                        <OnboardingPage />
                      </Suspense>
                    </MainLayout>
                  </ProtectedRoute>
                }
              />
              <Route
                path="/chat"
                element={
                  <ProtectedRoute>
                    <MainLayout>
                      <Suspense fallback={<LoadingSpinner message="Loading chat..." />}>
                        <ChatPage />
                      </Suspense>
                    </MainLayout>
                  </ProtectedRoute>
                }
              />
              <Route
                path="/voice"
                element={
                  <ProtectedRoute>
                    <MainLayout>
                      <Suspense fallback={<LoadingSpinner message="Loading voice session..." />}>
                        <VoicePage />
                      </Suspense>
                    </MainLayout>
                  </ProtectedRoute>
                }
              />
              <Route
                path="/meals"
                element={
                  <ProtectedRoute>
                    <MainLayout>
                      <Suspense fallback={<LoadingSpinner message="Loading meals..." />}>
                        <MealsPage />
                      </Suspense>
                    </MainLayout>
                  </ProtectedRoute>
                }
              />
              <Route
                path="/workouts"
                element={
                  <ProtectedRoute>
                    <MainLayout>
                      <Suspense fallback={<LoadingSpinner message="Loading workouts..." />}>
                        <WorkoutsPage />
                      </Suspense>
                    </MainLayout>
                  </ProtectedRoute>
                }
              />

              {/* 404 fallback */}
              <Route path="*" element={<Navigate to="/dashboard" replace />} />
            </Routes>
          </VoiceProvider>
        </UserProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
