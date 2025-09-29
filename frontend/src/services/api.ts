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
import { simulateReceiptProcessing } from '@/lib/mockData';

const API_BASE_URL = import.meta.env.VITE_APP_BASE_URL || 'http://localhost:8000/api/v1';

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

// Community API service
export const communityApi = {
  // Get all posts
  getPosts: async (params?: {
    page?: number;
    page_size?: number;
    post_type?: string;
    tags?: string[];
  }) => {
    const searchParams = new URLSearchParams();
    if (params?.page) searchParams.append('page', params.page.toString());
    if (params?.page_size) searchParams.append('page_size', params.page_size.toString());
    if (params?.post_type) searchParams.append('post_type', params.post_type);
    if (params?.tags) {
      params.tags.forEach(tag => searchParams.append('tags', tag));
    }
    
    const query = searchParams.toString();
    const endpoint = `/community/posts/${query ? `?${query}` : ''}`;
    
    const response = await apiRequest(endpoint);
    return response.json();
  },

  // Get single post
  getPost: async (postId: string) => {
    const response = await apiRequest(`/community/posts/${postId}`);
    return response.json();
  },

  // Create new post
  createPost: async (postData: {
    title: string;
    content: string;
    post_type: 'recipe' | 'tip' | 'savings_story' | 'general';
    recipe_id?: string;
    tags?: string[];
    is_public?: boolean;
  }) => {
    const response = await apiRequest('/community/posts/', {
      method: 'POST',
      body: JSON.stringify(postData),
    });
    return response.json();
  },

  // Update post
  updatePost: async (postId: string, updateData: {
    title?: string;
    content?: string;
    post_type?: 'recipe' | 'tip' | 'savings_story' | 'general';
    recipe_id?: string;
    tags?: string[];
    is_public?: boolean;
  }) => {
    const response = await apiRequest(`/community/posts/${postId}`, {
      method: 'PUT',
      body: JSON.stringify(updateData),
    });
    return response.json();
  },

  // Delete post
  deletePost: async (postId: string) => {
    const response = await apiRequest(`/community/posts/${postId}`, {
      method: 'DELETE',
    });
    return response.status === 204;
  },

  // Like/unlike post
  likePost: async (postId: string) => {
    const response = await apiRequest(`/community/posts/${postId}/like`, {
      method: 'POST',
    });
    return response.json();
  },

  // Get comments for a post
  getComments: async (postId: string, params?: {
    page?: number;
    page_size?: number;
  }) => {
    const searchParams = new URLSearchParams();
    if (params?.page) searchParams.append('page', params.page.toString());
    if (params?.page_size) searchParams.append('page_size', params.page_size.toString());
    
    const query = searchParams.toString();
    const endpoint = `/community/posts/${postId}/comments/${query ? `?${query}` : ''}`;
    
    const response = await apiRequest(endpoint);
    return response.json();
  },

  // Add comment to post
  addComment: async (postId: string, commentData: {
    content: string;
    parent_comment_id?: string;
  }) => {
    const response = await apiRequest(`/community/posts/${postId}/comments/`, {
      method: 'POST',
      body: JSON.stringify(commentData),
    });
    return response.json();
  },

  // Update comment
  updateComment: async (commentId: string, updateData: {
    content?: string;
  }) => {
    const response = await apiRequest(`/community/comments/${commentId}`, {
      method: 'PUT',
      body: JSON.stringify(updateData),
    });
    return response.json();
  },

  // Delete comment
  deleteComment: async (commentId: string) => {
    const response = await apiRequest(`/community/comments/${commentId}`, {
      method: 'DELETE',
    });
    return response.status === 204;
  },

  // Like/unlike comment
  likeComment: async (commentId: string) => {
    const response = await apiRequest(`/community/comments/${commentId}/like`, {
      method: 'POST',
    });
    return response.json();
  },
};

// Leftover Suggestions API service
export const leftoverApi = {
  // Get recipe suggestions based on current pantry items
  getPantrySuggestions: async (filters?: {
    max_suggestions?: number;
    min_match_percentage?: number;
    max_prep_time?: number;
    max_cook_time?: number;
    difficulty_levels?: string[];
    meal_types?: string[];
    dietary_restrictions?: string[];
    exclude_expired?: boolean;
    prioritize_expiring?: boolean;
    include_substitutes?: boolean;
  }) => {
    const searchParams = new URLSearchParams();
    
    if (filters?.max_suggestions) searchParams.append('max_suggestions', filters.max_suggestions.toString());
    if (filters?.min_match_percentage) searchParams.append('min_match_percentage', filters.min_match_percentage.toString());
    if (filters?.max_prep_time) searchParams.append('max_prep_time', filters.max_prep_time.toString());
    if (filters?.max_cook_time) searchParams.append('max_cook_time', filters.max_cook_time.toString());
    if (filters?.difficulty_levels && filters.difficulty_levels.length > 0) {
      searchParams.append('difficulty_level', filters.difficulty_levels[0]);
    }
    if (filters?.meal_types && filters.meal_types.length > 0) {
      searchParams.append('meal_type', filters.meal_types[0]);
    }
    if (filters?.exclude_expired !== undefined) searchParams.append('exclude_expired', filters.exclude_expired.toString());
    if (filters?.prioritize_expiring !== undefined) searchParams.append('include_expiring', filters.prioritize_expiring.toString());
    
    const query = searchParams.toString();
    const endpoint = `/leftovers/suggestions${query ? `?${query}` : ''}`;
    
    const response = await apiRequest(endpoint);
    return response.json();
  },

  // Get custom suggestions with filter object
  getCustomSuggestions: async (filters: {
    max_suggestions?: number;
    min_match_percentage?: number;
    max_prep_time?: number;
    max_cook_time?: number;
    difficulty_levels?: string[];
    meal_types?: string[];
    dietary_restrictions?: string[];
    exclude_expired?: boolean;
    prioritize_expiring?: boolean;
    include_substitutes?: boolean;
  }) => {
    const response = await apiRequest('/leftovers/suggestions/custom', {
      method: 'POST',
      body: JSON.stringify(filters),
    });
    return response.json();
  },

  // Get available ingredients
  getAvailableIngredients: async () => {
    const response = await apiRequest('/leftovers/ingredients');
    return response.json();
  },

  // Get debug suggestions
  getDebugSuggestions: async (filters?: {
    max_suggestions?: number;
    min_match_percentage?: number;
  }) => {
    const searchParams = new URLSearchParams();
    
    if (filters?.max_suggestions) searchParams.append('max_suggestions', filters.max_suggestions.toString());
    if (filters?.min_match_percentage) searchParams.append('min_match_percentage', filters.min_match_percentage.toString());
    
    const query = searchParams.toString();
    const endpoint = `/leftovers/suggestions/debug${query ? `?${query}` : ''}`;
    
    const response = await apiRequest(endpoint);
    return response.json();
  },
};

