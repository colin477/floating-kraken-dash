import React, { useState, useEffect } from 'react';
import { Receipt } from '@/types';
import { receiptApi } from '@/services/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  ArrowLeft,
  Calendar,
  DollarSign,
  Store,
  ShoppingBag,
  Image as ImageIcon,
  Download,
  Trash2,
  Receipt as ReceiptIcon,
  ChefHat,
  Clock,
  Users,
  Lightbulb,
  Plus,
  Check,
  AlertCircle
} from 'lucide-react';
import { format } from 'date-fns';

interface ReceiptDetailProps {
  receipt: Receipt;
  onBack: () => void;
  onDelete?: (receiptId: string) => void;
}

export const ReceiptDetail: React.FC<ReceiptDetailProps> = ({
  receipt,
  onBack,
  onDelete
}) => {
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [imageLoading, setImageLoading] = useState(false);
  const [imageError, setImageError] = useState<string | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [recipeSuggestions, setRecipeSuggestions] = useState<any>(null);
  const [suggestionsLoading, setSuggestionsLoading] = useState(false);
  const [suggestionsError, setSuggestionsError] = useState<string | null>(null);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [selectedItems, setSelectedItems] = useState<number[]>([]);
  const [addingToPantry, setAddingToPantry] = useState(false);
  const [addToPantryError, setAddToPantryError] = useState<string | null>(null);
  const [addToPantrySuccess, setAddToPantrySuccess] = useState<string | null>(null);

  useEffect(() => {
    const fetchImageUrl = async () => {
      try {
        setImageLoading(true);
        setImageError(null);
        const response = await receiptApi.getReceiptImageUrl(receipt.id);
        setImageUrl(response.image_url);
      } catch (error) {
        console.error('Failed to fetch receipt image:', error);
        setImageError('Failed to load receipt image');
      } finally {
        setImageLoading(false);
      }
    };

    fetchImageUrl();
  }, [receipt.id]);

  const handleDelete = async () => {
    if (!onDelete) return;
    
    if (window.confirm('Are you sure you want to delete this receipt? This action cannot be undone.')) {
      setIsDeleting(true);
      try {
        await onDelete(receipt.id);
        onBack(); // Navigate back after successful deletion
      } catch (error) {
        console.error('Failed to delete receipt:', error);
      } finally {
        setIsDeleting(false);
      }
    }
  };

  const fetchRecipeSuggestions = async () => {
    if (!receipt.processed || !receipt.items.length) {
      setSuggestionsError('Receipt must be processed and have items to generate suggestions');
      return;
    }

    setSuggestionsLoading(true);
    setSuggestionsError(null);
    
    try {
      const suggestions = await receiptApi.getReceiptRecipeSuggestions(receipt.id, {
        max_suggestions: 5,
        min_match_percentage: 0.3,
        difficulty_level: 'easy'
      });
      
      setRecipeSuggestions(suggestions);
      setShowSuggestions(true);
    } catch (error) {
      console.error('Failed to fetch recipe suggestions:', error);
      setSuggestionsError('Failed to load recipe suggestions. Please try again.');
    } finally {
      setSuggestionsLoading(false);
    }
  };

  const handleItemSelection = (index: number) => {
    setSelectedItems(prev =>
      prev.includes(index)
        ? prev.filter(i => i !== index)
        : [...prev, index]
    );
  };

  const handleSelectAll = () => {
    if (selectedItems.length === receipt.items.length) {
      setSelectedItems([]);
    } else {
      setSelectedItems(receipt.items.map((_, index) => index));
    }
  };

  const handleAddToPantry = async () => {
    if (selectedItems.length === 0) {
      setAddToPantryError('Please select at least one item to add to pantry');
      return;
    }

    setAddingToPantry(true);
    setAddToPantryError(null);
    setAddToPantrySuccess(null);

    try {
      const result = await receiptApi.addReceiptItemsToPantry(receipt.id, {
        selected_items: selectedItems,
        expiration_days: 7 // Default to 7 days
      });

      setAddToPantrySuccess(
        `Successfully added ${result.items_added} items to pantry${
          result.items_failed > 0 ? ` (${result.items_failed} failed)` : ''
        }`
      );
      setSelectedItems([]); // Clear selection after successful add
      
      // Clear success message after 5 seconds
      setTimeout(() => setAddToPantrySuccess(null), 5000);
      
    } catch (error) {
      console.error('Failed to add items to pantry:', error);
      setAddToPantryError(error instanceof Error ? error.message : 'Failed to add items to pantry');
    } finally {
      setAddingToPantry(false);
    }
  };

  const formatDate = (dateString: string) => {
    try {
      return format(new Date(dateString), 'EEEE, MMMM dd, yyyy');
    } catch (error) {
      return dateString;
    }
  };

  const getCategoryColor = (category: string) => {
    const colors: Record<string, string> = {
      'produce': 'bg-green-100 text-green-800',
      'meat': 'bg-red-100 text-red-800',
      'dairy': 'bg-blue-100 text-blue-800',
      'grains': 'bg-yellow-100 text-yellow-800',
      'canned_goods': 'bg-orange-100 text-orange-800',
      'frozen': 'bg-cyan-100 text-cyan-800',
      'beverages': 'bg-purple-100 text-purple-800',
      'snacks': 'bg-pink-100 text-pink-800',
      'condiments': 'bg-indigo-100 text-indigo-800',
      'spices': 'bg-amber-100 text-amber-800',
      'seafood': 'bg-teal-100 text-teal-800',
      'other': 'bg-gray-100 text-gray-800'
    };
    return colors[category] || colors.other;
  };

  const categoryTotals = receipt.items.reduce((acc, item) => {
    acc[item.category] = (acc[item.category] || 0) + item.price;
    return acc;
  }, {} as Record<string, number>);

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-4">
            <Button
              variant="outline"
              size="sm"
              onClick={onBack}
              className="flex items-center gap-2"
            >
              <ArrowLeft className="h-4 w-4" />
              Back to Receipts
            </Button>
            <div className="flex items-center gap-2">
              <ReceiptIcon className="h-6 w-6 text-green-600" />
              <h1 className="text-2xl font-bold">Receipt Details</h1>
            </div>
          </div>
          
          {onDelete && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleDelete}
              disabled={isDeleting}
              className="text-red-600 hover:text-red-700 hover:bg-red-50"
            >
              <Trash2 className="h-4 w-4 mr-2" />
              {isDeleting ? 'Deleting...' : 'Delete Receipt'}
            </Button>
          )}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Receipt Image */}
          <div className="lg:col-span-1">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <ImageIcon className="h-5 w-5" />
                  Receipt Image
                </CardTitle>
              </CardHeader>
              <CardContent>
                {imageLoading && (
                  <div className="aspect-[3/4] bg-gray-100 rounded-lg flex items-center justify-center">
                    <div className="text-center">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-600 mx-auto mb-2"></div>
                      <p className="text-sm text-gray-600">Loading image...</p>
                    </div>
                  </div>
                )}
                
                {imageError && (
                  <div className="aspect-[3/4] bg-gray-100 rounded-lg flex items-center justify-center">
                    <div className="text-center text-gray-500">
                      <ImageIcon className="h-12 w-12 mx-auto mb-2" />
                      <p className="text-sm">{imageError}</p>
                    </div>
                  </div>
                )}
                
                {imageUrl && !imageLoading && !imageError && (
                  <div className="space-y-3">
                    <img
                      src={imageUrl}
                      alt="Receipt"
                      className="w-full aspect-[3/4] object-cover rounded-lg border"
                    />
                    <Button
                      variant="outline"
                      size="sm"
                      className="w-full"
                      onClick={() => window.open(imageUrl, '_blank')}
                    >
                      <Download className="h-4 w-4 mr-2" />
                      View Full Size
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Receipt Details */}
          <div className="lg:col-span-2 space-y-6">
            {/* Summary Card */}
            <Card>
              <CardHeader>
                <CardTitle>Receipt Summary</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-4">
                    <div className="flex items-center gap-3">
                      <Store className="h-5 w-5 text-gray-500" />
                      <div>
                        <p className="text-sm text-gray-600">Store</p>
                        <p className="font-semibold text-lg">{receipt.store}</p>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-3">
                      <Calendar className="h-5 w-5 text-gray-500" />
                      <div>
                        <p className="text-sm text-gray-600">Date</p>
                        <p className="font-semibold">{formatDate(receipt.date)}</p>
                      </div>
                    </div>
                  </div>
                  
                  <div className="space-y-4">
                    <div className="flex items-center gap-3">
                      <DollarSign className="h-5 w-5 text-gray-500" />
                      <div>
                        <p className="text-sm text-gray-600">Total Amount</p>
                        <p className="font-bold text-2xl text-green-600">${receipt.total.toFixed(2)}</p>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-3">
                      <ShoppingBag className="h-5 w-5 text-gray-500" />
                      <div>
                        <p className="text-sm text-gray-600">Items</p>
                        <p className="font-semibold">{receipt.items.length} items</p>
                      </div>
                    </div>
                  </div>
                </div>
                
                <div className="mt-4 pt-4 border-t">
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-sm text-gray-600">Status</span>
                    <Badge variant={receipt.processed ? "default" : "secondary"}>
                      {receipt.processed ? "Processed" : "Pending"}
                    </Badge>
                  </div>
                  
                  {/* Recipe Suggestions Button */}
                  {receipt.processed && receipt.items.length > 0 && (
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={fetchRecipeSuggestions}
                        disabled={suggestionsLoading}
                        className="flex-1"
                      >
                        {suggestionsLoading ? (
                          <>
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-green-600 mr-2"></div>
                            Loading...
                          </>
                        ) : (
                          <>
                            <ChefHat className="h-4 w-4 mr-2" />
                            Get Recipe Ideas
                          </>
                        )}
                      </Button>
                      {showSuggestions && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => setShowSuggestions(false)}
                        >
                          Hide
                        </Button>
                      )}
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Items List */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle>Items ({receipt.items.length})</CardTitle>
                  {receipt.processed && receipt.items.length > 0 && (
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={handleSelectAll}
                        className="text-xs"
                      >
                        {selectedItems.length === receipt.items.length ? 'Deselect All' : 'Select All'}
                      </Button>
                      <Button
                        variant="default"
                        size="sm"
                        onClick={handleAddToPantry}
                        disabled={addingToPantry || selectedItems.length === 0}
                        className="text-xs"
                      >
                        {addingToPantry ? (
                          <>
                            <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-white mr-1"></div>
                            Adding...
                          </>
                        ) : (
                          <>
                            <Plus className="h-3 w-3 mr-1" />
                            Add to Pantry ({selectedItems.length})
                          </>
                        )}
                      </Button>
                    </div>
                  )}
                </div>
                {(addToPantryError || addToPantrySuccess) && (
                  <div className="mt-2">
                    {addToPantryError && (
                      <div className="flex items-center gap-2 text-sm text-red-600 bg-red-50 p-2 rounded">
                        <AlertCircle className="h-4 w-4" />
                        {addToPantryError}
                      </div>
                    )}
                    {addToPantrySuccess && (
                      <div className="flex items-center gap-2 text-sm text-green-600 bg-green-50 p-2 rounded">
                        <Check className="h-4 w-4" />
                        {addToPantrySuccess}
                      </div>
                    )}
                  </div>
                )}
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {receipt.items.map((item, index) => (
                    <div
                      key={index}
                      className={`flex items-center justify-between p-3 rounded-lg border-2 transition-colors ${
                        selectedItems.includes(index)
                          ? 'bg-green-50 border-green-200'
                          : 'bg-gray-50 border-transparent hover:bg-gray-100'
                      } ${receipt.processed ? 'cursor-pointer' : ''}`}
                      onClick={() => receipt.processed && handleItemSelection(index)}
                    >
                      <div className="flex items-center gap-3 flex-1">
                        {receipt.processed && (
                          <div className={`w-4 h-4 rounded border-2 flex items-center justify-center ${
                            selectedItems.includes(index)
                              ? 'bg-green-500 border-green-500'
                              : 'border-gray-300'
                          }`}>
                            {selectedItems.includes(index) && (
                              <Check className="h-3 w-3 text-white" />
                            )}
                          </div>
                        )}
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="font-medium">{item.name}</span>
                            <Badge className={`text-xs ${getCategoryColor(item.category)}`}>
                              {item.category.replace('_', ' ')}
                            </Badge>
                          </div>
                          {item.quantity > 1 && (
                            <p className="text-sm text-gray-600">Quantity: {item.quantity}</p>
                          )}
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="font-semibold text-lg">${item.price.toFixed(2)}</p>
                        {item.quantity > 1 && (
                          <p className="text-sm text-gray-600">
                            ${(item.price / item.quantity).toFixed(2)} each
                          </p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
                {receipt.processed && receipt.items.length > 0 && (
                  <div className="mt-4 p-3 bg-blue-50 rounded-lg">
                    <p className="text-sm text-blue-800">
                      💡 <strong>Tip:</strong> Click on items to select them, then use "Add to Pantry" to add them to your pantry with a 7-day default expiration.
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Category Breakdown */}
            <Card>
              <CardHeader>
                <CardTitle>Spending by Category</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {Object.entries(categoryTotals)
                    .sort(([,a], [,b]) => b - a)
                    .map(([category, total]) => (
                      <div key={category} className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Badge className={`text-xs ${getCategoryColor(category)}`}>
                            {category.replace('_', ' ')}
                          </Badge>
                          <span className="text-sm text-gray-600">
                            ({receipt.items.filter(item => item.category === category).length} items)
                          </span>
                        </div>
                        <span className="font-semibold">${total.toFixed(2)}</span>
                      </div>
                    ))}
                </div>
              </CardContent>
            </Card>

            {/* Recipe Suggestions */}
            {showSuggestions && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Lightbulb className="h-5 w-5 text-yellow-500" />
                    Recipe Suggestions
                    {recipeSuggestions && (
                      <Badge variant="secondary" className="ml-2">
                        {recipeSuggestions.total_suggestions} found
                      </Badge>
                    )}
                  </CardTitle>
                  {recipeSuggestions?.receipt_store && (
                    <p className="text-sm text-gray-600">
                      Based on items from {recipeSuggestions.receipt_store}
                    </p>
                  )}
                </CardHeader>
                <CardContent>
                  {suggestionsError && (
                    <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
                      <p className="text-sm text-red-800">{suggestionsError}</p>
                    </div>
                  )}
                  
                  {recipeSuggestions?.suggestions && recipeSuggestions.suggestions.length > 0 ? (
                    <div className="space-y-4">
                      {recipeSuggestions.suggestions.map((suggestion: any, index: number) => (
                        <div key={index} className="border rounded-lg p-4 hover:bg-gray-50 transition-colors">
                          <div className="flex items-start justify-between mb-3">
                            <div className="flex-1">
                              <h4 className="font-semibold text-lg mb-1">{suggestion.recipe.name}</h4>
                              <p className="text-sm text-gray-600 mb-2">{suggestion.recipe.description}</p>
                              <div className="flex items-center gap-4 text-sm text-gray-500">
                                <div className="flex items-center gap-1">
                                  <Clock className="h-4 w-4" />
                                  {(suggestion.recipe.prep_time || 0) + (suggestion.recipe.cook_time || 0)} min
                                </div>
                                <div className="flex items-center gap-1">
                                  <Users className="h-4 w-4" />
                                  {suggestion.recipe.servings} servings
                                </div>
                                <Badge variant="outline" className="text-xs">
                                  {suggestion.recipe.difficulty}
                                </Badge>
                              </div>
                            </div>
                            <div className="text-right">
                              <div className="text-lg font-semibold text-green-600 mb-1">
                                {Math.round(suggestion.match_percentage)}% match
                              </div>
                              <div className="text-xs text-gray-500">
                                {suggestion.matched_ingredients}/{suggestion.matched_ingredients + suggestion.missing_ingredients} ingredients
                              </div>
                            </div>
                          </div>
                          
                          <div className="mb-3">
                            <p className="text-sm text-gray-700 italic">
                              "{suggestion.suggestion_reason}"
                            </p>
                          </div>
                          
                          {/* Ingredients Preview */}
                          <div className="border-t pt-3">
                            <h5 className="text-sm font-medium text-gray-700 mb-2">Key Ingredients:</h5>
                            <div className="flex flex-wrap gap-1">
                              {suggestion.recipe.ingredients.slice(0, 6).map((ingredient: any, idx: number) => (
                                <Badge key={idx} variant="secondary" className="text-xs">
                                  {ingredient.name}
                                </Badge>
                              ))}
                              {suggestion.recipe.ingredients.length > 6 && (
                                <Badge variant="outline" className="text-xs">
                                  +{suggestion.recipe.ingredients.length - 6} more
                                </Badge>
                              )}
                            </div>
                          </div>
                          
                          {/* Meal Types */}
                          {suggestion.recipe.meal_types && suggestion.recipe.meal_types.length > 0 && (
                            <div className="mt-2 pt-2 border-t">
                              <div className="flex items-center gap-2">
                                <span className="text-xs text-gray-500">Meal types:</span>
                                {suggestion.recipe.meal_types.map((type: string, idx: number) => (
                                  <Badge key={idx} variant="outline" className="text-xs capitalize">
                                    {type}
                                  </Badge>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  ) : recipeSuggestions && recipeSuggestions.suggestions.length === 0 ? (
                    <div className="text-center py-8 text-gray-500">
                      <ChefHat className="h-12 w-12 mx-auto mb-3 text-gray-300" />
                      <p className="text-sm">No recipe suggestions found for these items.</p>
                      <p className="text-xs mt-1">Try adjusting the filters or add more items to your receipt.</p>
                    </div>
                  ) : null}
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};