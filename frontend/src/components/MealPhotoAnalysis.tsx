import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ArrowLeft, Camera, Upload, Loader2, Check, Clock, Users } from 'lucide-react';
import { simulateMealPhotoAnalysis } from '@/lib/mockData';
import { storage } from '@/lib/storage';
import { Recipe } from '@/types';
import { showSuccess } from '@/utils/toast';

interface MealPhotoAnalysisProps {
  onBack: () => void;
}

export const MealPhotoAnalysis = ({ onBack }: MealPhotoAnalysisProps) => {
  const [isProcessing, setIsProcessing] = useState(false);
  const [analyzedRecipe, setAnalyzedRecipe] = useState<Recipe | null>(null);
  const [step, setStep] = useState<'upload' | 'processing' | 'review' | 'complete'>('upload');
  const [uploadedImage, setUploadedImage] = useState<string>('');

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const imageUrl = URL.createObjectURL(file);
    setUploadedImage(imageUrl);
    setStep('processing');
    setIsProcessing(true);

    try {
      // Simulate AI processing
      const recipe = await simulateMealPhotoAnalysis(imageUrl);
      setAnalyzedRecipe(recipe);
      setStep('review');
    } catch (error) {
      console.error('Error analyzing meal photo:', error);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleSaveRecipe = () => {
    if (analyzedRecipe) {
      storage.addRecipe(analyzedRecipe);
      setStep('complete');
      showSuccess('Recipe saved to your collection!');
    }
  };

  const renderUploadStep = () => (
    <div className="text-center space-y-6">
      <div className="mx-auto w-24 h-24 bg-blue-100 rounded-full flex items-center justify-center">
        <Camera className="h-12 w-12 text-blue-600" />
      </div>
      
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Analyze Your Meal</h2>
        <p className="text-gray-600">
          Take a photo of any prepared meal and our AI will identify ingredients, quantities, and cooking methods to create a complete recipe.
        </p>
      </div>

      <div className="space-y-4">
        <label className="block">
          <input
            type="file"
            accept="image/*"
            capture="environment"
            onChange={handleFileUpload}
            className="hidden"
          />
          <Button className="w-full" size="lg">
            <Camera className="h-5 w-5 mr-2" />
            Take Photo
          </Button>
        </label>

        <label className="block">
          <input
            type="file"
            accept="image/*"
            onChange={handleFileUpload}
            className="hidden"
          />
          <Button variant="outline" className="w-full" size="lg">
            <Upload className="h-5 w-5 mr-2" />
            Upload Image
          </Button>
        </label>
      </div>

      <div className="text-sm text-gray-500">
        <p>Tips for best results:</p>
        <ul className="mt-2 space-y-1">
          <li>• Ensure the meal is well-lit and clearly visible</li>
          <li>• Include all components of the dish in the photo</li>
          <li>• Avoid shadows or reflections</li>
        </ul>
      </div>
    </div>
  );

  const renderProcessingStep = () => (
    <div className="text-center space-y-6">
      {uploadedImage && (
        <div className="mx-auto w-48 h-48 rounded-lg overflow-hidden">
          <img src={uploadedImage} alt="Uploaded meal" className="w-full h-full object-cover" />
        </div>
      )}
      
      <div className="mx-auto w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center">
        <Loader2 className="h-8 w-8 text-blue-600 animate-spin" />
      </div>
      
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Analyzing Your Meal</h2>
        <p className="text-gray-600">
          Our AI is identifying ingredients, estimating quantities, and determining cooking methods...
        </p>
      </div>

      <div className="space-y-2">
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div className="bg-blue-600 h-2 rounded-full animate-pulse" style={{ width: '75%' }} />
        </div>
        <p className="text-sm text-gray-500">This may take 20-45 seconds</p>
      </div>
    </div>
  );

  const renderReviewStep = () => {
    if (!analyzedRecipe) return null;

    return (
      <div className="space-y-6">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Recipe Generated!</h2>
          <p className="text-gray-600">
            Here's what our AI identified from your meal photo. You can save this recipe to your collection.
          </p>
        </div>

        <Card>
          <CardHeader>
            <div className="flex justify-between items-start">
              <div>
                <CardTitle className="text-xl">{analyzedRecipe.title}</CardTitle>
                <CardDescription className="mt-2">{analyzedRecipe.description}</CardDescription>
              </div>
              {uploadedImage && (
                <img src={uploadedImage} alt="Analyzed meal" className="w-20 h-20 rounded-lg object-cover" />
              )}
            </div>
            
            <div className="flex items-center gap-4 mt-4">
              <div className="flex items-center text-sm text-gray-600">
                <Clock className="h-4 w-4 mr-1" />
                {analyzedRecipe.prepTime + analyzedRecipe.cookTime} min
              </div>
              <div className="flex items-center text-sm text-gray-600">
                <Users className="h-4 w-4 mr-1" />
                {analyzedRecipe.servings} servings
              </div>
              <Badge variant="outline">{analyzedRecipe.difficulty}</Badge>
            </div>
          </CardHeader>
          
          <CardContent className="space-y-6">
            <div>
              <h4 className="font-semibold mb-3">Ingredients</h4>
              <div className="grid gap-2">
                {analyzedRecipe.ingredients.map((ingredient, index) => (
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
                {analyzedRecipe.instructions.map((instruction, index) => (
                  <li key={index} className="flex">
                    <span className="flex-shrink-0 w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm font-medium mr-3">
                      {index + 1}
                    </span>
                    <span className="text-gray-700">{instruction}</span>
                  </li>
                ))}
              </ol>
            </div>

            {analyzedRecipe.nutritionInfo && (
              <div>
                <h4 className="font-semibold mb-3">Nutrition (per serving)</h4>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>Calories: {analyzedRecipe.nutritionInfo.calories}</div>
                  <div>Protein: {analyzedRecipe.nutritionInfo.protein}g</div>
                  <div>Carbs: {analyzedRecipe.nutritionInfo.carbs}g</div>
                  <div>Fat: {analyzedRecipe.nutritionInfo.fat}g</div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        <div className="flex gap-3">
          <Button variant="outline" onClick={() => setStep('upload')} className="flex-1">
            Analyze Another
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
      <div className="mx-auto w-24 h-24 bg-green-100 rounded-full flex items-center justify-center">
        <Check className="h-12 w-12 text-green-600" />
      </div>
      
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Recipe Saved!</h2>
        <p className="text-gray-600">
          Your analyzed recipe has been added to your collection. You can now use it in meal planning or share it with the community.
        </p>
      </div>

      <div className="space-y-3">
        <Button onClick={onBack} className="w-full" size="lg">
          Back to Dashboard
        </Button>
        <Button variant="outline" onClick={() => setStep('upload')} className="w-full">
          Analyze Another Meal
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
              <h1 className="text-xl font-semibold">Meal Photo Analysis</h1>
              <p className="text-sm text-gray-600">AI-powered recipe extraction from meal photos</p>
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Card>
          <CardContent className="p-8">
            {step === 'upload' && renderUploadStep()}
            {step === 'processing' && renderProcessingStep()}
            {step === 'review' && renderReviewStep()}
            {step === 'complete' && renderCompleteStep()}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};