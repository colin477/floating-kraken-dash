import { useState, useEffect } from 'react';
import { User, UserProfile, Recipe } from '@/types';
import { storage } from '@/lib/storage';
import { AuthForm } from '@/components/AuthForm';
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

const Index = () => {
  const [user, setUser] = useState<User | null>(null);
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [setupLevel, setSetupLevel] = useState<'basic' | 'medium' | 'full' | null>(null);
  const [currentPage, setCurrentPage] = useState<string>('dashboard');
  const [selectedRecipe, setSelectedRecipe] = useState<Recipe | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isNewUser, setIsNewUser] = useState(false);
  const [editingListId, setEditingListId] = useState<string | null>(null);

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
    
    // Check for existing user session
    const savedUser = storage.getUser();
    const savedProfile = storage.getProfile();
    
    if (savedUser) {
      setUser(savedUser);
      setProfile(savedProfile);
      setIsNewUser(false); // Existing user
    }
    
    setIsLoading(false);
  }, []);

  const handleAuthSuccess = (newUser: User, isNewUserFlag: boolean) => {
    setUser(newUser);
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
    if (user) {
      const subscriptionMapping = {
        'basic': 'free' as const,
        'medium': 'basic' as const, 
        'full': 'premium' as const
      };
      
      const updatedUser = {
        ...user,
        subscription: subscriptionMapping[selectedLevel],
        // Remove trial end date for premium users
        ...(selectedLevel === 'full' ? { trialEndsAt: undefined } : {})
      };
      
      storage.setUser(updatedUser);
      setUser(updatedUser);
    }
    
    setSetupLevel(null); // Clear setup level after completion
    setIsNewUser(false); // No longer a new user
  };

  const handleLogout = () => {
    storage.clearUser();
    setUser(null);
    setProfile(null);
    setSetupLevel(null);
    setCurrentPage('dashboard');
    setIsNewUser(false);
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
      setCurrentPage(page);
      setSelectedRecipe(null);
      setEditingListId(null);
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

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading EZ Eatin'...</p>
        </div>
      </div>
    );
  }

  // Show auth form if no user
  if (!user) {
    return <AuthForm onAuthSuccess={handleAuthSuccess} />;
  }

  // For existing users (login), skip plan selection and go to dashboard
  if (!isNewUser && user) {
    // Render current page for existing users
    const renderCurrentPage = () => {
      switch (currentPage) {
        case 'dashboard':
          return <Dashboard user={user} profile={profile} onNavigate={handleNavigate} />;
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
            <MealPlanner user={user} profile={profile} onBack={() => handleNavigate('dashboard')} />
          ) : (
            <Dashboard user={user} profile={profile} onNavigate={handleNavigate} />
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
          return <Community user={user} onBack={() => handleNavigate('dashboard')} />;
        case 'profile':
          return profile ? (
            <Profile user={user} profile={profile} onBack={() => handleNavigate('dashboard')} onLogout={handleLogout} />
          ) : (
            <Dashboard user={user} profile={profile} onNavigate={handleNavigate} />
          );
        case 'family-members':
          return profile ? (
            <FamilyMembers user={user} profile={profile} onBack={() => handleNavigate('dashboard')} />
          ) : (
            <Dashboard user={user} profile={profile} onNavigate={handleNavigate} />
          );
        case 'recipes':
          return <Recipes user={user} onBack={() => handleNavigate('dashboard')} onRecipeSelect={handleRecipeSelect} onNavigate={handleNavigate} />;
        case 'recipe-detail':
          return selectedRecipe ? (
            <RecipeDetail recipe={selectedRecipe} onBack={() => handleNavigate('recipes')} />
          ) : (
            <Dashboard user={user} profile={profile} onNavigate={handleNavigate} />
          );
        case 'pantry':
          return <Pantry onBack={() => handleNavigate('dashboard')} />;
        default:
          return <Dashboard user={user} profile={profile} onNavigate={handleNavigate} />;
      }
    };

    return (
      <div>
        {renderCurrentPage()}
        
        {/* Development Reset Button - only show in development */}
        {process.env.NODE_ENV === 'development' && (
          <div className="fixed bottom-4 right-4">
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
        userId={user.id} 
        level={setupLevel}
        onComplete={() => handleProfileComplete(setupLevel)} 
      />
    );
  }

  // Fallback to dashboard
  return <Dashboard user={user} profile={profile} onNavigate={handleNavigate} />;
};

export default Index;