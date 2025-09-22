import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ArrowLeft, Calendar, ChefHat, ShoppingCart, Loader2, DollarSign, Clock, Users } from 'lucide-react';
import { User, UserProfile, PantryItem, Recipe, MealPlan, PlannedMeal, ShoppingListItem } from '@/types';
import { storage } from '@/lib/storage';
import { generateMealPlan } from '@/lib/mockData';
import { showSuccess } from '@/utils/toast';

interface MealPlannerProps {
  user: User;
  profile: UserProfile;
  onBack: () => void;
}

export const MealPlanner = ({ user, profile, onBack }: MealPlannerProps) => {
  const [isGenerating, setIsGenerating] = useState(false);
  const [currentMealPlan, setCurrentMealPlan] = useState<MealPlan | null>(null);
  const [pantryItems, setPantryItems] = useState<PantryItem[]>([]);
  const [step, setStep] = useState<'overview' | 'generating' | 'review'>('overview');

  useEffect(() => {
    setPantryItems(storage.getPantryItems());
    
    // Load existing meal plan if available
    const mealPlans = storage.getMealPlans();
    if (mealPlans.length > 0) {
      setCurrentMealPlan(mealPlans[mealPlans.length - 1]);
    }
  }, []);

  const handleGenerateMealPlan = async () => {
    setStep('generating');
    setIsGenerating(true);

    try {
      const { recipes, shoppingList } = await generateMealPlan(pantryItems, profile);
      
      // Create planned meals for the week
      const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
      const mealTypes = ['breakfast', 'lunch', 'dinner'] as const;
      
      const plannedMeals: PlannedMeal[] = [];
      let recipeIndex = 0;

      days.forEach(day => {
        mealTypes.forEach(mealType => {
          if (recipeIndex < recipes.length) {
            plannedMeals.push({
              id: `${day}-${mealType}`,
              day,
              mealType,
              recipe: recipes[recipeIndex % recipes.length],
              servings: 4
            });
            recipeIndex++;
          }
        });
      });

      const newMealPlan: MealPlan = {
        id: Date.now().toString(),
        userId: user.id,
        weekStarting: new Date().toISOString(),
        meals: plannedMeals,
        shoppingList,
        totalEstimatedCost: shoppingList.reduce((sum, item) => sum + item.estimatedPrice, 0),
        createdAt: new Date().toISOString()
      };

      storage.addMealPlan(newMealPlan);
      setCurrentMealPlan(newMealPlan);
      setStep('review');
      showSuccess('Your weekly meal plan is ready!');
    } catch (error) {
      console.error('Error generating meal plan:', error);
    } finally {
      setIsGenerating(false);
    }
  };

  const renderOverview = () => (
    <div className="space-y-6">
      <div className="text-center">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">AI Meal Planner</h2>
        <p className="text-gray-600">
          Generate a personalized weekly meal plan based on your pantry, preferences, and budget.
        </p>
      </div>

      {/* Current Status */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center">
              <div className="p-2 bg-green-100 rounded-lg">
                <ShoppingCart className="h-5 w-5 text-green-600" />
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-600">Pantry Items</p>
                <p className="text-lg font-bold text-gray-900">{pantryItems.length}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center">
              <div className="p-2 bg-blue-100 rounded-lg">
                <DollarSign className="h-5 w-5 text-blue-600" />
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-600">Weekly Budget</p>
                <p className="text-lg font-bold text-gray-900">${profile.weeklyBudget}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center">
              <div className="p-2 bg-purple-100 rounded-lg">
                <Users className="h-5 w-5 text-purple-600" />
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-600">Family Size</p>
                <p className="text-lg font-bold text-gray-900">{profile.familyMembers.length + 1}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Preferences Summary */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Your Preferences</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <h4 className="font-medium mb-2">Dietary Restrictions</h4>
            <div className="flex flex-wrap gap-2">
              {profile.dietaryRestrictions.length > 0 ? (
                profile.dietaryRestrictions.map(restriction => (
                  <Badge key={restriction} variant="outline">{restriction}</Badge>
                ))
              ) : (
                <span className="text-gray-500 text-sm">None specified</span>
              )}
            </div>
          </div>

          <div>
            <h4 className="font-medium mb-2">Taste Preferences</h4>
            <div className="flex flex-wrap gap-2">
              {profile.tastePreferences.length > 0 ? (
                profile.tastePreferences.map(preference => (
                  <Badge key={preference} variant="secondary">{preference}</Badge>
                ))
              ) : (
                <span className="text-gray-500 text-sm">None specified</span>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Current Meal Plan */}
      {currentMealPlan && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Current Meal Plan</CardTitle>
            <CardDescription>
              Week of {new Date(currentMealPlan.weekStarting).toLocaleDateString()}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex justify-between items-center">
              <div>
                <p className="text-sm text-gray-600">{currentMealPlan.meals.length} meals planned</p>
                <p className="text-lg font-semibold text-green-600">
                  Estimated cost: ${currentMealPlan.totalEstimatedCost.toFixed(2)}
                </p>
              </div>
              <Button variant="outline" onClick={() => setStep('review')}>
                View Plan
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      <Button onClick={handleGenerateMealPlan} className="w-full" size="lg">
        <Calendar className="h-5 w-5 mr-2" />
        Generate New Meal Plan
      </Button>
    </div>
  );

  const renderGenerating = () => (
    <div className="text-center space-y-6">
      <div className="mx-auto w-24 h-24 bg-purple-100 rounded-full flex items-center justify-center">
        <Loader2 className="h-12 w-12 text-purple-600 animate-spin" />
      </div>
      
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Creating Your Meal Plan</h2>
        <p className="text-gray-600">
          Our AI is analyzing your pantry, preferences, and budget to create the perfect weekly meal plan...
        </p>
      </div>

      <div className="space-y-2">
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div className="bg-purple-600 h-2 rounded-full animate-pulse" style={{ width: '70%' }} />
        </div>
        <p className="text-sm text-gray-500">This may take 20-40 seconds</p>
      </div>
    </div>
  );

  const renderReview = () => {
    if (!currentMealPlan) return null;

    const groupedMeals = currentMealPlan.meals.reduce((acc, meal) => {
      if (!acc[meal.day]) acc[meal.day] = [];
      acc[meal.day].push(meal);
      return acc;
    }, {} as Record<string, PlannedMeal[]>);

    return (
      <div className="space-y-6">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Your Weekly Meal Plan</h2>
          <p className="text-gray-600">
            Week of {new Date(currentMealPlan.weekStarting).toLocaleDateString()}
          </p>
          <div className="mt-4">
            <Badge variant="outline" className="text-lg px-4 py-2">
              Total Cost: ${currentMealPlan.totalEstimatedCost.toFixed(2)}
            </Badge>
          </div>
        </div>

        {/* Meal Plan Grid */}
        <div className="grid gap-4">
          {Object.entries(groupedMeals).map(([day, meals]) => (
            <Card key={day}>
              <CardHeader className="pb-3">
                <CardTitle className="text-lg">{day}</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid gap-3">
                  {meals.map(meal => (
                    <div key={meal.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <Badge variant="outline" className="text-xs capitalize">
                            {meal.mealType}
                          </Badge>
                          <h4 className="font-medium">{meal.recipe.title}</h4>
                        </div>
                        <div className="flex items-center gap-4 text-sm text-gray-600">
                          <div className="flex items-center">
                            <Clock className="h-3 w-3 mr-1" />
                            {meal.recipe.prepTime + meal.recipe.cookTime}min
                          </div>
                          <div className="flex items-center">
                            <Users className="h-3 w-3 mr-1" />
                            {meal.servings} servings
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Shopping List */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <ShoppingCart className="h-5 w-5 mr-2" />
              Shopping List
            </CardTitle>
            <CardDescription>
              Organized by store for optimal shopping
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {Object.entries(
                currentMealPlan.shoppingList.reduce((acc, item) => {
                  if (!acc[item.store]) acc[item.store] = [];
                  acc[item.store].push(item);
                  return acc;
                }, {} as Record<string, ShoppingListItem[]>)
              ).map(([store, items]) => (
                <div key={store}>
                  <h4 className="font-medium mb-2">{store}</h4>
                  <div className="grid gap-2">
                    {items.map(item => (
                      <div key={item.id} className="flex justify-between items-center p-2 border rounded">
                        <div>
                          <span className="font-medium">{item.name}</span>
                          <span className="text-gray-500 ml-2">
                            {item.quantity} {item.unit}
                          </span>
                        </div>
                        <span className="font-medium">${item.estimatedPrice.toFixed(2)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <div className="flex gap-3">
          <Button variant="outline" onClick={() => setStep('overview')} className="flex-1">
            Generate New Plan
          </Button>
          <Button onClick={onBack} className="flex-1">
            Back to Dashboard
          </Button>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center py-4">
            <Button variant="ghost" onClick={onBack} className="mr-4">
              <ArrowLeft className="h-4 w-4" />
            </Button>
            <div>
              <h1 className="text-xl font-semibold">Meal Planner</h1>
              <p className="text-sm text-gray-600">AI-powered weekly meal planning</p>
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Card>
          <CardContent className="p-8">
            {step === 'overview' && renderOverview()}
            {step === 'generating' && renderGenerating()}
            {step === 'review' && renderReview()}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};