
import { useState, useEffect, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { ArrowLeft, Search, Plus, Trash2, Package, Calendar, X, ChevronDown, Edit, AlertTriangle, TestTube } from 'lucide-react';
import { PantryItem, PantryItemCreate, PantryItemUpdate, PantryCategory, PantryUnit, PantryItemsListResponse, ExpiringItemsResponse } from '@/types';
import { pantryApi } from '@/services/api';
import { useAuth } from '@/hooks/useAuth';
import { showSuccess, showError } from '@/utils/toast';
import { shouldBypassAuth, shouldShowDemoIndicator, isDemoModeEnabled } from '@/lib/demoMode';

interface PantryProps {
  onBack: () => void;
}

// Common grocery items for autocomplete
const COMMON_GROCERY_ITEMS = [
  'Apples', 'Bananas', 'Oranges', 'Lemons', 'Limes', 'Strawberries', 'Blueberries', 'Grapes',
  'Chicken breast', 'Ground beef', 'Salmon', 'Eggs', 'Bacon', 'Turkey', 'Pork chops', 'Shrimp',
  'Milk', 'Cheese', 'Yogurt', 'Butter', 'Cream cheese', 'Sour cream', 'Heavy cream',
  'Bread', 'Rice', 'Pasta', 'Flour', 'Sugar', 'Salt', 'Black pepper', 'Olive oil', 'Vegetable oil',
  'Onions', 'Garlic', 'Tomatoes', 'Potatoes', 'Carrots', 'Celery', 'Bell peppers', 'Broccoli',
  'Spinach', 'Lettuce', 'Cucumbers', 'Mushrooms', 'Avocados', 'Sweet potatoes',
  'Canned tomatoes', 'Chicken broth', 'Vegetable broth', 'Soy sauce', 'Hot sauce', 'Ketchup',
  'Mustard', 'Mayonnaise', 'Vinegar', 'Honey', 'Maple syrup', 'Vanilla extract',
  'Frozen peas', 'Frozen corn', 'Ice cream', 'Frozen berries', 'Frozen chicken',
  'Cereal', 'Oats', 'Peanut butter', 'Jelly', 'Crackers', 'Chips', 'Nuts', 'Almonds'
];

export const Pantry = ({ onBack }: PantryProps) => {
  const { isAuthenticated, user, isLoading: authLoading } = useAuth();
  
  // Demo mode bypass logic
  const demoModeEnabled = isDemoModeEnabled();
  const bypassAuth = shouldBypassAuth();
  const effectivelyAuthenticated = isAuthenticated || bypassAuth;
  
  console.log('[Pantry] Auth state:', {
    isAuthenticated,
    user,
    authLoading,
    demoModeEnabled,
    bypassAuth,
    effectivelyAuthenticated
  });
  const [pantryItems, setPantryItems] = useState<PantryItem[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [showAddForm, setShowAddForm] = useState(false);
  const [showEditForm, setShowEditForm] = useState(false);
  const [editingItem, setEditingItem] = useState<PantryItem | null>(null);
  const [showExpiringItems, setShowExpiringItems] = useState(false);
  const [expiringItems, setExpiringItems] = useState<ExpiringItemsResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [newItem, setNewItem] = useState<PantryItemCreate>({
    name: '',
    category: PantryCategory.OTHER,
    quantity: 1,
    unit: PantryUnit.PIECE,
    expiration_date: '',
    purchase_date: '',
    notes: ''
  });

  // Autocomplete state
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [filteredSuggestions, setFilteredSuggestions] = useState<string[]>([]);
  const [selectedSuggestionIndex, setSelectedSuggestionIndex] = useState(-1);
  const inputRef = useRef<HTMLInputElement>(null);
  const suggestionsRef = useRef<HTMLDivElement>(null);

  // Load pantry items on component mount
  useEffect(() => {
    if (effectivelyAuthenticated) {
      loadPantryItems();
    }
  }, [effectivelyAuthenticated]);

  // Filter suggestions based on input
  useEffect(() => {
    if (newItem.name.trim().length > 0) {
      const filtered = COMMON_GROCERY_ITEMS
        .filter(item => 
          item.toLowerCase().includes(newItem.name.toLowerCase())
        )
        .slice(0, 8);
      
      setFilteredSuggestions(filtered);
      setShowSuggestions(filtered.length > 0);
      setSelectedSuggestionIndex(-1);
    } else {
      setShowSuggestions(false);
      setFilteredSuggestions([]);
    }
  }, [newItem.name]);

  // Handle clicking outside to close suggestions
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        inputRef.current && 
        !inputRef.current.contains(event.target as Node) &&
        suggestionsRef.current &&
        !suggestionsRef.current.contains(event.target as Node)
      ) {
        setShowSuggestions(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const loadPantryItems = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const response: PantryItemsListResponse = await pantryApi.getItems({
        category: selectedCategory !== 'all' ? selectedCategory as PantryCategory : undefined,
        page_size: 100 // Load all items for now
      });
      setPantryItems(response.items);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load pantry items';
      setError(errorMessage);
      showError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const loadExpiringItems = async () => {
    try {
      setIsLoading(true);
      const response: ExpiringItemsResponse = await pantryApi.getExpiringItems(7);
      setExpiringItems(response);
      setShowExpiringItems(true);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load expiring items';
      showError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRemoveItem = async (itemId: string) => {
    try {
      await pantryApi.deleteItem(itemId);
      setPantryItems(prev => prev.filter(item => item.id !== itemId));
      showSuccess('Item removed from pantry');
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to remove item';
      showError(errorMessage);
    }
  };

  const handleAddItem = async () => {
    if (!newItem.name.trim()) {
      showError('Please enter an item name');
      return;
    }

    if (newItem.quantity <= 0) {
      showError('Please enter a valid quantity');
      return;
    }

    try {
      const itemData: PantryItemCreate = {
        ...newItem,
        name: newItem.name.trim(),
        expiration_date: newItem.expiration_date || undefined,
        purchase_date: newItem.purchase_date || undefined,
        notes: newItem.notes || undefined
      };

      const createdItem = await pantryApi.createItem(itemData);
      setPantryItems(prev => [...prev, createdItem]);

      // Reset form
      setNewItem({
        name: '',
        category: PantryCategory.OTHER,
        quantity: 1,
        unit: PantryUnit.PIECE,
        expiration_date: '',
        purchase_date: '',
        notes: ''
      });

      setShowAddForm(false);
      setShowSuggestions(false);
      showSuccess(`Added ${createdItem.name} to your pantry!`);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to add item';
      showError(errorMessage);
    }
  };

  const handleEditItem = async () => {
    if (!editingItem) return;

    try {
      const updateData: PantryItemUpdate = {
        name: editingItem.name.trim(),
        category: editingItem.category,
        quantity: editingItem.quantity,
        unit: editingItem.unit,
        expiration_date: editingItem.expiration_date || undefined,
        purchase_date: editingItem.purchase_date || undefined,
        notes: editingItem.notes || undefined
      };

      const updatedItem = await pantryApi.updateItem(editingItem.id, updateData);
      setPantryItems(prev => prev.map(item => 
        item.id === editingItem.id ? updatedItem : item
      ));

      setShowEditForm(false);
      setEditingItem(null);
      showSuccess(`Updated ${updatedItem.name}!`);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to update item';
      showError(errorMessage);
    }
  };

  const handleCancelAdd = () => {
    setNewItem({
      name: '',
      category: PantryCategory.OTHER,
      quantity: 1,
      unit: PantryUnit.PIECE,
      expiration_date: '',
      purchase_date: '',
      notes: ''
    });
    setShowAddForm(false);
    setShowSuggestions(false);
  };

  const handleCancelEdit = () => {
    setShowEditForm(false);
    setEditingItem(null);
  };

  const handleItemNameChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setNewItem(prev => ({ ...prev, name: e.target.value }));
  };

  const handleSuggestionClick = (suggestion: string) => {
    setNewItem(prev => ({ ...prev, name: suggestion }));
    setShowSuggestions(false);
    setSelectedSuggestionIndex(-1);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (!showSuggestions) return;

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedSuggestionIndex(prev => 
          prev < filteredSuggestions.length - 1 ? prev + 1 : prev
        );
        break;
      case 'ArrowUp':
        e.preventDefault();
        setSelectedSuggestionIndex(prev => prev > 0 ? prev - 1 : -1);
        break;
      case 'Enter':
        e.preventDefault();
        if (selectedSuggestionIndex >= 0) {
          handleSuggestionClick(filteredSuggestions[selectedSuggestionIndex]);
        }
        break;
      case 'Escape':
        setShowSuggestions(false);
        setSelectedSuggestionIndex(-1);
        break;
    }
  };

  const highlightMatch = (text: string, query: string) => {
    if (!query) return text;
    
    const index = text.toLowerCase().indexOf(query.toLowerCase());
    if (index === -1) return text;
    
    return (
      <>
        {text.substring(0, index)}
        <span className="bg-yellow-200 font-medium">
          {text.substring(index, index + query.length)}
        </span>
        {text.substring(index + query.length)}
      </>
    );
  };

  const filteredItems = pantryItems.filter(item => {
    const matchesSearch = item.name.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = selectedCategory === 'all' || item.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  const groupedItems = filteredItems.reduce((acc, item) => {
    const category = item.category.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
    if (!acc[category]) acc[category] = [];
    acc[category].push(item);
    return acc;
  }, {} as Record<string, PantryItem[]>);

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  const getExpirationStatus = (item: PantryItem) => {
    if (!item.expiration_date) return null;
    
    const daysUntil = item.days_until_expiration;
    if (daysUntil === null || daysUntil === undefined) return null;
    
    if (daysUntil < 0) return { status: 'expired', color: 'text-red-600', text: 'Expired' };
    if (daysUntil <= 3) return { status: 'critical', color: 'text-red-500', text: `${daysUntil} days left` };
    if (daysUntil <= 7) return { status: 'warning', color: 'text-orange-500', text: `${daysUntil} days left` };
    return { status: 'good', color: 'text-green-600', text: `${daysUntil} days left` };
  };

  if (!effectivelyAuthenticated) {
    console.log('[Pantry] Not authenticated and demo mode not bypassing auth, showing auth required message');
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Card className="w-full max-w-md">
          <CardHeader>
            <CardTitle>Authentication Required</CardTitle>
            <CardDescription>
              Please log in to access your pantry.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button onClick={onBack} className="w-full">
              Back to Dashboard
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Demo Mode Indicator */}
      {shouldShowDemoIndicator() && (
        <div className="bg-yellow-100 border-b border-yellow-200 px-4 py-2">
          <div className="max-w-6xl mx-auto flex items-center justify-center">
            <TestTube className="h-4 w-4 text-yellow-600 mr-2" />
            <span className="text-sm text-yellow-800 font-medium">
              🧪 Demo Mode Active - Testing without authentication
            </span>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                if (typeof window !== 'undefined') {
                  (window as any).disableDemoMode();
                  window.location.reload();
                }
              }}
              className="ml-4 text-yellow-700 hover:text-yellow-900 text-xs"
            >
              Disable Demo Mode
            </Button>
          </div>
        </div>
      )}

      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between py-4">
            <div className="flex items-center">
              <Button variant="ghost" onClick={onBack} className="mr-4">
                <ArrowLeft className="h-4 w-4" />
              </Button>
              <div>
                <div className="flex items-center">
                  <h1 className="text-xl font-semibold">My Pantry</h1>
                  {shouldShowDemoIndicator() && (
                    <Badge variant="secondary" className="ml-2 text-xs">
                      Demo
                    </Badge>
                  )}
                </div>
                <p className="text-sm text-gray-600">
                  {shouldShowDemoIndicator()
                    ? 'Testing pantry management features'
                    : 'Manage your virtual pantry items'
                  }
                </p>
              </div>
            </div>
            
            <div className="flex gap-2">
              <Button variant="outline" onClick={loadExpiringItems} disabled={isLoading}>
                <AlertTriangle className="h-4 w-4 mr-2" />
                Expiring Items
              </Button>
              
              <Dialog open={showAddForm} onOpenChange={setShowAddForm}>
                <DialogTrigger asChild>
                  <Button>
                    <Plus className="h-4 w-4 mr-2" />
                    Add Item
                  </Button>
                </DialogTrigger>
                <DialogContent className="sm:max-w-md">
                  <DialogHeader>
                    <DialogTitle>Add Pantry Item</DialogTitle>
                    <DialogDescription>
                      Add a new item to your virtual pantry
                    </DialogDescription>
                  </DialogHeader>
                  
                  <div className="space-y-4 py-4">
                    <div className="space-y-2">
                      <Label htmlFor="item-name">Item Name *</Label>
                      <div className="relative">
                        <Input
                          ref={inputRef}
                          id="item-name"
                          placeholder="Start typing to see suggestions..."
                          value={newItem.name}
                          onChange={handleItemNameChange}
                          onKeyDown={handleKeyDown}
                          onFocus={() => {
                            if (filteredSuggestions.length > 0) {
                              setShowSuggestions(true);
                            }
                          }}
                          autoComplete="off"
                        />
                        
                        {/* Autocomplete Dropdown */}
                        {showSuggestions && filteredSuggestions.length > 0 && (
                          <div
                            ref={suggestionsRef}
                            className="absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-48 overflow-y-auto"
                          >
                            {filteredSuggestions.map((suggestion, index) => (
                              <div
                                key={suggestion}
                                className={`px-3 py-2 cursor-pointer text-sm hover:bg-gray-100 ${
                                  index === selectedSuggestionIndex ? 'bg-blue-50 text-blue-700' : ''
                                }`}
                                onClick={() => handleSuggestionClick(suggestion)}
                                onMouseEnter={() => setSelectedSuggestionIndex(index)}
                              >
                                {highlightMatch(suggestion, newItem.name)}
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="category">Category *</Label>
                      <select
                        id="category"
                        value={newItem.category}
                        onChange={(e) => setNewItem(prev => ({ ...prev, category: e.target.value as PantryCategory }))}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      >
                        {Object.values(PantryCategory).map(category => (
                          <option key={category} value={category}>
                            {category.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                          </option>
                        ))}
                      </select>
                    </div>
                    
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="quantity">Quantity *</Label>
                        <Input
                          id="quantity"
                          type="number"
                          min="0.1"
                          step="0.1"
                          placeholder="1"
                          value={newItem.quantity}
                          onChange={(e) => setNewItem(prev => ({ ...prev, quantity: parseFloat(e.target.value) || 0 }))}
                        />
                      </div>
                      
                      <div className="space-y-2">
                        <Label htmlFor="unit">Unit</Label>
                        <select
                          id="unit"
                          value={newItem.unit}
                          onChange={(e) => setNewItem(prev => ({ ...prev, unit: e.target.value as PantryUnit }))}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        >
                          {Object.values(PantryUnit).map(unit => (
                            <option key={unit} value={unit}>{unit}</option>
                          ))}
                        </select>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="purchase-date">Purchase Date</Label>
                        <Input
                          id="purchase-date"
                          type="date"
                          value={newItem.purchase_date}
                          onChange={(e) => setNewItem(prev => ({ ...prev, purchase_date: e.target.value }))}
                        />
                      </div>
                      
                      <div className="space-y-2">
                        <Label htmlFor="expiration">Expiration Date</Label>
                        <Input
                          id="expiration"
                          type="date"
                          value={newItem.expiration_date}
                          onChange={(e) => setNewItem(prev => ({ ...prev, expiration_date: e.target.value }))}
                        />
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="notes">Notes</Label>
                      <Input
                        id="notes"
                        placeholder="Optional notes about this item..."
                        value={newItem.notes}
                        onChange={(e) => setNewItem(prev => ({ ...prev, notes: e.target.value }))}
                      />
                    </div>
                  </div>
                  
                  <div className="flex gap-3">
                    <Button onClick={handleAddItem} className="flex-1">
                      <Plus className="h-4 w-4 mr-2" />
                      Add to Pantry
                    </Button>
                    <Button variant="outline" onClick={handleCancelAdd} className="flex-1">
                      <X className="h-4 w-4 mr-2" />
                      Cancel
                    </Button>
                  </div>
                </DialogContent>
              </Dialog>
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
              placeholder="Search pantry items..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>

          <div className="flex items-center gap-4">
            <span className="text-sm font-medium text-gray-700">Filter by category:</span>
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="px-3 py-1 border border-gray-300 rounded-md text-sm"
            >
              <option value="all">All Categories</option>
              {Object.values(PantryCategory).map(category => (
                <option key={category} value={category}>
                  {category.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Loading State */}
        {isLoading && (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-2 text-gray-600">Loading pantry items...</p>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="text-center py-12">
            <div className="text-red-600 mb-4">
              <AlertTriangle className="h-8 w-8 mx-auto mb-2" />
              <p>{error}</p>
            </div>
            <Button onClick={loadPantryItems}>Try Again</Button>
          </div>
        )}

        {/* Expiring Items Modal */}
        <Dialog open={showExpiringItems} onOpenChange={setShowExpiringItems}>
          <DialogContent className="sm:max-w-2xl">
            <DialogHeader>
              <DialogTitle>Expiring Items</DialogTitle>
              <DialogDescription>
                Items that are expiring soon or have already expired
              </DialogDescription>
            </DialogHeader>
            
            {expiringItems && (
              <div className="space-y-4 max-h-96 overflow-y-auto">
                {expiringItems.expired.length > 0 && (
                  <div>
                    <h3 className="font-medium text-red-600 mb-2">Expired Items</h3>
                    <div className="space-y-2">
                      {expiringItems.expired.map(item => (
                        <div key={item.id} className="flex justify-between items-center p-2 bg-red-50 rounded">
                          <span>{item.name} ({item.quantity} {item.unit})</span>
                          <span className="text-red-600 text-sm">
                            Expired {Math.abs(item.days_until_expiration || 0)} days ago
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                
                {expiringItems.expiring_soon.length > 0 && (
                  <div>
                    <h3 className="font-medium text-orange-600 mb-2">Expiring Soon</h3>
                    <div className="space-y-2">
                      {expiringItems.expiring_soon.map(item => (
                        <div key={item.id} className="flex justify-between items-center p-2 bg-orange-50 rounded">
                          <span>{item.name} ({item.quantity} {item.unit})</span>
                          <span className="text-orange-600 text-sm">
                            {item.days_until_expiration} days left
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                
                {expiringItems.expired.length === 0 && expiringItems.expiring_soon.length === 0 && (
                  <p className="text-center text-gray-600 py-4">
                    No items are expiring soon. Great job managing your pantry!
                  </p>
                )}
              </div>
            )}
          </DialogContent>
        </Dialog>

        {/* Edit Item Modal */}
        <Dialog open={showEditForm} onOpenChange={setShowEditForm}>
          <DialogContent className="sm:max-w-md">
            <DialogHeader>
              <DialogTitle>Edit Pantry Item</DialogTitle>
              <DialogDescription>
                Update the details of your pantry item
              </DialogDescription>
            </DialogHeader>
            
            {editingItem && (
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <Label htmlFor="edit-name">Item Name *</Label>
                  <Input
                    id="edit-name"
                    value={editingItem.name}
                    onChange={(e) => setEditingItem(prev => prev ? { ...prev, name: e.target.value } : null)}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="edit-category">Category *</Label>
                  <select
                    id="edit-category"
                    value={editingItem.category}
                    onChange={(e) => setEditingItem(prev => prev ? { ...prev, category: e.target.value as PantryCategory } : null)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    {Object.values(PantryCategory).map(category => (
                      <option key={category} value={category}>
                        {category.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                      </option>
                    ))}
                  </select>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="edit-quantity">Quantity *</Label>
                    <Input
                      id="edit-quantity"
                      type="number"
                      min="0.1"
                      step="0.1"
                      value={editingItem.quantity}
                      onChange={(e) => setEditingItem(prev => prev ? { ...prev, quantity: parseFloat(e.target.value) || 0 } : null)}
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="edit-unit">Unit</Label>
                    <select
                      id="edit-unit"
                      value={editingItem.unit}
                      onChange={(e) => setEditingItem(prev => prev ? { ...prev, unit: e.target.value as PantryUnit } : null)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    >
                      {Object.values(PantryUnit).map(unit => (
                        <option key={unit} value={unit}>{unit}</option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="edit-purchase-date">Purchase Date</Label>
                    <Input
                      id="edit-purchase-date"
                      type="date"
                      value={editingItem.purchase_date || ''}
                      onChange={(e) => setEditingItem(prev => prev ? { ...prev, purchase_date: e.target.value } : null)}
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="edit-expiration">Expiration Date</Label>
                    <Input
                      id="edit-expiration"
                      type="date"
                      value={editingItem.expiration_date || ''}
                      onChange={(e) => setEditingItem(prev => prev ? { ...prev, expiration_date: e.target.value } : null)}
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="edit-notes">Notes</Label>
                  <Input
                    id="edit-notes"
                    placeholder="Optional notes about this item..."
                    value={editingItem.notes || ''}
                    onChange={(e) => setEditingItem(prev => prev ? { ...prev, notes: e.target.value } : null)}
                  />
                </div>
              </div>
            )}
            
            <div className="flex gap-3">
              <Button onClick={handleEditItem} className="flex-1">
                <Edit className="h-4 w-4 mr-2" />
                Update Item
              </Button>
              <Button variant="outline" onClick={handleCancelEdit} className="flex-1">
                <X className="h-4 w-4 mr-2" />
                Cancel
              </Button>
            </div>
          </DialogContent>
        </Dialog>

        {/* Pantry Items */}
        {!isLoading && !error && (
          <>
            {Object.keys(groupedItems).length > 0 ? (
              <div className="space-y-8">
                {Object.entries(groupedItems).map(([category, items]) => (
                  <div key={category}>
                    <h2 className="text-lg font-semibold text-gray-900 mb-4">{category}</h2>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                      {items.map(item => {
                        const expirationStatus = getExpirationStatus(item);
                        return (
                          <Card key={item.id} className="hover:shadow-md transition-shadow">
                            <CardContent className="p-4">
                              <div className="flex justify-between items-start mb-3">
                                <div className="flex items-center">
                                  <Package className="h-5 w-5 text-gray-400 mr-2" />
                                  <h3 className="font-medium text-gray-900">{item.name}</h3>
                                </div>
                                <div className="flex gap-1">
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => {
                                      setEditingItem(item);
                                      setShowEditForm(true);
                                    }}
                                    className="text-blue-600 hover:text-blue-700 hover:bg-blue-50"
                                  >
                                    <Edit className="h-4 w-4" />
                                  </Button>
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => handleRemoveItem(item.id)}
                                    className="text-red-600 hover:text-red-700 hover:bg-red-50"
                                  >
                                    <Trash2 className="h-4 w-4" />
                                  </Button>
                                </div>
                              </div>
                              
                              <div className="space-y-2">
                                <div className="flex justify-between text-sm">
                                  <span className="text-gray-600">Category:</span>
                                  <span className="font-medium">
                                    {item.category.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                                  </span>
                                </div>
                                
                                <div className="flex justify-between text-sm">
                                  <span className="text-gray-600">Quantity:</span>
                                  <span className="font-medium">{item.quantity} {item.unit}</span>
                                </div>
                                
                                <div className="flex justify-between text-sm">
                                  <span className="text-gray-600">Added:</span>
                                  <span className="text-gray-500">
                                    {formatDate(item.created_at)}
                                  </span>
                                </div>
                                
                                {item.purchase_date && (
                                  <div className="flex justify-between text-sm">
                                    <span className="text-gray-600">Purchased:</span>
                                    <span className="text-gray-500">
                                      {formatDate(item.purchase_date)}
                                    </span>
                                  </div>
                                )}
                                
                                {item.expiration_date && (
                                  <div className="flex justify-between text-sm">
                                    <span className="text-gray-600">Expires:</span>
                                    <span className={`flex items-center ${expirationStatus?.color || 'text-gray-500'}`}>
                                      <Calendar className="h-3 w-3 mr-1" />
                                      {formatDate(item.expiration_date)}
                                      {expirationStatus && (
                                        <span className="ml-2 text-xs">
                                          ({expirationStatus.text})
                                        </span>
                                      )}
                                    </span>
                                  </div>
                                )}
                                
                                {item.notes && (
                                  <div className="text-sm">
                                    <span className="text-gray-600">Notes:</span>
                                    <p className="text-gray-500 mt-1">{item.notes}</p>
                                  </div>
                                )}
                                
                                <Badge
                                  variant="secondary"
                                  className="text-xs"
                                >
                                  {item.category.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                                </Badge>
                              </div>
                            </CardContent>
                          </Card>
                        );
                      })}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12">
                <Package className="h-12 w-12 text-gray-300 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  {searchTerm || selectedCategory !== 'all'
                    ? 'No items match your search'
                    : 'Your pantry is empty'
                  }
                </h3>
                <p className="text-gray-600 mb-4">
                  {searchTerm || selectedCategory !== 'all'
                    ? 'Try adjusting your search or filters'
                    : 'Start by adding items to your pantry!'
                  }
                </p>
                {(!searchTerm && selectedCategory === 'all') && (
                  <div className="space-x-4">
                    <Button onClick={() => setShowAddForm(true)}>
                      <Plus className="h-4 w-4 mr-2" />
                      Add Item Manually
                    </Button>
                    <Button variant="outline" onClick={onBack}>
                      Back to Dashboard
                    </Button>
                  </div>
                )}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};