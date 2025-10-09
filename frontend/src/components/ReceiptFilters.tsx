import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Search, Filter, X, Calendar, DollarSign, Store } from 'lucide-react';
import { ReceiptFilters as ReceiptFiltersType } from '@/hooks/useReceiptHistory';

interface ReceiptFiltersProps {
  filters: ReceiptFiltersType;
  onFiltersChange: (filters: ReceiptFiltersType) => void;
  onClearFilters: () => void;
}

export const ReceiptFilters: React.FC<ReceiptFiltersProps> = ({
  filters,
  onFiltersChange,
  onClearFilters
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [localFilters, setLocalFilters] = useState<ReceiptFiltersType>(filters);

  const handleFilterChange = (key: keyof ReceiptFiltersType, value: any) => {
    const newFilters = { ...localFilters, [key]: value };
    setLocalFilters(newFilters);
  };

  const applyFilters = () => {
    onFiltersChange(localFilters);
  };

  const clearFilters = () => {
    const clearedFilters: ReceiptFiltersType = {
      sortBy: 'date',
      sortOrder: 'desc'
    };
    setLocalFilters(clearedFilters);
    onFiltersChange(clearedFilters);
    onClearFilters();
  };

  const hasActiveFilters = Boolean(
    filters.store || 
    filters.dateFrom || 
    filters.dateTo || 
    filters.minTotal || 
    filters.maxTotal
  );

  return (
    <Card className="mb-6">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg flex items-center gap-2">
            <Filter className="h-5 w-5" />
            Filters & Search
            {hasActiveFilters && (
              <span className="bg-green-100 text-green-800 text-xs px-2 py-1 rounded-full">
                Active
              </span>
            )}
          </CardTitle>
          <div className="flex items-center gap-2">
            {hasActiveFilters && (
              <Button
                variant="outline"
                size="sm"
                onClick={clearFilters}
                className="text-xs"
              >
                <X className="h-3 w-3 mr-1" />
                Clear All
              </Button>
            )}
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsExpanded(!isExpanded)}
            >
              {isExpanded ? 'Less' : 'More'} Filters
            </Button>
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {/* Quick Search */}
        <div className="flex gap-2">
          <div className="flex-1">
            <Label htmlFor="store-search" className="text-sm font-medium">
              Store Name
            </Label>
            <div className="relative">
              <Store className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <Input
                id="store-search"
                placeholder="Search by store name..."
                value={localFilters.store || ''}
                onChange={(e) => handleFilterChange('store', e.target.value)}
                className="pl-10"
              />
            </div>
          </div>
          <div className="flex items-end">
            <Button onClick={applyFilters} className="px-6">
              <Search className="h-4 w-4 mr-2" />
              Search
            </Button>
          </div>
        </div>

        {/* Expanded Filters */}
        {isExpanded && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 pt-4 border-t">
            {/* Date Range */}
            <div className="space-y-2">
              <Label className="text-sm font-medium flex items-center gap-1">
                <Calendar className="h-4 w-4" />
                Date Range
              </Label>
              <div className="space-y-2">
                <div>
                  <Label htmlFor="date-from" className="text-xs text-gray-600">From</Label>
                  <Input
                    id="date-from"
                    type="date"
                    value={localFilters.dateFrom || ''}
                    onChange={(e) => handleFilterChange('dateFrom', e.target.value)}
                  />
                </div>
                <div>
                  <Label htmlFor="date-to" className="text-xs text-gray-600">To</Label>
                  <Input
                    id="date-to"
                    type="date"
                    value={localFilters.dateTo || ''}
                    onChange={(e) => handleFilterChange('dateTo', e.target.value)}
                  />
                </div>
              </div>
            </div>

            {/* Amount Range */}
            <div className="space-y-2">
              <Label className="text-sm font-medium flex items-center gap-1">
                <DollarSign className="h-4 w-4" />
                Amount Range
              </Label>
              <div className="space-y-2">
                <div>
                  <Label htmlFor="min-total" className="text-xs text-gray-600">Min Amount</Label>
                  <Input
                    id="min-total"
                    type="number"
                    placeholder="0.00"
                    step="0.01"
                    value={localFilters.minTotal || ''}
                    onChange={(e) => handleFilterChange('minTotal', e.target.value ? parseFloat(e.target.value) : undefined)}
                  />
                </div>
                <div>
                  <Label htmlFor="max-total" className="text-xs text-gray-600">Max Amount</Label>
                  <Input
                    id="max-total"
                    type="number"
                    placeholder="999.99"
                    step="0.01"
                    value={localFilters.maxTotal || ''}
                    onChange={(e) => handleFilterChange('maxTotal', e.target.value ? parseFloat(e.target.value) : undefined)}
                  />
                </div>
              </div>
            </div>

            {/* Sort Options */}
            <div className="space-y-2">
              <Label className="text-sm font-medium">Sort Options</Label>
              <div className="space-y-2">
                <div>
                  <Label htmlFor="sort-by" className="text-xs text-gray-600">Sort By</Label>
                  <select
                    id="sort-by"
                    value={localFilters.sortBy || 'date'}
                    onChange={(e) => handleFilterChange('sortBy', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  >
                    <option value="date">Date</option>
                    <option value="total">Amount</option>
                    <option value="store">Store</option>
                  </select>
                </div>
                <div>
                  <Label htmlFor="sort-order" className="text-xs text-gray-600">Order</Label>
                  <select
                    id="sort-order"
                    value={localFilters.sortOrder || 'desc'}
                    onChange={(e) => handleFilterChange('sortOrder', e.target.value as 'asc' | 'desc')}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  >
                    <option value="desc">Newest First</option>
                    <option value="asc">Oldest First</option>
                  </select>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Apply/Clear Actions for Expanded View */}
        {isExpanded && (
          <div className="flex justify-end gap-2 pt-4 border-t">
            <Button variant="outline" onClick={clearFilters}>
              <X className="h-4 w-4 mr-2" />
              Clear All
            </Button>
            <Button onClick={applyFilters}>
              <Search className="h-4 w-4 mr-2" />
              Apply Filters
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
};