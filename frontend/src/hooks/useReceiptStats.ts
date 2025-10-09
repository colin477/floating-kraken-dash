import { useState, useEffect, useCallback } from 'react';
import { receiptApi } from '@/services/api';
import { ReceiptStatsResponse } from '@/lib/mockReceiptData';

export interface UseReceiptStatsReturn {
  stats: ReceiptStatsResponse | null;
  loading: boolean;
  error: string | null;
  refreshStats: () => Promise<void>;
}

export const useReceiptStats = (): UseReceiptStatsReturn => {
  const [stats, setStats] = useState<ReceiptStatsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchStats = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const response: ReceiptStatsResponse = await receiptApi.getReceiptStats();
      setStats(response);
    } catch (err) {
      console.error('Error fetching receipt stats:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch receipt statistics');
      setStats(null);
    } finally {
      setLoading(false);
    }
  }, []);

  const refreshStats = useCallback(async () => {
    await fetchStats();
  }, [fetchStats]);

  // Fetch stats on mount
  useEffect(() => {
    fetchStats();
  }, [fetchStats]);

  return {
    stats,
    loading,
    error,
    refreshStats
  };
};