export interface User {
  id: string;
  email: string;
  name: string;
  createdAt: string;
  subscription: 'free' | 'basic' | 'premium';
  trialEndsAt?: string;
  monthlyUsage?: {
    receiptScans: number;
    mealPlans: number;
    communityPosts: number;
  };
}

export interface UserProfile {
  userId: string;
  dietaryRestrictions: string[];
  allergies: string[];
  tastePreferences: string[];
  mealPreferences: string[];
  kitchenEquipment: string[];
  weeklyBudget: number;
  zipCode: string;
  familyMembers: FamilyMember[];
  preferredGrocers?: string[];
}

export interface FamilyMember {
  id: string;
  name: string;
  age: number;
  dietaryRestrictions: string[];
  allergies: string[];
  lovedFoods: string[];
  dislikedFoods: string[];
}

export interface PantryItem {
  id: string;
  name: string;
  quantity: number;
  unit: string;
  expirationDate?: string;
  source: 'receipt' | 'manual';
  addedAt: string;
}

export interface Recipe {
  id: string;
  title: string;
  description: string;
  ingredients: RecipeIngredient[];
  instructions: string[];
  prepTime: number;
  cookTime: number;
  servings: number;
  difficulty: 'easy' | 'medium' | 'hard';
  tags: string[];
  nutritionInfo?: NutritionInfo;
  source: 'ai-generated' | 'community' | 'photo-analysis';
  createdAt: string;
}

export interface RecipeIngredient {
  name: string;
  quantity: number;
  unit: string;
  optional?: boolean;
}

export interface NutritionInfo {
  calories: number;
  protein: number;
  carbs: number;
  fat: number;
  fiber: number;
}

export interface MealPlan {
  id: string;
  userId: string;
  weekStarting: string;
  meals: PlannedMeal[];
  shoppingList: ShoppingListItem[];
  totalEstimatedCost: number;
  createdAt: string;
}

export interface PlannedMeal {
  id: string;
  day: string;
  mealType: 'breakfast' | 'lunch' | 'dinner' | 'snack';
  recipe: Recipe;
  servings: number;
}

export interface ShoppingListItem {
  id: string;
  name: string;
  quantity: number;
  unit: string;
  estimatedPrice: number;
  store: string;
  category: string;
  purchased: boolean;
}

export interface Receipt {
  id: string;
  userId: string;
  imageUrl: string;
  items: ReceiptItem[];
  total: number;
  store: string;
  date: string;
  processed: boolean;
}

export interface ReceiptItem {
  name: string;
  quantity: number;
  price: number;
  category: string;
}

export interface CommunityPost {
  id: string;
  userId: string;
  userName: string;
  title: string;
  content: string;
  type: 'recipe' | 'tip' | 'savings-story';
  likes: number;
  comments: Comment[];
  createdAt: string;
}

export interface Comment {
  id: string;
  userId: string;
  userName: string;
  content: string;
  createdAt: string;
}

// Subscription limits
export const SUBSCRIPTION_LIMITS = {
  free: {
    receiptScansPerMonth: 5,
    mealPlansPerWeek: 0, // No meal plans
    shoppingListsPerWeek: 1,
    communityPosts: 0, // Browse only
    storeDeals: 0, // No store deals
    familyProfiles: 0 // No family profiles
  },
  basic: {
    receiptScansPerMonth: -1, // Unlimited
    mealPlansPerWeek: -1, // Unlimited
    shoppingListsPerWeek: -1, // Unlimited
    communityPosts: -1, // Unlimited
    storeDeals: 2, // 1-2 stores max
    familyProfiles: 0 // No family profiles
  },
  premium: {
    receiptScansPerMonth: -1, // Unlimited
    mealPlansPerWeek: -1, // Unlimited
    shoppingListsPerWeek: -1, // Unlimited
    communityPosts: -1, // Unlimited
    storeDeals: -1, // All stores
    familyProfiles: -1 // Unlimited family profiles
  }
} as const;