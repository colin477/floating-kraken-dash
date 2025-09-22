import { Recipe, PantryItem, ReceiptItem, ShoppingListItem, CommunityPost } from '@/types';

export const mockRecipes: Recipe[] = [
  {
    id: '1',
    title: 'Quick Chicken Stir Fry',
    description: 'A delicious and healthy stir fry using ingredients from your pantry',
    ingredients: [
      { name: 'Chicken breast', quantity: 1, unit: 'lb' },
      { name: 'Bell peppers', quantity: 2, unit: 'pieces' },
      { name: 'Onion', quantity: 1, unit: 'piece' },
      { name: 'Soy sauce', quantity: 3, unit: 'tbsp' },
      { name: 'Garlic', quantity: 3, unit: 'cloves' },
      { name: 'Rice', quantity: 1, unit: 'cup' }
    ],
    instructions: [
      'Cook rice according to package instructions',
      'Cut chicken into bite-sized pieces',
      'Heat oil in a large pan over medium-high heat',
      'Cook chicken until golden brown, about 5-7 minutes',
      'Add vegetables and cook for 3-4 minutes',
      'Add soy sauce and garlic, stir for 1 minute',
      'Serve over rice'
    ],
    prepTime: 15,
    cookTime: 20,
    servings: 4,
    difficulty: 'easy',
    tags: ['quick', 'healthy', 'family-friendly'],
    nutritionInfo: {
      calories: 320,
      protein: 28,
      carbs: 35,
      fat: 8,
      fiber: 3
    },
    source: 'ai-generated',
    createdAt: new Date().toISOString()
  },
  {
    id: '2',
    title: 'Leftover Turkey Sandwich',
    description: 'Transform your leftover turkey into a gourmet sandwich',
    ingredients: [
      { name: 'Turkey slices', quantity: 4, unit: 'oz' },
      { name: 'Bread', quantity: 2, unit: 'slices' },
      { name: 'Lettuce', quantity: 2, unit: 'leaves' },
      { name: 'Tomato', quantity: 1, unit: 'piece' },
      { name: 'Mayo', quantity: 1, unit: 'tbsp' }
    ],
    instructions: [
      'Toast bread slices lightly',
      'Spread mayo on one slice',
      'Layer turkey, lettuce, and tomato',
      'Top with second slice of bread',
      'Cut diagonally and serve'
    ],
    prepTime: 5,
    cookTime: 0,
    servings: 1,
    difficulty: 'easy',
    tags: ['quick', 'leftovers', 'lunch'],
    source: 'ai-generated',
    createdAt: new Date().toISOString()
  }
];

export const mockCommunityPosts: CommunityPost[] = [
  {
    id: '1',
    userId: 'user1',
    userName: 'Sarah M.',
    title: 'Saved $50 this week with EZ Eatin!',
    content: 'By following the AI meal plan and shopping at the recommended stores, I cut my grocery bill from $150 to $100. The kids loved the recipes too!',
    type: 'savings-story',
    likes: 23,
    comments: [
      {
        id: '1',
        userId: 'user2',
        userName: 'Mike D.',
        content: 'That\'s amazing! Which stores did you shop at?',
        createdAt: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString()
      }
    ],
    createdAt: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString()
  },
  {
    id: '2',
    userId: 'user3',
    userName: 'Jennifer L.',
    title: 'Pro tip: Batch cook on Sundays',
    content: 'I spend 2 hours every Sunday preparing ingredients for the week. It makes weeknight cooking so much faster!',
    type: 'tip',
    likes: 15,
    comments: [],
    createdAt: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString()
  }
];

// AI simulation functions
export const simulateReceiptProcessing = (receiptImage: string): Promise<ReceiptItem[]> => {
  return new Promise((resolve) => {
    setTimeout(() => {
      const mockItems: ReceiptItem[] = [
        { name: 'Chicken breast', quantity: 2, price: 8.99, category: 'meat' },
        { name: 'Bell peppers', quantity: 3, price: 2.49, category: 'produce' },
        { name: 'Onions', quantity: 1, price: 1.29, category: 'produce' },
        { name: 'Rice', quantity: 1, price: 3.99, category: 'pantry' },
        { name: 'Soy sauce', quantity: 1, price: 2.79, category: 'condiments' },
        { name: 'Eggs', quantity: 12, price: 3.49, category: 'dairy' },
        { name: 'Milk', quantity: 1, price: 3.29, category: 'dairy' }
      ];
      resolve(mockItems);
    }, 2000);
  });
};

export const simulateMealPhotoAnalysis = (mealImage: string): Promise<Recipe> => {
  return new Promise((resolve) => {
    setTimeout(() => {
      const mockRecipe: Recipe = {
        id: Date.now().toString(),
        title: 'Analyzed Pasta Dish',
        description: 'AI-analyzed recipe based on your meal photo',
        ingredients: [
          { name: 'Pasta', quantity: 8, unit: 'oz' },
          { name: 'Tomato sauce', quantity: 1, unit: 'cup' },
          { name: 'Ground beef', quantity: 0.5, unit: 'lb' },
          { name: 'Onion', quantity: 0.5, unit: 'piece' },
          { name: 'Garlic', quantity: 2, unit: 'cloves' },
          { name: 'Parmesan cheese', quantity: 0.25, unit: 'cup' }
        ],
        instructions: [
          'Cook pasta according to package directions',
          'Brown ground beef in a large pan',
          'Add diced onion and garlic, cook until soft',
          'Add tomato sauce and simmer for 10 minutes',
          'Combine with pasta and top with cheese'
        ],
        prepTime: 10,
        cookTime: 25,
        servings: 4,
        difficulty: 'easy',
        tags: ['comfort-food', 'family-friendly'],
        source: 'photo-analysis',
        createdAt: new Date().toISOString()
      };
      resolve(mockRecipe);
    }, 3000);
  });
};

export const generateMealPlan = (pantryItems: PantryItem[], preferences: any): Promise<{ recipes: Recipe[], shoppingList: ShoppingListItem[] }> => {
  return new Promise((resolve) => {
    setTimeout(() => {
      const weeklyRecipes = [
        mockRecipes[0],
        mockRecipes[1],
        {
          ...mockRecipes[0],
          id: '3',
          title: 'Pantry Pasta',
          description: 'Simple pasta using your pantry ingredients'
        }
      ];

      const shoppingList: ShoppingListItem[] = [
        { id: '1', name: 'Fresh basil', quantity: 1, unit: 'bunch', estimatedPrice: 2.99, store: 'Kroger', category: 'produce', purchased: false },
        { id: '2', name: 'Parmesan cheese', quantity: 1, unit: 'container', estimatedPrice: 4.99, store: 'Kroger', category: 'dairy', purchased: false },
        { id: '3', name: 'Olive oil', quantity: 1, unit: 'bottle', estimatedPrice: 5.99, store: 'Walmart', category: 'pantry', purchased: false }
      ];

      resolve({ recipes: weeklyRecipes, shoppingList });
    }, 2500);
  });
};