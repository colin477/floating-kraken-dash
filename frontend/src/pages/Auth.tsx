import { useState, useEffect } from 'react';
import { User, UserProfile, Recipe } from '@/types';
import { storage } from '@/lib/storage';
import { AuthForm } from '@/components/AuthForm';
import { useAuth } from '@/hooks/useAuth';
import { TableSettingChoice } from '@/components/TableSettingChoice';
import { ProfileSetup } from '@/components/ProfileSetup';
import { Dashboard } from '@/components/Dashboard';
import { ReceiptScan } from '@/components/ReceiptScan';
import { MealPhotoAnalysis } from '@/components/MealPhotoAnalysis';
import { AddFromLink } from '@/components/AddFromLink';
import { CreateRecipe } from '@/components/CreateRecipe';
import { MealPlanner } from '@/components/MealPlanner';
import { Community } from '@/components/Community';
import { Profile } from '@/components/Profile';
import { Recipes } from '@/components/Recipes';
import { RecipeDetail } from '@/components/RecipeDetail';
import { Pantry } from '@/components/Pantry';
import { ShoppingListBuilder } from '@/components/ShoppingListBuilder';
import { ShoppingListManager } from '@/components/ShoppingListManager';
import { LeftoverManager } from '@/components/LeftoverManager';
import { FamilyMembers } from '@/components/FamilyMembers';
import { Sidebar } from '@/components/Sidebar';
import { Button } from '@/components/ui/button';
import { Menu } from 'lucide-react';
import { shouldBypassAuth, isDemoModeEnabled } from '@/lib/demoMode';

