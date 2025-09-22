import { useState, useEffect, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { ArrowLeft, Search, Plus, Trash2, Package, Calendar, X, ChevronDown } from 'lucide-react';
import { PantryItem } from '@/types';
import { storage } from '@/lib/storage';
import { showSuccess, showError } from '@/utils/toast';

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
  const [pantryItems, setPantryItems] = useState<PantryItem[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedSource, setSelectedSource] = useState<string>('all');
  const [showAddForm, setShowAddForm] = useState(false);
  const [newItem, setNewItem] = useState({
    name: '',
    quantity: '',
    unit: 'pieces',
    expirationDate: ''
  });

  // Autocomplete state
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [filteredSuggestions, setFilteredSuggestions] = useState<string[]>([]);
  const [selectedSuggestionIndex, setSelectedSuggestionIndex] = useState(-1);
  const inputRef = useRef<HTMLInputElement>(null);
  const suggestionsRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setPantryItems(storage.getPantryItems());
  }, []);

  // Filter suggestions based on input
  useEffect(() => {
    if (newItem.name.trim().length > 0) {
      const filtered = COMMON_GROCERY_ITEMS
        .filter(item => 
          item.toLowerCase().includes(newItem.name.toLowerCase())
        )
        .slice(0, 8); // Limit to 8 suggestions
      
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

  const filteredItems = pantryItems.filter(item => {
    const matchesSearch = item.name.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesSource = selectedSource === 'all' || item.source === selectedSource;
    return matchesSearch && matchesSource;
  });

  const handleRemoveItem = (itemId: string) => {
    const updatedItems = pantryItems.filter(item => item.id !== itemId);
    setPantryItems(updatedItems);
    storage.setPantryItems(updatedItems);
    showSuccess('Item removed from pantry');
  };

  const handleAddItem = () => {
    if (!newItem.name.trim()) {
      showError('Please enter an item name');
      return;
    }

    if (!newItem.quantity || Number(newItem.quantity) <= 0) {
      showError('Please enter a valid quantity');
      return;
    }

    const pantryItem: PantryItem = {
      id: Date.now().toString() + Math.random(),
      name: newItem.name.trim(),
      quantity: Number(newItem.quantity),
      unit: newItem.unit,
      expirationDate: newItem.expirationDate || undefined,
      source: 'manual',
      addedAt: new Date().toISOString()
    };

    const updatedItems = [...pantryItems, pantryItem];
    setPantryItems(updatedItems);
    storage.setPantryItems(updatedItems);

    // Reset form
    setNewItem({
      name: '',
      quantity: '',
      unit: 'pieces',
      expirationDate: ''
    });

    setShowAddForm(false);
    setShowSuggestions(false);
    showSuccess(`Added ${pantryItem.name} to your pantry!`);
  };

  const handleCancelAdd = () => {
    setNewItem({
      name: '',
      quantity: '',
      unit: 'pieces',
      expirationDate: ''
    });
    setShowAddForm(false);
    setShowSuggestions(false);
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

  const groupedItems = filteredItems.reduce((acc, item) => {
    const source = item.source === 'receipt' ? 'From Receipts' : 'Added Manually';
    if (!acc[source]) acc[source] = [];
    acc[source].push(item);
    return acc;
  }, {} as Record<string, PantryItem[]>);

  const commonUnits = [
    'pieces', 'lbs', 'oz', 'cups', 'tbsp', 'tsp', 'gallons', 'quarts', 'pints', 
    'liters', 'ml', 'kg', 'g', 'cans', 'bottles', 'boxes', 'bags', 'packages'
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between py-4">
            <div className="flex items-center">
              <Button variant="ghost" onClick={onBack} className="mr-4">
                <ArrowLeft className="h-4 w-4" />
              </Button>
              <div>
                <h1 className="text-xl font-semibold">My Pantry</h1>
                <p className="text-sm text-gray-600">Manage your virtual pantry items</p>
              </div>
            </div>
            
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
                    Manually add an item to your virtual pantry
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
                    <p className="text-xs text-gray-500">
                      Start typing to see suggestions, or enter a custom item name
                    </p>
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
                        onChange={(e) => setNewItem(prev => ({ ...prev, quantity: e.target.value }))}
                      />
                    </div>
                    
                    <div className="space-y-2">
                      <Label htmlFor="unit">Unit</Label>
                      <select
                        id="unit"
                        value={newItem.unit}
                        onChange={(e) => setNewItem(prev => ({ ...prev, unit: e.target.value }))}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      >
                        {commonUnits.map(unit => (
                          <option key={unit} value={unit}>{unit}</option>
                        ))}
                      </select>
                    </div>
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="expiration">Expiration Date (Optional)</Label>
                    <Input
                      id="expiration"
                      type="date"
                      value={newItem.expirationDate}
                      onChange={(e) => setNewItem(prev => ({ ...prev, expirationDate: e.target.value }))}
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
            <span className="text-sm font-medium text-gray-700">Filter by source:</span>
            <select
              value={selectedSource}
              onChange={(e) => setSelectedSource(e.target.value)}
              className="px-3 py-1 border border-gray-300 rounded-md text-sm"
            >
              <option value="all">All Sources</option>
              <option value="receipt">From Receipts</option>
              <option value="manual">Added Manually</option>
            </select>
          </div>
        </div>

        {/* Pantry Items */}
        {Object.keys(groupedItems).length > 0 ? (
          <div className="space-y-8">
            {Object.entries(groupedItems).map(([source, items]) => (
              <div key={source}>
                <h2 className="text-lg font-semibold text-gray-900 mb-4">{source}</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {items.map(item => (
                    <Card key={item.id} className="hover:shadow-md transition-shadow">
                      <CardContent className="p-4">
                        <div className="flex justify-between items-start mb-3">
                          <div className="flex items-center">
                            <Package className="h-5 w-5 text-gray-400 mr-2" />
                            <h3 className="font-medium text-gray-900">{item.name}</h3>
                          </div>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleRemoveItem(item.id)}
                            className="text-red-600 hover:text-red-700 hover:bg-red-50"
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                        
                        <div className="space-y-2">
                          <div className="flex justify-between text-sm">
                            <span className="text-gray-600">Quantity:</span>
                            <span className="font-medium">{item.quantity} {item.unit}</span>
                          </div>
                          
                          <div className="flex justify-between text-sm">
                            <span className="text-gray-600">Added:</span>
                            <span className="text-gray-500">
                              {new Date(item.addedAt).toLocaleDateString()}
                            </span>
                          </div>
                          
                          {item.expirationDate && (
                            <div className="flex justify-between text-sm">
                              <span className="text-gray-600">Expires:</span>
                              <span className="text-orange-600 flex items-center">
                                <Calendar className="h-3 w-3 mr-1" />
                                {new Date(item.expirationDate).toLocaleDateString()}
                              </span>
                            </div>
                          )}
                          
                          <Badge 
                            variant={item.source === 'receipt' ? 'default' : 'secondary'} 
                            className="text-xs"
                          >
                            {item.source === 'receipt' ? 'Receipt Scan' : 'Manual Entry'}
                          </Badge>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <Package className="h-12 w-12 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              {searchTerm || selectedSource !== 'all' 
                ? 'No items match your search' 
                : 'Your pantry is empty'
              }
            </h3>
            <p className="text-gray-600 mb-4">
              {searchTerm || selectedSource !== 'all'
                ? 'Try adjusting your search or filters'
                : 'Start by scanning a grocery receipt or adding items manually!'
              }
            </p>
            {(!searchTerm && selectedSource === 'all') && (
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
      </div>
    </div>
  );
};