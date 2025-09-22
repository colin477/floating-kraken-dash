import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { ArrowLeft, Link, Loader2, Check, Globe, Clock, Users } from 'lucide-react';
import { Recipe } from '@/types';
import { storage } from '@/lib/storage';
import { showSuccess, showError } from '@/utils/toast';

interface AddFromLinkProps {
  onBack: () => void;
}

// Mock function to simulate fetching recipe from URL
const fetchRecipeFromUrl = async (url: string): Promise<Recipe> => {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      // Simulate different responses based on URL
      if (!url.includes('http')) {
        reject(new Error('Please enter a valid URL'));
        return;
      }

      // Mock recipe data based on common recipe sites
      const mockRecipe: Recipe = {
        id: Date.now().toString(),
        title: url.includes('allrecipes') ? 'Classic Chocolate Chip Cookies' :
               url.includes('foodnetwork') ? 'Perfect Grilled Chicken' :
               url.includes('tasty') ? 'One-Pot Pasta Primavera' :
               'Imported Recipe from Web',
        description: 'A delicious recipe imported from the web with AI-powered ingredient and instruction extraction.',
        ingredients: [
          { name: 'Flour', quantity: 2, unit: 'cups' },
          { name: 'Sugar', quantity: 1, unit: 'cup' },
          { name: 'Butter', quantity: 0.5, unit: 'cup' },
          { name: 'Eggs', quantity: 2, unit: 'pieces' },
          { name: 'Vanilla extract', quantity: 1, unit: 'tsp' },
          { name: 'Baking powder', quantity: 1, unit: 'tsp' }
        ],
        instructions: [
          'Preheat oven to 350°F (175°C)',
          'In a large bowl, cream together butter and sugar',
          'Beat in eggs one at a time, then add vanilla',
          'In a separate bowl, combine flour and baking powder',
          'Gradually mix dry ingredients into wet ingredients',
          'Drop spoonfuls of dough onto baking sheet',
          'Bake for 10-12 minutes until golden brown',
          'Cool on wire rack before serving'
        ],
        prepTime: 15,
        cookTime: 12,
        servings: 24,
        difficulty: 'easy',
        tags: ['baked-goods', 'dessert', 'family-friendly'],
        nutritionInfo: {
          calories: 180,
          protein: 3,
          carbs: 25,
          fat: 8,
          fiber: 1
        },
        source: 'community',
        createdAt: new Date().toISOString()
      };

      resolve(mockRecipe);
    }, 2000);
  });
};

