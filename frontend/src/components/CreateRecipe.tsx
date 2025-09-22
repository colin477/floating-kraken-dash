import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { ArrowLeft, Plus, Trash2, Save, ChefHat, Clock, Users } from 'lucide-react';
import { Recipe, RecipeIngredient } from '@/types';
import { storage } from '@/lib/storage';
import { showSuccess, showError } from '@/utils/toast';

interface CreateRecipeProps {
  onBack: () => void;
}

export const CreateRecipe = ({ onBack }: CreateRecipeProps) => {
  const [recipe, setRecipe] = useState({
    title: '',
    description: '',
    prepTime: '',
    cookTime: '',
    servings: '',
    difficulty: 'easy' as 'easy' | 'medium' | 'hard'
  });

  const [ingredients, setIngredients] = useState<RecipeIngredient[]>([
    { name: '', quantity: 0, unit: 'pieces', optional: false }
  ]);

  const [instructions, setInstructions] = useState<string[]>(['']);
  const [tags, setTags] = useState<string[]>([]);
  const [newTag, setNewTag] = useState('');

  const [nutritionInfo, setNutritionInfo] = useState({
    calories: '',
    protein: '',
    carbs: '',
    fat: '',
    fiber: ''
  });

  const [includeNutrition, setIncludeNutrition] = useState(false);

  const commonUnits = [
    'pieces', 'cups', 'tbsp', 'tsp', 'lbs', 'oz', 'g', 'kg', 'ml', 'liters',
    'cans', 'bottles', 'packages', 'cloves', 'slices', 'bunches'
  ];

  const commonTags = [
    'quick', 'easy', 'healthy', 'vegetarian', 'vegan', 'gluten-free', 'dairy-free',
    'family-friendly', 'comfort-food', 'one-pot', 'make-ahead', 'freezer-friendly',
    'budget-friendly', 'high-protein', 'low-carb', 'keto', 'paleo'
  ];

  const handleRecipeChange = (field: string, value: string) => {
    setRecipe(prev => ({ ...prev, [field]: value }));
  };

  const handleIngredientChange = (index: number, field: keyof RecipeIngredient, value: any) => {
    setIngredients(prev => 
      prev.map((ingredient, i) => 
        i === index ? { ...ingredient, [field]: value } : ingredient
      )
    );
  };

  const addIngredient = () => {
    setIngredients(prev => [...prev, { name: '', quantity: 0, unit: 'pieces', optional: false }]);
  };

  const removeIngredient = (index: number) => {
    if (ingredients.length > 1) {
      setIngredients(prev => prev.filter((_, i) => i !== index));
    }
  };

  const handleInstructionChange = (index: number, value: string) => {
    setInstructions(prev => 
      prev.map((instruction, i) => i === index ? value : instruction)
    );
  };

  const addInstruction = () => {
    setInstructions(prev => [...prev, '']);
  };

  const removeInstruction = (index: number) => {
    if (instructions.length > 1) {
      setInstructions(prev => prev.filter((_, i) => i !== index));
    }
  };

  const addTag = () => {
    if (newTag.trim() && !tags.includes(newTag.trim())) {
      setTags(prev => [...prev, newTag.trim()]);
      setNewTag('');
    }
  };

  const removeTag = (tagToRemove: string) => {
    setTags(prev => prev.filter(tag => tag !== tagToRemove));
  };

  const addCommonTag = (tag: string) => {
    if (!tags.includes(tag)) {
      setTags(prev => [...prev, tag]);
    }
  };

  const handleSaveRecipe = () => {
    // Validation
    if (!recipe.title.trim()) {
      showError('Please enter a recipe title');
      return;
    }

    if (!recipe.description.trim()) {
      showError('Please enter a recipe description');
      return;
    }

    if (!recipe.prepTime || !recipe.cookTime || !recipe.servings) {
      showError('Please fill in prep time, cook time, and servings');
      return;
    }

    const validIngredients = ingredients.filter(ing => ing.name.trim() && ing.quantity > 0);
    if (validIngredients.length === 0) {
      showError('Please add at least one ingredient');
      return;
    }

    const validInstructions = instructions.filter(inst => inst.trim());
    if (validInstructions.length === 0) {
      showError('Please add at least one instruction');
      return;
    }

    // Create recipe object
    const newRecipe: Recipe = {
      id: Date.now().toString(),
      title: recipe.title.trim(),
      description: recipe.description.trim(),
      ingredients: validIngredients,
      instructions: validInstructions,
      prepTime: parseInt(recipe.prepTime),
      cookTime: parseInt(recipe.cookTime),
      servings: parseInt(recipe.servings),
      difficulty: recipe.difficulty,
      tags: tags,
      nutritionInfo: includeNutrition ? {
        calories: parseInt(nutritionInfo.calories) || 0,
        protein: parseInt(nutritionInfo.protein) || 0,
        carbs: parseInt(nutritionInfo.carbs) || 0,
        fat: parseInt(nutritionInfo.fat) || 0,
        fiber: parseInt(nutritionInfo.fiber) || 0
      } : undefined,
      source: 'community',
      createdAt: new Date().toISOString()
    };

    // Save recipe
    storage.addRecipe(newRecipe);
    showSuccess('Recipe created and saved to your collection!');
    onBack();
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between py-4">
            <div className="flex items-center">
              <Button variant="ghost" onClick={onBack} className="mr-4">
                <ArrowLeft className="h-4 w-4" />
              </Button>
              <div>
                <h1 className="text-xl font-semibold">Create Your Own Recipe</h1>
                <p className="text-sm text-gray-600">Build a recipe from scratch</p>
              </div>
            </div>
            <Button onClick={handleSaveRecipe}>
              <Save className="h-4 w-4 mr-2" />
              Save Recipe
            </Button>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="space-y-8">
          {/* Basic Information */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <ChefHat className="h-5 w-5 mr-2" />
                Basic Information
              </CardTitle>
              <CardDescription>
                Start with the basics - what's your recipe called and what makes it special?
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label htmlFor="title">Recipe Title *</Label>
                <Input
                  id="title"
                  value={recipe.title}
                  onChange={(e) => handleRecipeChange('title', e.target.value)}
                  placeholder="e.g., Grandma's Famous Chocolate Chip Cookies"
                />
              </div>

              <div>
                <Label htmlFor="description">Description *</Label>
                <Textarea
                  id="description"
                  value={recipe.description}
                  onChange={(e) => handleRecipeChange('description', e.target.value)}
                  placeholder="Describe your recipe - what makes it special, when to serve it, or any tips..."
                  rows={3}
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div>
                  <Label htmlFor="prep-time">Prep Time (minutes) *</Label>
                  <Input
                    id="prep-time"
                    type="number"
                    min="0"
                    value={recipe.prepTime}
                    onChange={(e) => handleRecipeChange('prepTime', e.target.value)}
                    placeholder="15"
                  />
                </div>
                <div>
                  <Label htmlFor="cook-time">Cook Time (minutes) *</Label>
                  <Input
                    id="cook-time"
                    type="number"
                    min="0"
                    value={recipe.cookTime}
                    onChange={(e) => handleRecipeChange('cookTime', e.target.value)}
                    placeholder="30"
                  />
                </div>
                <div>
                  <Label htmlFor="servings">Servings *</Label>
                  <Input
                    id="servings"
                    type="number"
                    min="1"
                    value={recipe.servings}
                    onChange={(e) => handleRecipeChange('servings', e.target.value)}
                    placeholder="4"
                  />
                </div>
                <div>
                  <Label htmlFor="difficulty">Difficulty</Label>
                  <select
                    id="difficulty"
                    value={recipe.difficulty}
                    onChange={(e) => handleRecipeChange('difficulty', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="easy">Easy</option>
                    <option value="medium">Medium</option>
                    <option value="hard">Hard</option>
                  </select>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Ingredients */}
          <Card>
            <CardHeader>
              <CardTitle>Ingredients</CardTitle>
              <CardDescription>
                List all the ingredients needed for your recipe
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {ingredients.map((ingredient, index) => (
                <div key={index} className="grid grid-cols-1 md:grid-cols-12 gap-4 items-end">
                  <div className="md:col-span-5">
                    <Label htmlFor={`ingredient-name-${index}`}>Ingredient Name</Label>
                    <Input
                      id={`ingredient-name-${index}`}
                      value={ingredient.name}
                      onChange={(e) => handleIngredientChange(index, 'name', e.target.value)}
                      placeholder="e.g., All-purpose flour"
                    />
                  </div>
                  <div className="md:col-span-2">
                    <Label htmlFor={`ingredient-quantity-${index}`}>Quantity</Label>
                    <Input
                      id={`ingredient-quantity-${index}`}
                      type="number"
                      min="0"
                      step="0.1"
                      value={ingredient.quantity || ''}
                      onChange={(e) => handleIngredientChange(index, 'quantity', parseFloat(e.target.value) || 0)}
                      placeholder="2"
                    />
                  </div>
                  <div className="md:col-span-2">
                    <Label htmlFor={`ingredient-unit-${index}`}>Unit</Label>
                    <select
                      id={`ingredient-unit-${index}`}
                      value={ingredient.unit}
                      onChange={(e) => handleIngredientChange(index, 'unit', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    >
                      {commonUnits.map(unit => (
                        <option key={unit} value={unit}>{unit}</option>
                      ))}
                    </select>
                  </div>
                  <div className="md:col-span-2 flex items-center">
                    <input
                      type="checkbox"
                      id={`ingredient-optional-${index}`}
                      checked={ingredient.optional}
                      onChange={(e) => handleIngredientChange(index, 'optional', e.target.checked)}
                      className="mr-2"
                    />
                    <Label htmlFor={`ingredient-optional-${index}`} className="text-sm">
                      Optional
                    </Label>
                  </div>
                  <div className="md:col-span-1">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => removeIngredient(index)}
                      disabled={ingredients.length === 1}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}
              
              <Button variant="outline" onClick={addIngredient} className="w-full">
                <Plus className="h-4 w-4 mr-2" />
                Add Ingredient
              </Button>
            </CardContent>
          </Card>

          {/* Instructions */}
          <Card>
            <CardHeader>
              <CardTitle>Instructions</CardTitle>
              <CardDescription>
                Step-by-step cooking instructions
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {instructions.map((instruction, index) => (
                <div key={index} className="flex gap-4 items-start">
                  <div className="flex-shrink-0 w-8 h-8 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm font-medium">
                    {index + 1}
                  </div>
                  <div className="flex-1">
                    <Textarea
                      value={instruction}
                      onChange={(e) => handleInstructionChange(index, e.target.value)}
                      placeholder={`Step ${index + 1}: Describe what to do...`}
                      rows={2}
                    />
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => removeInstruction(index)}
                    disabled={instructions.length === 1}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              ))}
              
              <Button variant="outline" onClick={addInstruction} className="w-full">
                <Plus className="h-4 w-4 mr-2" />
                Add Step
              </Button>
            </CardContent>
          </Card>

          {/* Tags */}
          <Card>
            <CardHeader>
              <CardTitle>Tags</CardTitle>
              <CardDescription>
                Add tags to help categorize and find your recipe
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex gap-2">
                <Input
                  value={newTag}
                  onChange={(e) => setNewTag(e.target.value)}
                  placeholder="Add a tag..."
                  onKeyDown={(e) => e.key === 'Enter' && addTag()}
                />
                <Button onClick={addTag}>Add</Button>
              </div>

              {tags.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {tags.map(tag => (
                    <Badge key={tag} variant="secondary" className="text-sm">
                      {tag}
                      <Button
                        variant="ghost"
                        size="sm"
                        className="ml-1 h-4 w-4 p-0 hover:bg-transparent"
                        onClick={() => removeTag(tag)}
                      >
                        ×
                      </Button>
                    </Badge>
                  ))}
                </div>
              )}

              <div>
                <p className="text-sm text-gray-600 mb-2">Common tags:</p>
                <div className="flex flex-wrap gap-2">
                  {commonTags.filter(tag => !tags.includes(tag)).map(tag => (
                    <Button
                      key={tag}
                      variant="outline"
                      size="sm"
                      onClick={() => addCommonTag(tag)}
                      className="text-xs"
                    >
                      + {tag}
                    </Button>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Nutrition Information (Optional) */}
          <Card>
            <CardHeader>
              <CardTitle>Nutrition Information (Optional)</CardTitle>
              <CardDescription>
                Add nutritional information per serving
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="include-nutrition"
                  checked={includeNutrition}
                  onChange={(e) => setIncludeNutrition(e.target.checked)}
                />
                <Label htmlFor="include-nutrition">Include nutrition information</Label>
              </div>

              {includeNutrition && (
                <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                  <div>
                    <Label htmlFor="calories">Calories</Label>
                    <Input
                      id="calories"
                      type="number"
                      min="0"
                      value={nutritionInfo.calories}
                      onChange={(e) => setNutritionInfo(prev => ({ ...prev, calories: e.target.value }))}
                      placeholder="250"
                    />
                  </div>
                  <div>
                    <Label htmlFor="protein">Protein (g)</Label>
                    <Input
                      id="protein"
                      type="number"
                      min="0"
                      value={nutritionInfo.protein}
                      onChange={(e) => setNutritionInfo(prev => ({ ...prev, protein: e.target.value }))}
                      placeholder="15"
                    />
                  </div>
                  <div>
                    <Label htmlFor="carbs">Carbs (g)</Label>
                    <Input
                      id="carbs"
                      type="number"
                      min="0"
                      value={nutritionInfo.carbs}
                      onChange={(e) => setNutritionInfo(prev => ({ ...prev, carbs: e.target.value }))}
                      placeholder="30"
                    />
                  </div>
                  <div>
                    <Label htmlFor="fat">Fat (g)</Label>
                    <Input
                      id="fat"
                      type="number"
                      min="0"
                      value={nutritionInfo.fat}
                      onChange={(e) => setNutritionInfo(prev => ({ ...prev, fat: e.target.value }))}
                      placeholder="10"
                    />
                  </div>
                  <div>
                    <Label htmlFor="fiber">Fiber (g)</Label>
                    <Input
                      id="fiber"
                      type="number"
                      min="0"
                      value={nutritionInfo.fiber}
                      onChange={(e) => setNutritionInfo(prev => ({ ...prev, fiber: e.target.value }))}
                      placeholder="5"
                    />
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Save Button */}
          <div className="flex gap-4">
            <Button variant="outline" onClick={onBack} className="flex-1">
              Cancel
            </Button>
            <Button onClick={handleSaveRecipe} className="flex-1">
              <Save className="h-4 w-4 mr-2" />
              Save Recipe
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};