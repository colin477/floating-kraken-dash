// API configuration and base service
import { shouldUseMockData } from '@/lib/demoMode';
import {
  getMockPantryItemsResponse,
  getMockExpiringItemsResponse,
  getMockPantryStatsResponse,
  mockCreatePantryItem,
  mockUpdatePantryItem,
  mockDeletePantryItem,
  mockGetPantryItem
} from '@/lib/mockPantryData';

const API_BASE_URL = 'http://localhost:8000/api/v1';

// Get auth token from localStorage
const getAuthToken = (): string | null => {
  const user = localStorage.getItem('ez-eatin-user');
  if (user) {
    const userData = JSON.parse(user);
    return userData.token || null;
  }
  return null;
};

// Base fetch wrapper with auth and demo mode support
const apiRequest = async (endpoint: string, options: RequestInit = {}): Promise<Response> => {
  const token = getAuthToken();
  
  const config: RequestInit = {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` }),
      ...options.headers,
    },
  };

  const response = await fetch(`${API_BASE_URL}${endpoint}`, config);
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(errorData.detail || `HTTP ${response.status}`);
  }
  
  return response;
};

// Mock response helper
const createMockResponse = (data: any): Promise<Response> => {
  return Promise.resolve(new Response(JSON.stringify(data), {
    status: 200,
    headers: { 'Content-Type': 'application/json' }
  }));
};

// Pantry API service with demo mode support
export const pantryApi = {
  // Get all pantry items
  getItems: async (params?: {
    category?: string;
    page?: number;
    page_size?: number;
    sort_by?: string;
    sort_order?: 'asc' | 'desc';
  }) => {
    if (shouldUseMockData()) {
      console.log('🧪 [Demo Mode] Using mock pantry items');
      // Simulate API delay
      await new Promise(resolve => setTimeout(resolve, 300));
      return getMockPantryItemsResponse(params);
    }

    try {
      const searchParams = new URLSearchParams();
      if (params?.category) searchParams.append('category', params.category);
      if (params?.page) searchParams.append('page', params.page.toString());
      if (params?.page_size) searchParams.append('page_size', params.page_size.toString());
      if (params?.sort_by) searchParams.append('sort_by', params.sort_by);
      if (params?.sort_order) searchParams.append('sort_order', params.sort_order);
      
      const query = searchParams.toString();
      const endpoint = `/pantry/${query ? `?${query}` : ''}`;
      
      const response = await apiRequest(endpoint);
      return response.json();
    } catch (error) {
      console.warn('🧪 [Demo Mode] API failed, falling back to mock data:', error);
      await new Promise(resolve => setTimeout(resolve, 300));
      return getMockPantryItemsResponse(params);
    }
  },

  // Create new pantry item
  createItem: async (itemData: {
    name: string;
    category: string;
    quantity: number;
    unit: string;
    expiration_date?: string;
    purchase_date?: string;
    notes?: string;
  }) => {
    if (shouldUseMockData()) {
      console.log('🧪 [Demo Mode] Creating mock pantry item:', itemData.name);
      // Simulate API delay
      await new Promise(resolve => setTimeout(resolve, 500));
      return mockCreatePantryItem(itemData);
    }

    try {
      const response = await apiRequest('/pantry/', {
        method: 'POST',
        body: JSON.stringify(itemData),
      });
      return response.json();
    } catch (error) {
      console.warn('🧪 [Demo Mode] API failed, falling back to mock creation:', error);
      await new Promise(resolve => setTimeout(resolve, 500));
      return mockCreatePantryItem(itemData);
    }
  },

  // Get specific pantry item
  getItem: async (itemId: string) => {
    if (shouldUseMockData()) {
      console.log('🧪 [Demo Mode] Getting mock pantry item:', itemId);
      await new Promise(resolve => setTimeout(resolve, 200));
      return mockGetPantryItem(itemId);
    }

    try {
      const response = await apiRequest(`/pantry/${itemId}`);
      return response.json();
    } catch (error) {
      console.warn('🧪 [Demo Mode] API failed, falling back to mock item:', error);
      await new Promise(resolve => setTimeout(resolve, 200));
      return mockGetPantryItem(itemId);
    }
  },

  // Update pantry item
  updateItem: async (itemId: string, updateData: {
    name?: string;
    category?: string;
    quantity?: number;
    unit?: string;
    expiration_date?: string;
    purchase_date?: string;
    notes?: string;
  }) => {
    if (shouldUseMockData()) {
      console.log('🧪 [Demo Mode] Updating mock pantry item:', itemId);
      await new Promise(resolve => setTimeout(resolve, 400));
      return mockUpdatePantryItem(itemId, updateData);
    }

    try {
      const response = await apiRequest(`/pantry/${itemId}`, {
        method: 'PUT',
        body: JSON.stringify(updateData),
      });
      return response.json();
    } catch (error) {
      console.warn('🧪 [Demo Mode] API failed, falling back to mock update:', error);
      await new Promise(resolve => setTimeout(resolve, 400));
      return mockUpdatePantryItem(itemId, updateData);
    }
  },

  // Delete pantry item
  deleteItem: async (itemId: string) => {
    if (shouldUseMockData()) {
      console.log('🧪 [Demo Mode] Deleting mock pantry item:', itemId);
      await new Promise(resolve => setTimeout(resolve, 300));
      mockDeletePantryItem(itemId);
      return { success: true };
    }

    try {
      const response = await apiRequest(`/pantry/${itemId}`, {
        method: 'DELETE',
      });
      return response.json();
    } catch (error) {
      console.warn('🧪 [Demo Mode] API failed, falling back to mock deletion:', error);
      await new Promise(resolve => setTimeout(resolve, 300));
      mockDeletePantryItem(itemId);
      return { success: true };
    }
  },

  // Get expiring items
  getExpiringItems: async (daysThreshold: number = 7) => {
    if (shouldUseMockData()) {
      console.log('🧪 [Demo Mode] Getting mock expiring items');
      await new Promise(resolve => setTimeout(resolve, 400));
      return getMockExpiringItemsResponse(daysThreshold);
    }

    try {
      const response = await apiRequest(`/pantry/expiring/items?days_threshold=${daysThreshold}`);
      return response.json();
    } catch (error) {
      console.warn('🧪 [Demo Mode] API failed, falling back to mock expiring items:', error);
      await new Promise(resolve => setTimeout(resolve, 400));
      return getMockExpiringItemsResponse(daysThreshold);
    }
  },

  // Get pantry statistics
  getStats: async () => {
    if (shouldUseMockData()) {
      console.log('🧪 [Demo Mode] Getting mock pantry stats');
      await new Promise(resolve => setTimeout(resolve, 300));
      return getMockPantryStatsResponse();
    }

    try {
      const response = await apiRequest('/pantry/stats/overview');
      return response.json();
    } catch (error) {
      console.warn('🧪 [Demo Mode] API failed, falling back to mock stats:', error);
      await new Promise(resolve => setTimeout(resolve, 300));
      return getMockPantryStatsResponse();
    }
  },

  // Search pantry items
  searchItems: async (query: string, limit: number = 20) => {
    if (shouldUseMockData()) {
      console.log('🧪 [Demo Mode] Searching mock pantry items:', query);
      await new Promise(resolve => setTimeout(resolve, 300));
      // Simple mock search implementation
      const mockResponse = getMockPantryItemsResponse();
      const filteredItems = mockResponse.items.filter(item =>
        item.name.toLowerCase().includes(query.toLowerCase())
      ).slice(0, limit);
      return { items: filteredItems, total_count: filteredItems.length };
    }

    try {
      const response = await apiRequest(`/pantry/search/items?q=${encodeURIComponent(query)}&limit=${limit}`);
      return response.json();
    } catch (error) {
      console.warn('🧪 [Demo Mode] API failed, falling back to mock search:', error);
      await new Promise(resolve => setTimeout(resolve, 300));
      const mockResponse = getMockPantryItemsResponse();
      const filteredItems = mockResponse.items.filter(item =>
        item.name.toLowerCase().includes(query.toLowerCase())
      ).slice(0, limit);
      return { items: filteredItems, total_count: filteredItems.length };
    }
  },
};

// Auth API service
export const authApi = {
  login: async (email: string, password: string) => {
    const response = await fetch(`${API_BASE_URL}/auth/login-form`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: new URLSearchParams({
        username: email,
        password: password,
      }),
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Login failed' }));
      throw new Error(errorData.detail || 'Login failed');
    }
    
    return response.json();
  },

  register: async (email: string, password: string, name: string) => {
    const response = await fetch(`${API_BASE_URL}/auth/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email,
        password,
        full_name: name,
      }),
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Registration failed' }));
      throw new Error(errorData.detail || 'Registration failed');
    }
    
    return response.json();
  },

  getCurrentUser: async () => {
    const response = await apiRequest('/auth/me');
    return response.json();
  },
};