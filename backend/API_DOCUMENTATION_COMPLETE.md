# EZ Eatin' API Documentation - Complete Reference

## Overview

The EZ Eatin' API is a comprehensive meal planning and recipe management system built with FastAPI. This documentation covers all endpoints available in the production system, including authentication, user profiles, pantry management, recipes, meal planning, shopping lists, community features, and leftover suggestions.

**Base URL**: `https://ezeatin-backend.onrender.com/api/v1`  
**Authentication**: Bearer Token (JWT)  
**Content Type**: `application/json`

## Table of Contents

1. [Authentication](#authentication)
2. [User Profile Management](#user-profile-management)
3. [Pantry Management](#pantry-management)
4. [Recipe Management](#recipe-management)
5. [Meal Planning](#meal-planning)
6. [Shopping Lists](#shopping-lists)
7. [Receipt Processing](#receipt-processing)
8. [Community Features](#community-features)
9. [Leftover Suggestions](#leftover-suggestions)
10. [Error Handling](#error-handling)
11. [Rate Limiting](#rate-limiting)

---

## Authentication

All authenticated endpoints require a Bearer token in the Authorization header:
```
Authorization: Bearer <your_jwt_token>
```

### Register User
**POST** `/auth/signup`

Create a new user account.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123",
  "full_name": "John Doe"
}
```

**Response (201):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400,
  "user": {
    "id": "507f1f77bcf86cd799439011",
    "email": "user@example.com",
    "full_name": "John Doe",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z",
    "is_active": true
  }
}
```

### Login
**POST** `/auth/login`

Authenticate user and receive access token.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400,
  "user": {
    "id": "507f1f77bcf86cd799439011",
    "email": "user@example.com",
    "full_name": "John Doe",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z",
    "is_active": true
  }
}
```

### Get Current User
**GET** `/auth/me`

Get current authenticated user information.

**Headers:**
```
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "id": "507f1f77bcf86cd799439011",
  "email": "user@example.com",
  "full_name": "John Doe",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "is_active": true
}
```

### Logout
**POST** `/auth/logout`

Logout current user (invalidate token).

**Headers:**
```
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "message": "Successfully logged out",
  "success": true
}
```

---

## User Profile Management

### Get User Profile
**GET** `/profile/`

Retrieve the current user's profile information.

**Headers:**
```
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "id": "507f1f77bcf86cd799439011",
  "user_id": "507f1f77bcf86cd799439011",
  "dietary_restrictions": ["vegetarian", "gluten_free"],
  "allergies": ["nuts", "shellfish"],
  "family_members": [
    {
      "id": "member_1",
      "name": "Jane Doe",
      "age": 8,
      "dietary_restrictions": ["dairy_free"],
      "allergies": ["milk"]
    }
  ],
  "preferences": {
    "cuisine_types": ["italian", "mexican"],
    "cooking_skill": "intermediate",
    "meal_prep_time": 30,
    "budget_per_week": 150.00
  },
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

### Update User Profile
**PUT** `/profile/`

Update the current user's profile information.

**Headers:**
```
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "dietary_restrictions": ["vegetarian", "gluten_free"],
  "allergies": ["nuts"],
  "preferences": {
    "cuisine_types": ["italian", "mexican", "asian"],
    "cooking_skill": "advanced",
    "meal_prep_time": 45,
    "budget_per_week": 200.00
  }
}
```

**Response (200):**
```json
{
  "id": "507f1f77bcf86cd799439011",
  "user_id": "507f1f77bcf86cd799439011",
  "dietary_restrictions": ["vegetarian", "gluten_free"],
  "allergies": ["nuts"],
  "family_members": [
    {
      "id": "member_1",
      "name": "Jane Doe",
      "age": 8,
      "dietary_restrictions": ["dairy_free"],
      "allergies": ["milk"]
    }
  ],
  "preferences": {
    "cuisine_types": ["italian", "mexican", "asian"],
    "cooking_skill": "advanced",
    "meal_prep_time": 45,
    "budget_per_week": 200.00
  },
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T11:45:00Z"
}
```

### Add Family Member
**POST** `/profile/family-members`

Add a new family member to the user's profile.

**Headers:**
```
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "name": "Bob Doe",
  "age": 12,
  "dietary_restrictions": ["vegetarian"],
  "allergies": []
}
```

**Response (200):**
```json
{
  "id": "507f1f77bcf86cd799439011",
  "user_id": "507f1f77bcf86cd799439011",
  "dietary_restrictions": ["vegetarian", "gluten_free"],
  "allergies": ["nuts"],
  "family_members": [
    {
      "id": "member_1",
      "name": "Jane Doe",
      "age": 8,
      "dietary_restrictions": ["dairy_free"],
      "allergies": ["milk"]
    },
    {
      "id": "member_2",
      "name": "Bob Doe",
      "age": 12,
      "dietary_restrictions": ["vegetarian"],
      "allergies": []
    }
  ],
  "preferences": {
    "cuisine_types": ["italian", "mexican", "asian"],
    "cooking_skill": "advanced",
    "meal_prep_time": 45,
    "budget_per_week": 200.00
  },
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T12:00:00Z"
}
```

### Update Family Member
**PUT** `/profile/family-members/{member_id}`

Update an existing family member's information.

**Headers:**
```
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "name": "Jane Smith",
  "age": 9,
  "dietary_restrictions": ["dairy_free", "gluten_free"],
  "allergies": ["milk", "wheat"]
}
```

**Response (200):**
```json
{
  "id": "507f1f77bcf86cd799439011",
  "user_id": "507f1f77bcf86cd799439011",
  "dietary_restrictions": ["vegetarian", "gluten_free"],
  "allergies": ["nuts"],
  "family_members": [
    {
      "id": "member_1",
      "name": "Jane Smith",
      "age": 9,
      "dietary_restrictions": ["dairy_free", "gluten_free"],
      "allergies": ["milk", "wheat"]
    },
    {
      "id": "member_2",
      "name": "Bob Doe",
      "age": 12,
      "dietary_restrictions": ["vegetarian"],
      "allergies": []
    }
  ],
  "preferences": {
    "cuisine_types": ["italian", "mexican", "asian"],
    "cooking_skill": "advanced",
    "meal_prep_time": 45,
    "budget_per_week": 200.00
  },
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T12:15:00Z"
}
```

### Remove Family Member
**DELETE** `/profile/family-members/{member_id}`

Remove a family member from the user's profile.

**Headers:**
```
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "id": "507f1f77bcf86cd799439011",
  "user_id": "507f1f77bcf86cd799439011",
  "dietary_restrictions": ["vegetarian", "gluten_free"],
  "allergies": ["nuts"],
  "family_members": [
    {
      "id": "member_2",
      "name": "Bob Doe",
      "age": 12,
      "dietary_restrictions": ["vegetarian"],
      "allergies": []
    }
  ],
  "preferences": {
    "cuisine_types": ["italian", "mexican", "asian"],
    "cooking_skill": "advanced",
    "meal_prep_time": 45,
    "budget_per_week": 200.00
  },
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T12:30:00Z"
}
```

---

## Pantry Management

### Get Pantry Items
**GET** `/pantry/`

Retrieve all pantry items for the current user.

**Headers:**
```
Authorization: Bearer <token>
```

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `page_size` (optional): Items per page (default: 50)
- `category` (optional): Filter by category
- `expiring_soon` (optional): Filter items expiring within days

**Response (200):**
```json
{
  "pantry_items": [
    {
      "id": "507f1f77bcf86cd799439012",
      "user_id": "507f1f77bcf86cd799439011",
      "name": "Chicken Breast",
      "category": "meat",
      "quantity": 2.5,
      "unit": "lbs",
      "expiration_date": "2024-01-20",
      "purchase_date": "2024-01-15",
      "location": "freezer",
      "notes": "Organic, free-range",
      "estimated_value": 12.99,
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total_count": 25,
  "page": 1,
  "page_size": 50,
  "total_pages": 1
}
```

### Add Pantry Item
**POST** `/pantry/`

Add a new item to the user's pantry.

**Headers:**
```
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "name": "Tomatoes",
  "category": "produce",
  "quantity": 6,
  "unit": "pieces",
  "expiration_date": "2024-01-18",
  "purchase_date": "2024-01-15",
  "location": "refrigerator",
  "notes": "Roma tomatoes",
  "estimated_value": 4.50
}
```

**Response (201):**
```json
{
  "id": "507f1f77bcf86cd799439013",
  "user_id": "507f1f77bcf86cd799439011",
  "name": "Tomatoes",
  "category": "produce",
  "quantity": 6,
  "unit": "pieces",
  "expiration_date": "2024-01-18",
  "purchase_date": "2024-01-15",
  "location": "refrigerator",
  "notes": "Roma tomatoes",
  "estimated_value": 4.50,
  "created_at": "2024-01-15T11:00:00Z",
  "updated_at": "2024-01-15T11:00:00Z"
}
```

### Get Pantry Item
**GET** `/pantry/{item_id}`

Retrieve a specific pantry item.

**Headers:**
```
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "id": "507f1f77bcf86cd799439013",
  "user_id": "507f1f77bcf86cd799439011",
  "name": "Tomatoes",
  "category": "produce",
  "quantity": 6,
  "unit": "pieces",
  "expiration_date": "2024-01-18",
  "purchase_date": "2024-01-15",
  "location": "refrigerator",
  "notes": "Roma tomatoes",
  "estimated_value": 4.50,
  "created_at": "2024-01-15T11:00:00Z",
  "updated_at": "2024-01-15T11:00:00Z"
}
```

### Update Pantry Item
**PUT** `/pantry/{item_id}`

Update an existing pantry item.

**Headers:**
```
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "quantity": 4,
  "notes": "Used 2 for salad"
}
```

**Response (200):**
```json
{
  "id": "507f1f77bcf86cd799439013",
  "user_id": "507f1f77bcf86cd799439011",
  "name": "Tomatoes",
  "category": "produce",
  "quantity": 4,
  "unit": "pieces",
  "expiration_date": "2024-01-18",
  "purchase_date": "2024-01-15",
  "location": "refrigerator",
  "notes": "Used 2 for salad",
  "estimated_value": 4.50,
  "created_at": "2024-01-15T11:00:00Z",
  "updated_at": "2024-01-15T14:30:00Z"
}
```

### Delete Pantry Item
**DELETE** `/pantry/{item_id}`

Remove an item from the pantry.

**Headers:**
```
Authorization: Bearer <token>
```

**Response (204):**
```
No Content
```

### Get Expiring Items
**GET** `/pantry/expiring/items`

Get items that are expiring soon.

**Headers:**
```
Authorization: Bearer <token>
```

**Query Parameters:**
- `days` (optional): Number of days to look ahead (default: 7)

**Response (200):**
```json
{
  "expiring_items": [
    {
      "id": "507f1f77bcf86cd799439013",
      "user_id": "507f1f77bcf86cd799439011",
      "name": "Tomatoes",
      "category": "produce",
      "quantity": 4,
      "unit": "pieces",
      "expiration_date": "2024-01-18",
      "days_until_expiration": 3,
      "estimated_value": 4.50
    }
  ],
  "total_count": 1,
  "total_value_at_risk": 4.50
}
```

### Get Pantry Statistics
**GET** `/pantry/stats/overview`

Get pantry statistics and insights.

**Headers:**
```
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "total_items": 25,
  "total_estimated_value": 156.75,
  "items_by_category": {
    "produce": 8,
    "meat": 4,
    "dairy": 6,
    "grains": 7
  },
  "expiring_soon_count": 3,
  "expiring_soon_value": 12.50,
  "items_by_location": {
    "refrigerator": 12,
    "freezer": 8,
    "pantry": 5
  }
}
```

### Search Pantry Items
**GET** `/pantry/search/items`

Search pantry items by name or category.

**Headers:**
```
Authorization: Bearer <token>
```

**Query Parameters:**
- `q`: Search query
- `category` (optional): Filter by category

**Response (200):**
```json
[
  {
    "id": "507f1f77bcf86cd799439013",
    "user_id": "507f1f77bcf86cd799439011",
    "name": "Tomatoes",
    "category": "produce",
    "quantity": 4,
    "unit": "pieces",
    "expiration_date": "2024-01-18",
    "purchase_date": "2024-01-15",
    "location": "refrigerator",
    "notes": "Used 2 for salad",
    "estimated_value": 4.50,
    "created_at": "2024-01-15T11:00:00Z",
    "updated_at": "2024-01-15T14:30:00Z"
  }
]
```

---

## Recipe Management

### Get User Recipes
**GET** `/recipes/`

Retrieve all recipes for the current user.

**Headers:**
```
Authorization: Bearer <token>
```

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `page_size` (optional): Items per page (default: 20)
- `difficulty` (optional): Filter by difficulty (easy, medium, hard)
- `meal_type` (optional): Filter by meal type
- `tags` (optional): Filter by tags (comma-separated)

**Response (200):**
```json
{
  "recipes": [
    {
      "id": "507f1f77bcf86cd799439014",
      "user_id": "507f1f77bcf86cd799439011",
      "title": "Chicken Parmesan",
      "description": "Classic Italian-American dish with breaded chicken",
      "ingredients": [
        {
          "name": "Chicken Breast",
          "quantity": 2,
          "unit": "pieces",
          "notes": "Pounded thin"
        },
        {
          "name": "Breadcrumbs",
          "quantity": 1,
          "unit": "cup",
          "notes": "Italian seasoned"
        }
      ],
      "instructions": [
        "Preheat oven to 375°F",
        "Bread the chicken with flour, egg, and breadcrumbs",
        "Bake for 25 minutes until golden"
      ],
      "prep_time": 15,
      "cook_time": 25,
      "total_time": 40,
      "servings": 4,
      "difficulty": "medium",
      "tags": ["italian", "comfort-food", "family-friendly"],
      "meal_types": ["dinner"],
      "dietary_restrictions": [],
      "nutrition_info": {
        "calories_per_serving": 450,
        "protein_g": 35,
        "carbs_g": 25,
        "fat_g": 22
      },
      "photo_url": "https://example.com/chicken-parm.jpg",
      "source_url": null,
      "created_at": "2024-01-15T12:00:00Z",
      "updated_at": "2024-01-15T12:00:00Z"
    }
  ],
  "total_count": 15,
  "page": 1,
  "page_size": 20,
  "total_pages": 1
}
```

### Create Recipe
**POST** `/recipes/`

Create a new recipe.

**Headers:**
```
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "title": "Vegetable Stir Fry",
  "description": "Quick and healthy vegetable stir fry",
  "ingredients": [
    {
      "name": "Mixed Vegetables",
      "quantity": 2,
      "unit": "cups",
      "notes": "Bell peppers, broccoli, carrots"
    },
    {
      "name": "Soy Sauce",
      "quantity": 2,
      "unit": "tablespoons",
      "notes": "Low sodium"
    }
  ],
  "instructions": [
    "Heat oil in wok over high heat",
    "Add vegetables and stir fry for 5 minutes",
    "Add soy sauce and cook 2 more minutes"
  ],
  "prep_time": 10,
  "cook_time": 7,
  "servings": 2,
  "difficulty": "easy",
  "tags": ["vegetarian", "quick", "healthy"],
  "meal_types": ["lunch", "dinner"],
  "dietary_restrictions": ["vegetarian", "vegan"]
}
```

**Response (201):**
```json
{
  "id": "507f1f77bcf86cd799439015",
  "user_id": "507f1f77bcf86cd799439011",
  "title": "Vegetable Stir Fry",
  "description": "Quick and healthy vegetable stir fry",
  "ingredients": [
    {
      "name": "Mixed Vegetables",
      "quantity": 2,
      "unit": "cups",
      "notes": "Bell peppers, broccoli, carrots"
    },
    {
      "name": "Soy Sauce",
      "quantity": 2,
      "unit": "tablespoons",
      "notes": "Low sodium"
    }
  ],
  "instructions": [
    "Heat oil in wok over high heat",
    "Add vegetables and stir fry for 5 minutes",
    "Add soy sauce and cook 2 more minutes"
  ],
  "prep_time": 10,
  "cook_time": 7,
  "total_time": 17,
  "servings": 2,
  "difficulty": "easy",
  "tags": ["vegetarian", "quick", "healthy"],
  "meal_types": ["lunch", "dinner"],
  "dietary_restrictions": ["vegetarian", "vegan"],
  "nutrition_info": null,
  "photo_url": null,
  "source_url": null,
  "created_at": "2024-01-15T13:00:00Z",
  "updated_at": "2024-01-15T13:00:00Z"
}
```

### Get Recipe
**GET** `/recipes/{recipe_id}`

Retrieve a specific recipe.

**Headers:**
```
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "id": "507f1f77bcf86cd799439015",
  "user_id": "507f1f77bcf86cd799439011",
  "title": "Vegetable Stir Fry",
  "description": "Quick and healthy vegetable stir fry",
  "ingredients": [
    {
      "name": "Mixed Vegetables",
      "quantity": 2,
      "unit": "cups",
      "notes": "Bell peppers, broccoli, carrots"
    },
    {
      "name": "Soy Sauce",
      "quantity": 2,
      "unit": "tablespoons",
      "notes": "Low sodium"
    }
  ],
  "instructions": [
    "Heat oil in wok over high heat",
    "Add vegetables and stir fry for 5 minutes",
    "Add soy sauce and cook 2 more minutes"
  ],
  "prep_time": 10,
  "cook_time": 7,
  "total_time": 17,
  "servings": 2,
  "difficulty": "easy",
  "tags": ["vegetarian", "quick", "healthy"],
  "meal_types": ["lunch", "dinner"],
  "dietary_restrictions": ["vegetarian", "vegan"],
  "nutrition_info": null,
  "photo_url": null,
  "source_url": null,
  "created_at": "2024-01-15T13:00:00Z",
  "updated_at": "2024-01-15T13:00:00Z"
}
```

### Update Recipe
**PUT** `/recipes/{recipe_id}`

Update an existing recipe.

**Headers:**
```
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "title": "Asian Vegetable Stir Fry",
  "prep_time": 12,
  "tags": ["vegetarian", "quick", "healthy", "asian"]
}
```

**Response (200):**
```json
{
  "id": "507f1f77bcf86cd799439015",
  "user_id": "507f1f77bcf86cd799439011",
  "title": "Asian Vegetable Stir Fry",
  "description": "Quick and healthy vegetable stir fry",
  "ingredients": [
    {
      "name": "Mixed Vegetables",
      "quantity": 2,
      "unit": "cups",
      "notes": "Bell peppers, broccoli, carrots"
    },
    {
      "name": "Soy Sauce",
      "quantity": 2,
      "unit": "tablespoons",
      "notes": "Low sodium"
    }
  ],
  "instructions": [
    "Heat oil in wok over high heat",
    "Add vegetables and stir fry for 5 minutes",
    "Add soy sauce and cook 2 more minutes"
  ],
  "prep_time": 12,
  "cook_time": 7,
  "total_time": 19,
  "servings": 2,
  "difficulty": "easy",
  "tags": ["vegetarian", "quick", "healthy", "asian"],
  "meal_types": ["lunch", "dinner"],
  "dietary_restrictions": ["vegetarian", "vegan"],
  "nutrition_info": null,
  "photo_url": null,
  "source_url": null,
  "created_at": "2024-01-15T13:00:00Z",
  "updated_at": "2024-01-15T13:30:00Z"
}
```

### Delete Recipe
**DELETE** `/recipes/{recipe_id}`

Delete a recipe.

**Headers:**
```
Authorization: Bearer <token>
```

**Response (204):**
```
No Content
```

### Search Recipes
**GET** `/recipes/search/recipes`

Search recipes by title, ingredients, or tags.

**Headers:**
```
Authorization: Bearer <token>
```

**Query Parameters:**
- `q`: Search query
- `difficulty` (optional): Filter by difficulty
- `meal_type` (optional): Filter by meal type
- `max_prep_time` (optional): Maximum prep time in minutes

**Response (200):**
```json
{
  "recipes": [
    {
      "id": "507f1f77bcf86cd799439015",
      "user_id": "507f1f77bcf86cd799439011",
      "title": "Asian Vegetable Stir Fry",
      "description": "Quick and healthy vegetable stir fry",
      "prep_time": 12,
      "cook_time": 7,
      "total_time": 19,
      "servings": 2,
      "difficulty": "easy",
      "tags": ["vegetarian", "quick", "healthy", "asian"],
      "meal_types": ["lunch", "dinner"]
    }
  ],
  "total_count": 1,
  "search_term": "stir fry",
  "filters_applied": {
    "difficulty": null,
    "meal_type": null,
    "max_prep_time": null
  }
}
```

### Get Recipes by Ingredients
**GET** `/recipes/by-ingredients/search`

Find recipes that can be made with available pantry ingredients.

**Headers:**
```
Authorization: Bearer <token>
```

**Query Parameters:**
- `ingredients`: Comma-separated list of ingredient names
- `match_threshold` (optional): Minimum percentage of ingredients to match (default: 0.5)

**Response (200):**
```json
[
  {
    "id": "507f1f77bcf86cd799439015",
    "user_id": "507f1f77bcf86cd799439011",
    "title": "Asian Vegetable Stir Fry",
    "description": "Quick and healthy vegetable stir fry",
    "ingredients": [
      {
        "name": "Mixed Vegetables",
        "quantity": 2,
        "unit": "cups",
        "notes": "Bell peppers, broccoli, carrots"
      }
    ],
    "prep_time": 12,
    "cook_time": 7,
    "total_time": 19,
    "servings": 2,
    "difficulty": "easy",
    "match_percentage": 0.75
  }
]
```

### Get Recipe Statistics
**GET** `/recipes/stats/overview`

Get recipe statistics and insights.

**Headers:**
```
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "total_recipes": 15,
  "recipes_by_difficulty": {
    "easy": 8,
    "medium": 5,
    "hard": 2
  },
  "recipes_by_meal_type": {
    "breakfast": 3,
    "lunch": 6,
    "dinner": 12,
    "snack": 2
  },
  "average_prep_time": 18.5,
  "average_cook_time": 25.3,
  "most_used_tags": [
    {
      "tag": "quick",
      "count": 8
    },
    {
      "tag": "healthy",
      "count": 6
    }
  ]
}
```

---

## Meal Planning

### Get Meal Plans
**GET** `/meal-plans/`

Retrieve all meal plans for the current user.

**Headers:**
```
Authorization: Bearer <token>
```

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `page_size` (optional): Items per page (default: 10)
- `status` (optional): Filter by status (draft, active, completed, archived)

**Response (200):**


```json
{
  "meal_plans": [
    {
      "id": "507f1f77bcf86cd799439016",
      "user_id": "507f1f77bcf86cd799439011",
      "title": "Week of January 15th",
      "description": "Healthy family meals for the week",
      "week_starting": "2024-01-15",
      "status": "active",
      "meals": [
        {
          "id": "meal_1",
          "day": "monday",
          "meal_type": "dinner",
          "recipe_id": "507f1f77bcf86cd799439014",
          "recipe_title": "Chicken Parmesan",
          "servings": 4,
          "estimated_prep_time": 15,
          "estimated_cook_time": 25,
          "notes": "Family favorite",
          "ingredients_needed": [
            {
              "name": "Chicken Breast",
              "quantity": 2,
              "unit": "pieces",
              "available_in_pantry": true
            }
          ]
        }
      ],
      "shopping_list": [
        {
          "id": "shop_1",
          "name": "Breadcrumbs",
          "quantity": 1,
          "unit": "cup",
          "category": "baking",
          "estimated_price": 2.99,
          "store": "Local Grocery",
          "purchased": false,
          "meal_ids": ["meal_1"]
        }
      ],
      "total_estimated_cost": 45.50,
      "budget_target": 60.00,
      "preferences_used": {
        "dietary_restrictions": ["vegetarian"],
        "cuisine_preferences": ["italian", "mexican"]
      },
      "generation_notes": "Generated based on pantry items and preferences",
      "created_at": "2024-01-15T09:00:00Z",
      "updated_at": "2024-01-15T09:00:00Z",
      "meals_count": 7,
      "shopping_items_count": 12,
      "days_covered": ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    }
  ],
  "total_count": 3,
  "page": 1,
  "page_size": 10,
  "total_pages": 1
}
```

### Create Meal Plan
**POST** `/meal-plans/`

Create a new meal plan.

**Headers:**
```
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "title": "Week of January 22nd",
  "description": "Budget-friendly meals",
  "week_starting": "2024-01-22",
  "budget_target": 50.00,
  "preferences": {
    "dietary_restrictions": ["vegetarian"],
    "max_prep_time": 30
  }
}
```

**Response (201):**
```json
{
  "id": "507f1f77bcf86cd799439017",
  "user_id": "507f1f77bcf86cd799439011",
  "title": "Week of January 22nd",
  "description": "Budget-friendly meals",
  "week_starting": "2024-01-22",
  "status": "draft",
  "meals": [],
  "shopping_list": [],
  "total_estimated_cost": 0.00,
  "budget_target": 50.00,
  "preferences_used": {
    "dietary_restrictions": ["vegetarian"],
    "max_prep_time": 30
  },
  "generation_notes": null,
  "created_at": "2024-01-15T14:00:00Z",
  "updated_at": "2024-01-15T14:00:00Z",
  "meals_count": 0,
  "shopping_items_count": 0,
  "days_covered": []
}
```

### Generate AI Meal Plan
**POST** `/meal-plans/generate`

Generate a meal plan using AI based on user preferences and pantry items.

**Headers:**
```
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "week_starting": "2024-01-29",
  "budget_target": 75.00,
  "meal_types": ["dinner"],
  "days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
  "servings_per_meal": 4,
  "use_pantry_items": true,
  "dietary_restrictions": ["vegetarian"],
  "cuisine_preferences": ["italian", "mexican"],
  "avoid_ingredients": ["mushrooms"],
  "max_prep_time": 45,
  "difficulty_preference": "easy"
}
```

**Response (201):**
```json
{
  "meal_plan_id": "507f1f77bcf86cd799439018",
  "title": "AI Generated Plan - Week of January 29th",
  "meals_generated": 5,
  "shopping_items_generated": 18,
  "total_estimated_cost": 68.75,
  "generation_notes": "Generated 5 vegetarian dinner meals within budget. Used 12 pantry items to reduce costs.",
  "success": true,
  "warnings": [
    "Some preferred ingredients were not available in pantry",
    "One meal slightly exceeds preferred prep time"
  ]
}
```

---

## Shopping Lists

### Get Shopping Lists
**GET** `/shopping-lists/`

Retrieve all shopping lists for the current user.

**Headers:**
```
Authorization: Bearer <token>
```

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `page_size` (optional): Items per page (default: 20)
- `status` (optional): Filter by status (active, completed, archived)

**Response (200):**
```json
{
  "shopping_lists": [
    {
      "id": "507f1f77bcf86cd799439020",
      "user_id": "507f1f77bcf86cd799439011",
      "title": "Weekly Grocery Run",
      "description": "Groceries for the week",
      "status": "active",
      "items": [
        {
          "id": "item_1",
          "name": "Milk",
          "quantity": 1,
          "unit": "gallon",
          "category": "dairy",
          "estimated_price": 3.99,
          "actual_price": null,
          "store": "Local Grocery",
          "status": "pending",
          "notes": "2% milk",
          "priority": 3,
          "purchased_at": null
        }
      ],
      "stores": ["Local Grocery", "Walmart"],
      "total_estimated_cost": 45.67,
      "total_actual_cost": 0.00,
      "budget_limit": 60.00,
      "shopping_date": "2024-01-16",
      "tags": ["weekly", "groceries"],
      "created_at": "2024-01-15T16:00:00Z",
      "updated_at": "2024-01-15T16:00:00Z",
      "items_count": 15,
      "purchased_items_count": 0,
      "completion_percentage": 0.0,
      "budget_used_percentage": 0.0
    }
  ],
  "total_count": 5,
  "page": 1,
  "page_size": 20,
  "total_pages": 1
}
```

### Create Shopping List from Meal Plan
**POST** `/shopping-lists/from-meal-plan/{meal_plan_id}`

Create a shopping list from an existing meal plan.

**Headers:**
```
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "title": "Groceries for Week Plan",
  "shopping_date": "2024-01-16",
  "budget_limit": 70.00
}
```

**Response (201):**
```json
{
  "id": "507f1f77bcf86cd799439023",
  "user_id": "507f1f77bcf86cd799439011",
  "title": "Groceries for Week Plan",
  "status": "active",
  "meal_plan_id": "507f1f77bcf86cd799439016",
  "items_count": 12,
  "total_estimated_cost": 45.50,
  "budget_limit": 70.00,
  "shopping_date": "2024-01-16",
  "created_at": "2024-01-15T18:00:00Z"
}
```

---

## Receipt Processing

### Upload Receipt
**POST** `/receipts/upload`

Upload a receipt image for processing.

**Headers:**
```
Authorization: Bearer <token>
Content-Type: multipart/form-data
```

**Request Body (Form Data):**
- `file`: Receipt image file (JPEG, PNG, PDF)
- `store_name` (optional): Name of the store
- `purchase_date` (optional): Date of purchase (YYYY-MM-DD)

**Response (201):**
```json
{
  "id": "507f1f77bcf86cd799439024",
  "user_id": "507f1f77bcf86cd799439011",
  "store_name": "Local Grocery",
  "purchase_date": "2024-01-15",
  "total_amount": 45.67,
  "items": [
    {
      "name": "Milk",
      "quantity": 1,
      "unit": "gallon",
      "price": 3.99,
      "category": "dairy"
    },
    {
      "name": "Bread",
      "quantity": 1,
      "unit": "loaf",
      "price": 2.50,
      "category": "grains"
    }
  ],
  "processing_status": "completed",
  "confidence_score": 0.95,
  "created_at": "2024-01-15T19:00:00Z",
  "updated_at": "2024-01-15T19:00:00Z"
}
```

### Get User Receipts
**GET** `/receipts/`

Retrieve all receipts for the current user.

**Headers:**
```
Authorization: Bearer <token>
```

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `page_size` (optional): Items per page (default: 20)
- `store_name` (optional): Filter by store name
- `date_from` (optional): Filter receipts from date (YYYY-MM-DD)
- `date_to` (optional): Filter receipts to date (YYYY-MM-DD)

**Response (200):**
```json
{
  "receipts": [
    {
      "id": "507f1f77bcf86cd799439024",
      "user_id": "507f1f77bcf86cd799439011",
      "store_name": "Local Grocery",
      "purchase_date": "2024-01-15",
      "total_amount": 45.67,
      "items_count": 15,
      "processing_status": "completed",
      "confidence_score": 0.95,
      "created_at": "2024-01-15T19:00:00Z",
      "updated_at": "2024-01-15T19:00:00Z"
    }
  ],
  "total_count": 8,
  "page": 1,
  "page_size": 20,
  "total_pages": 1
}
```

### Process Receipt
**POST** `/receipts/{receipt_id}/process`

Process a receipt to extract items and add to pantry.

**Headers:**
```
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "auto_add_to_pantry": true,
  "default_location": "pantry",
  "estimate_expiration": true
}
```

**Response (200):**
```json
{
  "receipt_id": "507f1f77bcf86cd799439024",
  "items_processed": 15,
  "items_added_to_pantry": 12,
  "items_skipped": 3,
  "processing_notes": "3 items skipped due to non-food category",
  "pantry_items_created": [
    {
      "id": "507f1f77bcf86cd799439025",
      "name": "Milk",
      "category": "dairy",
      "quantity": 1,
      "unit": "gallon",
      "estimated_value": 3.99,
      "expiration_date": "2024-01-22"
    }
  ]
}
```

### Add Receipt Items to Pantry
**POST** `/receipts/{receipt_id}/add-to-pantry`

Add specific receipt items to the pantry.

**Headers:**
```
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "items": [
    {
      "receipt_item_id": "item_1",
      "location": "refrigerator",
      "expiration_date": "2024-01-22",
      "notes": "Organic milk"
    },
    {
      "receipt_item_id": "item_2",
      "location": "pantry",
      "expiration_date": "2024-01-25"
    }
  ]
}
```

**Response (200):**
```json
{
  "items_added": 2,
  "items_failed": 0,
  "pantry_items": [
    {
      "id": "507f1f77bcf86cd799439026",
      "name": "Milk",
      "category": "dairy",
      "location": "refrigerator",
      "expiration_date": "2024-01-22",
      "notes": "Organic milk"
    },
    {
      "id": "507f1f77bcf86cd799439027",
      "name": "Bread",
      "category": "grains",
      "location": "pantry",
      "expiration_date": "2024-01-25"
    }
  ]
}
```

### Get Receipt Statistics
**GET** `/receipts/stats/overview`

Get receipt processing statistics.

**Headers:**
```
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "total_receipts": 25,
  "total_amount_spent": 1247.85,
  "average_receipt_amount": 49.91,
  "most_frequent_store": "Local Grocery",
  "receipts_this_month": 8,
  "amount_spent_this_month": 387.45,
  "items_added_to_pantry": 156,
  "processing_success_rate": 94.2
}
```

---

## Community Features

### Get Community Posts
**GET** `/community/posts/`

Retrieve community posts with pagination.

**Headers:**
```
Authorization: Bearer <token> (optional for public posts)
```

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `page_size` (optional): Items per page (default: 20)
- `post_type` (optional): Filter by post type (recipe, tip, savings_story, general)
- `tags` (optional): Filter by tags (comma-separated)
- `user_id` (optional): Filter by specific user

**Response (200):**
```json
{
  "posts": [
    {
      "id": "507f1f77bcf86cd799439028",
      "user_id": "507f1f77bcf86cd799439011",
      "title": "Amazing Budget Pasta Recipe",
      "content": "This pasta recipe feeds a family of 4 for under $5!",
      "post_type": "recipe",
      "recipe_id": "507f1f77bcf86cd799439015",
      "tags": ["budget", "pasta", "family"],
      "likes_count": 15,
      "comments_count": 8,
      "is_public": true,
      "created_at": "2024-01-15T20:00:00Z",
      "updated_at": "2024-01-15T20:00:00Z",
      "user_display_name": "John Doe",
      "user_avatar_url": null,
      "is_liked_by_user": false,
      "recipe_title": "Asian Vegetable Stir Fry"
    }
  ],
  "total_count": 45,
  "page": 1,
  "page_size": 20,
  "total_pages": 3
}
```

### Create Community Post
**POST** `/community/posts/`

Create a new community post.

**Headers:**
```
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "title": "Money-Saving Grocery Tips",
  "content": "Here are my top 5 tips for saving money on groceries...",
  "post_type": "tip",
  "tags": ["savings", "grocery", "tips"],
  "is_public": true
}
```

**Response (201):**
```json
{
  "id": "507f1f77bcf86cd799439029",
  "user_id": "507f1f77bcf86cd799439011",
  "title": "Money-Saving Grocery Tips",
  "content": "Here are my top 5 tips for saving money on groceries...",
  "post_type": "tip",
  "recipe_id": null,
  "tags": ["savings", "grocery", "tips"],
  "likes_count": 0,
  "comments_count": 0,
  "is_public": true,
  "created_at": "2024-01-15T21:00:00Z",
  "updated_at": "2024-01-15T21:00:00Z",
  "user_display_name": "John Doe",
  "user_avatar_url": null,
  "is_liked_by_user": false,
  "recipe_title": null
}
```

### Get Community Post
**GET** `/community/posts/{post_id}`

Retrieve a specific community post.

**Headers:**
```
Authorization: Bearer <token> (optional for public posts)
```

**Response (200):**
```json
{
  "id": "507f1f77bcf86cd799439028",
  "user_id": "507f1f77bcf86cd799439011",
  "title": "Amazing Budget Pasta Recipe",
  "content": "This pasta recipe feeds a family of 4 for under $5!",
  "post_type": "recipe",
  "recipe_id": "507f1f77bcf86cd799439015",
  "tags": ["budget", "pasta", "family"],
  "likes_count": 15,
  "comments_count": 8,
  "is_public": true,
  "created_at": "2024-01-15T20:00:00Z",
  "updated_at": "2024-01-15T20:00:00Z",
  "user_display_name": "John Doe",
  "user_avatar_url": null,
  "is_liked_by_user": false,
  "recipe_title": "Asian Vegetable Stir Fry"
}
```

### Update Community Post
**PUT** `/community/posts/{post_id}`

Update an existing community post (author only).

**Headers:**
```
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "title": "Updated: Amazing Budget Pasta Recipe",
  "content": "This updated pasta recipe feeds a family of 4 for under $4!",
  "tags": ["budget", "pasta", "family", "updated"]
}
```

**Response (200):**
```json
{
  "id": "507f1f77bcf86cd799439028",
  "user_id": "507f1f77bcf86cd799439011",
  "title": "Updated: Amazing Budget Pasta Recipe",
  "content": "This updated pasta recipe feeds a family of 4 for under $4!",
  "post_type": "recipe",
  "recipe_id": "507f1f77bcf86cd799439015",
  "tags": ["budget", "pasta", "family", "updated"],
  "likes_count": 15,
  "comments_count": 8,
  "is_public": true,
  "created_at": "2024-01-15T20:00:00Z",
  "updated_at": "2024-01-15T22:00:00Z",
  "user_display_name": "John Doe",
  "user_avatar_url": null,
  "is_liked_by_user": false,
  "recipe_title": "Asian Vegetable Stir Fry"
}
```

### Delete Community Post
**DELETE** `/community/posts/{post_id}`

Delete a community post (author only).

**Headers:**
```
Authorization: Bearer <token>
```

**Response (204):**
```
No Content
```

### Like Community Post
**POST** `/community/posts/{post_id}/like`

Like or unlike a community post.

**Headers:**
```
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "id": "507f1f77bcf86cd799439028",
  "likes_count": 16,
  "is_liked_by_user": true,
  "updated_at": "2024-01-15T22:30:00Z"
}
```

### Add Comment to Post
**POST** `/community/posts/{post_id}/comments/`

Add a comment to a community post.

**Headers:**
```
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "content": "Great recipe! I tried it and my family loved it.",
  "parent_comment_id": null
}
```

**Response (201):**
```json
{
  "id": "507f1f77bcf86cd799439030",
  "post_id": "507f1f77bcf86cd799439028",
  "user_id": "507f1f77bcf86cd799439011",
  "content": "Great recipe! I tried it and my family loved it.",
  "parent_comment_id": null,
  "likes_count": 0,
  "created_at": "2024-01-15T23:00:00Z",
  "updated_at": "2024-01-15T23:00:00Z",
  "user_display_name": "John Doe",
  "user_avatar_url": null,
  "is_liked_by_user": false,
  "replies": []
}
```

### Get Post Comments
**GET** `/community/posts/{post_id}/comments/`

Get comments for a specific post.

**Headers:**
```
Authorization: Bearer <token> (optional)
```

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `page_size` (optional): Items per page (default: 20)

**Response (200):**
```json
{
  "comments": [
    {
      "id": "507f1f77bcf86cd799439030",
      "post_id": "507f1f77bcf86cd799439028",
      "user_id": "507f1f77bcf86cd799439011",
      "content": "Great recipe! I tried it and my family loved it.",
      "parent_comment_id": null,
      "likes_count": 2,
      "created_at": "2024-01-15T23:00:00Z",
      "updated_at": "2024-01-15T23:00:00Z",
      "user_display_name": "John Doe",
      "user_avatar_url": null,
      "is_liked_by_user": false,
      "replies": [
        {
          "id": "507f1f77bcf86cd799439031",
          "post_id": "507f1f77bcf86cd799439028",
          "user_id": "507f1f77bcf86cd799439032",
          "content": "Thanks for sharing! What did you substitute for the pasta?",
          "parent_comment_id": "507f1f77bcf86cd799439030",
          "likes_count": 0,
          "created_at": "2024-01-16T08:00:00Z",
          "updated_at": "2024-01-16T08:00:00Z",
          "user_display_name": "Jane Smith",
          "user_avatar_url": null,
          "is_liked_by_user": false,
          "replies": []
        }
      ]
    }
  ],
  "total_count": 8,
  "page": 1,
  "page_size": 20,
  "total_pages": 1
}
```

### Update Comment
**PUT** `/community/comments/{comment_id}`

Update a comment (author only).

**Headers:**
```
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "content": "Great recipe! I tried it and my whole family absolutely loved it."
}
```

**Response (200):**
```json
{
  "id": "507f1f77bcf86cd799439030",
  "post_id": "507f1f77bcf86cd799439028",
  "user_id": "507f1f77bcf86cd799439011",
  "content": "Great recipe! I tried it and my whole family absolutely loved it.",
  "parent_comment_id": null,
  "likes_count": 2,
  "created_at": "2024-01-15T23:00:00Z",
  "updated_at": "2024-01-16T09:00:00Z",
  "user_display_name": "John Doe",
  "user_avatar_url": null,
  "is_liked_by_user": false,
  "replies": []
}
```

### Delete Comment
**DELETE** `/community/comments/{comment_id}`

Delete a comment (author only).

**Headers:**
```
Authorization: Bearer <token>
```

**Response (204):**
```
No Content
```

### Like Comment
**POST** `/community/comments/{comment_id}/like`

Like or unlike a comment.

**Headers:**
```
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "id": "507f1f77bcf86cd799439030",
  "likes_count": 3,
  "is_liked_by_user": true,
  "updated_at": "2024-01-16T10:00:00Z"
}
```

### Get Community Statistics
**GET** `/community/stats/overview`

Get community statistics and insights.

**Headers:**
```
Authorization: Bearer <token> (optional)
```

**Response (200):**
```json
{
  "total_posts": 156,
  "total_comments": 423,
  "total_likes": 1247,
  "posts_by_type": {
    "recipe": 45,
    "tip": 67,
    "savings_story": 23,
    "general": 21
  },
  "most_active_users": [
    {
      "user_id": "507f1f77bcf86cd799439011",
      "display_name": "John Doe",
      "post_count": 12,
      "comment_count": 34
    }
  ],
  "trending_tags": [
    {
      "tag": "budget",
      "count": 23
    },
    {
      "tag": "quick",
      "count": 18
    }
  ],
  "recent_activity_count": 45
}
```

---

## Leftover Suggestions

### Get Leftover Suggestions
**GET** `/leftovers/suggestions`

Get recipe suggestions based on available pantry items.

**Headers:**
```
Authorization: Bearer <token>
```

**Query Parameters:**
- `ingredients` (optional): Comma-separated list of specific ingredients
- `max_prep_time` (optional): Maximum preparation time in minutes
- `difficulty` (optional): Preferred difficulty level (easy, medium, hard)
- `meal_type` (optional): Preferred meal type
- `limit` (optional): Maximum number of suggestions (default: 10)

**Response (200):**
```json
{
  "suggestions": [
    {
      "recipe_id": "507f1f77bcf86cd799439015",
      "title": "Asian Vegetable Stir Fry",
      "description": "Quick and healthy vegetable stir fry",
      "match_score": 0.85,
      "matched_ingredients": [
        {
          "name": "Mixed Vegetables",
          "available_quantity": 3,
          "required_quantity": 2,
          "unit": "cups"
        },
        {
          "name": "Soy Sauce",
          "available_quantity": 1,
          "required_quantity": 2,
          "unit": "tablespoons"
        }
      ],
      "missing_ingredients": [],
      "prep_time": 12,
      "cook_time": 7,
      "difficulty": "easy",
      "estimated_cost_savings": 8.50,
      "pantry_usage_percentage": 100
    },
    {
      "recipe_id": "507f1f77bcf86cd799439014",
      "title": "Chicken Parmesan",
      "description": "Classic Italian-American dish",
      "match_score": 0.65,
      "matched_ingredients": [
        {
          "name": "Chicken Breast",
          "available_quantity": 2.5,
          "required_quantity": 2,
          "unit": "pieces"
        }
      ],
      "missing_ingredients": [
        {
          "name": "Breadcrumbs",
          "required_quantity": 1,
          "unit": "cup",
          "estimated_cost": 2.99
        }
      ],
      "prep_time": 15,
      "cook_time": 25,
      "difficulty": "medium",
      "estimated_cost_savings": 12.00,
      "pantry_usage_percentage": 60
    }
  ],
  "total_suggestions": 8,
  "pantry_items_used": 15,
  "total_potential_savings": 45.75,
  "generation_notes": "Suggestions based on 25 pantry items with focus on items expiring soon"
}
```

### Get Available Ingredients
**GET** `/leftovers/ingredients`

Get list of available pantry ingredients for recipe matching.

**Headers:**
```
Authorization: Bearer <token>
```

**Query Parameters:**
- `category` (optional): Filter by ingredient category
- `expiring_soon` (optional): Only include items expiring within specified days

**Response (200):**
```json
[
  {
    "name": "Chicken Breast",
    "category": "meat",
    "quantity": 2.5,
    "unit": "lbs",
    "expiration_date": "2024-01-20",
    "days_until_expiration": 5,
    "estimated_value": 12.99,
    "location": "freezer"
  },
  {
    "name": "Mixed Vegetables",
    "category": "produce",
    "quantity": 3,
    "unit": "cups",
    "expiration_date": "2024-01-18",
    "days_until_expiration": 3,
    "estimated_value": 6.50,
    "location": "refrigerator"
  }
]
```

### Get Custom Suggestions
**POST** `/leftovers/suggestions/custom`

Get customized recipe suggestions with specific parameters.

**Headers:**
```
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "ingredients": ["chicken", "vegetables", "rice"],
  "dietary_restrictions": ["gluten_free"],
  "max_prep_time": 30,
  "difficulty": "easy",
  "meal_type": "dinner",
  "servings": 4,
  "cuisine_preference": "asian",
  "avoid_ingredients": ["mushrooms"],
  "prioritize_expiring": true
}
```

**Response (200):**
```json
{
  "suggestions": [
    {
      "recipe_id": "custom_suggestion_1",
      "title": "Gluten-Free Chicken and Vegetable Rice Bowl",
      "description": "A healthy, gluten-free dinner using your available ingredients",
      "match_score": 0.92,
      "matched_ingredients": [
        {
          "name": "Chicken Breast",
          "available_quantity": 2.5,
          "required_quantity": 1.5,
          "unit": "lbs"
        },
        {
          "name": "Mixed Vegetables",
          "available_quantity": 3,
          "required_quantity": 2,
          "unit": "cups"
        },
        {
          "name": "Rice",
          "available_quantity": 2,
          "required_quantity": 1,
          "unit": "cups"
        }
      ],
      "missing_ingredients": [],
      "prep_time": 20,
      "cook_time": 25,
      "difficulty": "easy",
      "estimated_cost_savings": 15.50,
      "pantry_usage_percentage": 85,
      "dietary_compliance": ["gluten_free"],
      "instructions": [
        "Cook rice according to package directions",
        "Season and cook chicken breast until done",
        "Stir-fry vegetables until tender-crisp",
        "Combine all ingredients and serve"
      ]
    }
  ],
  "total_suggestions": 3,
  "customization_applied": {
    "dietary_restrictions": ["gluten_free"],
    "max_prep_time": 30,
    "difficulty": "easy",
    "meal_type": "dinner",
    "prioritize_expiring": true
  }
}
```

### Get Debug Suggestions
**GET** `/leftovers/suggestions/debug`

Get detailed debugging information for suggestion algorithm (development/testing).

**Headers:**
```
Authorization: Bearer <token>
```

**Query Parameters:**
- `ingredients` (optional): Comma-separated list of ingredients to analyze
- `verbose` (optional): Include detailed algorithm steps (default: false)

**Response (200):**
```json
{
  "pantry_analysis": {
    "total_items": 25,
    "expiring_soon": 5,
    "categories_represented": ["produce", "meat", "dairy", "grains"],
    "estimated_total_value": 156.75
  },
  "algorithm_steps": [
    {
      "step": "ingredient_matching",
      "recipes_found": 45,
      "match_threshold": 0.6,
      "processing_time_ms": 125
    },
    {
      "step": "scoring_calculation",
      "factors_considered": ["match_percentage", "expiration_urgency", "cost_savings"],
      "top_scores": [0.92, 0.85, 0.78],
      "processing_time_ms": 67
    },
    {
      "step": "filtering_and_ranking",
      "filters_applied": ["dietary_restrictions", "difficulty", "prep_time"],
      "final_suggestions": 8,
      "processing_time_ms": 34
    }
  ],
  "suggestions": [
    {
      "recipe_id": "507f1f77bcf86cd799439015",
      "title": "Asian Vegetable Stir Fry",
      "debug_info": {
        "raw_match_score": 0.87,
        "expiration_bonus": 0.15,
        "cost_savings_bonus": 0.08,
        "final_score": 0.92,
        "ingredients_analysis": {
          "total_required": 4,
          "available_in_pantry": 4,
          "match_percentage": 100,
          "missing_cost": 0.00
        }
      }
    }
  ],
  "performance_metrics": {
    "total_processing_time_ms": 226,
    "recipes_analyzed": 45,
    "pantry_items_processed": 25,
    "cache_hits": 12,
    "cache_misses": 3
  }
}
```

### Leftover Service Health Check
**GET** `/leftovers/health`

Check the health status of the leftover suggestions service.

**Headers:**
```
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "status": "healthy",
  "service": "leftover_suggestions",
  "version": "1.0.0",
  "timestamp": "2024-01-16T12:00:00Z",
  "checks": {
    "database_connection": "healthy",
    "recipe_index": "healthy",
    "pantry_access": "healthy",
    "algorithm_performance": "optimal"
  },
  "metrics": {
    "average_response_time_ms": 145,
    "suggestions_generated_today": 234,
    "cache_hit_rate": 0.78,
    "error_rate": 0.02
  }
}
```

---

## Error Handling

The API uses standard HTTP status codes and returns consistent error responses.

### Error Response Format

All error responses follow this structure:

```json
{
  "detail": "Error message description",
  "error_code": "SPECIFIC_ERROR_CODE",
  "timestamp": "2024-01-16T12:00:00Z",
  "path": "/api/v1/endpoint",
  "request_id": "req_123456789"
}
```

### Common HTTP Status Codes

| Status Code | Description | Common Causes |
|-------------|-------------|---------------|
| **400** | Bad Request | Invalid request body, missing required fields, validation errors |
| **401** | Unauthorized | Missing or invalid authentication token |
| **403** | Forbidden | Valid token but insufficient permissions |
| **404** | Not Found | Resource doesn't exist or user doesn't have access |
| **409** | Conflict | Resource already exists (e.g., duplicate email) |
| **422** | Unprocessable Entity | Request body validation failed |
| **429** | Too Many Requests | Rate limit exceeded |
| **500** | Internal Server Error | Unexpected server error |
| **503** | Service Unavailable | Database or external service unavailable |

### Specific Error Codes

#### Authentication Errors
```json
{
  "detail": "Invalid authentication credentials",
  "error_code": "INVALID_CREDENTIALS",
  "timestamp": "2024-01-16T12:00:00Z",
  "path": "/api/v1/auth/login",
  "request_id": "req_123456789"
}
```

#### Validation Errors
```json
{
  "detail": "Validation error",
  "error_code": "VALIDATION_ERROR",
  "timestamp": "2024-01-16T12:00:00Z",
  "path": "/api/v1/recipes/",
  "request_id": "req_123456789",
  "validation_errors": [
    {
      "field": "title",
      "message": "Recipe title cannot be empty"
    },
    {
      "field": "ingredients",
      "message": "Recipe must have at least one ingredient"
    }
  ]
}
```

#### Resource Not Found
```json
{
  "detail": "Recipe not found",
  "error_code": "RESOURCE_NOT_FOUND",
  "timestamp": "2024-01-16T12:00:00Z",
  "path": "/api/v1/recipes/invalid_id",
  "request_id": "req_123456789"
}
```

#### Rate Limit Exceeded
```json
{
  "detail": "Rate limit exceeded. Try again in 60 seconds.",
  "error_code": "RATE_LIMIT_EXCEEDED",
  "timestamp": "2024-01-16T12:00:00Z",
  "path": "/api/v1/auth/login",
  "request_id": "req_123456789",
  "retry_after": 60,
  "limit": "5 requests per minute"
}
```

#### Database Connection Error
```json
{
  "detail": "Database temporarily unavailable",
  "error_code": "DATABASE_UNAVAILABLE",
  "timestamp": "2024-01-16T12:00:00Z",
  "path": "/api/v1/pantry/",
  "request_id": "req_123456789"
}
```

---

## Rate Limiting

The API implements rate limiting to ensure fair usage and prevent abuse.

### Rate Limit Headers

All responses include rate limiting information in headers:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642348800
X-RateLimit-Window: 60
```

### Rate Limits by Endpoint Category

| Endpoint Category | Rate Limit | Window |
|-------------------|------------|---------|
| **Authentication** | 5 requests | per minute |
| **General API** | 100 requests | per minute |
| **File Upload** | 10 requests | per minute |
| **AI Generation** | 20 requests | per hour |
| **Search** | 50 requests | per minute |

### Rate Limit Bypass

Premium users or specific API keys may have higher rate limits. Contact support for rate limit increases.

---

## Health Check

### System Health Check
**GET** `/healthz`

Check the overall health of the API system.

**Response (200):**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-16T12:00:00Z",
  "version": "1.0.0",
  "environment": "production",
  "database_connected": true,
  "services": {
    "authentication": "healthy",
    "pantry_management": "healthy",
    "recipe_engine": "healthy",
    "meal_planning": "healthy",
    "community": "healthy",
    "leftover_suggestions": "healthy"
  },
  "performance": {
    "average_response_time_ms": 125,
    "requests_per_minute": 450,
    "error_rate": 0.01
  }
}
```

---

## Postman Collection

### Import Collection

You can import the EZ Eatin' API collection into Postman using this configuration:

```json
{
  "info": {
    "name": "EZ Eatin' API",
    "description": "Complete API collection for EZ Eatin' meal planning application",
    "version": "1.0.0",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "auth": {
    "type": "bearer",
    "bearer": [
      {
        "key": "token",
        "value": "{{auth_token}}",
        "type": "string"
      }
    ]
  },
  "variable": [
    {
      "key": "base_url",
      "value": "https://ezeatin-backend.onrender.com/api/v1",
      "type": "string"
    },
    {
      "key": "auth_token",
      "value": "",
      "type": "string"
    }
  ],
  "item": [
    {
      "name": "Authentication",
      "item": [
        {
          "name": "Register User",
          "request": {
            "method": "POST",
            "header": [
              {
                "key": "Content-Type",
                "value": "application/json"
              }
            ],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"email\": \"user@example.com\",\n  \"password\": \"securepassword123\",\n  \"full_name\": \"John Doe\"\n}"
            },
            "url": {
              "raw": "{{base_url}}/auth/signup",
              "host": ["{{base_url}}"],
              "path": ["auth", "signup"]
            }
          }
        },
        {
          "name": "Login",
          "request": {
            "method": "POST",
            "header": [
              {
                "key": "Content-Type",
                "value": "application/json"
              }
            ],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"email\": \"user@example.com\",\n  \"password\": \"securepassword123\"\n}"
            },
            "url": {
              "raw": "{{base_url}}/auth/login",
              "host": ["{{base_url}}"],
              "path": ["auth", "login"]
            }
          },
          "event": [
            {
              "listen": "test",
              "script": {
                "exec": [
                  "if (pm.response.code === 200) {",
                  "    const response = pm.response.json();",
                  "    pm.collectionVariables.set('auth_token', response.access_token);",
                  "}"
                ]
              }
            }
          ]
        },
        {
          "name": "Get Current User",
          "request": {
            "method": "GET",
            "header": [
              {
                "key": "Authorization",
                "value": "Bearer {{auth_token}}"
              }
            ],
            "url": {
              "raw": "{{base_url}}/auth/me",
              "host": ["{{base_url}}"],
              "path": ["auth", "me"]
            }
          }
        }
      ]
    },
    {
      "name": "Pantry Management",
      "item": [
        {
          "name": "Get Pantry Items",
          "request": {
            "method": "GET",
            "header": [
              {
                "key": "Authorization",
                "value": "Bearer {{auth_token}}"
              }
            ],
            "url": {
              "raw": "{{base_url}}/pantry/",
              "host": ["{{base_url}}"],
              "path": ["pantry", ""]
            }
          }
        },
        {
          "name": "Add Pantry Item",
          "request": {
            "method": "POST",
            "header": [
              {
                "key": "Authorization",
                "value": "Bearer {{auth_token}}"
              },
              {
                "key": "Content-Type",
                "value": "application/json"
              }
            ],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"name\": \"Tomatoes\",\n  \"category\": \"produce\",\n  \"quantity\": 6,\n  \"unit\": \"pieces\",\n  \"expiration_date\": \"2024-01-18\",\n  \"purchase_date\": \"2024-01-15\",\n  \"location\": \"refrigerator\",\n  \"notes\": \"Roma tomatoes\",\n  \"estimated_value\": 4.50\n}"
            },
            "url": {
              "raw": "{{base_url}}/pantry/",
              "host": ["{{base_url}}"],
              "path": ["pantry", ""]
            }
          }
        }
      ]
    },
    {
      "name": "Recipe Management",
      "item": [
        {
          "name": "Get User Recipes",
          "request": {
            "method": "GET",
            "header": [
              {
                "key": "Authorization",
                "value": "Bearer {{auth_token}}"
              }
            ],
            "url": {
              "raw": "{{base_url}}/recipes/",
              "host": ["{{base_url}}"],
              "path": ["recipes", ""]
            }
          }
        },
        {
          "name": "Create Recipe",
          "request": {
            "method": "POST",
            "header": [
              {
                "key": "Authorization",
                "value": "Bearer {{auth_token}}"
              },
              {
                "key": "Content-Type",
                "value": "application/json"
              }
            ],
            "body": {
              "mode": "raw",
              "raw": "{\n  \"title\": \"Vegetable Stir Fry\",\n  \"description\": \"Quick and healthy vegetable stir fry\",\n  \"ingredients\": [\n    {\n      \"name\": \"Mixed Vegetables\",\n      \"quantity\": 2,\n      \"unit\": \"cups\",\n      \"notes\": \"Bell peppers, broccoli, carrots\"\n    }\n  ],\n  \"instructions\": [\n    \"Heat oil in wok over high heat\",\n    \"Add vegetables and stir fry for 5 minutes\"\n  ],\n  \"prep_time\": 10,\n  \"cook_time\": 7,\n  \"servings\": 2,\n  \"difficulty\": \"easy\",\n  \"tags\": [\"vegetarian\", \"quick\", \"healthy\"],\n  \"meal_types\": [\"lunch\", \"dinner\"]\n}"
            },
            "url": {
              "raw": "{{base_url}}/recipes/",
              "host": ["{{base_url}}"],
              "path": ["recipes", ""]
            }
          }
        }
      ]
    }
  ]
}
```

### Environment Setup

Create a Postman environment with these variables:

| Variable | Value | Description |
|----------|-------|-------------|
| `base_url` | `https://ezeatin-backend.onrender.com/api/v1` | API base URL |
| `auth_token` | `(auto-populated)` | JWT authentication token |

### Testing Workflow

1. **Authentication**: Run the "Login" request to get an auth token
2. **Profile Setup**: Create or update your user profile
3. **Pantry Management**: Add some pantry items
4. **Recipe Creation**: Create a few recipes
5. **Meal Planning**: Generate a meal plan
6. **Community**: Create and interact with community posts

---

## SDK and Code Examples

### JavaScript/TypeScript Example

```typescript
class EZEatinAPI {
  private baseURL = 'https://ezeatin-backend.onrender.com/api/v1';
  private authToken: string | null = null;

  async login(email: string, password: string) {
    const response = await fetch(`${this.baseURL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    
    if (response.ok) {
      const data = await response.json();
      this.authToken = data.access_token;
      return data;
    }
    throw new Error('Login failed');
  }

  async getPantryItems() {
    const response = await fetch(`${this.baseURL}/pantry/`, {
      headers: { 'Authorization': `Bearer ${this.authToken}` }
    });
    
    if (response.ok) {
      return await response.json();
    }
    throw new Error('Failed to fetch pantry items');
  }

  async createRecipe(recipe: any) {
    const response = await fetch(`${this.baseURL}/recipes/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.authToken}`
      },
      body: JSON.stringify(recipe)
    });
    
    if (response.ok) {
      return await response.json();
    }
    throw new Error('Failed to create recipe');
  }
}
```

### Python Example

```python
import requests
from typing import Dict, Any, Optional

class EZEatinAPI:
    def __init__(self, base_url: str = "https://ezeatin-backend.onrender.com/api/v1"):
        self.base_url = base_url
        self.auth_token: Optional[str] = None
        self.session = requests.Session()

    def login(self, email: str, password: str) -> Dict[str, Any]:
        response = self.session.post(
            f"{self.base_url}/auth/login",
            json={"email": email, "password": password}
        )
        response.raise_for_status()
        
        data = response.json()
        self.auth_token = data["access_token"]
        self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
        return data

    def get_pantry_items(self) -> Dict[str, Any]:
        response = self.session.get(f"{self.base_url}/pantry/")
        response.raise_for_status()
        return response.json()

    def create_recipe(self, recipe_data: Dict[str, Any]) -> Dict[str, Any]:
        response = self.session.post(
            f"{self.base_url}/recipes/",
            json=recipe_data
        )
        response.raise_for_status()
        return response.json()

    def get_leftover_suggestions(self, ingredients: list = None) -> Dict[str, Any]:
        params = {}
        if ingredients:
            params["ingredients"] = ",".join(ingredients)
        
        response = self.session.get(
            f"{self.base_url}/leftovers/suggestions",
            params=params
        )
        response.raise_for_status()
        return response.json()

# Usage example
api = EZEatinAPI()
api.login("user@example.com", "password123")
pantry = api.get_pantry_items()
suggestions = api.get_leftover_suggestions(["chicken", "vegetables"])
```

---

## Support and Resources

### Documentation Links
- **API Reference**: This document
- **Getting Started Guide**: [User Documentation](#user-documentation)
- **Developer Guide**: [Developer Documentation](#developer-documentation)

### Support Channels
- **GitHub Issues**: Report bugs and request features
- **Email Support**: support@ezeatin.com
- **Community Forum**: Join our community discussions

### Rate Limits and Quotas
- **Free Tier**: 1,000 requests per day
- **Premium Tier**: 10,000 requests per day
- **Enterprise**: Custom limits available

### API Versioning
- **Current Version**: v1
- **Deprecation Policy**: 6 months notice for breaking changes
- **Backward Compatibility**: Maintained within major versions

---

*This documentation is automatically updated with each API release. Last updated: January 16, 2024*