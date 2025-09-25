import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ArrowLeft, RefreshCw, Calendar, AlertTriangle, ChefHat, Clock, Users, Lightbulb, Loader2 } from 'lucide-react';
import { PantryItem, Recipe, LeftoverSuggestion, LeftoverSuggestionsResponse } from '@/types';
import { pantryApi, leftoverApi } from '@/services/api';
import { shouldUseMockData } from '@/lib/demoMode';
import { storage } from '@/lib/storage';
import { mockRecipes } from '@/lib/mockData';
import { showError } from '@/utils/toast';

interface LeftoverManagerProps {
  onBack: () => void;
}

// Mock leftover recipes based on common pantry items
const generateLeftoverRecipes = (pantryItems: PantryItem[]): Recipe[] => {
  const leftoverRecipes: Recipe[] = [
    {
      id: 'leftover-1',
      title: 'Pantry Pasta Surprise',
      description: 'Transform your leftover ingredients into a delicious pasta dish',
      ingredients: [
        { name: 'Pasta', quantity: 8, unit: 'oz' },
        { name: 'Any leftover vegetables', quantity: 1, unit: 'cup' },
        { name: 'Olive oil', quantity: 2, unit: 'tbsp' },
        { name: 'Garlic', quantity: 2, unit: 'cloves' },
        { name: 'Parmesan cheese', quantity: 0.25, unit: 'cup', optional: true }
      ],
      instructions: [
        'Cook pasta according to package directions',
        'Heat olive oil in a large pan',
        'Add garlic and cook for 1 minute',
        'Add leftover vegetables and heat through',
        'Toss with cooked pasta',
        'Top with cheese if available'
      ],
      prepTime: 5,
      cookTime: 15,
      servings: 4,
      difficulty: 'easy',
      tags: ['leftovers', 'quick', 'pantry-friendly'],
      source: 'ai-generated',
      createdAt: new Date().toISOString()
    },
    {
      id: 'leftover-2',
      title: 'Everything Fried Rice',
      description: 'Use up leftover rice and vegetables in this versatile dish',
      ingredients: [
        { name: 'Cooked rice', quantity: 2, unit: 'cups' },
        { name: 'Eggs', quantity: 2, unit: 'pieces' },
        { name: 'Mixed leftover vegetables', quantity: 1, unit: 'cup' },
        { name: 'Soy sauce', quantity: 2, unit: 'tbsp' },
        { name: 'Oil', quantity: 1, unit: 'tbsp' },
        { name: 'Green onions', quantity: 2, unit: 'pieces', optional: true }
      ],
      instructions: [
        'Heat oil in a large pan or wok',
        'Scramble eggs and set aside',
        'Add rice to the pan and break up clumps',
        'Add leftover vegetables and heat through',
        'Stir in soy sauce and scrambled eggs',
        'Garnish with green onions if available'
      ],
      prepTime: 5,
      cookTime: 10,
      servings: 3,
      difficulty: 'easy',
      tags: ['leftovers', 'rice', 'quick', 'asian-inspired'],
      source: 'ai-generated',
      createdAt: new Date().toISOString()
    },
    {
      id: 'leftover-3',
      title: 'Leftover Soup',
      description: 'Turn any leftover proteins and vegetables into a hearty soup',
      ingredients: [
        { name: 'Leftover meat or protein', quantity: 1, unit: 'cup' },
        { name: 'Leftover vegetables', quantity: 1.5, unit: 'cups' },
        { name: 'Broth or water', quantity: 4, unit: 'cups' },
        { name: 'Onion', quantity: 1, unit: 'piece' },
        { name: 'Garlic', quantity: 2, unit: 'cloves' },
        { name: 'Herbs and spices', quantity: 1, unit: 'tsp' }
      ],
      instructions: [
        'Sauté onion and garlic in a large pot',
        'Add broth and bring to a boil',
        'Add leftover vegetables and simmer for 10 minutes',
        'Add leftover protein and heat through',
        'Season with herbs and spices to taste',
        'Simmer for 5 more minutes and serve'
      ],
      prepTime: 10,
      cookTime: 25,
      servings: 4,
      difficulty: 'easy',
      tags: ['leftovers', 'soup', 'comfort-food', 'healthy'],
      source: 'ai-generated',
      createdAt: new Date().toISOString()
    }
  ];

  return leftoverRecipes;
};

