import { PantryItem, PantryCategory, PantryUnit, PantryItemsListResponse, ExpiringItemsResponse, PantryStatsResponse } from '@/types';

// Mock pantry items for testing
export const mockPantryItems: PantryItem[] = [
  {
    id: '1',
    user_id: 'demo-user',
    name: 'Chicken Breast',
    category: PantryCategory.MEAT,
    quantity: 2,
    unit: PantryUnit.POUND,
    expiration_date: new Date(Date.now() + 3 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // 3 days from now
    purchase_date: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // 2 days ago
    notes: 'Organic, free-range',
    created_at: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
    updated_at: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
    days_until_expiration: 3
  },
  {
    id: '2',
    user_id: 'demo-user',
    name: 'Bell Peppers',
    category: PantryCategory.PRODUCE,
    quantity: 4,
    unit: PantryUnit.PIECE,
    expiration_date: new Date(Date.now() + 5 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // 5 days from now
    purchase_date: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // 1 day ago
    notes: 'Red and yellow mix',
    created_at: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
    updated_at: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
    days_until_expiration: 5
  },
  {
    id: '3',
    user_id: 'demo-user',
    name: 'Milk',
    category: PantryCategory.DAIRY,
    quantity: 1,
    unit: PantryUnit.GALLON,
    expiration_date: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // 7 days from now
    purchase_date: new Date().toISOString().split('T')[0], // Today
    notes: '2% fat',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    days_until_expiration: 7
  },
  {
    id: '4',
    user_id: 'demo-user',
    name: 'Rice',
    category: PantryCategory.GRAINS,
    quantity: 2,
    unit: PantryUnit.POUND,
    expiration_date: new Date(Date.now() + 365 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // 1 year from now
    purchase_date: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // 1 week ago
    notes: 'Jasmine rice',
    created_at: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
    updated_at: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
    days_until_expiration: 365
  },
  {
    id: '5',
    user_id: 'demo-user',
    name: 'Canned Tomatoes',
    category: PantryCategory.CANNED_GOODS,
    quantity: 3,
    unit: PantryUnit.CAN,
    expiration_date: new Date(Date.now() + 180 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // 6 months from now
    purchase_date: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // 5 days ago
    notes: 'Diced, no salt added',
    created_at: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(),
    updated_at: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(),
    days_until_expiration: 180
  },
  {
    id: '6',
    user_id: 'demo-user',
    name: 'Yogurt',
    category: PantryCategory.DAIRY,
    quantity: 6,
    unit: PantryUnit.CONTAINER,
    expiration_date: new Date(Date.now() + 1 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // 1 day from now (expiring soon)
    purchase_date: new Date(Date.now() - 10 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // 10 days ago
    notes: 'Greek yogurt, vanilla',
    created_at: new Date(Date.now() - 10 * 24 * 60 * 60 * 1000).toISOString(),
    updated_at: new Date(Date.now() - 10 * 24 * 60 * 60 * 1000).toISOString(),
    days_until_expiration: 1
  },
  {
    id: '7',
    user_id: 'demo-user',
    name: 'Bread',
    category: PantryCategory.GRAINS,
    quantity: 1,
    unit: PantryUnit.PACKAGE,
    expiration_date: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // 1 day ago (expired)
    purchase_date: new Date(Date.now() - 8 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // 8 days ago
    notes: 'Whole wheat',
    created_at: new Date(Date.now() - 8 * 24 * 60 * 60 * 1000).toISOString(),
    updated_at: new Date(Date.now() - 8 * 24 * 60 * 60 * 1000).toISOString(),
    days_until_expiration: -1
  },
  {
    id: '8',
    user_id: 'demo-user',
    name: 'Olive Oil',
    category: PantryCategory.CONDIMENTS,
    quantity: 1,
    unit: PantryUnit.BOTTLE,
    expiration_date: new Date(Date.now() + 300 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // 10 months from now
    purchase_date: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // 1 month ago
    notes: 'Extra virgin',
    created_at: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
    updated_at: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
    days_until_expiration: 300
  },
  {
    id: '9',
    user_id: 'demo-user',
    name: 'Frozen Peas',
    category: PantryCategory.FROZEN,
    quantity: 2,
    unit: PantryUnit.BAG,
    expiration_date: new Date(Date.now() + 90 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // 3 months from now
    purchase_date: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // 3 days ago
    notes: 'Organic',
    created_at: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
    updated_at: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
    days_until_expiration: 90
  },
  {
    id: '10',
    user_id: 'demo-user',
    name: 'Bananas',
    category: PantryCategory.PRODUCE,
    quantity: 6,
    unit: PantryUnit.PIECE,
    expiration_date: new Date(Date.now() + 2 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // 2 days from now (expiring soon)
    purchase_date: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // 1 day ago
    notes: 'Ripe, good for smoothies',
    created_at: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
    updated_at: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
    days_until_expiration: 2
  }
];

// Mock API responses
export const getMockPantryItemsResponse = (params?: {
  category?: string;
  page?: number;
  page_size?: number;
}): PantryItemsListResponse => {
  let filteredItems = [...mockPantryItems];
  
  // Filter by category if specified
  if (params?.category && params.category !== 'all') {
    filteredItems = filteredItems.filter(item => item.category === params.category);
  }
  
  const pageSize = params?.page_size || 100;
  const page = params?.page || 1;
  const startIndex = (page - 1) * pageSize;
  const endIndex = startIndex + pageSize;
  const paginatedItems = filteredItems.slice(startIndex, endIndex);
  
  return {
    items: paginatedItems,
    total_count: filteredItems.length,
    page: page,
    page_size: pageSize,
    total_pages: Math.ceil(filteredItems.length / pageSize)
  };
};

export const getMockExpiringItemsResponse = (daysThreshold: number = 7): ExpiringItemsResponse => {
  const expiringSoon = mockPantryItems.filter(item => 
    item.days_until_expiration !== null && 
    item.days_until_expiration !== undefined &&
    item.days_until_expiration > 0 && 
    item.days_until_expiration <= daysThreshold
  );
  
  const expired = mockPantryItems.filter(item => 
    item.days_until_expiration !== null && 
    item.days_until_expiration !== undefined &&
    item.days_until_expiration < 0
  );
  
  return {
    expiring_soon: expiringSoon,
    expired: expired,
    days_threshold: daysThreshold
  };
};

export const getMockPantryStatsResponse = (): PantryStatsResponse => {
  const itemsByCategory = mockPantryItems.reduce((acc, item) => {
    acc[item.category] = (acc[item.category] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);
  
  const expiringSoonCount = mockPantryItems.filter(item => 
    item.days_until_expiration !== null && 
    item.days_until_expiration !== undefined &&
    item.days_until_expiration > 0 && 
    item.days_until_expiration <= 7
  ).length;
  
  const expiredCount = mockPantryItems.filter(item => 
    item.days_until_expiration !== null && 
    item.days_until_expiration !== undefined &&
    item.days_until_expiration < 0
  ).length;
  
  return {
    total_items: mockPantryItems.length,
    items_by_category: itemsByCategory,
    expiring_soon_count: expiringSoonCount,
    expired_count: expiredCount,
    total_value_estimate: 125.50 // Mock estimated value
  };
};

// Mock CRUD operations
let mockItemsState = [...mockPantryItems];

export const mockCreatePantryItem = (itemData: any): PantryItem => {
  const newItem: PantryItem = {
    id: Date.now().toString(),
    user_id: 'demo-user',
    name: itemData.name,
    category: itemData.category,
    quantity: itemData.quantity,
    unit: itemData.unit,
    expiration_date: itemData.expiration_date,
    purchase_date: itemData.purchase_date,
    notes: itemData.notes,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    days_until_expiration: itemData.expiration_date ? 
      Math.ceil((new Date(itemData.expiration_date).getTime() - new Date().getTime()) / (1000 * 60 * 60 * 24)) : 
      null
  };
  
  mockItemsState.push(newItem);
  return newItem;
};

export const mockUpdatePantryItem = (itemId: string, updateData: any): PantryItem => {
  const itemIndex = mockItemsState.findIndex(item => item.id === itemId);
  if (itemIndex === -1) {
    throw new Error('Item not found');
  }
  
  const updatedItem = {
    ...mockItemsState[itemIndex],
    ...updateData,
    updated_at: new Date().toISOString(),
    days_until_expiration: updateData.expiration_date ? 
      Math.ceil((new Date(updateData.expiration_date).getTime() - new Date().getTime()) / (1000 * 60 * 60 * 24)) : 
      mockItemsState[itemIndex].days_until_expiration
  };
  
  mockItemsState[itemIndex] = updatedItem;
  return updatedItem;
};

export const mockDeletePantryItem = (itemId: string): void => {
  const itemIndex = mockItemsState.findIndex(item => item.id === itemId);
  if (itemIndex === -1) {
    throw new Error('Item not found');
  }
  
  mockItemsState.splice(itemIndex, 1);
};

export const mockGetPantryItem = (itemId: string): PantryItem => {
  const item = mockItemsState.find(item => item.id === itemId);
  if (!item) {
    throw new Error('Item not found');
  }
  return item;
};

// Reset mock data (useful for testing)
export const resetMockPantryData = (): void => {
  mockItemsState = [...mockPantryItems];
};

// Get current mock state
export const getCurrentMockItems = (): PantryItem[] => {
  return [...mockItemsState];
};