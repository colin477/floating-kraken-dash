import { User, UserProfile, Recipe, MealPlan, PantryItem, Receipt, CommunityPost } from '@/types';

const STORAGE_KEYS = {
  USER: 'ez-eatin-user',
  PROFILE: 'ez-eatin-profile',
  PANTRY: 'ez-eatin-pantry',
  RECIPES: 'ez-eatin-recipes',
  MEAL_PLANS: 'ez-eatin-meal-plans',
  RECEIPTS: 'ez-eatin-receipts',
  COMMUNITY_POSTS: 'ez-eatin-community-posts',
} as const;

export const storage = {
  // User management
  getUser: (): User | null => {
    const user = localStorage.getItem(STORAGE_KEYS.USER);
    return user ? JSON.parse(user) : null;
  },

  setUser: (user: User): void => {
    localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(user));
  },

  clearUser: (): void => {
    localStorage.removeItem(STORAGE_KEYS.USER);
  },

  // Clear all user data - reset to beginning
  clearAllUserData: (): void => {
    Object.values(STORAGE_KEYS).forEach(key => {
      localStorage.removeItem(key);
    });
  },

  // Profile management
  getProfile: (): UserProfile | null => {
    const profile = localStorage.getItem(STORAGE_KEYS.PROFILE);
    return profile ? JSON.parse(profile) : null;
  },

  setProfile: (profile: UserProfile): void => {
    localStorage.setItem(STORAGE_KEYS.PROFILE, JSON.stringify(profile));
  },

  // Pantry management
  getPantryItems: (): PantryItem[] => {
    const items = localStorage.getItem(STORAGE_KEYS.PANTRY);
    return items ? JSON.parse(items) : [];
  },

  setPantryItems: (items: PantryItem[]): void => {
    localStorage.setItem(STORAGE_KEYS.PANTRY, JSON.stringify(items));
  },

  addPantryItem: (item: PantryItem): void => {
    const items = storage.getPantryItems();
    items.push(item);
    storage.setPantryItems(items);
  },

  // Recipe management
  getRecipes: (): Recipe[] => {
    const recipes = localStorage.getItem(STORAGE_KEYS.RECIPES);
    return recipes ? JSON.parse(recipes) : [];
  },

  setRecipes: (recipes: Recipe[]): void => {
    localStorage.setItem(STORAGE_KEYS.RECIPES, JSON.stringify(recipes));
  },

  addRecipe: (recipe: Recipe): void => {
    const recipes = storage.getRecipes();
    recipes.push(recipe);
    storage.setRecipes(recipes);
  },

  // Meal plan management
  getMealPlans: (): MealPlan[] => {
    const plans = localStorage.getItem(STORAGE_KEYS.MEAL_PLANS);
    return plans ? JSON.parse(plans) : [];
  },

  setMealPlans: (plans: MealPlan[]): void => {
    localStorage.setItem(STORAGE_KEYS.MEAL_PLANS, JSON.stringify(plans));
  },

  addMealPlan: (plan: MealPlan): void => {
    const plans = storage.getMealPlans();
    plans.push(plan);
    storage.setMealPlans(plans);
  },

  // Receipt management
  getReceipts: (): Receipt[] => {
    const receipts = localStorage.getItem(STORAGE_KEYS.RECEIPTS);
    return receipts ? JSON.parse(receipts) : [];
  },

  setReceipts: (receipts: Receipt[]): void => {
    localStorage.setItem(STORAGE_KEYS.RECEIPTS, JSON.stringify(receipts));
  },

  addReceipt: (receipt: Receipt): void => {
    const receipts = storage.getReceipts();
    receipts.push(receipt);
    storage.setReceipts(receipts);
  },

  // Community management
  getCommunityPosts: (): CommunityPost[] => {
    const posts = localStorage.getItem(STORAGE_KEYS.COMMUNITY_POSTS);
    return posts ? JSON.parse(posts) : [];
  },

  setCommunityPosts: (posts: CommunityPost[]): void => {
    localStorage.setItem(STORAGE_KEYS.COMMUNITY_POSTS, JSON.stringify(posts));
  },

  addCommunityPost: (post: CommunityPost): void => {
    const posts = storage.getCommunityPosts();
    posts.push(post);
    storage.setCommunityPosts(posts);
  },
};