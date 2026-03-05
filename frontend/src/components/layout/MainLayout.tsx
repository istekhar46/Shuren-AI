import React from 'react';
import { Header } from './Header';
import { Footer } from './Footer';
import { useUser } from '../../contexts/UserContext';

interface MainLayoutProps {
  children: React.ReactNode;
  className?: string;
}

export const MainLayout: React.FC<MainLayoutProps> = ({
  children,
  className = '',
}) => {
  const { onboardingCompleted } = useUser();

  return (
    <div className="h-[100vh] flex flex-col" style={{ background: 'var(--color-bg-primary)', color: 'var(--color-text-secondary)' }}>
      <Header onboardingCompleted={onboardingCompleted} />
      <main className={`flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 ${className}`}>
        {children}
      </main>
      <Footer />
    </div>
  );
};
