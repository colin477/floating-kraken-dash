import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import { User, UserProfile, PantryItem, Recipe, MealPlan } from '@/types';
import { storage } from '@/lib/storage';
import { profileApi } from '@/services/api';
import { Camera, ChefHat, ShoppingCart, Users, Calendar, DollarSign, Clock, ArrowRight, Utensils, ListChecks, RefreshCw, Plus, Link, Edit, List, FolderPlus } from 'lucide-react';
import { showSuccess } from '@/utils/toast';

interface DashboardProps {
  user: User;
  profile: UserProfile | null;
  onNavigate: (page: string) => void;
}

interface DashboardStats {
  pantry_items_count: number;
  saved_recipes_count: number;
}

export const Dashboard = ({ user, profile, onNavigate }: DashboardProps) => {
  const [pantryItems, setPantryItems] = useState<PantryItem[]>([]);
  const [recentRecipes, setRecentRecipes] = useState<Recipe[]>([]);
  const [currentMealPlan, setCurrentMealPlan] = useState<MealPlan | null>(null);
  const [stats, setStats] = useState<DashboardStats | null>(null);

  useEffect(() => {
    const fetchDashboardStats = async () => {
      try {
        const data = await profileApi.getDashboardStats();
        setStats(data);
      } catch (error) {
        console.error('Failed to fetch dashboard stats:', error);
      }
    };

    fetchDashboardStats();
    setPantryItems(storage.getPantryItems());
    setRecentRecipes(storage.getRecipes().slice(-3));
    const mealPlans = storage.getMealPlans();
    if (mealPlans.length > 0) {
      setCurrentMealPlan(mealPlans[mealPlans.length - 1]);
    }
  }, []);

  const trialDaysLeft = user.trialEndsAt 
    ? Math.ceil((new Date(user.trialEndsAt).getTime() - Date.now()) / (1000 * 60 * 60 * 24))
    : 0;

  const handleQuickAction = (action: string) => {
    switch (action) {
      case 'what-can-i-make':
        // Navigate to recipes page to see what can be made with current ingredients
        onNavigate('recipes');
        break;
      case 'weekly-meal-plan':
        onNavigate('meal-planner');
        break;
      case 'my-shopping-lists':
        onNavigate('shopping-lists');
        break;
      case 'create-shopping-list':
        onNavigate('create-shopping-list');
        break;
      case 'use-leftovers':
        // Navigate to dedicated leftover manager
        onNavigate('leftovers');
        break;
      default:
        console.log('Unknown action:', action);
    }
  };

  const handleAddRecipeOption = (option: string) => {
    switch (option) {
      case 'photo':
        onNavigate('meal-photo');
        break;
      case 'receipt':
        onNavigate('receipt-scan');
        break;
      case 'link':
        onNavigate('add-from-link');
        break;
      case 'create':
        onNavigate('create-recipe');
        break;
      default:
        break;
    }
  };

  const handleShoppingListOption = (option: string) => {
    switch (option) {
      case 'my-lists':
        onNavigate('shopping-lists');
        break;
      case 'create-new':
        onNavigate('create-shopping-list');
        break;
      default:
        break;
    }
  };

  // Show loading state if profile is not yet available
  if (!profile) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading your profile...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <div className="bg-card shadow-sm border-b border-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div>
              <h1 className="text-3xl font-bold text-primary">EZ Eatin'</h1>
              <p className="text-muted-foreground mt-1">Welcome back, {user.name}!</p>
            </div>
            <div className="flex items-center gap-4">
              {user.subscription === 'free' && (
                <Badge variant="outline" className="text-destructive border-destructive">
                  {trialDaysLeft} days left in trial
                </Badge>
              )}
              <Button variant="outline" onClick={() => onNavigate('profile')}>
                Profile
              </Button>
              <Button variant="outline" onClick={() => onNavigate('community')}>
                Community
              </Button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Quick Action Buttons */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-foreground mb-4">Quick Actions</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
            {/* Add Recipe Dropdown */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Card className="cursor-pointer hover:shadow-lg transition-all duration-200 hover:scale-[1.02] border-2 border-dashed border-primary/30 hover:border-primary/60">
                  <CardContent className="p-6">
                    <div className="flex items-center">
                      <div className="p-2 bg-primary/10 rounded-lg">
                        <Plus className="h-5 w-5 text-primary" />
                      </div>
                      <div className="ml-3">
                        <p className="text-sm font-medium text-foreground">Add Recipe</p>
                        <p className="text-xs text-muted-foreground">Multiple ways</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="start" className="w-56">
                <DropdownMenuItem onClick={() => handleAddRecipeOption('photo')}>
                  <Camera className="h-4 w-4 mr-2" />
                  Add from photo
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => handleAddRecipeOption('receipt')}>
                  <ShoppingCart className="h-4 w-4 mr-2" />
                  Scan receipt
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => handleAddRecipeOption('link')}>
                  <Link className="h-4 w-4 mr-2" />
                  Add from link
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => handleAddRecipeOption('create')}>
                  <Edit className="h-4 w-4 mr-2" />
                  Create my own
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>

            <Card 
              className="cursor-pointer hover:shadow-lg transition-all duration-200 hover:scale-[1.02] border-2 border-dashed border-green-500/30 hover:border-green-500/60"
              onClick={() => handleQuickAction('what-can-i-make')}
            >
              <CardContent className="p-6">
                <div className="flex items-center">
                  <div className="p-2 bg-green-100 rounded-lg">
                    <Utensils className="h-5 w-5 text-green-600" />
                  </div>
                  <div className="ml-3">
                    <p className="text-sm font-medium text-foreground">What Can I Make?</p>
                    <p className="text-xs text-muted-foreground">From pantry</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card 
              className="cursor-pointer hover:shadow-lg transition-all duration-200 hover:scale-[1.02] border-2 border-dashed border-blue-500/30 hover:border-blue-500/60"
              onClick={() => handleQuickAction('weekly-meal-plan')}
            >
              <CardContent className="p-6">
                <div className="flex items-center">
                  <div className="p-2 bg-blue-100 rounded-lg">
                    <Calendar className="h-5 w-5 text-blue-600" />
                  </div>
                  <div className="ml-3">
                    <p className="text-sm font-medium text-foreground">Weekly Meal Plan</p>
                    <p className="text-xs text-muted-foreground">Plan your week</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* My Shopping Lists Dropdown */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Card className="cursor-pointer hover:shadow-lg transition-all duration-200 hover:scale-[1.02] border-2 border-dashed border-purple-500/30 hover:border-purple-500/60">
                  <CardContent className="p-6">
                    <div className="flex items-center">
                      <div className="p-2 bg-purple-100 rounded-lg">
                        <ListChecks className="h-5 w-5 text-purple-600" />
                      </div>
                      <div className="ml-3">
                        <p className="text-sm font-medium text-foreground">My Shopping Lists</p>
                        <p className="text-xs text-muted-foreground">Manage lists</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="start" className="w-56">
                <DropdownMenuItem onClick={() => handleShoppingListOption('my-lists')}>
                  <List className="h-4 w-4 mr-2" />
                  My Lists
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => handleShoppingListOption('create-new')}>
                  <FolderPlus className="h-4 w-4 mr-2" />
                  Create New List
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>

            <Card 
              className="cursor-pointer hover:shadow-lg transition-all duration-200 hover:scale-[1.02] border-2 border-dashed border-orange-500/30 hover:border-orange-500/60"
              onClick={() => handleQuickAction('use-leftovers')}
            >
              <CardContent className="p-6">
                <div className="flex items-center">
                  <div className="p-2 bg-orange-100 rounded-lg">
                    <RefreshCw className="h-5 w-5 text-orange-600" />
                  </div>
                  <div className="ml-3">
                    <p className="text-sm font-medium text-foreground">Use Leftovers</p>
                    <p className="text-xs text-muted-foreground">Transform leftovers</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <Card className="shadow-sm cursor-pointer hover:shadow-md transition-shadow" onClick={() => onNavigate('pantry')}>
            <CardContent className="p-6">
              <div className="flex items-center">
                <div className="p-3 bg-primary/10 rounded-xl">
                  <ShoppingCart className="h-6 w-6 text-primary" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-muted-foreground">Pantry Items</p>
                  <p className="text-2xl font-bold text-foreground">{stats?.pantry_items_count ?? pantryItems.length}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="shadow-sm cursor-pointer hover:shadow-md transition-shadow" onClick={() => onNavigate('recipes')}>
            <CardContent className="p-6">
              <div className="flex items-center">
                <div className="p-3 bg-secondary/20 rounded-xl">
                  <ChefHat className="h-6 w-6 text-secondary-foreground" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-muted-foreground">Saved Recipes</p>
                  <p className="text-2xl font-bold text-foreground">{stats?.saved_recipes_count ?? recentRecipes.length}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="shadow-sm">
            <CardContent className="p-6">
              <div className="flex items-center">
                <div className="p-3 bg-accent/20 rounded-xl">
                  <DollarSign className="h-6 w-6 text-accent-foreground" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-muted-foreground">Weekly Budget</p>
                  <p className="text-2xl font-bold text-foreground">${profile.weeklyBudget || 100}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="shadow-sm cursor-pointer hover:shadow-md transition-shadow" onClick={() => onNavigate('family-members')}>
            <CardContent className="p-6">
              <div className="flex items-center">
                <div className="p-3 bg-destructive/10 rounded-xl">
                  <Users className="h-6 w-6 text-destructive" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-muted-foreground">Family Members</p>
                  <p className="text-2xl font-bold text-foreground">{(profile.familyMembers?.length || 0) + 1}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Current Meal Plan */}
        <div className="mb-8">
          <Card className="shadow-sm">
            <CardHeader>
              <CardTitle className="flex items-center">
                <Calendar className="h-5 w-5 mr-2 text-primary" />
                Current Meal Plan
              </CardTitle>
            </CardHeader>
            <CardContent>
              {currentMealPlan ? (
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-muted-foreground">Week of {new Date(currentMealPlan.weekStarting).toLocaleDateString()}</span>
                    <Badge variant="outline">{currentMealPlan.meals.length} meals planned</Badge>
                  </div>
                  <div className="text-lg font-semibold text-primary">
                    Estimated cost: ${currentMealPlan.totalEstimatedCost.toFixed(2)}
                  </div>
                  <Button variant="outline" className="w-full" onClick={() => onNavigate('meal-planner')}>
                    View Full Plan
                  </Button>
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  <Calendar className="h-12 w-12 mx-auto mb-4 text-muted-foreground/50" />
                  <p>No meal plan yet. Generate your first weekly plan!</p>
                  <Button className="mt-4" onClick={() => onNavigate('meal-planner')}>
                    Create Meal Plan
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Generate Meal Plan Action */}
        <div className="mb-8">
          <Card className="cursor-pointer hover:shadow-lg transition-all duration-200 hover:scale-[1.02]" onClick={() => onNavigate('meal-planner')}>
            <CardHeader>
              <div className="flex items-center justify-center">
                <div className="p-3 bg-accent/20 rounded-xl">
                  <Calendar className="h-8 w-8 text-accent-foreground" />
                </div>
                <div className="ml-4 text-center">
                  <CardTitle className="text-lg">Generate New Meal Plan</CardTitle>
                  <CardDescription>AI-powered weekly planning</CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent className="text-center">
              <p className="text-sm text-muted-foreground">
                Create a personalized weekly meal plan based on your pantry, preferences, and budget.
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Recent Recipes */}
        <Card className="shadow-sm">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center">
                <ChefHat className="h-5 w-5 mr-2 text-primary" />
                Recent Recipes
              </CardTitle>
              {recentRecipes.length > 0 && (
                <Button variant="ghost" size="sm" onClick={() => onNavigate('recipes')}>
                  View All
                  <ArrowRight className="h-4 w-4 ml-1" />
                </Button>
              )}
            </div>
          </CardHeader>
          <CardContent>
            {recentRecipes.length > 0 ? (
              <div className="space-y-3">
                {recentRecipes.map(recipe => (
                  <div 
                    key={recipe.id} 
                    className="flex items-center justify-between p-4 border border-border rounded-lg bg-muted/30 cursor-pointer hover:bg-muted/50 transition-colors"
                    onClick={() => onNavigate(`recipe-${recipe.id}`)}
                  >
                    <div>
                      <h4 className="font-medium text-foreground">{recipe.title}</h4>
                      <div className="flex items-center text-sm text-muted-foreground mt-1">
                        <Clock className="h-4 w-4 mr-1" />
                        {recipe.prepTime + recipe.cookTime} min
                        <Badge variant="outline" className="ml-2 text-xs">
                          {recipe.difficulty}
                        </Badge>
                      </div>
                    </div>
                    <ArrowRight className="h-4 w-4 text-muted-foreground" />
                  </div>
                ))}
                <Button variant="outline" className="w-full mt-4" onClick={() => onNavigate('recipes')}>
                  View All Recipes
                </Button>
              </div>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                <ChefHat className="h-12 w-12 mx-auto mb-4 text-muted-foreground/50" />
                <p className="mb-4">No recipes yet. Start by scanning a receipt or meal photo!</p>
              </div>
            )}

            {/* Centered Action Buttons */}
            <div className="mt-6 pt-6 border-t border-border">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <Card className="cursor-pointer hover:shadow-md transition-all duration-200 hover:scale-[1.02] border-2 border-dashed border-primary/30 hover:border-primary/60" onClick={() => onNavigate('receipt-scan')}>
                  <CardContent className="p-4 text-center">
                    <div className="p-3 bg-primary/10 rounded-xl mx-auto w-fit mb-3">
                      <ShoppingCart className="h-6 w-6 text-primary" />
                    </div>
                    <h3 className="font-medium text-sm mb-1">Scan Receipt</h3>
                    <p className="text-xs text-muted-foreground">Add groceries to pantry</p>
                  </CardContent>
                </Card>

                <Card className="cursor-pointer hover:shadow-md transition-all duration-200 hover:scale-[1.02] border-2 border-dashed border-secondary/30 hover:border-secondary/60" onClick={() => onNavigate('meal-photo')}>
                  <CardContent className="p-4 text-center">
                    <div className="p-3 bg-secondary/20 rounded-xl mx-auto w-fit mb-3">
                      <Camera className="h-6 w-6 text-secondary-foreground" />
                    </div>
                    <h3 className="font-medium text-sm mb-1">Analyze Photo</h3>
                    <p className="text-xs text-muted-foreground">Get recipes from meals</p>
                  </CardContent>
                </Card>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};