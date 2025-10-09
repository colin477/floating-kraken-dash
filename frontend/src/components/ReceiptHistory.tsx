import React, { useState } from 'react';
import { Receipt } from '@/types';
import { useReceiptHistory } from '@/hooks/useReceiptHistory';
import { ReceiptFilters } from '@/components/ReceiptFilters';
import { ReceiptCard } from '@/components/ReceiptCard';
import { ReceiptDetail } from '@/components/ReceiptDetail';
import { ReceiptStats } from '@/components/ReceiptStats';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  ArrowLeft, 
  Receipt as ReceiptIcon, 
  BarChart3, 
  RefreshCw,
  AlertCircle,
  ChevronLeft,
  ChevronRight
} from 'lucide-react';

interface ReceiptHistoryProps {
  onBack: () => void;
}

export const ReceiptHistory: React.FC<ReceiptHistoryProps> = ({ onBack }) => {
  const [selectedReceipt, setSelectedReceipt] = useState<Receipt | null>(null);
  const [activeTab, setActiveTab] = useState<'receipts' | 'analytics'>('receipts');
  
  const {
    receipts,
    loading,
    error,
    totalCount,
    currentPage,
    totalPages,
    filters,
    setFilters,
    setPage,
    refreshReceipts,
    deleteReceipt
  } = useReceiptHistory(12); // 12 receipts per page for nice grid layout

  const handleReceiptView = (receipt: Receipt) => {
    setSelectedReceipt(receipt);
  };

  const handleReceiptDelete = async (receiptId: string) => {
    try {
      await deleteReceipt(receiptId);
    } catch (error) {
      // Error is already handled in the hook
    }
  };

  const handleBackFromDetail = () => {
    setSelectedReceipt(null);
  };

  const clearFilters = () => {
    setFilters({
      sortBy: 'date',
      sortOrder: 'desc'
    });
  };

  // If viewing a specific receipt, show the detail view
  if (selectedReceipt) {
    return (
      <ReceiptDetail
        receipt={selectedReceipt}
        onBack={handleBackFromDetail}
        onDelete={handleReceiptDelete}
      />
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="max-w-7xl mx-auto">
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
              Back to Dashboard
            </Button>
            <div className="flex items-center gap-2">
              <ReceiptIcon className="h-6 w-6 text-green-600" />
              <h1 className="text-2xl font-bold">Receipt History</h1>
            </div>
          </div>
          
          <Button
            variant="outline"
            size="sm"
            onClick={refreshReceipts}
            disabled={loading}
            className="flex items-center gap-2"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={(value) => setActiveTab(value as 'receipts' | 'analytics')} className="mb-6">
          <TabsList className="grid w-full max-w-md grid-cols-2">
            <TabsTrigger value="receipts" className="flex items-center gap-2">
              <ReceiptIcon className="h-4 w-4" />
              Receipts ({totalCount})
            </TabsTrigger>
            <TabsTrigger value="analytics" className="flex items-center gap-2">
              <BarChart3 className="h-4 w-4" />
              Analytics
            </TabsTrigger>
          </TabsList>

          <TabsContent value="receipts" className="space-y-6">
            {/* Filters */}
            <ReceiptFilters
              filters={filters}
              onFiltersChange={setFilters}
              onClearFilters={clearFilters}
            />

            {/* Error State */}
            {error && (
              <Card className="border-red-200 bg-red-50">
                <CardContent className="p-4">
                  <div className="flex items-center gap-2 text-red-700">
                    <AlertCircle className="h-5 w-5" />
                    <span className="font-medium">Error loading receipts</span>
                  </div>
                  <p className="text-red-600 text-sm mt-1">{error}</p>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={refreshReceipts}
                    className="mt-3"
                  >
                    Try Again
                  </Button>
                </CardContent>
              </Card>
            )}

            {/* Loading State */}
            {loading && (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {[...Array(6)].map((_, i) => (
                  <Card key={i} className="animate-pulse">
                    <CardContent className="p-6">
                      <div className="space-y-3">
                        <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                        <div className="h-4 bg-gray-200 rounded w-1/2"></div>
                        <div className="h-8 bg-gray-200 rounded w-1/3"></div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}

            {/* Empty State */}
            {!loading && !error && receipts.length === 0 && (
              <Card>
                <CardContent className="p-12 text-center">
                  <ReceiptIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">No receipts found</h3>
                  <p className="text-gray-600 mb-4">
                    {Object.keys(filters).some(key => filters[key as keyof typeof filters] && key !== 'sortBy' && key !== 'sortOrder')
                      ? "No receipts match your current filters. Try adjusting your search criteria."
                      : "You haven't uploaded any receipts yet. Start by scanning your first receipt!"}
                  </p>
                  {Object.keys(filters).some(key => filters[key as keyof typeof filters] && key !== 'sortBy' && key !== 'sortOrder') && (
                    <Button variant="outline" onClick={clearFilters}>
                      Clear Filters
                    </Button>
                  )}
                </CardContent>
              </Card>
            )}

            {/* Receipts Grid */}
            {!loading && !error && receipts.length > 0 && (
              <>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {receipts.map((receipt) => (
                    <ReceiptCard
                      key={receipt.id}
                      receipt={receipt}
                      onView={handleReceiptView}
                      onDelete={handleReceiptDelete}
                    />
                  ))}
                </div>

                {/* Pagination */}
                {totalPages > 1 && (
                  <div className="flex items-center justify-between">
                    <div className="text-sm text-gray-600">
                      Showing {((currentPage - 1) * 12) + 1} to {Math.min(currentPage * 12, totalCount)} of {totalCount} receipts
                    </div>
                    
                    <div className="flex items-center gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setPage(currentPage - 1)}
                        disabled={currentPage === 1}
                      >
                        <ChevronLeft className="h-4 w-4" />
                        Previous
                      </Button>
                      
                      <div className="flex items-center gap-1">
                        {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                          let pageNum;
                          if (totalPages <= 5) {
                            pageNum = i + 1;
                          } else if (currentPage <= 3) {
                            pageNum = i + 1;
                          } else if (currentPage >= totalPages - 2) {
                            pageNum = totalPages - 4 + i;
                          } else {
                            pageNum = currentPage - 2 + i;
                          }
                          
                          return (
                            <Button
                              key={pageNum}
                              variant={currentPage === pageNum ? "default" : "outline"}
                              size="sm"
                              onClick={() => setPage(pageNum)}
                              className="w-8 h-8 p-0"
                            >
                              {pageNum}
                            </Button>
                          );
                        })}
                      </div>
                      
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setPage(currentPage + 1)}
                        disabled={currentPage === totalPages}
                      >
                        Next
                        <ChevronRight className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                )}
              </>
            )}
          </TabsContent>

          <TabsContent value="analytics">
            <ReceiptStats />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};