import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { User, OnboardingState, OnboardingStatusResponse } from '@/types';
import { authApi, profileApi } from '@/services/api';
import { storage } from '@/lib/storage';

// Helper function to decode JWT token and check expiry
const isTokenExpired = (token: string): boolean => {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    const currentTime = Math.floor(Date.now() / 1000);
    // Check if token expires within 30 seconds
    return payload.exp < (currentTime + 30);
  } catch (error) {
    console.error('[AuthContext] Error decoding token:', error);
    return true; // Treat invalid tokens as expired
  }
};

// Helper function to check if token needs refresh and handle it
const ensureValidToken = async (user: User): Promise<User | null> => {
  if (!user.token || !isTokenExpired(user.token)) {
    return user; // Token is still valid
  }

  console.log('[AuthContext] Token is expiring soon, user needs to re-authenticate');
  // For now, we'll return null to trigger re-authentication
  // In a future enhancement, we could implement refresh token logic
  return null;
};

export interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  onboardingState: OnboardingState;
  isOnboardingLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, name: string) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
  checkOnboardingStatus: () => Promise<void>;
  selectPlan: (planType: 'free' | 'basic' | 'premium', setupLevel: 'basic' | 'medium' | 'full') => Promise<void>;
  completeOnboarding: () => Promise<void>;
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [onboardingState, setOnboardingState] = useState<OnboardingState>({
    isOnboardingComplete: false,
    currentStep: null,
    planSelected: false,
    profileCompleted: false,
    setupLevel: null,
    planType: null,
  });
  const [isOnboardingLoading, setIsOnboardingLoading] = useState(false);

  const isAuthenticated = !!user;
  
  // Test comment for Fast Refresh verification - HMR Context Test

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
            console.log('🔍 [AuthContext] INIT - currentUser.subscription:', currentUser?.subscription);
            
            const finalUser = { ...currentUser, token: storedUser.token, subscription: currentUser?.subscription || 'free' };
            console.log('🔍 [AuthContext] INIT - Final user.subscription:', finalUser.subscription);
            setUser(finalUser);
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
      // DEBUG: Log the actual API response to diagnose the name field issue
      console.log('🔍 [AuthContext] Raw API response.user:', response.user);
      console.log('🔍 [AuthContext] Available user fields:', Object.keys(response.user));
      console.log('🔍 [AuthContext] response.user.name:', response.user.name);
      console.log('🔍 [AuthContext] response.user.full_name:', response.user.full_name);
      
      const userData = {
        id: response.user.id,
        email: response.user.email,
        name: response.user.name || response.user.full_name, // Handle both name and full_name
        createdAt: response.user.created_at,
        subscription: response.user.subscription || 'free',
        token: response.access_token,
      };
      
      console.log('🔍 [AuthContext] LOGIN - Final userData.subscription:', userData.subscription);
      console.log('🔍 [AuthContext] LOGIN - response.user.subscription:', response.user.subscription);
      
      console.log('🔍 [AuthContext] Final userData.name:', userData.name);
      
      console.log('[AuthContext] Login successful, setting user data');
      setUser(userData);
      storage.setUser(userData);

      // After successful login, check onboarding status
      console.log('[AuthContext] Checking onboarding status after login...');
      try {
        const status: OnboardingStatusResponse = await profileApi.getOnboardingStatus();
        console.log('[AuthContext] Onboarding status:', status);
        
        setOnboardingState({
          isOnboardingComplete: status.onboarding_completed,
          currentStep: status.current_step || null,
          planSelected: status.plan_selected || false,
          profileCompleted: status.profile_completed || false,
          setupLevel: status.setup_level || null,
          planType: status.plan_type || null,
        });

        // If onboarding is complete, try to load user profile
        if (status.onboarding_completed) {
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
            console.warn('[AuthContext] Failed to load profile:', profileError);
          }
        }
      } catch (onboardingError) {
        console.warn('[AuthContext] Failed to check onboarding status, assuming incomplete:', onboardingError);
        // Set default state for users where we can't check status
        setOnboardingState({
          isOnboardingComplete: false,
          currentStep: 'plan-selection',
          planSelected: false,
          profileCompleted: false,
          setupLevel: null,
          planType: null,
        });
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
      
      console.log('🔍 [AuthContext] DETAILED ERROR ANALYSIS:');
      console.log('🔍 [AuthContext] Raw error object:', error);
      console.log('🔍 [AuthContext] Error message:', errorMessage);
      console.log('🔍 [AuthContext] Is network error?', isNetworkError);
      console.log('🔍 [AuthContext] Error message analysis:', {
        message: errorMessage,
        isNetworkError,
        shouldShowToUser: !isNetworkError,
        willUseMockData: isNetworkError,
        willThrowError: !isNetworkError
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
      // DEBUG: Log the actual API response to diagnose the name field issue
      console.log('🔍 [AuthContext] Registration - Raw API response.user:', response.user);
      console.log('🔍 [AuthContext] Registration - Available user fields:', Object.keys(response.user));
      console.log('🔍 [AuthContext] Registration - response.user.name:', response.user.name);
      console.log('🔍 [AuthContext] Registration - response.user.full_name:', response.user.full_name);
      
      const userData = {
        id: response.user.id,
        email: response.user.email,
        name: response.user.name || response.user.full_name, // Handle both name and full_name
        createdAt: response.user.created_at,
        subscription: response.user.subscription || 'free',
        token: response.access_token,
      };
      
      console.log('🔍 [AuthContext] REGISTER - Final userData.subscription:', userData.subscription);
      console.log('🔍 [AuthContext] REGISTER - response.user.subscription:', response.user.subscription);
      
      console.log('🔍 [AuthContext] Registration - Final userData.name:', userData.name);
      
      console.log('[AuthContext] Registration successful, setting user data');
      setUser(userData);
      storage.setUser(userData);

      // For new registrations, set initial onboarding state
      console.log('[AuthContext] New user registered, setting initial onboarding state');
      setOnboardingState({
        isOnboardingComplete: false,
        currentStep: 'plan-selection',
        planSelected: false,
        profileCompleted: false,
        setupLevel: null,
        planType: null,
      });
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
        
        // DEBUG: Enhanced logging to diagnose the name field issue
        console.log('🔍 [AuthContext] getCurrentUser - Raw API response:', currentUser);
        console.log('🔍 [AuthContext] getCurrentUser - Available fields:', Object.keys(currentUser || {}));
        console.log('🔍 [AuthContext] getCurrentUser - currentUser.name:', currentUser?.name);
        console.log('🔍 [AuthContext] getCurrentUser - currentUser.full_name:', currentUser?.full_name);
        console.log('🔍 [AuthContext] getCurrentUser - typeof currentUser:', typeof currentUser);
        console.log('🔍 [AuthContext] getCurrentUser - currentUser is null/undefined:', !currentUser);
        
        if (!currentUser) {
          console.error('❌ [AuthContext] getCurrentUser returned null/undefined');
          logout();
          return;
        }
        
        // Ensure name field is properly mapped with fallback logic
        const mappedName = currentUser.name || currentUser.full_name || 'Unknown User';
        const mappedUser = {
          ...currentUser,
          name: mappedName
        };
        
        console.log('🔍 [AuthContext] getCurrentUser - Final mappedUser.name:', mappedUser.name);
        console.log('🔍 [AuthContext] getCurrentUser - Final mappedUser object:', mappedUser);
        
        setUser(prev => prev ? { ...mappedUser, token: prev.token } : null);
      }
    } catch (error) {
      console.error('❌ [AuthContext] Failed to refresh user:', error);
      console.error('❌ [AuthContext] Error details:', {
        message: error?.message,
        stack: error?.stack,
        name: error?.name
      });
      logout();
    }
  };

  const checkOnboardingStatus = async () => {
    if (!user) return;
    
    setIsOnboardingLoading(true);
    try {
      console.log('[AuthContext] Checking onboarding status...');
      const status: OnboardingStatusResponse = await profileApi.getOnboardingStatus();
      console.log('[AuthContext] Onboarding status:', status);
      
      setOnboardingState({
        isOnboardingComplete: status.onboarding_completed,
        currentStep: status.current_step || null,
        planSelected: status.plan_selected || false,
        profileCompleted: status.profile_completed || false,
        setupLevel: status.setup_level || null,
        planType: status.plan_type || null,
      });
    } catch (error) {
      console.error('[AuthContext] Failed to check onboarding status:', error);
      // Set default state for new users
      setOnboardingState({
        isOnboardingComplete: false,
        currentStep: 'plan-selection',
        planSelected: false,
        profileCompleted: false,
        setupLevel: null,
        planType: null,
      });
    } finally {
      setIsOnboardingLoading(false);
    }
  };

  const selectPlan = async (planType: 'free' | 'basic' | 'premium', setupLevel: 'basic' | 'medium' | 'full') => {
    try {
      console.log('[AuthContext] Selecting plan:', { planType, setupLevel });
      
      // Ensure token is valid before making the API call
      if (user) {
        const validUser = await ensureValidToken(user);
        if (!validUser) {
          console.error('[AuthContext] Token expired, user needs to re-authenticate');
          logout();
          throw new Error('Session expired. Please log in again.');
        }
        
        // Update user if token was refreshed
        if (validUser !== user) {
          setUser(validUser);
        }
      }
      
      await profileApi.selectPlan({ plan_type: planType, setup_level: setupLevel });
      
      // Update onboarding state
      setOnboardingState(prev => ({
        ...prev,
        planSelected: true,
        planType,
        setupLevel,
        currentStep: 'profile-setup',
      }));
      
      console.log('[AuthContext] Plan selected successfully');
    } catch (error) {
      console.error('[AuthContext] Failed to select plan:', error);
      throw error;
    }
  };

  const completeOnboarding = async () => {
    try {
      console.log('[AuthContext] Completing onboarding...');
      await profileApi.completeOnboarding();
      
      // Update onboarding state
      setOnboardingState(prev => ({
        ...prev,
        isOnboardingComplete: true,
        profileCompleted: true,
        currentStep: null,
      }));
      
      console.log('[AuthContext] Onboarding completed successfully');
    } catch (error) {
      console.error('[AuthContext] Failed to complete onboarding:', error);
      throw error;
    }
  };

  const value: AuthContextType = {
    user,
    isLoading,
    isAuthenticated,
    onboardingState,
    isOnboardingLoading,
    login,
    register,
    logout,
    refreshUser,
    checkOnboardingStatus,
    selectPlan,
    completeOnboarding,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export { AuthProvider };
export default AuthProvider;