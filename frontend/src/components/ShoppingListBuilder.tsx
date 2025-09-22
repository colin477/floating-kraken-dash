import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import { ArrowLeft, Plus, Trash2, ShoppingCart, Store, DollarSign, Check, X, Edit, ChevronDown, Copy, FolderPlus } from 'lucide-react';
import { ShoppingListItem } from '@/types';
import { storage } from '@/lib/storage';
import { showSuccess, showError } from '@/utils/toast';

interface ShoppingListBuilderProps {
  onBack: () => void;
  initialListId?: string | null;
}

interface SavedShoppingList {
  id: string;
  name: string;
  items: ShoppingListItem[];
  createdAt: string;
  updatedAt: string;
}

const GROCERY_STORES = [
  'Kroger', 'Walmart', 'Target', 'Whole Foods', 'Safeway', 'Publix', 'Costco', 'Sam\'s Club', 'Aldi', 'Other'
];

const ITEM_CATEGORIES = [
  'produce', 'meat', 'dairy', 'pantry', 'frozen', 'bakery', 'deli', 'beverages', 'snacks', 'household', 'other'
];

const STORAGE_KEY = 'ez-eatin-shopping-lists';
const CURRENT_LIST_KEY = 'ez-eatin-current-list-id';

export const ShoppingListBuilder = ({ onBack, initialListId }: ShoppingListBuilderProps) => {
  const [savedLists, setSavedLists] = useState<SavedShoppingList[]>([]);
  const [currentListId, setCurrentListId] = useState<string>('');
  const [currentList, setCurrentList] = useState<SavedShoppingList | null>(null);
  const [shoppingList, setShoppingList] = useState<ShoppingListItem[]>([]);
  const [newItem, setNewItem] = useState({
    name: '',
    quantity: '',
    unit: 'pieces',
    estimatedPrice: '',
    store: 'Kroger',
    category: 'other'
  });
  const [selectedStore, setSelectedStore] = useState<string>('all');
  const [totalCost, setTotalCost] = useState(0);
  
  // List management state
  const [showCreateList, setShowCreateList] = useState(false);
  const [showRenameList, setShowRenameList] = useState(false);
  const [newListName, setNewListName] = useState('');
  const [renameListName, setRenameListName] = useState('');

  // Load saved lists and current list on component mount
  useEffect(() => {
    loadSavedLists();
  }, []);

  // Handle initial list selection if provided
  useEffect(() => {
    if (initialListId && savedLists.length > 0) {
      const targetList = savedLists.find(list => list.id === initialListId);
      if (targetList) {
        setCurrentListId(initialListId);
        setCurrentList(targetList);
        localStorage.setItem(CURRENT_LIST_KEY, initialListId);
      }
    }
  }, [initialListId, savedLists]);

  // Update shopping list when current list changes
  useEffect(() => {
    if (currentList) {
      setShoppingList(currentList.items);
      setRenameListName(currentList.name);
    }
  }, [currentList]);

  // Calculate total cost and save list when shopping list changes
  useEffect(() => {
    const total = shoppingList.reduce((sum, item) => sum + item.estimatedPrice, 0);
    setTotalCost(total);
    
    // Auto-save current list
    if (currentList) {
      saveCurrentList();
    }
  }, [shoppingList]);

  const loadSavedLists = () => {
    // Load saved lists
    const saved = localStorage.getItem(STORAGE_KEY);
    let lists: SavedShoppingList[] = saved ? JSON.parse(saved) : [];
    
    // Migration: Check for old single list format
    const oldList = localStorage.getItem('current-shopping-list');
    if (oldList && lists.length === 0) {
      const oldItems: ShoppingListItem[] = JSON.parse(oldList);
      if (oldItems.length > 0) {
        const migratedList: SavedShoppingList = {
          id: 'migrated-list',
          name: 'My Shopping List',
          items: oldItems,
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString()
        };
        lists = [migratedList];
        localStorage.setItem(STORAGE_KEY, JSON.stringify(lists));
        localStorage.removeItem('current-shopping-list');
      }
    }
    
    setSavedLists(lists);
    
    // Load current list ID (only if no initialListId provided)
    if (!initialListId) {
      const currentId = localStorage.getItem(CURRENT_LIST_KEY);
      if (currentId && lists.find(list => list.id === currentId)) {
        setCurrentListId(currentId);
        setCurrentList(lists.find(list => list.id === currentId) || null);
      } else if (lists.length > 0) {
        // Default to first list if no current list set
        setCurrentListId(lists[0].id);
        setCurrentList(lists[0]);
        localStorage.setItem(CURRENT_LIST_KEY, lists[0].id);
      } else {
        // Create default list if none exist
        createDefaultList();
      }
    }
  };

  const createDefaultList = () => {
    const defaultList: SavedShoppingList = {
      id: Date.now().toString(),
      name: 'My Shopping List',
      items: [],
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    };
    
    const newLists = [defaultList];
    setSavedLists(newLists);
    setCurrentListId(defaultList.id);
    setCurrentList(defaultList);
    
    localStorage.setItem(STORAGE_KEY, JSON.stringify(newLists));
    localStorage.setItem(CURRENT_LIST_KEY, defaultList.id);
  };

  const saveCurrentList = () => {
    if (!currentList) return;
    
    const updatedList = {
      ...currentList,
      items: shoppingList,
      updatedAt: new Date().toISOString()
    };
    
    const updatedLists = savedLists.map(list => 
      list.id === currentList.id ? updatedList : list
    );
    
    setSavedLists(updatedLists);
    setCurrentList(updatedList);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updatedLists));
  };

  const handleCreateList = () => {
    if (!newListName.trim()) {
      showError('Please enter a list name');
      return;
    }

    const newList: SavedShoppingList = {
      id: Date.now().toString(),
      name: newListName.trim(),
      items: [],
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    };

    const updatedLists = [...savedLists, newList];
    setSavedLists(updatedLists);
    setCurrentListId(newList.id);
    setCurrentList(newList);
    
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updatedLists));
    localStorage.setItem(CURRENT_LIST_KEY, newList.id);
    
    setNewListName('');
    setShowCreateList(false);
    showSuccess(`Created "${newList.name}" shopping list!`);
  };

  const handleSelectList = (listId: string) => {
    const list = savedLists.find(l => l.id === listId);
    if (list) {
      setCurrentListId(listId);
      setCurrentList(list);
      localStorage.setItem(CURRENT_LIST_KEY, listId);
    }
  };

  const handleRenameList = () => {
    if (!renameListName.trim() || !currentList) {
      showError('Please enter a valid list name');
      return;
    }

    const updatedList = {
      ...currentList,
      name: renameListName.trim(),
      updatedAt: new Date().toISOString()
    };

    const updatedLists = savedLists.map(list => 
      list.id === currentList.id ? updatedList : list
    );

    setSavedLists(updatedLists);
    setCurrentList(updatedList);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updatedLists));
    
    setShowRenameList(false);
    showSuccess(`Renamed list to "${updatedList.name}"`);
  };

  const handleDuplicateList = () => {
    if (!currentList) return;

    const duplicatedList: SavedShoppingList = {
      id: Date.now().toString(),
      name: `${currentList.name} (Copy)`,
      items: currentList.items.map(item => ({ ...item, id: Date.now().toString() + Math.random() })),
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    };

    const updatedLists = [...savedLists, duplicatedList];
    setSavedLists(updatedLists);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updatedLists));
    
    showSuccess(`Duplicated "${currentList.name}"`);
  };

  const handleDeleteList = () => {
    if (!currentList || savedLists.length <= 1) {
      showError('Cannot delete the last shopping list');
      return;
    }

    const updatedLists = savedLists.filter(list => list.id !== currentList.id);
    setSavedLists(updatedLists);
    
    // Switch to first remaining list
    const newCurrentList = updatedLists[0];
    setCurrentListId(newCurrentList.id);
    setCurrentList(newCurrentList);
    
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updatedLists));
    localStorage.setItem(CURRENT_LIST_KEY, newCurrentList.id);
    
    showSuccess(`Deleted "${currentList.name}"`);
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

    const item: ShoppingListItem = {
      id: Date.now().toString() + Math.random(),
      name: newItem.name.trim(),
      quantity: Number(newItem.quantity),
      unit: newItem.unit,
      estimatedPrice: Number(newItem.estimatedPrice) || 0,
      store: newItem.store,
      category: newItem.category,
      purchased: false
    };

    setShoppingList(prev => [...prev, item]);
    
    // Reset form
    setNewItem({
      name: '',
      quantity: '',
      unit: 'pieces',
      estimatedPrice: '',
      store: newItem.store, // Keep the same store
      category: 'other'
    });

    showSuccess(`Added ${item.name} to your shopping list!`);
  };

  const handleRemoveItem = (itemId: string) => {
    setShoppingList(prev => prev.filter(item => item.id !== itemId));
    showSuccess('Item removed from shopping list');
  };

  const handleTogglePurchased = (itemId: string) => {
    setShoppingList(prev => 
      prev.map(item => 
        item.id === itemId 
          ? { ...item, purchased: !item.purchased }
          : item
      )
    );
  };

  const handleClearList = () => {
    setShoppingList([]);
    showSuccess('Shopping list cleared');
  };

  const handleExportList = () => {
    if (!currentList) return;
    
    const listText = shoppingList
      .filter(item => selectedStore === 'all' || item.store === selectedStore)
      .map(item => `${item.purchased ? '✓' : '☐'} ${item.name} - ${item.quantity} ${item.unit} (${item.store})`)
      .join('\n');
    
    const fullText = `${currentList.name}\n\nTotal Items: ${shoppingList.length}\nEstimated Cost: $${totalCost.toFixed(2)}\n\n${listText}`;
    
    navigator.clipboard.writeText(fullText);
    showSuccess('Shopping list copied to clipboard!');
  };

  const filteredItems = shoppingList.filter(item => 
    selectedStore === 'all' || item.store === selectedStore
  );

  const groupedItems = filteredItems.reduce((acc, item) => {
    if (!acc[item.store]) acc[item.store] = [];
    acc[item.store].push(item);
    
    return acc;
  }, {} as Record<string, ShoppingListItem[]>);

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
                <h1 className="text-xl font-semibold">
                  {initialListId ? 'Edit Shopping List' : 'Shopping Lists'}
                </h1>
                <p className="text-sm text-gray-600">
                  {initialListId ? 'Modify your existing shopping list' : 'Create and manage multiple shopping lists'}
                </p>
              </div>
            </div>
            
            {/* List Selector and Actions */}
            <div className="flex items-center gap-3">
              {/* Current List Selector */}
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="outline" className="min-w-[200px] justify-between">
                    <span className="truncate">{currentList?.name || 'Select List'}</span>
                    <ChevronDown className="h-4 w-4 ml-2" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-64">
                  <div className="px-2 py-1.5 text-sm font-medium text-gray-700">
                    Your Shopping Lists
                  </div>
                  <DropdownMenuSeparator />
                  {savedLists.map(list => (
                    <DropdownMenuItem
                      key={list.id}
                      onClick={() => handleSelectList(list.id)}
                      className={`flex items-center justify-between ${
                        list.id === currentListId ? 'bg-blue-50 text-blue-700' : ''
                      }`}
                    >
                      <div className="flex-1 truncate">
                        <div className="font-medium">{list.name}</div>
                        <div className="text-xs text-gray-500">
                          {list.items.length} items • Updated {new Date(list.updatedAt).toLocaleDateString()}
                        </div>
                      </div>
                      {list.id === currentListId && (
                        <Check className="h-4 w-4 ml-2" />
                      )}
                    </DropdownMenuItem>
                  ))}
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={() => setShowCreateList(true)}>
                    <FolderPlus className="h-4 w-4 mr-2" />
                    Create New List
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>

              {/* List Actions */}
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="outline" size="sm">
                    <Edit className="h-4 w-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem onClick={() => setShowRenameList(true)}>
                    <Edit className="h-4 w-4 mr-2" />
                    Rename List
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={handleDuplicateList}>
                    <Copy className="h-4 w-4 mr-2" />
                    Duplicate List
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem 
                    onClick={handleDeleteList}
                    className="text-red-600 hover:text-red-700"
                    disabled={savedLists.length <= 1}
                  >
                    <Trash2 className="h-4 w-4 mr-2" />
                    Delete List
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Add Item Form */}
          <div className="lg:col-span-1">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Plus className="h-5 w-5 mr-2" />
                  Add Item
                </CardTitle>
                <CardDescription>
                  Add items to "{currentList?.name}"
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label htmlFor="item-name">Item Name *</Label>
                  <Input
                    id="item-name"
                    value={newItem.name}
                    onChange={(e) => setNewItem(prev => ({ ...prev, name: e.target.value }))}
                    placeholder="Enter item name"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="quantity">Quantity *</Label>
                    <Input
                      id="quantity"
                      type="number"
                      min="0.1"
                      step="0.1"
                      value={newItem.quantity}
                      onChange={(e) => setNewItem(prev => ({ ...prev, quantity: e.target.value }))}
                      placeholder="1"
                    />
                  </div>
                  <div>
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

                <div>
                  <Label htmlFor="price">Estimated Price ($)</Label>
                  <Input
                    id="price"
                    type="number"
                    min="0"
                    step="0.01"
                    value={newItem.estimatedPrice}
                    onChange={(e) => setNewItem(prev => ({ ...prev, estimatedPrice: e.target.value }))}
                    placeholder="0.00"
                  />
                </div>

                <div>
                  <Label htmlFor="store">Store</Label>
                  <select
                    id="store"
                    value={newItem.store}
                    onChange={(e) => setNewItem(prev => ({ ...prev, store: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    {GROCERY_STORES.map(store => (
                      <option key={store} value={store}>{store}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <Label htmlFor="category">Category</Label>
                  <select
                    id="category"
                    value={newItem.category}
                    onChange={(e) => setNewItem(prev => ({ ...prev, category: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    {ITEM_CATEGORIES.map(category => (
                      <option key={category} value={category}>
                        {category.charAt(0).toUpperCase() + category.slice(1)}
                      </option>
                    ))}
                  </select>
                </div>

                <Button onClick={handleAddItem} className="w-full">
                  <Plus className="h-4 w-4 mr-2" />
                  Add to List
                </Button>
              </CardContent>
            </Card>

            {/* Summary */}
            <Card className="mt-6">
              <CardHeader>
                <CardTitle className="flex items-center">
                  <DollarSign className="h-5 w-5 mr-2" />
                  Summary
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span>Total Items:</span>
                    <span className="font-medium">{shoppingList.length}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Purchased:</span>
                    <span className="font-medium text-green-600">
                      {shoppingList.filter(item => item.purchased).length}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>Remaining:</span>
                    <span className="font-medium text-orange-600">
                      {shoppingList.filter(item => !item.purchased).length}
                    </span>
                  </div>
                  <div className="flex justify-between text-lg font-semibold pt-2 border-t">
                    <span>Estimated Total:</span>
                    <span className="text-green-600">${totalCost.toFixed(2)}</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Shopping List */}
          <div className="lg:col-span-2">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center">
                    <ShoppingCart className="h-5 w-5 mr-2" />
                    {currentList?.name} ({shoppingList.length} items)
                  </CardTitle>
                  <div className="flex gap-2">
                    <Button variant="outline" size="sm" onClick={handleExportList}>
                      Export List
                    </Button>
                    <Button variant="outline" size="sm" onClick={handleClearList}>
                      Clear All
                    </Button>
                  </div>
                </div>
                
                {/* Store Filter */}
                <div className="flex items-center gap-4 mt-4">
                  <span className="text-sm font-medium">Filter by store:</span>
                  <select
                    value={selectedStore}
                    onChange={(e) => setSelectedStore(e.target.value)}
                    className="px-3 py-1 border border-gray-300 rounded-md text-sm"
                  >
                    <option value="all">All Stores</option>
                    {GROCERY_STORES.map(store => (
                      <option key={store} value={store}>{store}</option>
                    ))}
                  </select>
                </div>
              </CardHeader>
              
              <CardContent>
                {Object.keys(groupedItems).length > 0 ? (
                  <div className="space-y-6">
                    {Object.entries(groupedItems).map(([store, items]) => (
                      <div key={store}>
                        <div className="flex items-center gap-2 mb-4">
                          <Store className="h-4 w-4 text-gray-500" />
                          <h3 className="font-semibold text-lg">{store}</h3>
                          <Badge variant="outline">
                            {items.length} items
                          </Badge>
                        </div>
                        
                        <div className="grid gap-3">
                          {items.map(item => (
                            <div 
                              key={item.id} 
                              className={`flex items-center justify-between p-4 border rounded-lg transition-all ${
                                item.purchased 
                                  ? 'bg-green-50 border-green-200 opacity-75' 
                                  : 'bg-white border-gray-200 hover:border-gray-300'
                              }`}
                            >
                              <div className="flex items-center space-x-3">
                                <Checkbox
                                  checked={item.purchased}
                                  onCheckedChange={() => handleTogglePurchased(item.id)}
                                />
                                <div className={item.purchased ? 'line-through text-gray-500' : ''}>
                                  <h4 className="font-medium">{item.name}</h4>
                                  <div className="flex items-center gap-4 text-sm text-gray-600">
                                    <span>{item.quantity} {item.unit}</span>
                                    <Badge variant="secondary" className="text-xs">
                                      {item.category}
                                    </Badge>
                                    {item.estimatedPrice > 0 && (
                                      <span className="font-medium text-green-600">
                                        ${item.estimatedPrice.toFixed(2)}
                                      </span>
                                    )}
                                  </div>
                                </div>
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
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <ShoppingCart className="h-12 w-12 text-gray-300 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-gray-900 mb-2">Your shopping list is empty</h3>
                    <p className="text-gray-600">Add items using the form on the left to get started!</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>

      {/* Create New List Dialog */}
      <Dialog open={showCreateList} onOpenChange={setShowCreateList}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create New Shopping List</DialogTitle>
            <DialogDescription>
              Give your new shopping list a name to help you organize different types of shopping trips.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div>
              <Label htmlFor="new-list-name">List Name *</Label>
              <Input
                id="new-list-name"
                value={newListName}
                onChange={(e) => setNewListName(e.target.value)}
                placeholder="e.g., Weekly Groceries, Camping Trip, Party Supplies"
                onKeyDown={(e) => e.key === 'Enter' && handleCreateList()}
              />
            </div>
            <div className="text-sm text-gray-500">
              <p>Popular list names:</p>
              <div className="flex flex-wrap gap-2 mt-2">
                {['Weekly Groceries', 'Camping Trip', 'Party Supplies', 'Vacation Shopping', 'Holiday Baking'].map(name => (
                  <Button
                    key={name}
                    variant="outline"
                    size="sm"
                    onClick={() => setNewListName(name)}
                    className="text-xs"
                  >
                    {name}
                  </Button>
                ))}
              </div>
            </div>
          </div>
          <div className="flex gap-3">
            <Button onClick={handleCreateList} className="flex-1">
              <FolderPlus className="h-4 w-4 mr-2" />
              Create List
            </Button>
            <Button variant="outline" onClick={() => setShowCreateList(false)} className="flex-1">
              Cancel
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Rename List Dialog */}
      <Dialog open={showRenameList} onOpenChange={setShowRenameList}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Rename Shopping List</DialogTitle>
            <DialogDescription>
              Change the name of your current shopping list.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div>
              <Label htmlFor="rename-list-name">List Name *</Label>
              <Input
                id="rename-list-name"
                value={renameListName}
                onChange={(e) => setRenameListName(e.target.value)}
                placeholder="Enter new list name"
                onKeyDown={(e) => e.key === 'Enter' && handleRenameList()}
              />
            </div>
          </div>
          <div className="flex gap-3">
            <Button onClick={handleRenameList} className="flex-1">
              <Edit className="h-4 w-4 mr-2" />
              Rename List
            </Button>
            <Button variant="outline" onClick={() => setShowRenameList(false)} className="flex-1">
              Cancel
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};