export const LeftoverManager = ({ onBack }: LeftoverManagerProps) => {
  const [pantryItems, setPantryItems] = useState<PantryItem[]>([]);
  const [leftoverSuggestions, setLeftoverSuggestions] = useState<LeftoverSuggestion[]>([]);
  const [expiringItems, setExpiringItems] = useState<PantryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingSuggestions, setLoadingSuggestions] = useState(false);

  useEffect(() => {
    loadPantryData();
  }, []);

  const loadPantryData = async () => {
    try {
      setLoading(true);
      
      if (shouldUseMockData()) {
        console.log('🧪 [Demo Mode] Using mock pantry data');
        const items = storage.getPantryItems();
        setPantryItems(items);
        
        // Generate mock leftover recipes
        const recipes = generateLeftoverRecipes(items);
        const mockSuggestions: LeftoverSuggestion[] = recipes.map((recipe, index) => ({
          recipe,
          match_score: 85 - (index * 10),
          match_percentage: 80 - (index * 5),
          matched_ingredients: [],
          missing_ingredients: [],
          total_ingredients: recipe.ingredients.length,
          available_ingredients_count: Math.floor(recipe.ingredients.length * 0.8),
          missing_ingredients_count: Math.ceil(recipe.ingredients.length * 0.2),
          suggestion_reason: `Great match for your available ingredients`,
          priority_score: 90 - (index * 5),
          estimated_prep_time: recipe.prepTime,
          difficulty_bonus: 5,
          freshness_bonus: 10,
          expiration_urgency: index === 0 ? 15 : 5
        }));
        setLeftoverSuggestions(mockSuggestions);
        
        // Find items expiring soon (within 3 days)
        const threeDaysFromNow = new Date();
        threeDaysFromNow.setDate(threeDaysFromNow.getDate() + 3);
        
        const expiring = items.filter(item => {
          if (!item.expiration_date) return false;
          const expirationDate = new Date(item.expiration_date);
          return expirationDate <= threeDaysFromNow;
        });
        
        setExpiringItems(expiring);
      } else {
        // Load real pantry data
        const pantryResponse = await pantryApi.getItems();
        const items = pantryResponse.items || [];
        setPantryItems(items);
        
        // Get expiring items
        const expiringResponse = await pantryApi.getExpiringItems(3);
        setExpiringItems(expiringResponse.expiring_soon || []);
        
        // Load leftover suggestions
        await loadLeftoverSuggestions();
      }
    } catch (error) {
      console.warn('🧪 [Demo Mode] API failed, falling back to mock data:', error);
      const items = storage.getPantryItems();
      setPantryItems(items);
      
      const recipes = generateLeftoverRecipes(items);
      const mockSuggestions: LeftoverSuggestion[] = recipes.map((recipe, index) => ({
        recipe,
        match_score: 85 - (index * 10),
        match_percentage: 80 - (index * 5),
        matched_ingredients: [],
        missing_ingredients: [],
        total_ingredients: recipe.ingredients.length,
        available_ingredients_count: Math.floor(recipe.ingredients.length * 0.8),
        missing_ingredients_count: Math.ceil(recipe.ingredients.length * 0.2),
        suggestion_reason: `Great match for your available ingredients`,
        priority_score: 90 - (index * 5),
        estimated_prep_time: recipe.prepTime,
        difficulty_bonus: 5,
        freshness_bonus: 10,
        expiration_urgency: index === 0 ? 15 : 5
      }));
      setLeftoverSuggestions(mockSuggestions);
    } finally {
      setLoading(false);
    }
  };

  const loadLeftoverSuggestions = async () => {
    try {
      setLoadingSuggestions(true);
      
      const response: LeftoverSuggestionsResponse = await leftoverApi.getPantrySuggestions({
        max_suggestions: 10,
        min_match_percentage: 0.3,
        prioritize_expiring: true,
        include_substitutes: true
      });
      
      setLeftoverSuggestions(response.suggestions || []);
    } catch (error) {
      console.error('Failed to load leftover suggestions:', error);
      showError('Failed to load recipe suggestions. Please try again.');
    } finally {
      setLoadingSuggestions(false);
    }
  };

  const handleSaveRecipe = (recipe: Recipe) => {
    storage.addRecipe(recipe);
    // Show success message or navigate to recipe detail
  };

  const handleRefreshSuggestions = async () => {
    await loadLeftoverSuggestions();
  };

  const getItemsBySource = () => {
    // Note: source property might not exist in all pantry items
    const receiptItems = pantryItems.filter(item => (item as any).source === 'receipt');
    const manualItems = pantryItems.filter(item => (item as any).source === 'manual');
    return { receiptItems, manualItems };
  };

  const { receiptItems, manualItems } = getItemsBySource();

  const leftoverTips = [
    "Store leftovers in clear containers so you can see what you have",
    "Label containers with dates to track freshness",
    "Use the 'first in, first out' rule - use older items first",
    "Transform leftovers by changing the cooking method (roast → soup)",
    "Freeze portions you can't use within 3-4 days",
    "Mix different leftover proteins in stir-fries or pasta dishes"
  ];

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Loading your pantry and suggestions...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center py-4">
            <Button variant="ghost" onClick={onBack} className="mr-4">
              <ArrowLeft className="h-4 w-4" />
            </Button>
            <div>
              <h1 className="text-xl font-semibold">Leftover Manager</h1>
              <p className="text-sm text-gray-600">Transform your leftovers and reduce food waste</p>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Pantry Overview */}
          <div className="lg:col-span-1 space-y-6">
            {/* Expiring Items Alert */}
            {expiringItems.length > 0 && (
              <Card className="border-orange-200 bg-orange-50">
                <CardHeader>
                  <CardTitle className="flex items-center text-orange-800">
                    <AlertTriangle className="h-5 w-5 mr-2" />
                    Use Soon!
                  </CardTitle>
                  <CardDescription className="text-orange-700">
                    Items expiring within 3 days
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {expiringItems.map(item => (
                      <div key={item.id} className="flex justify-between items-center p-2 bg-white rounded border">
                        <span className="font-medium">{item.name}</span>
                        <div className="text-sm text-orange-600 flex items-center">
                          <Calendar className="h-3 w-3 mr-1" />
                          {new Date(item.expiration_date!).toLocaleDateString()}
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Pantry Summary */}
            <Card>
              <CardHeader>
                <CardTitle>Your Pantry</CardTitle>
                <CardDescription>
                  Current items available for leftover recipes
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4 text-center">
                    <div className="p-3 bg-blue-50 rounded-lg">
                      <div className="text-2xl font-bold text-blue-600">{receiptItems.length}</div>
                      <div className="text-sm text-blue-600">From Receipts</div>
                    </div>
                    <div className="p-3 bg-green-50 rounded-lg">
                      <div className="text-2xl font-bold text-green-600">{manualItems.length}</div>
                      <div className="text-sm text-green-600">Added Manually</div>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <h4 className="font-medium text-sm">Recent Items:</h4>
                    {pantryItems.slice(0, 5).map(item => (
                      <div key={item.id} className="flex justify-between items-center text-sm">
                        <span>{item.name}</span>
                        <Badge variant="outline" className="text-xs">
                          {item.quantity} {item.unit}
                        </Badge>
                      </div>
                    ))}
                    {pantryItems.length > 5 && (
                      <p className="text-xs text-gray-500">
                        +{pantryItems.length - 5} more items
                      </p>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Tips */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Lightbulb className="h-5 w-5 mr-2" />
                  Leftover Tips
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {leftoverTips.slice(0, 3).map((tip, index) => (
                    <div key={index} className="text-sm text-gray-700 flex items-start">
                      <span className="text-green-600 mr-2">•</span>
                      <span>{tip}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Leftover Recipes */}
          <div className="lg:col-span-2">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <div className="flex items-center">
                    <RefreshCw className="h-5 w-5 mr-2" />
                    Leftover Recipe Ideas
                  </div>
                  <Button 
                    variant="outline" 
                    size="sm" 
                    onClick={handleRefreshSuggestions}
                    disabled={loadingSuggestions}
                  >
                    {loadingSuggestions ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <RefreshCw className="h-4 w-4" />
                    )}
                  </Button>
                </CardTitle>
                <CardDescription>
                  AI-powered recipe suggestions based on your pantry items
                </CardDescription>
              </CardHeader>
              <CardContent>
                {leftoverSuggestions.length > 0 ? (
                  <div className="grid gap-6">
                    {leftoverSuggestions.map(suggestion => (
                      <Card key={suggestion.recipe.id} className="border-l-4 border-l-green-500">
                        <CardHeader>
                          <div className="flex justify-between items-start">
                            <div>
                              <CardTitle className="text-lg">{suggestion.recipe.title}</CardTitle>
                              <CardDescription className="mt-1">{suggestion.recipe.description}</CardDescription>
                              <div className="flex items-center gap-4 mt-2">
                                <Badge variant="secondary" className="text-xs">
                                  {Math.round(suggestion.match_percentage)}% match
                                </Badge>
                                <Badge variant="outline" className="text-xs">
                                  {suggestion.recipe.difficulty}
                                </Badge>
                                <span className="text-xs text-gray-500">
                                  Score: {Math.round(suggestion.match_score)}
                                </span>
                              </div>
                            </div>
                          </div>
                          
                          <div className="flex items-center gap-4 mt-3">
                            <div className="flex items-center text-sm text-gray-600">
                              <Clock className="h-4 w-4 mr-1" />
                              {suggestion.recipe.prepTime + suggestion.recipe.cookTime} min
                            </div>
                            <div className="flex items-center text-sm text-gray-600">
                              <Users className="h-4 w-4 mr-1" />
                              {suggestion.recipe.servings} servings
                            </div>
                            <div className="flex items-center text-sm text-green-600">
                              <span className="text-xs">
                                {suggestion.available_ingredients_count}/{suggestion.total_ingredients} ingredients available
                              </span>
                            </div>
                          </div>
                        </CardHeader>
                        
                        <CardContent>
                          <div className="space-y-4">
                            <div>
                              <h4 className="font-medium mb-2">Suggestion Reason:</h4>
                              <p className="text-sm text-gray-700 bg-green-50 p-2 rounded">
                                {suggestion.suggestion_reason}
                              </p>
                            </div>

                            <div>
                              <h4 className="font-medium mb-2">Key Ingredients:</h4>
                              <div className="flex flex-wrap gap-2">
                                {suggestion.recipe.ingredients.slice(0, 4).map((ingredient, index) => (
                                  <Badge key={index} variant="outline" className="text-xs">
                                    {ingredient.name}
                                  </Badge>
                                ))}
                                {suggestion.recipe.ingredients.length > 4 && (
                                  <Badge variant="outline" className="text-xs">
                                    +{suggestion.recipe.ingredients.length - 4} more
                                  </Badge>
                                )}
                              </div>
                            </div>

                            <div>
                              <h4 className="font-medium mb-2">Quick Steps:</h4>
                              <ol className="text-sm text-gray-700 space-y-1">
                                {suggestion.recipe.instructions.slice(0, 3).map((instruction, index) => (
                                  <li key={index} className="flex">
                                    <span className="text-green-600 mr-2 font-medium">{index + 1}.</span>
                                    <span>{instruction}</span>
                                  </li>
                                ))}
                                {suggestion.recipe.instructions.length > 3 && (
                                  <li className="text-gray-500 text-xs">
                                    +{suggestion.recipe.instructions.length - 3} more steps
                                  </li>
                                )}
                              </ol>
                            </div>

                            <div className="flex gap-2 pt-2">
                              <Button 
                                size="sm" 
                                onClick={() => handleSaveRecipe(suggestion.recipe)}
                                className="flex-1"
                              >
                                <ChefHat className="h-4 w-4 mr-2" />
                                Save Recipe
                              </Button>
                              <Button variant="outline" size="sm" className="flex-1">
                                View Full Recipe
                              </Button>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <RefreshCw className="h-12 w-12 text-gray-300 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-gray-900 mb-2">No leftover recipes available</h3>
                    <p className="text-gray-600 mb-4">
                      Add some items to your pantry to get personalized leftover recipe suggestions!
                    </p>
                    <Button onClick={onBack}>
                      Back to Dashboard
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Additional Tips */}
            <Card className="mt-6">
              <CardHeader>
                <CardTitle>More Leftover Tips</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {leftoverTips.slice(3).map((tip, index) => (
                    <div key={index + 3} className="text-sm text-gray-700 flex items-start p-3 bg-gray-50 rounded-lg">
                      <span className="text-green-600 mr-2">💡</span>
                      <span>{tip}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};