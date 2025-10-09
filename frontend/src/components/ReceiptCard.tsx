import React, { useState } from 'react';
import { Receipt } from '@/types';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  Calendar, 
  DollarSign, 
  Store, 
  ShoppingBag, 
  Eye, 
  Trash2, 
  MoreVertical,
  Receipt as ReceiptIcon
} from 'lucide-react';
import { format } from 'date-fns';

interface ReceiptCardProps {
  receipt: Receipt;
  onView: (receipt: Receipt) => void;
  onDelete: (receiptId: string) => void;
}

export const ReceiptCard: React.FC<ReceiptCardProps> = ({
  receipt,
  onView,
  onDelete
}) => {
  const [showActions, setShowActions] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  const handleDelete = async () => {
    if (window.confirm('Are you sure you want to delete this receipt? This action cannot be undone.')) {
      setIsDeleting(true);
      try {
        await onDelete(receipt.id);
      } catch (error) {
        console.error('Failed to delete receipt:', error);
      } finally {
        setIsDeleting(false);
      }
    }
  };

  const formatDate = (dateString: string) => {
    try {
      return format(new Date(dateString), 'MMM dd, yyyy');
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

  const topCategories = receipt.items.reduce((acc, item) => {
    acc[item.category] = (acc[item.category] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const sortedCategories = Object.entries(topCategories)
    .sort(([,a], [,b]) => b - a)
    .slice(0, 3);

  return (
    <Card className="hover:shadow-md transition-shadow duration-200 relative">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-green-100 rounded-lg">
              <ReceiptIcon className="h-5 w-5 text-green-600" />
            </div>
            <div>
              <h3 className="font-semibold text-lg flex items-center gap-2">
                <Store className="h-4 w-4 text-gray-500" />
                {receipt.store}
              </h3>
              <div className="flex items-center gap-4 text-sm text-gray-600 mt-1">
                <span className="flex items-center gap-1">
                  <Calendar className="h-3 w-3" />
                  {formatDate(receipt.date)}
                </span>
                <span className="flex items-center gap-1">
                  <ShoppingBag className="h-3 w-3" />
                  {receipt.items.length} items
                </span>
              </div>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            <div className="text-right">
              <div className="text-2xl font-bold text-green-600 flex items-center gap-1">
                <DollarSign className="h-5 w-5" />
                {receipt.total.toFixed(2)}
              </div>
              {receipt.processed && (
                <Badge variant="secondary" className="text-xs">
                  Processed
                </Badge>
              )}
            </div>
            
            <div className="relative">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowActions(!showActions)}
                className="p-1 h-8 w-8"
              >
                <MoreVertical className="h-4 w-4" />
              </Button>
              
              {showActions && (
                <div className="absolute right-0 top-8 bg-white border border-gray-200 rounded-md shadow-lg z-10 min-w-[120px]">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      onView(receipt);
                      setShowActions(false);
                    }}
                    className="w-full justify-start text-left px-3 py-2 text-sm"
                  >
                    <Eye className="h-4 w-4 mr-2" />
                    View Details
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      handleDelete();
                      setShowActions(false);
                    }}
                    disabled={isDeleting}
                    className="w-full justify-start text-left px-3 py-2 text-sm text-red-600 hover:text-red-700 hover:bg-red-50"
                  >
                    <Trash2 className="h-4 w-4 mr-2" />
                    {isDeleting ? 'Deleting...' : 'Delete'}
                  </Button>
                </div>
              )}
            </div>
          </div>
        </div>
      </CardHeader>
      
      <CardContent>
        {/* Top Categories */}
        <div className="mb-4">
          <h4 className="text-sm font-medium text-gray-700 mb-2">Top Categories</h4>
          <div className="flex flex-wrap gap-2">
            {sortedCategories.map(([category, count]) => (
              <Badge
                key={category}
                className={`text-xs ${getCategoryColor(category)}`}
              >
                {category.replace('_', ' ')} ({count})
              </Badge>
            ))}
          </div>
        </div>
        
        {/* Sample Items */}
        <div className="mb-4">
          <h4 className="text-sm font-medium text-gray-700 mb-2">Items Preview</h4>
          <div className="text-sm text-gray-600">
            {receipt.items.slice(0, 3).map((item, index) => (
              <div key={index} className="flex justify-between items-center py-1">
                <span className="truncate flex-1 mr-2">
                  {item.name} {item.quantity > 1 && `(${item.quantity})`}
                </span>
                <span className="font-medium">${item.price.toFixed(2)}</span>
              </div>
            ))}
            {receipt.items.length > 3 && (
              <div className="text-xs text-gray-500 mt-1">
                +{receipt.items.length - 3} more items
              </div>
            )}
          </div>
        </div>
        
        {/* Action Buttons */}
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => onView(receipt)}
            className="flex-1"
          >
            <Eye className="h-4 w-4 mr-2" />
            View Details
          </Button>
        </div>
      </CardContent>
      
      {/* Click outside to close actions menu */}
      {showActions && (
        <div
          className="fixed inset-0 z-5"
          onClick={() => setShowActions(false)}
        />
      )}
    </Card>
  );
};