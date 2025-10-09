import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { Checkbox } from '@/components/ui/checkbox';
import {
  ChefHat,
  Sparkles,
  Plus,
  X,
  Clock,
  Users,
  Utensils,
  AlertCircle,
  CheckCircle,
  Loader2,
  Lightbulb,
  Star,
  TrendingUp
} from 'lucide-react';
import { aiRecipeApi } from '@/services/api';
import { showSuccess, showError } from '@/utils/toast';

interface AIRecipeGeneratorProps {
  initialIngredients?: string[];
  onRecipeGenerated?: (recipe: any) => void;
  className?: string;
}

export const AIRecipeGenerator: React.FC<AIRecipeGeneratorProps> = ({
  initialIngredients = [],
  onRecipeGenerated,
  className = ''
}) => {
  const [ingredients, setIngredients] = useState<string[]>(initialIngredients);
  const [newIngredient, setNewIngredient] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedRecipe, setGeneratedRecipe] = useState<any>(null);
  const [serviceStatus, setServiceStatus] = useState<any>(null);
  
  // Generation preferences
  const [cuisinePreference, setCuisinePreference] = useState('');
  const [mealType, setMealType] = useState('');
  const [difficultyPreference, setDifficultyPreference] = useState('');
  const [servings, setServings] = useState(4);
  const [maxPrepTime, setMaxPrepTime] = useState<number | undefined>();
  const [maxCookTime, setMaxCookTime] = useState<number | undefined>();
  const [dietaryRestrictions, setDietaryRestrictions] = useState<string[]>([]);
  const [excludeIngredients, setExcludeIngredients] = useState<string[]>([]);
  const [includeNutrition, setIncludeNutrition] = useState(true);

  // UI state
  const [showAdvancedOptions, setShowAdvancedOptions] = useState(false);
  const [generationHistory, setGenerationHistory] = useState<any[]>([]);

  useEffect(() => {
    fetchServiceStatus();
  }, []);

  const fetchServiceStatus = async () => {
    try {
      const status = await aiRecipeApi.getServiceStatus();
      setServiceStatus(status);
    } catch (error) {
      console.error('Failed to fetch AI service status:', error);
    }
  };

  const addIngredient = () => {
    if (newIngredient.trim() && !ingredients.includes(newIngredient.trim())) {
      setIngredients([...ingredients, newIngredient.trim()]);
      setNewIngredient('');
    }
  };

  const removeIngredient = (ingredient: string) => {
    setIngredients(ingredients.filter(ing => ing !== ingredient));
  };

  const addExcludeIngredient = (ingredient: string) => {
    if (ingredient.trim() && !excludeIngredients.includes(ingredient.trim())) {
      setExcludeIngredients([...excludeIngredients, ingredient.trim()]);
    }
  };

  const removeExcludeIngredient = (ingredient: string) => {
    setExcludeIngredients(excludeIngredients.filter(ing => ing !== ingredient));
  };

  const toggleDietaryRestriction = (restriction: string) => {
    if (dietaryRestrictions.includes(restriction)) {
      setDietaryRestrictions(dietaryRestrictions.filter(r => r !== restriction));
    } else {
      setDietaryRestrictions([...dietaryRestrictions, restriction]);
    }
  };

  const generateRecipe = async () => {
    if (ingredients.length === 0) {
      showError('Please add at least one ingredient');
      return;
    }

    setIsGenerating(true);
    try {
      const requestData = {
        ingredients,
        cuisine_preference: cuisinePreference || undefined,
        meal_type: mealType || undefined,
        dietary_restrictions: dietaryRestrictions.length > 0 ? dietaryRestrictions : undefined,
        difficulty_preference: difficultyPreference || undefined,
        servings,
        max_prep_time: maxPrepTime,
        max_cook_time: maxCookTime,
        exclude_ingredients: excludeIngredients.length > 0 ? excludeIngredients : undefined,
        include_nutrition: includeNutrition
      };

      const response = await aiRecipeApi.generateFromIngredients(requestData);
      
      if (response.success && response.recipe) {
        setGeneratedRecipe(response);
        setGenerationHistory([response, ...generationHistory.slice(0, 4)]); // Keep last 5
        onRecipeGenerated?.(response.recipe);
        showSuccess('Recipe generated successfully!');
      } else {
        showError(response.error_message || 'Failed to generate recipe');
      }
    } catch (error) {
      console.error('Recipe generation error:', error);
      showError('Failed to generate recipe. Please try again.');
    } finally {
      setIsGenerating(false);
    }
  };

  const generateBulkRecipes = async () => {
    if (ingredients.length === 0) {
      showError('Please add at least one ingredient');
      return;
    }

    setIsGenerating(true);
    try {
      const requestData = {
        ingredients,
        recipe_count: 3,
        variety_preference: 'diverse',
        base_preferences: {
          ingredients,
          cuisine_preference: cuisinePreference || undefined,
          meal_type: mealType || undefined,
          dietary_restrictions: dietaryRestrictions.length > 0 ? dietaryRestrictions : undefined,
          difficulty_preference: difficultyPreference || undefined,
          servings,
          max_prep_time: maxPrepTime,
          max_cook_time: maxCookTime,
          exclude_ingredients: excludeIngredients.length > 0 ? excludeIngredients : undefined,
          include_nutrition: includeNutrition
        }
      };

      const response = await aiRecipeApi.generateBulkFromIngredients(requestData);
      
      if (response.success && response.recipes.length > 0) {
        // Show the first successful recipe
        const firstSuccessful = response.recipes.find((r: any) => r.success);
        if (firstSuccessful) {
          setGeneratedRecipe(firstSuccessful);
          onRecipeGenerated?.(firstSuccessful.recipe);
        }
        
        // Add all successful recipes to history
        const successfulRecipes = response.recipes.filter((r: any) => r.success);
        setGenerationHistory([...successfulRecipes, ...generationHistory].slice(0, 10));
        
        showSuccess(`Generated ${response.total_generated} recipes successfully!`);
      } else {
        showError('Failed to generate bulk recipes');
      }
    } catch (error) {
      console.error('Bulk recipe generation error:', error);
      showError('Failed to generate recipes. Please try again.');
    } finally {
      setIsGenerating(false);
    }
  };

  const cuisineOptions = [
    'Italian', 'Asian', 'Mexican', 'Mediterranean', 'American', 'Indian', 
    'French', 'Thai', 'Japanese', 'Chinese', 'Greek', 'Spanish'
  ];

  const mealTypeOptions = [
    { value: 'breakfast', label: 'Breakfast' },
    { value: 'lunch', label: 'Lunch' },
    { value: 'dinner', label: 'Dinner' },
    { value: 'snack', label: 'Snack' },
    { value: 'dessert', label: 'Dessert' }
  ];

  const difficultyOptions = [
    { value: 'easy', label: 'Easy' },
    { value: 'medium', label: 'Medium' },
    { value: 'hard', label: 'Hard' }
  ];

  const dietaryOptions = [
    'vegetarian', 'vegan', 'gluten_free', 'dairy_free', 'nut_free', 
    'low_carb', 'keto', 'paleo', 'halal', 'kosher'
  ];

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Service Status */}
      {serviceStatus && (
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-2">
              {serviceStatus.status.demo_mode ? (
                <AlertCircle className="h-4 w-4 text-yellow-500" />
              ) : (
                <CheckCircle className="h-4 w-4 text-green-500" />
              )}
              <span className="text-sm">
                {serviceStatus.status.demo_mode 
                  ? 'AI Recipe Generator (Demo Mode)' 
                  : 'AI Recipe Generator (Active)'}
              </span>
              {serviceStatus.status.demo_mode && (
                <Badge variant="outline" className="text-xs">
                  Demo
                </Badge>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Ingredients Input */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <ChefHat className="h-5 w-5" />
            Available Ingredients
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-2">
            <Input
              placeholder="Add an ingredient..."
              value={newIngredient}
              onChange={(e) => setNewIngredient(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && addIngredient()}
              className="flex-1"
            />
            <Button onClick={addIngredient} size="sm">
              <Plus className="h-4 w-4" />
            </Button>
          </div>
          
          <div className="flex flex-wrap gap-2">
            {ingredients.map((ingredient, index) => (
              <Badge key={index} variant="secondary" className="flex items-center gap-1">
                {ingredient}
                <X 
                  className="h-3 w-3 cursor-pointer hover:text-red-500" 
                  onClick={() => removeIngredient(ingredient)}
                />
              </Badge>
            ))}
          </div>
          
          {ingredients.length === 0 && (
            <p className="text-sm text-gray-500 text-center py-4">
              Add ingredients to generate AI-powered recipes
            </p>
          )}
        </CardContent>
      </Card>

      {/* Basic Preferences */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Utensils className="h-5 w-5" />
            Recipe Preferences
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Label htmlFor="cuisine">Cuisine Style</Label>
              <select
                id="cuisine"
                value={cuisinePreference}
                onChange={(e) => setCuisinePreference(e.target.value)}
                className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">Any cuisine</option>
                {cuisineOptions.map(cuisine => (
                  <option key={cuisine} value={cuisine}>{cuisine}</option>
                ))}
              </select>
            </div>

            <div>
              <Label htmlFor="meal-type">Meal Type</Label>
              <select
                id="meal-type"
                value={mealType}
                onChange={(e) => setMealType(e.target.value)}
                className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">Any meal</option>
                {mealTypeOptions.map(option => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <Label htmlFor="difficulty">Difficulty</Label>
              <select
                id="difficulty"
                value={difficultyPreference}
                onChange={(e) => setDifficultyPreference(e.target.value)}
                className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">Any difficulty</option>
                {difficultyOptions.map(option => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <Label htmlFor="servings">Servings</Label>
              <Input
                id="servings"
                type="number"
                min="1"
                max="12"
                value={servings}
                onChange={(e) => setServings(parseInt(e.target.value) || 4)}
              />
            </div>
          </div>

          {/* Advanced Options Toggle */}
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowAdvancedOptions(!showAdvancedOptions)}
            className="w-full"
          >
            {showAdvancedOptions ? 'Hide' : 'Show'} Advanced Options
          </Button>

          {/* Advanced Options */}
          {showAdvancedOptions && (
            <div className="space-y-4 pt-4 border-t">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="prep-time">Max Prep Time (minutes)</Label>
                  <Input
                    id="prep-time"
                    type="number"
                    min="5"
                    max="180"
                    value={maxPrepTime || ''}
                    onChange={(e) => setMaxPrepTime(e.target.value ? parseInt(e.target.value) : undefined)}
                    placeholder="No limit"
                  />
                </div>

                <div>
                  <Label htmlFor="cook-time">Max Cook Time (minutes)</Label>
                  <Input
                    id="cook-time"
                    type="number"
                    min="5"
                    max="300"
                    value={maxCookTime || ''}
                    onChange={(e) => setMaxCookTime(e.target.value ? parseInt(e.target.value) : undefined)}
                    placeholder="No limit"
                  />
                </div>
              </div>

              {/* Dietary Restrictions */}
              <div>
                <Label>Dietary Restrictions</Label>
                <div className="flex flex-wrap gap-2 mt-2">
                  {dietaryOptions.map(restriction => (
                    <Badge
                      key={restriction}
                      variant={dietaryRestrictions.includes(restriction) ? "default" : "outline"}
                      className="cursor-pointer"
                      onClick={() => toggleDietaryRestriction(restriction)}
                    >
                      {restriction.replace('_', ' ')}
                    </Badge>
                  ))}
                </div>
              </div>

              {/* Include Nutrition */}
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="nutrition"
                  checked={includeNutrition}
                  onCheckedChange={(checked) => setIncludeNutrition(checked === true)}
                />
                <Label htmlFor="nutrition">Include nutritional information</Label>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Generation Buttons */}
      <div className="flex gap-3">
        <Button
          onClick={generateRecipe}
          disabled={isGenerating || ingredients.length === 0}
          className="flex-1"
        >
          {isGenerating ? (
            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
          ) : (
            <Sparkles className="h-4 w-4 mr-2" />
          )}
          Generate Recipe
        </Button>

        <Button
          onClick={generateBulkRecipes}
          disabled={isGenerating || ingredients.length === 0}
          variant="outline"
          className="flex-1"
        >
          {isGenerating ? (
            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
          ) : (
            <TrendingUp className="h-4 w-4 mr-2" />
          )}
          Generate 3 Recipes
        </Button>
      </div>

      {/* Generated Recipe Display */}
      {generatedRecipe && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Star className="h-5 w-5 text-yellow-500" />
              Generated Recipe
              {generatedRecipe.fallback_used && (
                <Badge variant="outline" className="text-xs">Demo</Badge>
              )}
            </CardTitle>
            <div className="flex items-center gap-4 text-sm text-gray-600">
              <span className="flex items-center gap-1">
                <TrendingUp className="h-4 w-4" />
                {Math.round(generatedRecipe.confidence_score * 100)}% confidence
              </span>
              <span className="flex items-center gap-1">
                <Lightbulb className="h-4 w-4" />
                {Math.round(generatedRecipe.ingredient_match_percentage)}% ingredient match
              </span>
            </div>
          </CardHeader>
          <CardContent>
            {generatedRecipe.recipe && (
              <div className="space-y-4">
                <div>
                  <h3 className="font-semibold text-lg">{generatedRecipe.recipe.title}</h3>
                  <p className="text-gray-600">{generatedRecipe.recipe.description}</p>
                </div>

                <div className="flex items-center gap-4 text-sm">
                  <div className="flex items-center gap-1">
                    <Clock className="h-4 w-4" />
                    {(generatedRecipe.recipe.prep_time || 0) + (generatedRecipe.recipe.cook_time || 0)} min total
                  </div>
                  <div className="flex items-center gap-1">
                    <Users className="h-4 w-4" />
                    {generatedRecipe.recipe.servings} servings
                  </div>
                  <Badge variant="outline">
                    {generatedRecipe.recipe.difficulty}
                  </Badge>
                </div>

                <div>
                  <h4 className="font-medium mb-2">Ingredients:</h4>
                  <ul className="space-y-1">
                    {generatedRecipe.recipe.ingredients.map((ing: any, index: number) => (
                      <li key={index} className="text-sm">
                        {ing.quantity} {ing.unit} {ing.name}
                        {ing.notes && <span className="text-gray-500"> ({ing.notes})</span>}
                      </li>
                    ))}
                  </ul>
                </div>

                <div>
                  <h4 className="font-medium mb-2">Instructions:</h4>
                  <ol className="space-y-2">
                    {generatedRecipe.recipe.instructions.map((instruction: string, index: number) => (
                      <li key={index} className="text-sm">
                        <span className="font-medium text-gray-700">{index + 1}.</span> {instruction}
                      </li>
                    ))}
                  </ol>
                </div>

                {generatedRecipe.recipe.nutrition_info && (
                  <div>
                    <h4 className="font-medium mb-2">Nutrition (per serving):</h4>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-sm">
                      <div>Calories: {generatedRecipe.recipe.nutrition_info.calories_per_serving}</div>
                      <div>Protein: {generatedRecipe.recipe.nutrition_info.protein_g}g</div>
                      <div>Carbs: {generatedRecipe.recipe.nutrition_info.carbs_g}g</div>
                      <div>Fat: {generatedRecipe.recipe.nutrition_info.fat_g}g</div>
                    </div>
                  </div>
                )}

                <div className="flex flex-wrap gap-1">
                  {generatedRecipe.recipe.tags.map((tag: string, index: number) => (
                    <Badge key={index} variant="secondary" className="text-xs">
                      {tag}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Generation History */}
      {generationHistory.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Clock className="h-5 w-5" />
              Recent Generations
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {generationHistory.slice(0, 3).map((generation, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-2 bg-gray-50 rounded cursor-pointer hover:bg-gray-100"
                  onClick={() => setGeneratedRecipe(generation)}
                >
                  <div>
                    <p className="font-medium text-sm">{generation.recipe?.title}</p>
                    <p className="text-xs text-gray-500">
                      {Math.round(generation.confidence_score * 100)}% confidence
                    </p>
                  </div>
                  <Badge variant="outline" className="text-xs">
                    {generation.fallback_used ? 'Demo' : 'AI'}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default AIRecipeGenerator;