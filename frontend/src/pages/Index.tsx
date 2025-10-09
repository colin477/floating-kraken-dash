import { useState, useEffect, useCallback } from 'react';
import { User, UserProfile, Recipe } from '@/types';
import { storage } from '@/lib/storage';
import { AuthForm } from '@/components/AuthForm';
import { useAuth } from '@/hooks/useAuth';
import { OnboardingGuard } from '@/components/OnboardingGuard';
import { Dashboard } from '@/components/Dashboard';
import { ReceiptScan } from '@/components/ReceiptScan';
import { ReceiptHistory } from '@/components/ReceiptHistory';
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

// GLOBAL TEST FUNCTION TO DEBUG NAVIGATION ISSUE
(window as any).testNavigationFunction = (page: string) => {
  console.log('🌍 [GLOBAL] Test navigation function called with page:', page);
  alert('🌍 GLOBAL TEST FUNCTION CALLED with page: ' + page);
  return true;
};

const Index = () => {
  const { user: authUser, isAuthenticated, isLoading: authLoading, logout } = useAuth();
  
  // Demo mode support
  const demoModeEnabled = isDemoModeEnabled();
  const bypassAuth = shouldBypassAuth();
  const effectivelyAuthenticated = isAuthenticated || bypassAuth;
  
  // DEBUG: Enhanced logging for authentication and demo mode state
  console.log('[Index] AUTH STATE:', {
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
  const [currentPage, setCurrentPage] = useState<string>('dashboard');
  const [selectedRecipe, setSelectedRecipe] = useState<Recipe | null>(null);
  
  // DEBUG: Watch currentPage changes with detailed stack trace
  useEffect(() => {
    console.log('🔍 [Index] currentPage changed to:', currentPage);
    console.log('🔍 [Index] currentPage change stack trace:', new Error().stack);
    
    // Special logging for receipts page changes
    if (currentPage === 'receipts') {
      console.log('🧾 [Index] SUCCESS! currentPage is now receipts');
    } else if (currentPage === 'dashboard') {
      console.log('📊 [Index] currentPage is dashboard - checking if this was unexpected');
    }
  }, [currentPage]);
  const [editingListId, setEditingListId] = useState<string | null>(null);
  
  // Sidebar state management
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  
  const toggleSidebar = () => {
    setIsSidebarOpen(!isSidebarOpen);
  };

  useEffect(() => {
    console.log('🔍 [Index] Main useEffect triggered - this might reset currentPage!');
    console.log('🔍 [Index] Main useEffect - currentPage before:', currentPage);
    console.log('🔍 [Index] Main useEffect - dependencies:', { isAuthenticated, authUser: !!authUser });
    
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
          familyMembers: [],
          preferredGrocers: ['kroger-local', 'safeway-local']
        };
        storage.setProfile(demoProfile);
        savedProfile = demoProfile;
        console.log('🧪 [Demo Mode] Created demo profile');
      }
      
      setProfile(savedProfile);
    }
    
    console.log('🔍 [Index] Main useEffect completed - currentPage after:', currentPage);
  }, [isAuthenticated, authUser]);

  const handleAuthSuccess = (newUser: User, isNewUserFlag: boolean) => {
    // Server-side onboarding status will be checked by OnboardingGuard
    if (!isNewUserFlag) {
      // Existing user - load profile if available
      const existingProfile = storage.getProfile();
      setProfile(existingProfile);
    }
  };

  const handleLogout = () => {
    console.log('[Index] LOGOUT: Starting handleLogout...');
    console.log('[Index] LOGOUT: Current authUser:', authUser);
    console.log('[Index] LOGOUT: Current isAuthenticated:', isAuthenticated);
    console.log('[Index] LOGOUT: Demo mode enabled:', demoModeEnabled);
    console.log('[Index] LOGOUT: Should bypass auth:', bypassAuth);
    console.log('[Index] LOGOUT: Effectively authenticated before logout:', effectivelyAuthenticated);
    console.log('[Index] LOGOUT: Window override before logout:', (window as any).__DEMO_MODE_OVERRIDE__);
    
    logout();
    setProfile(null);
    setCurrentPage('dashboard');
    
    console.log('[Index] LOGOUT: Logout completed, state cleared');
    console.log('[Index] LOGOUT: Window override after logout:', (window as any).__DEMO_MODE_OVERRIDE__);
    
    // DEBUG: Check demo mode state before page reload
    console.log('[Index] LOGOUT: Demo mode state before reload:', {
      demoModeEnabled: isDemoModeEnabled(),
      bypassAuth: shouldBypassAuth(),
      windowOverride: (window as any).__DEMO_MODE_OVERRIDE__
    });
    
    // Force a page reload to ensure clean state after logout
    setTimeout(() => {
      console.log('[Index] LOGOUT: Forcing page reload for clean state');
      window.location.reload();
    }, 100);
  };

  // Create a completely new function to force React to recognize the change
  const handleNavigate = (page: string) => {
    // FORCE FRESH FUNCTION - NO USECALLBACK TO AVOID STALE CLOSURES
    const debugTimestamp = Date.now();
    console.log('🔥🔥🔥 [Index] BRAND NEW handleNavigate FUNCTION CALL:', debugTimestamp);
    console.log('🚨🚨🚨 [Index] handleNavigate called - THIS SHOULD ALWAYS SHOW! 🚨🚨🚨');
    console.log('🔍 [Index] handleNavigate DETAILED DEBUG:', {
      page,
      currentPage,
      currentPageBefore: currentPage,
      windowWidth: window.innerWidth,
      isSidebarOpen,
      timestamp: new Date().toISOString(),
      callStack: new Error().stack
    });
    
    // Add alert for receipts specifically
    if (page === 'receipts') {
      alert('🧾 BRAND NEW FUNCTION - handleNavigate called for receipts! Current page: ' + currentPage);
      console.log('🧾🧾🧾 [Index] RECEIPTS NAVIGATION TRIGGERED! 🧾🧾🧾');
      console.log('🧾 [Index] About to set currentPage from:', currentPage, 'to:', page);
    }
    
    try {
      // Handle recipe detail navigation
      if (page.startsWith('recipe-')) {
        const recipeId = page.replace('recipe-', '');
        const recipes = storage.getRecipes();
        const recipe = recipes.find(r => r.id === recipeId);
        if (recipe) {
          console.log('📖 [Index] Navigating to recipe detail:', recipeId);
          setSelectedRecipe(recipe);
          setCurrentPage('recipe-detail');
        } else {
          console.warn('⚠️ [Index] Recipe not found:', recipeId);
        }
      } else {
        console.log('📄 [Index] Navigating to page:', page);
        console.log('📄 [Index] Current page before setState:', currentPage);
        
        // Refresh profile data when navigating back to dashboard
        if (page === 'dashboard') {
          const updatedProfile = storage.getProfile();
          setProfile(updatedProfile);
          console.log('🔄 [Index] Refreshed profile for dashboard');
        }
        
        // Special logging for receipts navigation
        if (page === 'receipts') {
          console.log('🧾 [Index] Navigating to receipts page - this should work!');
          console.log('🧾 [Index] BEFORE setCurrentPage - currentPage:', currentPage);
        }
        
        // Log before state change
        console.log('🔄 [Index] About to call setCurrentPage with:', page);
        // Use functional update to ensure we get the latest state
        setCurrentPage((prevPage) => {
          console.log('🔄 [Index] setCurrentPage functional update - prev:', prevPage, 'new:', page);
          return page;
        });
        console.log('🔄 [Index] setCurrentPage called with:', page);
        
        setSelectedRecipe(null);
        setEditingListId(null);
        
        // Special logging after receipts navigation
        if (page === 'receipts') {
          console.log('🧾 [Index] AFTER setCurrentPage - should be receipts now');
          // Force a re-render check with multiple timeouts
          setTimeout(() => {
            console.log('🧾 [Index] TIMEOUT CHECK 100ms - currentPage should be receipts but might still be stale:', currentPage);
          }, 100);
          setTimeout(() => {
            console.log('🧾 [Index] TIMEOUT CHECK 500ms - currentPage should definitely be receipts now:', currentPage);
          }, 500);
        }
        
        console.log('✅ [Index] Page state updated to:', page);
      }
      
      // Close sidebar on mobile after navigation
      if (window.innerWidth <= 1023) {
        console.log('📱 [Index] Closing sidebar on mobile/tablet');
        setIsSidebarOpen(false);
      }
      
      console.log('✅ [Index] Navigation completed successfully');
    } catch (error) {
      console.error('❌ [Index] Error during navigation:', error);
      alert('❌ Navigation error: ' + String(error));
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

  // Use OnboardingGuard to handle server-authoritative onboarding flow
  const renderCurrentPage = () => {
    console.log('🔍 [Index] renderCurrentPage called with currentPage:', currentPage);
    console.log('🔍 [Index] renderCurrentPage - auth state:', {
      effectivelyAuthenticated,
      effectiveUser: !!effectiveUser,
      isAuthenticated,
      authUser: !!authUser,
      demoModeEnabled,
      bypassAuth
    });
    
    switch (currentPage) {
      case 'dashboard':
        console.log('📊 [Index] Rendering Dashboard');
        return <Dashboard user={effectiveUser} profile={profile} onNavigate={handleNavigate} />;
      case 'receipt-scan':
        console.log('📷 [Index] Rendering ReceiptScan');
        return <ReceiptScan onBack={() => handleNavigate('dashboard')} />;
      case 'receipts':
        console.log('🧾 [Index] Rendering ReceiptHistory - THIS SHOULD SHOW THE RECEIPTS PAGE!');
        try {
          return <ReceiptHistory onBack={() => handleNavigate('dashboard')} />;
        } catch (error) {
          console.error('❌ [Index] Error rendering ReceiptHistory:', error);
          return (
            <div className="min-h-screen bg-gray-50 p-4">
              <div className="max-w-7xl mx-auto">
                <div className="bg-red-50 border border-red-200 rounded-lg p-6">
                  <h2 className="text-xl font-semibold text-red-800 mb-4">Error Loading Receipts</h2>
                  <p className="text-red-600 mb-4">There was an error loading the receipts page:</p>
                  <pre className="bg-red-100 p-4 rounded text-sm text-red-800 overflow-auto">
                    {String(error)}
                  </pre>
                  <button
                    onClick={() => handleNavigate('dashboard')}
                    className="mt-4 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
                  >
                    ← Back to Dashboard
                  </button>
                </div>
              </div>
            </div>
          );
        }
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
        console.log('🔍 [Index] Rendering FamilyMembers with:', {
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
    <OnboardingGuard>
      <div className="flex h-screen bg-background">
        {/* Sidebar */}
        <Sidebar
          isOpen={isSidebarOpen}
          onToggle={toggleSidebar}
          currentPage={currentPage}
          onNavigate={(page: string) => {
            console.log('🔥 [INLINE] Inline onNavigate called with page:', page);
            alert('🔥 INLINE FUNCTION CALLED with page: ' + page);
            handleNavigate(page);
          }}
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
    </OnboardingGuard>
  );
};

export default Index;