export const AddFromLink = ({ onBack }: AddFromLinkProps) => {
  const [url, setUrl] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [extractedRecipe, setExtractedRecipe] = useState<Recipe | null>(null);
  const [step, setStep] = useState<'input' | 'loading' | 'review' | 'complete'>('input');

  const handleFetchRecipe = async () => {
    if (!url.trim()) {
      showError('Please enter a recipe URL');
      return;
    }

    setStep('loading');
    setIsLoading(true);

    try {
      const recipe = await fetchRecipeFromUrl(url);
      setExtractedRecipe(recipe);
      setStep('review');
    } catch (error) {
      showError(error instanceof Error ? error.message : 'Failed to fetch recipe');
      setStep('input');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSaveRecipe = () => {
    if (extractedRecipe) {
      storage.addRecipe(extractedRecipe);
      setStep('complete');
      showSuccess('Recipe saved to your collection!');
    }
  };

  const handleTryAnother = () => {
    setUrl('');
    setExtractedRecipe(null);
    setStep('input');
  };

  const renderInputStep = () => (
    <div className="space-y-6">
      <div className="text-center">
        <div className="mx-auto w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mb-4">
          <Link className="h-8 w-8 text-blue-600" />
        </div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Add Recipe from Link</h2>
        <p className="text-gray-600">
          Paste a link to any recipe from popular cooking websites and our AI will extract the ingredients and instructions.
        </p>
      </div>

      <div className="space-y-4">
        <div>
          <Label htmlFor="recipe-url">Recipe URL</Label>
          <Input
            id="recipe-url"
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://www.allrecipes.com/recipe/..."
            className="mt-1"
            onKeyDown={(e) => e.key === 'Enter' && handleFetchRecipe()}
          />
        </div>

        <Button onClick={handleFetchRecipe} className="w-full" size="lg">
          <Globe className="h-5 w-5 mr-2" />
          Import Recipe
        </Button>
      </div>

      <div className="bg-blue-50 p-4 rounded-lg">
        <h4 className="font-medium text-blue-900 mb-2">Supported Sites</h4>
        <div className="grid grid-cols-2 gap-2 text-sm text-blue-700">
          <div>• AllRecipes.com</div>
          <div>• Food Network</div>
          <div>• Tasty.co</div>
          <div>• BBC Good Food</div>
          <div>• Serious Eats</div>
          <div>• And many more!</div>
        </div>
      </div>

      <div className="text-sm text-gray-500">
        <p><strong>Tips for best results:</strong></p>
        <ul className="mt-2 space-y-1">
          <li>• Use direct links to recipe pages</li>
          <li>• Avoid shortened URLs (bit.ly, etc.)</li>
          <li>• Make sure the page contains a complete recipe</li>
        </ul>
      </div>
    </div>
  );

  const renderLoadingStep = () => (
    <div className="text-center space-y-6">
      <div className="mx-auto w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center">
        <Loader2 className="h-8 w-8 text-blue-600 animate-spin" />
      </div>
      
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Importing Recipe</h2>
        <p className="text-gray-600">
          Our AI is analyzing the webpage and extracting the recipe information...
        </p>
      </div>

      <div className="space-y-2">
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div className="bg-blue-600 h-2 rounded-full animate-pulse" style={{ width: '65%' }} />
        </div>
        <p className="text-sm text-gray-500">This usually takes 15-30 seconds</p>
      </div>

      <div className="text-left bg-gray-50 p-4 rounded-lg">
        <p className="text-sm text-gray-600 mb-2">Processing:</p>
        <div className="space-y-1 text-sm">
          <div className="flex items-center text-green-600">
            <Check className="h-4 w-4 mr-2" />
            Webpage loaded successfully
          </div>
          <div className="flex items-center text-green-600">
            <Check className="h-4 w-4 mr-2" />
            Recipe content identified
          </div>
          <div className="flex items-center text-blue-600">
            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            Extracting ingredients and instructions...
          </div>
        </div>
      </div>
    </div>
  );

  const renderReviewStep = () => {
    if (!extractedRecipe) return null;

    return (
      <div className="space-y-6">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Review Imported Recipe</h2>
          <p className="text-gray-600">
            Check the extracted information and save to your collection.
          </p>
        </div>

        <Card>
          <CardHeader>
            <div className="flex justify-between items-start">
              <div>
                <CardTitle className="text-xl">{extractedRecipe.title}</CardTitle>
                <CardDescription className="mt-2">{extractedRecipe.description}</CardDescription>
              </div>
              <Badge variant="outline" className="ml-2">
                Imported
              </Badge>
            </div>
            
            <div className="flex items-center gap-4 mt-4">
              <div className="flex items-center text-gray-600">
                <Clock className="h-4 w-4 mr-1" />
                {extractedRecipe.prepTime + extractedRecipe.cookTime} min
              </div>
              <div className="flex items-center text-gray-600">
                <Users className="h-4 w-4 mr-1" />
                {extractedRecipe.servings} servings
              </div>
              <Badge variant="outline">{extractedRecipe.difficulty}</Badge>
            </div>

            <div className="flex flex-wrap gap-2 mt-4">
              {extractedRecipe.tags.map(tag => (
                <Badge key={tag} variant="secondary" className="text-xs">
                  {tag}
                </Badge>
              ))}
            </div>
          </CardHeader>
          
          <CardContent className="space-y-6">
            <div>
              <h4 className="font-semibold mb-3">Ingredients</h4>
              <div className="grid gap-2">
                {extractedRecipe.ingredients.map((ingredient, index) => (
                  <div key={index} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                    <span>{ingredient.name}</span>
                    <span className="text-sm text-gray-600">
                      {ingredient.quantity} {ingredient.unit}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            <div>
              <h4 className="font-semibold mb-3">Instructions</h4>
              <ol className="space-y-2">
                {extractedRecipe.instructions.map((instruction, index) => (
                  <li key={index} className="flex">
                    <span className="flex-shrink-0 w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm font-medium mr-3">
                      {index + 1}
                    </span>
                    <span className="text-gray-700">{instruction}</span>
                  </li>
                ))}
              </ol>
            </div>

            {extractedRecipe.nutritionInfo && (
              <div>
                <h4 className="font-semibold mb-3">Nutrition (per serving)</h4>
                <div className="grid grid-cols-5 gap-4 text-sm">
                  <div className="text-center">
                    <div className="font-bold text-lg">{extractedRecipe.nutritionInfo.calories}</div>
                    <div className="text-gray-600">Calories</div>
                  </div>
                  <div className="text-center">
                    <div className="font-bold text-lg">{extractedRecipe.nutritionInfo.protein}g</div>
                    <div className="text-gray-600">Protein</div>
                  </div>
                  <div className="text-center">
                    <div className="font-bold text-lg">{extractedRecipe.nutritionInfo.carbs}g</div>
                    <div className="text-gray-600">Carbs</div>
                  </div>
                  <div className="text-center">
                    <div className="font-bold text-lg">{extractedRecipe.nutritionInfo.fat}g</div>
                    <div className="text-gray-600">Fat</div>
                  </div>
                  <div className="text-center">
                    <div className="font-bold text-lg">{extractedRecipe.nutritionInfo.fiber}g</div>
                    <div className="text-gray-600">Fiber</div>
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        <div className="flex gap-3">
          <Button variant="outline" onClick={handleTryAnother} className="flex-1">
            Import Another
          </Button>
          <Button onClick={handleSaveRecipe} className="flex-1">
            Save Recipe
          </Button>
        </div>
      </div>
    );
  };

  const renderCompleteStep = () => (
    <div className="text-center space-y-6">
      <div className="mx-auto w-16 h-16 bg-green-100 rounded-full flex items-center justify-center">
        <Check className="h-8 w-8 text-green-600" />
      </div>
      
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Recipe Imported!</h2>
        <p className="text-gray-600">
          Your recipe has been saved to your collection and is ready to use in meal planning.
        </p>
      </div>

      <div className="space-y-3">
        <Button onClick={onBack} className="w-full" size="lg">
          Back to Dashboard
        </Button>
        <Button variant="outline" onClick={handleTryAnother} className="w-full">
          Import Another Recipe
        </Button>
      </div>
    </div>
  );

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
              <h1 className="text-xl font-semibold">Add Recipe from Link</h1>
              <p className="text-sm text-gray-600">Import recipes from cooking websites</p>
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Card>
          <CardContent className="p-8">
            {step === 'input' && renderInputStep()}
            {step === 'loading' && renderLoadingStep()}
            {step === 'review' && renderReviewStep()}
            {step === 'complete' && renderCompleteStep()}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};