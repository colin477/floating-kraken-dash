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
  Receipt as ReceiptIcon
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
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Status</span>
                    <Badge variant={receipt.processed ? "default" : "secondary"}>
                      {receipt.processed ? "Processed" : "Pending"}
                    </Badge>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Items List */}
            <Card>
              <CardHeader>
                <CardTitle>Items ({receipt.items.length})</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {receipt.items.map((item, index) => (
                    <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
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
          </div>
        </div>
      </div>
    </div>
  );
};