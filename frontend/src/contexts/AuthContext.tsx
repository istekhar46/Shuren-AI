import React, { createContext, useContext, useState, useEffect } from 'react';
import type { ReactNode } from 'react';
import type { User } from '../types';

interface AuthContextType {
  isAuthenticated: boolean;
  user: User | null;
  token: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName: string) => Promise<void>;
  logout: () => void;
  loading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  // Initialize auth state from localStorage on mount
  useEffect(() => {
    const storedToken = localStorage.getItem('auth_token');
    const storedUser = localStorage.getItem('auth_user');

    if (storedToken && storedUser) {
      try {
        const parsedUser = JSON.parse(storedUser);
        setToken(storedToken);
        setUser(parsedUser);
      } catch (error) {
        // Invalid stored data, clear it
        localStorage.removeItem('auth_token');
        localStorage.removeItem('auth_user');
      }
    }

    setLoading(false);
  }, []);

  const login = async (email: string, password: string): Promise<void> => {
    // Import authService dynamically to avoid circular dependency
    const { authService } = await import('../services/authService');
    
    const response = await authService.login(email, password);
    
    // Store token
    localStorage.setItem('auth_token', response.access_token);
    setToken(response.access_token);
    
    // Fetch full user data
    const userData = await authService.getCurrentUser();
    localStorage.setItem('auth_user', JSON.stringify(userData));
    setUser(userData);
  };

  const register = async (email: string, password: string, fullName: string): Promise<void> => {
    // Import authService dynamically to avoid circular dependency
    const { authService } = await import('../services/authService');
    
    const response = await authService.register(email, password, fullName);
    
    // Store token
    localStorage.setItem('auth_token', response.access_token);
    setToken(response.access_token);
    
    // Fetch full user data
    const userData = await authService.getCurrentUser();
    localStorage.setItem('auth_user', JSON.stringify(userData));
    setUser(userData);
  };

  const logout = (): void => {
    // Clear localStorage
    localStorage.removeItem('auth_token');
    localStorage.removeItem('auth_user');
    
    // Clear state
    setToken(null);
    setUser(null);
  };

  const value: AuthContextType = {
    isAuthenticated: !!token && !!user,
    user,
    token,
    login,
    register,
    logout,
    loading,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
