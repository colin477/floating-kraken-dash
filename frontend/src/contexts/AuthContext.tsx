import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { User } from '@/types';
import { authApi, profileApi } from '@/services/api';
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
        console.log('[AuthContext] Stored user:', JSON.stringify(storedUser));
        
        if (storedUser && storedUser.token) {
          console.log('[AuthContext] Found stored user with token, verifying...');
          console.log('[AuthContext] Making API call to /auth/me...');
          
          // Add timeout to the API call to prevent hanging
          const timeoutPromise = new Promise((_, reject) => {
            setTimeout(() => reject(new Error('API call timeout')), 10000); // 10 second timeout
          });
          
          try {
            const currentUser = await Promise.race([
              authApi.getCurrentUser(),
              timeoutPromise
            ]);
            console.log('[AuthContext] Token verified, current user:', currentUser);
            setUser({ ...currentUser, token: storedUser.token });
          } catch (apiError) {
            console.error('[AuthContext] API call failed or timed out:', apiError);
            // Clear invalid stored user data
            storage.clearUser();
          }
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
      console.log('[AuthContext] Starting login process...');
      const response = await authApi.login(email, password);
      const userData = {
        id: response.user.id,
        email: response.user.email,
        name: response.user.name,
        createdAt: response.user.created_at,
        subscription: response.user.subscription || 'free',
        token: response.access_token,
      };
      
      console.log('[AuthContext] Login successful, setting user data');
      setUser(userData);
      storage.setUser(userData);

      // After successful login, try to load user profile
      console.log('[AuthContext] Attempting to load user profile...');
      try {
        const profileData = await profileApi.getProfile();
        console.log('[AuthContext] Profile loaded successfully:', profileData);
        
        // Convert backend profile format to frontend format
        const frontendProfile = {
          userId: userData.id,
          dietaryRestrictions: profileData.dietary_restrictions || [],
          allergies: profileData.allergies || [],
          tastePreferences: profileData.taste_preferences || [],
          mealPreferences: profileData.meal_preferences || [],
          kitchenEquipment: profileData.kitchen_equipment || [],
          weeklyBudget: profileData.weekly_budget || 0,
          zipCode: profileData.zip_code || '',
          familyMembers: profileData.family_members || [],
          preferredGrocers: profileData.preferred_grocers || []
        };
        
        storage.setProfile(frontendProfile);
        console.log('[AuthContext] Profile saved to localStorage');
      } catch (profileError) {
        console.warn('[AuthContext] Failed to load profile, user may need to create one:', profileError);
        // Profile doesn't exist yet - this is normal for new users
        // The app will handle profile creation flow
      }
    } catch (error) {
      console.error('[AuthContext] 🚨 LOGIN ERROR CAUGHT:');
      console.error('[AuthContext] Error type:', error?.constructor?.name);
      console.error('[AuthContext] Error message:', error?.message);
      console.error('[AuthContext] Full error object:', error);
      
      // Always re-throw authentication-related errors to display to the user
      // Only fall back to mock data for genuine network/server connectivity issues
      const errorMessage = error?.message || '';
      
      // Check if this is a network/connectivity error (not an authentication error)
      const isNetworkError = errorMessage.includes('fetch') ||
                            errorMessage.includes('NetworkError') ||
                            errorMessage.includes('Failed to fetch') ||
                            errorMessage.includes('Connection refused') ||
                            errorMessage.includes('ECONNREFUSED') ||
                            errorMessage.includes('timeout') ||
                            errorMessage.includes('ETIMEDOUT');
      
      console.log('[AuthContext] Is network error?', isNetworkError);
      console.log('[AuthContext] Error message analysis:', {
        message: errorMessage,
        isNetworkError,
        shouldShowToUser: !isNetworkError
      });
      
      if (isNetworkError) {
        console.warn('[AuthContext] ❌ Network/server connectivity error - falling back to mock data for demo purposes');
        console.warn('[AuthContext] This means the error will NOT be shown to the user');
        // Only use mock data for genuine network/connectivity errors
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
      } else {
        console.error('[AuthContext] ✅ Authentication or other error - RE-THROWING error to display to user');
        console.error('[AuthContext] Error being re-thrown:', errorMessage);
        // Re-throw ALL non-network errors so they get displayed to the user
        // This includes authentication errors, validation errors, etc.
        throw error;
      }
    }
  };

  const register = async (email: string, password: string, name: string) => {
    try {
      console.log('[AuthContext] Starting registration process...');
      const response = await authApi.register(email, password, name);
      const userData = {
        id: response.user.id,
        email: response.user.email,
        name: response.user.name,
        createdAt: response.user.created_at,
        subscription: response.user.subscription || 'free',
        token: response.access_token,
      };
      
      console.log('[AuthContext] Registration successful, setting user data');
      setUser(userData);
      storage.setUser(userData);

      // For new registrations, don't try to load profile - they need to create one
      console.log('[AuthContext] New user registered, profile creation will be handled by onboarding flow');
    } catch (error) {
      console.error('[AuthContext] Registration failed:', error);
      
      // Check if this is a legitimate registration error (400 for duplicate email) vs network/server error
      const isRegistrationError = error?.message?.includes('Email already registered') ||
                                 error?.message?.includes('400') ||
                                 error?.message?.includes('Bad Request') ||
                                 error?.message?.includes('already exists');
      
      if (isRegistrationError) {
        console.error('[AuthContext] Registration failed - throwing error to display to user');
        // Re-throw the error so it gets displayed to the user
        throw error;
      } else {
        console.warn('[AuthContext] Network/server error during registration, falling back to mock data for demo purposes');
        // Only use mock data for non-registration errors (network issues, server down, etc.)
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
    }
  };

  const logout = () => {
    console.log('[AuthContext] LOGOUT: Starting logout process...');
    console.log('[AuthContext] LOGOUT: Current user before logout:', user);
    console.log('[AuthContext] LOGOUT: Current isAuthenticated before logout:', !!user);
    console.log('[AuthContext] LOGOUT: Window override before clearing:', (window as any).__DEMO_MODE_OVERRIDE__);
    
    setUser(null);
    storage.clearAllUserData();
    
    // Disable demo mode on logout to ensure proper redirect to auth form
    // Use the persistent disableDemoMode function to survive page reloads
    if (typeof window !== 'undefined') {
      const demoOverride = {
        enabled: false,
        bypassAuth: false,
        useMockData: false,
        showDemoIndicator: false,
      };
      
      // Set both window override and persistent localStorage
      (window as any).__DEMO_MODE_OVERRIDE__ = demoOverride;
      localStorage.setItem('__DEMO_MODE_OVERRIDE__', JSON.stringify(demoOverride));
      
      console.log('[AuthContext] LOGOUT: Demo mode override set to:', demoOverride);
      console.log('[AuthContext] LOGOUT: Window override after setting:', (window as any).__DEMO_MODE_OVERRIDE__);
      console.log('[AuthContext] LOGOUT: Persistent override stored in localStorage');
    }
    
    console.log('[AuthContext] LOGOUT: User state cleared, storage cleared');
    console.log('[AuthContext] LOGOUT: New isAuthenticated after logout:', false);
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