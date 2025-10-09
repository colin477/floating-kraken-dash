import { Receipt, ReceiptItem, PantryCategory } from '@/types';

// Mock receipt data for testing
export const mockReceipts: Receipt[] = [
  {
    id: '1',
    userId: 'demo-user',
    imageUrl: '/api/placeholder/receipt1.jpg',
    items: [
      { name: 'Chicken Breast', quantity: 2, price: 8.99, category: PantryCategory.MEAT },
      { name: 'Bell Peppers', quantity: 3, price: 2.49, category: PantryCategory.PRODUCE },
      { name: 'Onions', quantity: 1, price: 1.29, category: PantryCategory.PRODUCE },
      { name: 'Rice', quantity: 1, price: 3.99, category: PantryCategory.GRAINS },
      { name: 'Soy Sauce', quantity: 1, price: 2.79, category: PantryCategory.CONDIMENTS }
    ],
    total: 19.55,
    store: 'Kroger',
    date: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // 2 days ago
    processed: true
  },
  {
    id: '2',
    userId: 'demo-user',
    imageUrl: '/api/placeholder/receipt2.jpg',
    items: [
      { name: 'Milk', quantity: 1, price: 3.29, category: PantryCategory.DAIRY },
      { name: 'Eggs', quantity: 12, price: 3.49, category: PantryCategory.DAIRY },
      { name: 'Bread', quantity: 1, price: 2.99, category: PantryCategory.GRAINS },
      { name: 'Bananas', quantity: 6, price: 1.99, category: PantryCategory.PRODUCE },
      { name: 'Yogurt', quantity: 4, price: 4.99, category: PantryCategory.DAIRY }
    ],
    total: 16.75,
    store: 'Safeway',
    date: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // 5 days ago
    processed: true
  },
  {
    id: '3',
    userId: 'demo-user',
    imageUrl: '/api/placeholder/receipt3.jpg',
    items: [
      { name: 'Ground Beef', quantity: 1, price: 5.99, category: PantryCategory.MEAT },
      { name: 'Pasta', quantity: 2, price: 2.98, category: PantryCategory.GRAINS },
      { name: 'Tomato Sauce', quantity: 3, price: 4.47, category: PantryCategory.CANNED_GOODS },
      { name: 'Cheese', quantity: 1, price: 4.99, category: PantryCategory.DAIRY },
      { name: 'Garlic', quantity: 1, price: 0.99, category: PantryCategory.PRODUCE }
    ],
    total: 19.42,
    store: 'Walmart',
    date: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // 1 week ago
    processed: true
  },
  {
    id: '4',
    userId: 'demo-user',
    imageUrl: '/api/placeholder/receipt4.jpg',
    items: [
      { name: 'Salmon Fillet', quantity: 1, price: 12.99, category: PantryCategory.SEAFOOD },
      { name: 'Asparagus', quantity: 1, price: 3.99, category: PantryCategory.PRODUCE },
      { name: 'Lemon', quantity: 3, price: 1.99, category: PantryCategory.PRODUCE },
      { name: 'Olive Oil', quantity: 1, price: 6.99, category: PantryCategory.CONDIMENTS }
    ],
    total: 25.96,
    store: 'Whole Foods',
    date: new Date(Date.now() - 10 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // 10 days ago
    processed: true
  },
  {
    id: '5',
    userId: 'demo-user',
    imageUrl: '/api/placeholder/receipt5.jpg',
    items: [
      { name: 'Frozen Pizza', quantity: 2, price: 7.98, category: PantryCategory.FROZEN },
      { name: 'Ice Cream', quantity: 1, price: 4.99, category: PantryCategory.FROZEN },
      { name: 'Chips', quantity: 1, price: 3.49, category: PantryCategory.SNACKS },
      { name: 'Soda', quantity: 1, price: 5.99, category: PantryCategory.BEVERAGES }
    ],
    total: 22.45,
    store: 'Target',
    date: new Date(Date.now() - 14 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // 2 weeks ago
    processed: true
  },
  {
    id: '6',
    userId: 'demo-user',
    imageUrl: '/api/placeholder/receipt6.jpg',
    items: [
      { name: 'Apples', quantity: 3, price: 2.97, category: PantryCategory.PRODUCE },
      { name: 'Carrots', quantity: 1, price: 1.49, category: PantryCategory.PRODUCE },
      { name: 'Potatoes', quantity: 5, price: 3.99, category: PantryCategory.PRODUCE },
      { name: 'Butter', quantity: 1, price: 3.99, category: PantryCategory.DAIRY },
      { name: 'Salt', quantity: 1, price: 1.29, category: PantryCategory.SPICES }
    ],
    total: 13.73,
    store: 'King Soopers',
    date: new Date(Date.now() - 21 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // 3 weeks ago
    processed: true
  }
];

// Response types for receipt API
export interface ReceiptsListResponse {
  receipts: Receipt[];
  total_count: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface ReceiptStatsResponse {
  total_receipts: number;
  total_spent: number;
  average_receipt_total: number;
  receipts_by_store: Record<string, number>;
  spending_by_category: Record<string, number>;
  spending_by_month: Record<string, number>;
  most_frequent_items: Array<{ name: string; count: number; total_spent: number }>;
}

// Mock API responses
export const getMockReceiptsResponse = (params?: {
  page?: number;
  page_size?: number;
  store?: string;
  date_from?: string;
  date_to?: string;
  min_total?: number;
  max_total?: number;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}): ReceiptsListResponse => {
  let filteredReceipts = [...mockReceipts];
  
  // Filter by store if specified
  if (params?.store) {
    filteredReceipts = filteredReceipts.filter(receipt => 
      receipt.store.toLowerCase().includes(params.store!.toLowerCase())
    );
  }
  
  // Filter by date range
  if (params?.date_from) {
    filteredReceipts = filteredReceipts.filter(receipt => receipt.date >= params.date_from!);
  }
  if (params?.date_to) {
    filteredReceipts = filteredReceipts.filter(receipt => receipt.date <= params.date_to!);
  }
  
  // Filter by total amount
  if (params?.min_total) {
    filteredReceipts = filteredReceipts.filter(receipt => receipt.total >= params.min_total!);
  }
  if (params?.max_total) {
    filteredReceipts = filteredReceipts.filter(receipt => receipt.total <= params.max_total!);
  }
  
  // Sort receipts
  if (params?.sort_by) {
    filteredReceipts.sort((a, b) => {
      let aValue: any, bValue: any;
      
      switch (params.sort_by) {
        case 'date':
          aValue = new Date(a.date);
          bValue = new Date(b.date);
          break;
        case 'total':
          aValue = a.total;
          bValue = b.total;
          break;
        case 'store':
          aValue = a.store;
          bValue = b.store;
          break;
        default:
          aValue = a.date;
          bValue = b.date;
      }
      
      if (params.sort_order === 'desc') {
        return aValue > bValue ? -1 : aValue < bValue ? 1 : 0;
      } else {
        return aValue < bValue ? -1 : aValue > bValue ? 1 : 0;
      }
    });
  } else {
    // Default sort by date descending (newest first)
    filteredReceipts.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
  }
  
  const pageSize = params?.page_size || 20;
  const page = params?.page || 1;
  const startIndex = (page - 1) * pageSize;
  const endIndex = startIndex + pageSize;
  const paginatedReceipts = filteredReceipts.slice(startIndex, endIndex);
  
  return {
    receipts: paginatedReceipts,
    total_count: filteredReceipts.length,
    page: page,
    page_size: pageSize,
    total_pages: Math.ceil(filteredReceipts.length / pageSize)
  };
};

export const getMockReceipt = (receiptId: string): Receipt => {
  const receipt = mockReceipts.find(r => r.id === receiptId);
  if (!receipt) {
    throw new Error('Receipt not found');
  }
  return receipt;
};

export const getMockReceiptImageUrl = (receiptId: string): { image_url: string } => {
  const receipt = mockReceipts.find(r => r.id === receiptId);
  if (!receipt) {
    throw new Error('Receipt not found');
  }
  return { image_url: receipt.imageUrl };
};

export const getMockReceiptStatsResponse = (): ReceiptStatsResponse => {
  const totalReceipts = mockReceipts.length;
  const totalSpent = mockReceipts.reduce((sum, receipt) => sum + receipt.total, 0);
  const averageReceiptTotal = totalSpent / totalReceipts;
  
  // Receipts by store
  const receiptsByStore = mockReceipts.reduce((acc, receipt) => {
    acc[receipt.store] = (acc[receipt.store] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);
  
  // Spending by category
  const spendingByCategory = mockReceipts.reduce((acc, receipt) => {
    receipt.items.forEach(item => {
      acc[item.category] = (acc[item.category] || 0) + item.price;
    });
    return acc;
  }, {} as Record<string, number>);
  
  // Spending by month (last 6 months)
  const spendingByMonth = mockReceipts.reduce((acc, receipt) => {
    const month = new Date(receipt.date).toISOString().slice(0, 7); // YYYY-MM format
    acc[month] = (acc[month] || 0) + receipt.total;
    return acc;
  }, {} as Record<string, number>);
  
  // Most frequent items
  const itemCounts = mockReceipts.reduce((acc, receipt) => {
    receipt.items.forEach(item => {
      if (!acc[item.name]) {
        acc[item.name] = { count: 0, total_spent: 0 };
      }
      acc[item.name].count += item.quantity;
      acc[item.name].total_spent += item.price;
    });
    return acc;
  }, {} as Record<string, { count: number; total_spent: number }>);
  
  const mostFrequentItems = Object.entries(itemCounts)
    .map(([name, data]) => ({ name, ...data }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 10);
  
  return {
    total_receipts: totalReceipts,
    total_spent: Math.round(totalSpent * 100) / 100,
    average_receipt_total: Math.round(averageReceiptTotal * 100) / 100,
    receipts_by_store: receiptsByStore,
    spending_by_category: spendingByCategory,
    spending_by_month: spendingByMonth,
    most_frequent_items: mostFrequentItems
  };
};

// Mock CRUD operations
let mockReceiptsState = [...mockReceipts];

export const mockDeleteReceipt = (receiptId: string): void => {
  const receiptIndex = mockReceiptsState.findIndex(receipt => receipt.id === receiptId);
  if (receiptIndex === -1) {
    throw new Error('Receipt not found');
  }
  
  mockReceiptsState.splice(receiptIndex, 1);
};

// Reset mock data (useful for testing)
export const resetMockReceiptData = (): void => {
  mockReceiptsState = [...mockReceipts];
};

// Get current mock state
export const getCurrentMockReceipts = (): Receipt[] => {
  return [...mockReceiptsState];
};