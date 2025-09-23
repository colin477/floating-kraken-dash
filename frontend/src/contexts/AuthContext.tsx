import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { User } from '@/types';
import { authApi } from '@/services/api';
import { storage } from '@/lib/storage';

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, name: string) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const isAuthenticated = !!user;

  // Initialize auth state from localStorage
  useEffect(() => {
    const initializeAuth = async () => {
      try {
        console.log('[AuthContext] Initializing auth...');
        const storedUser = storage.getUser();
        console.log('[AuthContext] Stored user:', storedUser);
        
        if (storedUser && storedUser.token) {
          console.log('[AuthContext] Found stored user with token, verifying...');
          // Verify token is still valid by fetching current user
          const currentUser = await authApi.getCurrentUser();
          console.log('[AuthContext] Token verified, current user:', currentUser);
          setUser({ ...currentUser, token: storedUser.token });
        } else {
          console.log('[AuthContext] No stored user or token found');
        }
      } catch (error) {
        console.error('[AuthContext] Failed to initialize auth:', error);
        // Clear invalid stored user data
        storage.clearUser();
      } finally {
        console.log('[AuthContext] Auth initialization complete, isLoading set to false');
        setIsLoading(false);
      }
    };

    initializeAuth();
  }, []);

  const login = async (email: string, password: string) => {
    try {
      const response = await authApi.login(email, password);
      const userData = {
        id: response.user.id,
        email: response.user.email,
        name: response.user.name,
        createdAt: response.user.created_at,
        subscription: response.user.subscription || 'free',
        token: response.access_token,
      };
      
      setUser(userData);
      storage.setUser(userData);
    } catch (error) {
      console.warn('[AuthContext] API login failed, using mock data:', error);
      // Fallback to mock login for demo purposes
      const mockUserData = {
        id: Date.now().toString(),
        email: email,
        name: email.split('@')[0],
        createdAt: new Date().toISOString(),
        subscription: 'basic' as const,
        token: 'mock-jwt-token-' + Date.now(), // Mock JWT token
      };
      
      setUser(mockUserData);
      storage.setUser(mockUserData);
    }
  };

  const register = async (email: string, password: string, name: string) => {
    try {
      const response = await authApi.register(email, password, name);
      const userData = {
        id: response.user.id,
        email: response.user.email,
        name: response.user.name,
        createdAt: response.user.created_at,
        subscription: response.user.subscription || 'free',
        token: response.access_token,
      };
      
      setUser(userData);
      storage.setUser(userData);
    } catch (error) {
      console.warn('[AuthContext] API registration failed, using mock data:', error);
      // Fallback to mock registration for demo purposes
      const mockUserData = {
        id: Date.now().toString(),
        email: email,
        name: name,
        createdAt: new Date().toISOString(),
        subscription: 'free' as const,
        token: 'mock-jwt-token-' + Date.now(), // Mock JWT token
      };
      
      setUser(mockUserData);
      storage.setUser(mockUserData);
    }
  };

  const logout = () => {
    setUser(null);
    storage.clearAllUserData();
  };

  const refreshUser = async () => {
    try {
      if (user?.token) {
        const currentUser = await authApi.getCurrentUser();
        setUser(prev => prev ? { ...currentUser, token: prev.token } : null);
      }
    } catch (error) {
      console.error('Failed to refresh user:', error);
      logout();
    }
  };

  const value: AuthContextType = {
    user,
    isLoading,
    isAuthenticated,
    login,
    register,
    logout,
    refreshUser,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};