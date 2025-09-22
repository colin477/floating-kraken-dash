import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { ArrowLeft, Search, Clock, Users, ChefHat, Filter } from 'lucide-react';
import { User, Recipe } from '@/types';
import { storage } from '@/lib/storage';
import { mockRecipes } from '@/lib/mockData';

interface RecipesProps {
  user: User;
  onBack: () => void;
  onRecipeSelect?: (recipe: Recipe) => void;
  onNavigate?: (page: string) => void;
}

export const Recipes = ({ user, onBack, onRecipeSelect, onNavigate }: RecipesProps) => {
  const [recipes, setRecipes] = useState<Recipe[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedDifficulty, setSelectedDifficulty] = useState<string>('all');
  const [selectedSource, setSelectedSource] = useState<string>('all');

  useEffect(() => {
    const savedRecipes = storage.getRecipes();
    if (savedRecipes.length === 0) {
      // Initialize with mock data if no recipes exist
      storage.setRecipes(mockRecipes);
      setRecipes(mockRecipes);
    } else {
      setRecipes(savedRecipes);
    }
  }, []);

  const filteredRecipes = recipes.filter(recipe => {
    const matchesSearch = recipe.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         recipe.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         recipe.tags.some(tag => tag.toLowerCase().includes(searchTerm.toLowerCase()));
    
    const matchesDifficulty = selectedDifficulty === 'all' || recipe.difficulty === selectedDifficulty;
    const matchesSource = selectedSource === 'all' || recipe.source === selectedSource;
    
    return matchesSearch && matchesDifficulty && matchesSource;
  });

  const handleRecipeClick = (recipe: Recipe) => {
    if (onRecipeSelect) {
      onRecipeSelect(recipe);
    }
  };

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
              <h1 className="text-xl font-semibold">My Recipes</h1>
              <p className="text-sm text-gray-600">Your saved recipe collection</p>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Search and Filters */}
        <div className="mb-8 space-y-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
            <Input
              placeholder="Search recipes by name, description, or tags..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>

          <div className="flex flex-wrap gap-4">
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-gray-500" />
              <span className="text-sm font-medium text-gray-700">Filters:</span>
            </div>
            
            <select
              value={selectedDifficulty}
              onChange={(e) => setSelectedDifficulty(e.target.value)}
              className="px-3 py-1 border border-gray-300 rounded-md text-sm"
            >
              <option value="all">All Difficulties</option>
              <option value="easy">Easy</option>
              <option value="medium">Medium</option>
              <option value="hard">Hard</option>
            </select>

            <select
              value={selectedSource}
              onChange={(e) => setSelectedSource(e.target.value)}
              className="px-3 py-1 border border-gray-300 rounded-md text-sm"
            >
              <option value="all">All Sources</option>
              <option value="ai-generated">AI Generated</option>
              <option value="photo-analysis">Photo Analysis</option>
              <option value="community">Community</option>
            </select>
          </div>
        </div>

        {/* Recipe Grid */}
        {filteredRecipes.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredRecipes.map(recipe => (
              <Card 
                key={recipe.id} 
                className="cursor-pointer hover:shadow-lg transition-all duration-200 hover:scale-[1.02]"
                onClick={() => handleRecipeClick(recipe)}
              >
                <CardHeader>
                  <div className="flex justify-between items-start mb-2">
                    <CardTitle className="text-lg line-clamp-2">{recipe.title}</CardTitle>
                    <Badge variant="outline" className="ml-2 flex-shrink-0">
                      {recipe.difficulty}
                    </Badge>
                  </div>
                  <CardDescription className="line-clamp-2">
                    {recipe.description}
                  </CardDescription>
                </CardHeader>
                
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between text-sm text-gray-600">
                      <div className="flex items-center">
                        <Clock className="h-4 w-4 mr-1" />
                        {recipe.prepTime + recipe.cookTime} min
                      </div>
                      <div className="flex items-center">
                        <Users className="h-4 w-4 mr-1" />
                        {recipe.servings} servings
                      </div>
                    </div>

                    <div className="flex flex-wrap gap-1">
                      {recipe.tags.slice(0, 3).map(tag => (
                        <Badge key={tag} variant="secondary" className="text-xs">
                          {tag}
                        </Badge>
                      ))}
                      {recipe.tags.length > 3 && (
                        <Badge variant="secondary" className="text-xs">
                          +{recipe.tags.length - 3} more
                        </Badge>
                      )}
                    </div>

                    <div className="flex justify-between items-center">
                      <Badge variant="outline" className="text-xs">
                        {recipe.source === 'ai-generated' && 'AI Generated'}
                        {recipe.source === 'photo-analysis' && 'Photo Analysis'}
                        {recipe.source === 'community' && 'Community'}
                      </Badge>
                      <span className="text-xs text-gray-500">
                        {new Date(recipe.createdAt).toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <ChefHat className="h-12 w-12 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              {searchTerm || selectedDifficulty !== 'all' || selectedSource !== 'all' 
                ? 'No recipes match your filters' 
                : 'No recipes yet'
              }
            </h3>
            <p className="text-gray-600 mb-4">
              {searchTerm || selectedDifficulty !== 'all' || selectedSource !== 'all'
                ? 'Try adjusting your search or filters'
                : 'Start by adding your first recipe from the dashboard!'
              }
            </p>
            {(!searchTerm && selectedDifficulty === 'all' && selectedSource === 'all') && (
              <Button variant="outline" onClick={onBack}>
                Back to Dashboard
              </Button>
            )}
          </div>
        )}
      </div>
    </div>
  );
};