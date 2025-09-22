import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { ArrowLeft, Clock, Users, ChefHat, Share2, Heart, Bookmark } from 'lucide-react';
import { Recipe } from '@/types';
import { showSuccess } from '@/utils/toast';

interface RecipeDetailProps {
  recipe: Recipe;
  onBack: () => void;
}

export const RecipeDetail = ({ recipe, onBack }: RecipeDetailProps) => {
  const [isFavorited, setIsFavorited] = useState(false);
  const [isBookmarked, setIsBookmarked] = useState(false);

  const handleFavorite = () => {
    setIsFavorited(!isFavorited);
    showSuccess(isFavorited ? 'Removed from favorites' : 'Added to favorites');
  };

  const handleBookmark = () => {
    setIsBookmarked(!isBookmarked);
    showSuccess(isBookmarked ? 'Bookmark removed' : 'Recipe bookmarked');
  };

  const handleShare = () => {
    if (navigator.share) {
      navigator.share({
        title: recipe.title,
        text: recipe.description,
        url: window.location.href,
      });
    } else {
      navigator.clipboard.writeText(window.location.href);
      showSuccess('Recipe link copied to clipboard!');
    }
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
                <h1 className="text-xl font-semibold">Recipe Details</h1>
                <p className="text-sm text-gray-600">View and save recipe information</p>
              </div>
            </div>
            
            <div className="flex items-center gap-2">
              <Button variant="ghost" size="sm" onClick={handleFavorite}>
                <Heart className={`h-4 w-4 ${isFavorited ? 'fill-red-500 text-red-500' : ''}`} />
              </Button>
              <Button variant="ghost" size="sm" onClick={handleBookmark}>
                <Bookmark className={`h-4 w-4 ${isBookmarked ? 'fill-blue-500 text-blue-500' : ''}`} />
              </Button>
              <Button variant="ghost" size="sm" onClick={handleShare}>
                <Share2 className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Card>
          <CardHeader>
            <div className="flex justify-between items-start">
              <div className="flex-1">
                <CardTitle className="text-2xl mb-2">{recipe.title}</CardTitle>
                <CardDescription className="text-lg">{recipe.description}</CardDescription>
              </div>
            </div>
            
            <div className="flex items-center gap-6 mt-4">
              <div className="flex items-center text-gray-600">
                <Clock className="h-5 w-5 mr-2" />
                <div>
                  <div className="font-medium">Total Time</div>
                  <div className="text-sm">{recipe.prepTime + recipe.cookTime} minutes</div>
                </div>
              </div>
              
              <div className="flex items-center text-gray-600">
                <Users className="h-5 w-5 mr-2" />
                <div>
                  <div className="font-medium">Servings</div>
                  <div className="text-sm">{recipe.servings} people</div>
                </div>
              </div>
              
              <div className="flex items-center text-gray-600">
                <ChefHat className="h-5 w-5 mr-2" />
                <div>
                  <div className="font-medium">Difficulty</div>
                  <Badge variant="outline" className="mt-1">
                    {recipe.difficulty}
                  </Badge>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-2 mt-4">
              <span className="text-sm font-medium text-gray-600">Tags:</span>
              <div className="flex flex-wrap gap-2">
                {recipe.tags.map(tag => (
                  <Badge key={tag} variant="secondary" className="text-xs">
                    {tag}
                  </Badge>
                ))}
              </div>
            </div>

            <div className="flex items-center justify-between mt-4 pt-4 border-t">
              <Badge variant="outline">
                {recipe.source === 'ai-generated' && 'AI Generated'}
                {recipe.source === 'photo-analysis' && 'Photo Analysis'}
                {recipe.source === 'community' && 'Community Recipe'}
              </Badge>
              <span className="text-sm text-gray-500">
                Created {new Date(recipe.createdAt).toLocaleDateString()}
              </span>
            </div>
          </CardHeader>
          
          <CardContent className="space-y-8">
            {/* Ingredients */}
            <div>
              <h3 className="text-xl font-semibold mb-4">Ingredients</h3>
              <div className="grid gap-3">
                {recipe.ingredients.map((ingredient, index) => (
                  <div key={index} className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                    <span className="font-medium">{ingredient.name}</span>
                    <span className="text-gray-600">
                      {ingredient.quantity} {ingredient.unit}
                      {ingredient.optional && (
                        <Badge variant="outline" className="ml-2 text-xs">
                          optional
                        </Badge>
                      )}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            <Separator />

            {/* Instructions */}
            <div>
              <h3 className="text-xl font-semibold mb-4">Instructions</h3>
              <ol className="space-y-4">
                {recipe.instructions.map((instruction, index) => (
                  <li key={index} className="flex">
                    <span className="flex-shrink-0 w-8 h-8 bg-primary text-primary-foreground rounded-full flex items-center justify-center text-sm font-medium mr-4">
                      {index + 1}
                    </span>
                    <span className="text-gray-700 leading-relaxed pt-1">{instruction}</span>
                  </li>
                ))}
              </ol>
            </div>

            {/* Nutrition Info */}
            {recipe.nutritionInfo && (
              <>
                <Separator />
                <div>
                  <h3 className="text-xl font-semibold mb-4">Nutrition Information</h3>
                  <p className="text-sm text-gray-600 mb-4">Per serving</p>
                  <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                    <div className="text-center p-4 bg-gray-50 rounded-lg">
                      <div className="text-2xl font-bold text-primary">{recipe.nutritionInfo.calories}</div>
                      <div className="text-sm text-gray-600">Calories</div>
                    </div>
                    <div className="text-center p-4 bg-gray-50 rounded-lg">
                      <div className="text-2xl font-bold text-primary">{recipe.nutritionInfo.protein}g</div>
                      <div className="text-sm text-gray-600">Protein</div>
                    </div>
                    <div className="text-center p-4 bg-gray-50 rounded-lg">
                      <div className="text-2xl font-bold text-primary">{recipe.nutritionInfo.carbs}g</div>
                      <div className="text-sm text-gray-600">Carbs</div>
                    </div>
                    <div className="text-center p-4 bg-gray-50 rounded-lg">
                      <div className="text-2xl font-bold text-primary">{recipe.nutritionInfo.fat}g</div>
                      <div className="text-sm text-gray-600">Fat</div>
                    </div>
                    <div className="text-center p-4 bg-gray-50 rounded-lg">
                      <div className="text-2xl font-bold text-primary">{recipe.nutritionInfo.fiber}g</div>
                      <div className="text-sm text-gray-600">Fiber</div>
                    </div>
                  </div>
                </div>
              </>
            )}

            {/* Action Buttons */}
            <div className="flex gap-4 pt-4">
              <Button onClick={onBack} className="flex-1">
                Back to Recipes
              </Button>
              <Button variant="outline" onClick={handleShare} className="flex-1">
                <Share2 className="h-4 w-4 mr-2" />
                Share Recipe
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};