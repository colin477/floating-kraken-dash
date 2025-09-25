export interface User {
  id: string;
  email: string;
  name: string;
  createdAt: string;
  subscription: 'free' | 'basic' | 'premium';
  trialEndsAt?: string;
  token?: string; // JWT token for API authentication
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
  user_id: string;
  name: string;
  category: PantryCategory;
  quantity: number;
  unit: PantryUnit;
  expiration_date?: string;
  purchase_date?: string;
  notes?: string;
  created_at: string;
  updated_at: string;
  days_until_expiration?: number;
}

export interface PantryItemCreate {
  name: string;
  category: PantryCategory;
  quantity: number;
  unit: PantryUnit;
  expiration_date?: string;
  purchase_date?: string;
  notes?: string;
}

export interface PantryItemUpdate {
  name?: string;
  category?: PantryCategory;
  quantity?: number;
  unit?: PantryUnit;
  expiration_date?: string;
  purchase_date?: string;
  notes?: string;
}

export enum PantryCategory {
  PRODUCE = "produce",
  DAIRY = "dairy",
  MEAT = "meat",
  SEAFOOD = "seafood",
  GRAINS = "grains",
  CANNED_GOODS = "canned_goods",
  FROZEN = "frozen",
  BEVERAGES = "beverages",
  SNACKS = "snacks",
  CONDIMENTS = "condiments",
  SPICES = "spices",
  BAKING = "baking",
  OTHER = "other"
}

export enum PantryUnit {
  PIECE = "piece",
  POUND = "lb",
  OUNCE = "oz",
  GRAM = "g",
  KILOGRAM = "kg",
  CUP = "cup",
  TABLESPOON = "tbsp",
  TEASPOON = "tsp",
  LITER = "L",
  MILLILITER = "ml",
  GALLON = "gal",
  QUART = "qt",
  PINT = "pt",
  FLUID_OUNCE = "fl oz",
  PACKAGE = "package",
  CAN = "can",
  BOTTLE = "bottle",
  BAG = "bag",
  BOX = "box",
  CONTAINER = "container"
}

export interface PantryItemsListResponse {
  items: PantryItem[];
  total_count: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface ExpiringItemsResponse {
  expiring_soon: PantryItem[];
  expired: PantryItem[];
  days_threshold: number;
}

export interface PantryStatsResponse {
  total_items: number;
  items_by_category: Record<string, number>;
  expiring_soon_count: number;
  expired_count: number;
  total_value_estimate?: number;
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

// Sprint 6: Community Features Types
export interface CommunityPost {
  id: string;
  user_id: string;
  title: string;
  content: string;
  post_type: 'recipe' | 'tip' | 'savings_story' | 'general';
  recipe_id?: string;
  tags: string[];
  likes_count: number;
  comments_count: number;
  is_public: boolean;
  created_at: string;
  updated_at: string;
  user_display_name?: string;
  user_avatar_url?: string;
  is_liked_by_user?: boolean;
  recipe_title?: string;
}

export interface CommunityPostCreate {
  title: string;
  content: string;
  post_type: 'recipe' | 'tip' | 'savings_story' | 'general';
  recipe_id?: string;
  tags?: string[];
  is_public?: boolean;
}

export interface CommunityPostUpdate {
  title?: string;
  content?: string;
  post_type?: 'recipe' | 'tip' | 'savings_story' | 'general';
  recipe_id?: string;
  tags?: string[];
  is_public?: boolean;
}

export interface Comment {
  id: string;
  post_id: string;
  user_id: string;
  content: string;
  parent_comment_id?: string;
  likes_count: number;
  created_at: string;
  updated_at: string;
  user_display_name?: string;
  user_avatar_url?: string;
  is_liked_by_user?: boolean;
  replies?: Comment[];
}

export interface CommentCreate {
  content: string;
  parent_comment_id?: string;
}

export interface CommentUpdate {
  content?: string;
}

export interface CommunityPostsListResponse {
  posts: CommunityPost[];
  total_count: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface CommentsListResponse {
  comments: Comment[];
  total_count: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// Sprint 6: Leftover Suggestions Types
export interface IngredientMatch {
  required_ingredient: string;
  available_ingredient?: string;
  match_type: 'exact' | 'fuzzy' | 'category' | 'substitute';
  match_confidence: number;
  is_matched: boolean;
  quantity_available?: number;
  quantity_required?: number;
  unit?: string;
  notes?: string;
}

export interface LeftoverSuggestion {
  recipe: Recipe;
  match_score: number;
  match_percentage: number;
  matched_ingredients: IngredientMatch[];
  missing_ingredients: IngredientMatch[];
  total_ingredients: number;
  available_ingredients_count: number;
  missing_ingredients_count: number;
  suggestion_reason: string;
  priority_score: number;
  estimated_prep_time?: number;
  difficulty_bonus: number;
  freshness_bonus: number;
  expiration_urgency: number;
}

export interface LeftoverSuggestionsResponse {
  suggestions: LeftoverSuggestion[];
  total_suggestions: number;
  user_id: string;
  pantry_items_count: number;
  recipes_analyzed: number;
  min_match_percentage: number;
  generated_at: string;
  filters_applied: Record<string, any>;
  performance_metrics?: Record<string, any>;
}

export interface SuggestionFilters {
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
}

export interface SuggestionRequest {
  ingredients: string[];
  filters?: SuggestionFilters;
  include_debug_info?: boolean;
  force_refresh?: boolean;
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