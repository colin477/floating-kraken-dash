import { useState, useEffect, useCallback } from 'react';
import { receiptApi } from '@/services/api';
import { Receipt } from '@/types';
import { ReceiptsListResponse } from '@/lib/mockReceiptData';

export interface ReceiptFilters {
  store?: string;
  dateFrom?: string;
  dateTo?: string;
  minTotal?: number;
  maxTotal?: number;
  sortBy?: 'date' | 'total' | 'store';
  sortOrder?: 'asc' | 'desc';
}

export interface UseReceiptHistoryReturn {
  receipts: Receipt[];
  loading: boolean;
  error: string | null;
  totalCount: number;
  currentPage: number;
  totalPages: number;
  filters: ReceiptFilters;
  setFilters: (filters: ReceiptFilters) => void;
  setPage: (page: number) => void;
  refreshReceipts: () => Promise<void>;
  deleteReceipt: (receiptId: string) => Promise<void>;
}

export const useReceiptHistory = (pageSize: number = 20): UseReceiptHistoryReturn => {
  const [receipts, setReceipts] = useState<Receipt[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [totalCount, setTotalCount] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(0);
  const [filters, setFilters] = useState<ReceiptFilters>({
    sortBy: 'date',
    sortOrder: 'desc'
  });

  const fetchReceipts = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const params = {
        page: currentPage,
        page_size: pageSize,
        store: filters.store,
        date_from: filters.dateFrom,
        date_to: filters.dateTo,
        min_total: filters.minTotal,
        max_total: filters.maxTotal,
        sort_by: filters.sortBy,
        sort_order: filters.sortOrder
      };

      // Remove undefined values
      const cleanParams = Object.fromEntries(
        Object.entries(params).filter(([_, value]) => value !== undefined)
      );

      const response: ReceiptsListResponse = await receiptApi.getReceipts(cleanParams);
      
      setReceipts(response.receipts);
      setTotalCount(response.total_count);
      setTotalPages(response.total_pages);
    } catch (err) {
      console.error('Error fetching receipts:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch receipts');
      setReceipts([]);
      setTotalCount(0);
      setTotalPages(0);
    } finally {
      setLoading(false);
    }
  }, [currentPage, pageSize, filters]);

  const refreshReceipts = useCallback(async () => {
    await fetchReceipts();
  }, [fetchReceipts]);

  const deleteReceipt = useCallback(async (receiptId: string) => {
    try {
      setError(null);
      await receiptApi.deleteReceipt(receiptId);
      
      // Remove the deleted receipt from the current list
      setReceipts(prev => prev.filter(receipt => receipt.id !== receiptId));
      setTotalCount(prev => prev - 1);
      
      // If this was the last receipt on the current page and we're not on page 1,
      // go back to the previous page
      if (receipts.length === 1 && currentPage > 1) {
        setCurrentPage(prev => prev - 1);
      } else {
        // Otherwise, refresh the current page
        await fetchReceipts();
      }
    } catch (err) {
      console.error('Error deleting receipt:', err);
      setError(err instanceof Error ? err.message : 'Failed to delete receipt');
      throw err; // Re-throw so the component can handle it
    }
  }, [receipts.length, currentPage, fetchReceipts]);

  const setPage = useCallback((page: number) => {
    setCurrentPage(page);
  }, []);

  const handleSetFilters = useCallback((newFilters: ReceiptFilters) => {
    setFilters(newFilters);
    setCurrentPage(1); // Reset to first page when filters change
  }, []);

  // Fetch receipts when dependencies change
  useEffect(() => {
    fetchReceipts();
  }, [fetchReceipts]);

  return {
    receipts,
    loading,
    error,
    totalCount,
    currentPage,
    totalPages,
    filters,
    setFilters: handleSetFilters,
    setPage,
    refreshReceipts,
    deleteReceipt
  };
};