const Auth = () => {
  const { user: authUser, isAuthenticated, isLoading: authLoading, logout } = useAuth();
  
  // Demo mode support
  const demoModeEnabled = isDemoModeEnabled();
  const bypassAuth = shouldBypassAuth();
  const effectivelyAuthenticated = isAuthenticated || bypassAuth;
  
  // DEBUG: Enhanced logging for authentication and demo mode state
  console.log('[Auth] AUTH STATE:', {
    authUser: !!authUser,
    isAuthenticated,
    demoModeEnabled,
    bypassAuth,
    effectivelyAuthenticated,
    authLoading,
    timestamp: new Date().toISOString(),
    windowOverride: (window as any).__DEMO_MODE_OVERRIDE__
  });
  
  // Create a demo user when in demo mode
  const effectiveUser = authUser || (bypassAuth ? {
    id: 'demo-user',
    email: 'demo@example.com',
    name: 'Demo User',
    createdAt: new Date().toISOString(),
    subscription: 'basic' as const,
    token: 'demo-token'
  } : null);
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [setupLevel, setSetupLevel] = useState<'basic' | 'medium' | 'full' | null>(null);
  const [currentPage, setCurrentPage] = useState<string>('dashboard');
  const [selectedRecipe, setSelectedRecipe] = useState<Recipe | null>(null);
  const [isNewUser, setIsNewUser] = useState(false);
  const [editingListId, setEditingListId] = useState<string | null>(null);
  
  // Sidebar state management
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  
  const toggleSidebar = () => {
    setIsSidebarOpen(!isSidebarOpen);
  };

  useEffect(() => {
    // Check for reset parameter in URL for testing purposes
    const urlParams = new URLSearchParams(window.location.search);
    const shouldReset = urlParams.get('reset') === 'true';
    
    if (shouldReset) {
      // Clear all data if reset parameter is present
      storage.clearAllUserData();
      // Remove the reset parameter from URL
      window.history.replaceState({}, document.title, window.location.pathname);
    }
    
    // Load profile when user is authenticated (or in demo mode)
    if (effectivelyAuthenticated && effectiveUser) {
      let savedProfile = storage.getProfile();
      
      // If in demo mode and no profile exists, create a demo profile
      if (bypassAuth && !savedProfile) {
        const demoProfile: UserProfile = {
          userId: effectiveUser.id,
          dietaryRestrictions: ['Vegetarian'],
          allergies: [],
          tastePreferences: ['Savory', 'Comfort food'],
          mealPreferences: ['Quick meals (under 30 min)', 'Kid-friendly'],
          kitchenEquipment: ['Oven', 'Stovetop', 'Microwave'],
          weeklyBudget: 150,
          zipCode: '80202',
          familyMembers: [],
          preferredGrocers: ['kroger-local', 'safeway-local']
        };
        storage.setProfile(demoProfile);
        savedProfile = demoProfile;
        console.log('🧪 [Demo Mode] Created demo profile');
      }
      
      setProfile(savedProfile);
      setIsNewUser(false); // Existing user
    }
  }, [isAuthenticated, authUser]);

  const handleAuthSuccess = (newUser: User, isNewUserFlag: boolean) => {
    setIsNewUser(isNewUserFlag);
    
    if (!isNewUserFlag) {
      // Existing user - should already have profile, go straight to dashboard
      const existingProfile = storage.getProfile();
      setProfile(existingProfile);
    }
    // New users will go through plan selection flow
  };

  const handleTableSettingChoice = (level: 'basic' | 'medium' | 'full') => {
    setSetupLevel(level);
  };

  const handleProfileComplete = (selectedLevel: 'basic' | 'medium' | 'full') => {
    const savedProfile = storage.getProfile();
    setProfile(savedProfile);
    
    // Update user subscription based on selected level
    if (authUser) {
      const subscriptionMapping = {
        'basic': 'free' as const,
        'medium': 'basic' as const,
        'full': 'premium' as const
      };
      
      const updatedUser = {
        ...authUser,
        subscription: subscriptionMapping[selectedLevel],
        // Remove trial end date for premium users
        ...(selectedLevel === 'full' ? { trialEndsAt: undefined } : {})
      };
      
      storage.setUser(updatedUser);
    }
    
    setSetupLevel(null); // Clear setup level after completion
    setIsNewUser(false); // No longer a new user
  };

  const handleLogout = () => {
    console.log('[Auth] LOGOUT: Starting handleLogout...');
    console.log('[Auth] LOGOUT: Current authUser:', authUser);
    console.log('[Auth] LOGOUT: Current isAuthenticated:', isAuthenticated);
    console.log('[Auth] LOGOUT: Demo mode enabled:', demoModeEnabled);
    console.log('[Auth] LOGOUT: Should bypass auth:', bypassAuth);
    console.log('[Auth] LOGOUT: Effectively authenticated before logout:', effectivelyAuthenticated);
    console.log('[Auth] LOGOUT: Window override before logout:', (window as any).__DEMO_MODE_OVERRIDE__);
    
    logout();
    setProfile(null);
    setSetupLevel(null);
    setCurrentPage('dashboard');
    setIsNewUser(false);
    
    console.log('[Auth] LOGOUT: Logout completed, state cleared');
    console.log('[Auth] LOGOUT: Window override after logout:', (window as any).__DEMO_MODE_OVERRIDE__);
    
    // DEBUG: Check demo mode state before page reload
    console.log('[Auth] LOGOUT: Demo mode state before reload:', {
      demoModeEnabled: isDemoModeEnabled(),
      bypassAuth: shouldBypassAuth(),
      windowOverride: (window as any).__DEMO_MODE_OVERRIDE__
    });
    
    // Force a page reload to ensure clean state after logout
    setTimeout(() => {
      console.log('[Auth] LOGOUT: Forcing page reload for clean state');
      window.location.reload();
    }, 100);
  };

  const handleNavigate = (page: string) => {
    // Handle recipe detail navigation
    if (page.startsWith('recipe-')) {
      const recipeId = page.replace('recipe-', '');
      const recipes = storage.getRecipes();
      const recipe = recipes.find(r => r.id === recipeId);
      if (recipe) {
        setSelectedRecipe(recipe);
        setCurrentPage('recipe-detail');
      }
    } else {
      // Refresh profile data when navigating back to dashboard
      if (page === 'dashboard') {
        const updatedProfile = storage.getProfile();
        setProfile(updatedProfile);
      }
      
      setCurrentPage(page);
      setSelectedRecipe(null);
      setEditingListId(null);
    }
    
    // Close sidebar on mobile after navigation
    if (window.innerWidth <= 1023) {
      setIsSidebarOpen(false);
    }
  };

  const handleRecipeSelect = (recipe: Recipe) => {
    setSelectedRecipe(recipe);
    setCurrentPage('recipe-detail');
  };

  const handleEditShoppingList = (listId: string) => {
    setEditingListId(listId);
    setCurrentPage('edit-shopping-list');
  };

  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading EZ Eatin'...</p>
        </div>
      </div>
    );
  }

  // Show auth form if not authenticated (unless demo mode bypasses auth)
  if (!effectivelyAuthenticated || !effectiveUser) {
    return <AuthForm onAuthSuccess={handleAuthSuccess} />;
  }

  // For existing users (login), skip plan selection and go to dashboard
  if (!isNewUser && effectiveUser) {
    // Render current page for existing users
    const renderCurrentPage = () => {
      switch (currentPage) {
        case 'dashboard':
          return <Dashboard user={effectiveUser} profile={profile} onNavigate={handleNavigate} />;
        case 'receipt-scan':
          return <ReceiptScan onBack={() => handleNavigate('dashboard')} />;
        case 'meal-photo':
          return <MealPhotoAnalysis onBack={() => handleNavigate('dashboard')} />;
        case 'add-from-link':
          return <AddFromLink onBack={() => handleNavigate('dashboard')} />;
        case 'create-recipe':
          return <CreateRecipe onBack={() => handleNavigate('dashboard')} />;
        case 'meal-planner':
          return profile ? (
            <MealPlanner user={effectiveUser} profile={profile} onBack={() => handleNavigate('dashboard')} />
          ) : (
            <Dashboard user={effectiveUser} profile={profile} onNavigate={handleNavigate} />
          );
        case 'shopping-lists':
          return (
            <ShoppingListManager 
              onBack={() => handleNavigate('dashboard')} 
              onCreateNew={() => handleNavigate('create-shopping-list')}
              onEditList={handleEditShoppingList}
            />
          );
        case 'create-shopping-list':
          return <ShoppingListBuilder onBack={() => handleNavigate('shopping-lists')} />;
        case 'edit-shopping-list':
          return <ShoppingListBuilder onBack={() => handleNavigate('shopping-lists')} initialListId={editingListId} />;
        case 'leftovers':
          return <LeftoverManager onBack={() => handleNavigate('dashboard')} />;
        case 'community':
          return <Community user={effectiveUser} onBack={() => handleNavigate('dashboard')} />;
        case 'profile':
          return profile ? (
            <Profile user={effectiveUser} profile={profile} onBack={() => handleNavigate('dashboard')} onLogout={handleLogout} />
          ) : (
            <Dashboard user={effectiveUser} profile={profile} onNavigate={handleNavigate} />
          );
        case 'family-members':
          console.log('🔍 [Auth] Rendering FamilyMembers with:', {
            effectiveUser: effectiveUser,
            effectiveUserExists: !!effectiveUser,
            effectiveUserName: effectiveUser?.name,
            profile: profile,
            profileExists: !!profile,
            timestamp: new Date().toISOString()
          });
          return profile ? (
            <FamilyMembers user={effectiveUser} profile={profile} onBack={() => handleNavigate('dashboard')} />
          ) : (
            <Dashboard user={effectiveUser} profile={profile} onNavigate={handleNavigate} />
          );
        case 'recipes':
          return <Recipes user={effectiveUser} onBack={() => handleNavigate('dashboard')} onRecipeSelect={handleRecipeSelect} onNavigate={handleNavigate} />;
        case 'recipe-detail':
          return selectedRecipe ? (
            <RecipeDetail recipe={selectedRecipe} onBack={() => handleNavigate('recipes')} />
          ) : (
            <Dashboard user={effectiveUser} profile={profile} onNavigate={handleNavigate} />
          );
        case 'pantry':
          return <Pantry onBack={() => handleNavigate('dashboard')} />;
        default:
          return <Dashboard user={effectiveUser} profile={profile} onNavigate={handleNavigate} />;
      }
    };

    return (
      <div className="flex h-screen bg-background">
        {/* Sidebar */}
        <Sidebar
          isOpen={isSidebarOpen}
          onToggle={toggleSidebar}
          currentPage={currentPage}
          onNavigate={handleNavigate}
          user={effectiveUser ? {
            name: effectiveUser.name,
            email: effectiveUser.email,
            subscription: effectiveUser.subscription
          } : undefined}
        />
        
        {/* Main Content Area */}
        <div className="flex-1 flex flex-col lg:ml-0">
          {/* Header with hamburger menu for mobile/tablet */}
          <header className="lg:hidden bg-background border-b border-border p-4 flex items-center justify-between">
            <Button
              variant="ghost"
              size="sm"
              onClick={toggleSidebar}
              className="p-2"
              aria-label="Toggle sidebar"
            >
              <Menu className="h-6 w-6" />
            </Button>
            <h1 className="text-lg font-semibold">EZ Eatin'</h1>
            <div className="w-10" /> {/* Spacer for centering */}
          </header>
          
          {/* Page Content */}
          <main className="flex-1 overflow-auto">
            <div className="lg:pl-0">
              {renderCurrentPage()}
            </div>
          </main>
        </div>
        
        {/* Development Reset Button - only show in development */}
        {process.env.NODE_ENV === 'development' && (
          <div className="fixed bottom-4 right-4 z-50">
            <button
              onClick={() => {
                storage.clearAllUserData();
                window.location.reload();
              }}
              className="bg-red-500 text-white px-3 py-2 rounded-lg text-xs hover:bg-red-600 transition-colors"
              title="Reset all data (development only)"
            >
              Reset Data
            </button>
          </div>
        )}
      </div>
    );
  }

  // For new users, show plan selection flow
  // Show table setting choice if new user exists but no setup level chosen
  if (isNewUser && !profile && !setupLevel) {
    return <TableSettingChoice onChoice={handleTableSettingChoice} />;
  }

  // Show profile setup if new user exists, setup level chosen, but no profile
  if (isNewUser && !profile && setupLevel) {
    return (
      <ProfileSetup
        userId={effectiveUser.id}
        level={setupLevel}
        onComplete={() => handleProfileComplete(setupLevel)}
      />
    );
  }

  // Fallback to dashboard
  return <Dashboard user={effectiveUser} profile={profile} onNavigate={handleNavigate} />;
};

export default Auth;