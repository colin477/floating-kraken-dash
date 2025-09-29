import React from 'react'
import { render, RenderOptions } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import AuthProvider from '../contexts/AuthContext'
import { vi } from 'vitest'

// Create a custom render function that includes providers
const AllTheProviders = ({ children }: { children: React.ReactNode }) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  })

  return (
    <BrowserRouter>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          {children}
        </AuthProvider>
      </QueryClientProvider>
    </BrowserRouter>
  )
}

const customRender = (
  ui: React.ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) => render(ui, { wrapper: AllTheProviders, ...options })

export * from '@testing-library/react'
export { customRender as render }

// Mock user data for testing
export const mockUser = {
  id: 'test-user-id',
  email: 'test@example.com',
  full_name: 'Test User',
  is_active: true,
  is_verified: true,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z'
}

export const mockAuthTokens = {
  access_token: 'mock-access-token',
  refresh_token: 'mock-refresh-token',
  token_type: 'bearer',
  expires_in: 3600
}

export const mockProfile = {
  id: 'test-profile-id',
  user_id: 'test-user-id',
  dietary_restrictions: ['vegetarian'],
  allergies: ['nuts'],
  cooking_skill: 'intermediate',
  household_size: 2,
  budget_range: 'medium',
  preferred_cuisines: ['italian', 'mexican'],
  meal_prep_time: '30-60',
  kitchen_equipment: ['oven', 'stovetop', 'microwave'],
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z'
}

export const mockPantryItem = {
  id: 'test-pantry-item-id',
  user_id: 'test-user-id',
  name: 'Test Tomatoes',
  category: 'vegetables',
  quantity: 5,
  unit: 'pieces',
  expiry_date: '2024-12-31',
  location: 'refrigerator',
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z'
}

export const mockRecipe = {
  id: 'test-recipe-id',
  user_id: 'test-user-id',
  title: 'Test Recipe',
  description: 'A test recipe for testing',
  ingredients: [
    { name: 'tomatoes', quantity: 2, unit: 'pieces' },
    { name: 'onion', quantity: 1, unit: 'piece' }
  ],
  instructions: [
    'Chop the tomatoes',
    'Dice the onion',
    'Cook together'
  ],
  prep_time: 15,
  cook_time: 30,
  servings: 4,
  difficulty: 'easy',
  cuisine: 'italian',
  tags: ['vegetarian', 'healthy'],
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z'
}

// Helper function to create mock API responses
export const createMockResponse = <T,>(data: T, status = 200) => ({
  ok: status >= 200 && status < 300,
  status,
  json: async () => data,
  text: async () => JSON.stringify(data),
})

// Helper function to wait for async operations
export const waitFor = (ms: number) => new Promise(resolve => setTimeout(resolve, ms))

// Helper function to create mock events
export const createMockEvent = (type: string, properties: Record<string, any> = {}) => ({
  type,
  preventDefault: vi.fn(),
  stopPropagation: vi.fn(),
  target: { value: '' },
  currentTarget: { value: '' },
  ...properties,
})

// Helper function to mock API calls
export const mockApiCall = (endpoint: string, response: any, status = 200) => {
  global.fetch = vi.fn().mockImplementation((url: string) => {
    if (url.includes(endpoint)) {
      return Promise.resolve(createMockResponse(response, status))
    }
    return Promise.reject(new Error(`Unexpected API call to ${url}`))
  })
}

// Helper function to mock multiple API calls
export const mockMultipleApiCalls = (mocks: Array<{ endpoint: string; response: any; status?: number }>) => {
  global.fetch = vi.fn().mockImplementation((url: string) => {
    const mock = mocks.find(m => url.includes(m.endpoint))
    if (mock) {
      return Promise.resolve(createMockResponse(mock.response, mock.status || 200))
    }
    return Promise.reject(new Error(`Unexpected API call to ${url}`))
  })
}

// Helper function to reset all mocks
export const resetAllMocks = () => {
  vi.clearAllMocks()
  localStorage.clear()
  sessionStorage.clear()
}