import React, { useEffect } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { TableSettingChoice } from '@/components/TableSettingChoice';
import { ProfileSetup } from '@/components/ProfileSetup';

interface OnboardingGuardProps {
  children: React.ReactNode;
}

export const OnboardingGuard: React.FC<OnboardingGuardProps> = ({ children }) => {
  const { 
    user, 
    onboardingState, 
    isOnboardingLoading, 
    checkOnboardingStatus,
    selectPlan,
    completeOnboarding 
  } = useAuth();

  // Check onboarding status when component mounts or user changes
  useEffect(() => {
    if (user && !onboardingState.isOnboardingComplete) {
      checkOnboardingStatus();
    }
  }, [user]); // Remove checkOnboardingStatus from dependencies to prevent infinite loop

  // Show loading while checking onboarding status
  if (isOnboardingLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Checking your setup progress...</p>
        </div>
      </div>
    );
  }

  // If onboarding is complete, render children (main app)
  if (onboardingState.isOnboardingComplete) {
    return <>{children}</>;
  }

  // If user is not authenticated, let AuthContext handle it
  if (!user) {
    return <>{children}</>;
  }

  // Handle onboarding steps based on server-side state
  const handlePlanSelection = async (level: 'basic' | 'medium' | 'full') => {
    const planMapping = {
      'basic': 'free' as const,
      'medium': 'basic' as const,
      'full': 'premium' as const
    };

    try {
      await selectPlan(planMapping[level], level);
    } catch (error) {
      console.error('Failed to select plan:', error);
      
      // Check if this is a 401 authentication error
      const errorMessage = error?.message || '';
      if (errorMessage.includes('401') ||
          errorMessage.includes('Unauthorized') ||
          errorMessage.includes('Session expired') ||
          errorMessage.includes('Could not validate credentials')) {
        console.error('[OnboardingGuard] Authentication error during plan selection:', errorMessage);
        // The AuthContext will handle logout automatically, just show user-friendly message
        alert('Your session has expired. Please log in again to continue.');
        return;
      }
      
      // Handle other types of errors
      alert('Failed to select plan. Please try again.');
    }
  };

  const handleProfileComplete = async () => {
    try {
      await completeOnboarding();
    } catch (error) {
      console.error('Failed to complete onboarding:', error);
      // Handle error - could show toast or error message
    }
  };

  // Step 1: Plan Selection (if not selected)
  if (!onboardingState.planSelected || onboardingState.currentStep === 'plan-selection') {
    return <TableSettingChoice onChoice={handlePlanSelection} />;
  }

  // Step 2: Profile Setup (if plan selected but profile not completed)
  if (onboardingState.planSelected && !onboardingState.profileCompleted && onboardingState.setupLevel) {
    return (
      <ProfileSetup
        userId={user.id}
        level={onboardingState.setupLevel}
        onComplete={handleProfileComplete}
      />
    );
  }

  // Fallback: if we're in an unexpected state, show plan selection
  return <TableSettingChoice onChoice={handlePlanSelection} />;
};