// Profile API service
export const profileApi = {
  // Get user profile
  getProfile: async () => {
    const response = await apiRequest('/profile/');
    return response.json();
  },

  // Create or update user profile
  updateProfile: async (profileData: {
    dietary_restrictions?: string[];
    allergies?: string[];
    taste_preferences?: string[];
    meal_preferences?: string[];
    kitchen_equipment?: string[];
    weekly_budget?: number;
    zip_code?: string;
    preferred_grocers?: string[];
    subscription?: string;
    trial_ends_at?: string;
  }) => {
    const response = await apiRequest('/profile/', {
      method: 'PUT',
      body: JSON.stringify(profileData),
    });
    return response.json();
  },

  // Add family member
  addFamilyMember: async (memberData: {
    name: string;
    age: number;
    dietary_restrictions?: string[];
    allergies?: string[];
    loved_foods?: string[];
    disliked_foods?: string[];
  }) => {
    console.log('🌐 [API] addFamilyMember called with data:', memberData);
    
    try {
      const response = await apiRequest('/profile/family-members', {
        method: 'POST',
        body: JSON.stringify(memberData),
      });
      
      console.log('🌐 [API] addFamilyMember response status:', response.status);
      const result = await response.json();
      console.log('🌐 [API] addFamilyMember response data:', result);
      
      return result;
    } catch (error) {
      console.error('🌐 [API] addFamilyMember error:', error);
      throw error;
    }
  },

  // Update family member
  updateFamilyMember: async (memberId: string, memberData: {
    name?: string;
    age?: number;
    dietary_restrictions?: string[];
    allergies?: string[];
    loved_foods?: string[];
    disliked_foods?: string[];
  }) => {
    console.log('🌐 [API] updateFamilyMember called with:', { memberId, memberData });
    
    try {
      const response = await apiRequest(`/profile/family-members/${memberId}`, {
        method: 'PUT',
        body: JSON.stringify(memberData),
      });
      
      console.log('🌐 [API] updateFamilyMember response status:', response.status);
      const result = await response.json();
      console.log('🌐 [API] updateFamilyMember response data:', result);
      
      return result;
    } catch (error) {
      console.error('🌐 [API] updateFamilyMember error:', error);
      throw error;
    }
  },

  // Remove family member
  removeFamilyMember: async (memberId: string) => {
    console.log('🌐 [API] removeFamilyMember called with memberId:', memberId);
    
    try {
      const response = await apiRequest(`/profile/family-members/${memberId}`, {
        method: 'DELETE',
      });
      
      console.log('🌐 [API] removeFamilyMember response status:', response.status);
      const result = await response.json();
      console.log('🌐 [API] removeFamilyMember response data:', result);
      
      return result;
    } catch (error) {
      console.error('🌐 [API] removeFamilyMember error:', error);
      throw error;
    }
  },
};

// Receipt API service
export const receiptApi = {
  // Upload receipt image and process it
  uploadAndProcess: async (file: File) => {
    if (shouldUseMockData()) {
      console.log('🧪 [Demo Mode] Using mock receipt processing for file:', file.name);
      // Simulate receipt processing with demo data
      const mockItems = await simulateReceiptProcessing(file.name);
      return {
        success: true,
        items: mockItems,
        message: 'Receipt processed successfully (demo mode)'
      };
    }

    try {
      const formData = new FormData();
      formData.append('file', file);

      // Use a different content type for file upload
      const token = getAuthToken();
      const config: RequestInit = {
        method: 'POST',
        headers: {
          ...(token && { Authorization: `Bearer ${token}` }),
          // Don't set Content-Type - let browser set it with boundary for FormData
        },
        body: formData,
      };

      const response = await fetch(`${API_BASE_URL}/receipts/upload`, config);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Upload failed' }));
        throw new Error(errorData.detail || `HTTP ${response.status}`);
      }
      
      return response.json();
    } catch (error) {
      console.warn('🧪 [Demo Mode] API failed, falling back to mock receipt processing:', error);
      const mockItems = await simulateReceiptProcessing(file.name);
      return {
        success: true,
        items: mockItems,
        message: 'Receipt processed successfully (demo mode fallback)'
      };
    }
  },
};