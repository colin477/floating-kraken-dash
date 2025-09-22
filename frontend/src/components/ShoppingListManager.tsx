import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import { ArrowLeft, Plus, Edit, Trash2, ShoppingCart, Calendar, DollarSign, MoreVertical, Copy } from 'lucide-react';
import { showSuccess, showError } from '@/utils/toast';

interface ShoppingListManagerProps {
  onBack: () => void;
  onCreateNew: () => void;
  onEditList: (listId: string) => void;
}

interface SavedShoppingList {
  id: string;
  name: string;
  items: ShoppingListItem[];
  createdAt: string;
  updatedAt: string;
}

interface ShoppingListItem {
  id: string;
  name: string;
  quantity: number;
  unit: string;
  estimatedPrice: number;
  store: string;
  category: string;
  purchased: boolean;
}

const STORAGE_KEY = 'ez-eatin-shopping-lists';

export const ShoppingListManager = ({ onBack, onCreateNew, onEditList }: ShoppingListManagerProps) => {
  const [savedLists, setSavedLists] = useState<SavedShoppingList[]>([]);

  useEffect(() => {
    loadSavedLists();
  }, []);

  const loadSavedLists = () => {
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
  };

  const handleDuplicateList = (list: SavedShoppingList) => {
    const duplicatedList: SavedShoppingList = {
      id: Date.now().toString(),
      name: `${list.name} (Copy)`,
      items: list.items.map(item => ({ ...item, id: Date.now().toString() + Math.random() })),
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    };

    const updatedLists = [...savedLists, duplicatedList];
    setSavedLists(updatedLists);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updatedLists));
    
    showSuccess(`Duplicated "${list.name}"`);
  };

  const handleDeleteList = (listId: string) => {
    const listToDelete = savedLists.find(list => list.id === listId);
    if (!listToDelete) return;

    if (savedLists.length <= 1) {
      showError('Cannot delete the last shopping list');
      return;
    }

    const updatedLists = savedLists.filter(list => list.id !== listId);
    setSavedLists(updatedLists);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updatedLists));
    
    showSuccess(`Deleted "${listToDelete.name}"`);
  };

  const getListStats = (list: SavedShoppingList) => {
    const totalItems = list.items.length;
    const purchasedItems = list.items.filter(item => item.purchased).length;
    const totalCost = list.items.reduce((sum, item) => sum + item.estimatedPrice, 0);
    const completionPercentage = totalItems > 0 ? Math.round((purchasedItems / totalItems) * 100) : 0;
    
    return { totalItems, purchasedItems, totalCost, completionPercentage };
  };

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
                <h1 className="text-xl font-semibold">My Shopping Lists</h1>
                <p className="text-sm text-gray-600">View and manage all your shopping lists</p>
              </div>
            </div>
            
            <Button onClick={onCreateNew}>
              <Plus className="h-4 w-4 mr-2" />
              Create New List
            </Button>
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Summary Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center">
                <div className="p-3 bg-blue-100 rounded-xl">
                  <ShoppingCart className="h-6 w-6 text-blue-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Total Lists</p>
                  <p className="text-2xl font-bold text-gray-900">{savedLists.length}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center">
                <div className="p-3 bg-green-100 rounded-xl">
                  <Calendar className="h-6 w-6 text-green-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Total Items</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {savedLists.reduce((sum, list) => sum + list.items.length, 0)}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center">
                <div className="p-3 bg-purple-100 rounded-xl">
                  <DollarSign className="h-6 w-6 text-purple-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Total Value</p>
                  <p className="text-2xl font-bold text-gray-900">
                    ${savedLists.reduce((sum, list) => 
                      sum + list.items.reduce((itemSum, item) => itemSum + item.estimatedPrice, 0), 0
                    ).toFixed(2)}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Shopping Lists */}
        {savedLists.length > 0 ? (
          <div className="grid gap-6">
            {savedLists.map(list => {
              const stats = getListStats(list);
              
              return (
                <Card key={list.id} className="hover:shadow-md transition-shadow">
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <CardTitle className="text-lg">{list.name}</CardTitle>
                        <CardDescription className="mt-1">
                          Created {new Date(list.createdAt).toLocaleDateString()} • 
                          Updated {new Date(list.updatedAt).toLocaleDateString()}
                        </CardDescription>
                      </div>
                      
                      <div className="flex items-center gap-2">
                        <Button
                          variant="default"
                          onClick={() => onEditList(list.id)}
                        >
                          <Edit className="h-4 w-4 mr-2" />
                          Edit List
                        </Button>
                        
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="outline" size="sm">
                              <MoreVertical className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem onClick={() => handleDuplicateList(list)}>
                              <Copy className="h-4 w-4 mr-2" />
                              Duplicate List
                            </DropdownMenuItem>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem 
                              onClick={() => handleDeleteList(list.id)}
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
                  </CardHeader>
                  
                  <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
                      <div className="text-center p-3 bg-gray-50 rounded-lg">
                        <div className="text-lg font-bold text-gray-900">{stats.totalItems}</div>
                        <div className="text-sm text-gray-600">Total Items</div>
                      </div>
                      
                      <div className="text-center p-3 bg-green-50 rounded-lg">
                        <div className="text-lg font-bold text-green-600">{stats.purchasedItems}</div>
                        <div className="text-sm text-gray-600">Purchased</div>
                      </div>
                      
                      <div className="text-center p-3 bg-blue-50 rounded-lg">
                        <div className="text-lg font-bold text-blue-600">{stats.completionPercentage}%</div>
                        <div className="text-sm text-gray-600">Complete</div>
                      </div>
                      
                      <div className="text-center p-3 bg-purple-50 rounded-lg">
                        <div className="text-lg font-bold text-purple-600">${stats.totalCost.toFixed(2)}</div>
                        <div className="text-sm text-gray-600">Est. Total</div>
                      </div>
                    </div>

                    {/* Progress Bar */}
                    <div className="w-full bg-gray-200 rounded-full h-2 mb-4">
                      <div 
                        className="bg-green-600 h-2 rounded-full transition-all duration-300" 
                        style={{ width: `${stats.completionPercentage}%` }}
                      />
                    </div>

                    {/* Recent Items Preview */}
                    {list.items.length > 0 && (
                      <div>
                        <h4 className="font-medium text-sm text-gray-700 mb-2">Recent Items:</h4>
                        <div className="flex flex-wrap gap-2">
                          {list.items.slice(0, 6).map(item => (
                            <Badge 
                              key={item.id} 
                              variant={item.purchased ? "default" : "secondary"}
                              className="text-xs"
                            >
                              {item.name}
                            </Badge>
                          ))}
                          {list.items.length > 6 && (
                            <Badge variant="outline" className="text-xs">
                              +{list.items.length - 6} more
                            </Badge>
                          )}
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              );
            })}
          </div>
        ) : (
          <div className="text-center py-12">
            <ShoppingCart className="h-12 w-12 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No shopping lists yet</h3>
            <p className="text-gray-600 mb-4">
              Create your first shopping list to get started with organized grocery shopping!
            </p>
            <Button onClick={onCreateNew}>
              <Plus className="h-4 w-4 mr-2" />
              Create Your First List
            </Button>
          </div>
        )}
      </div>
    </div>
  );
};