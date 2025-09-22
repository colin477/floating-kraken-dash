# EZ Eatin' Backend Development Plan

## 1) Executive Summary

Building a FastAPI backend for EZ Eatin' - an AI-driven meal planning application that helps families reduce grocery costs and meal planning time. The backend will support user authentication, profile management, pantry tracking, recipe management, meal planning, community features, and AI-powered receipt/photo processing.

**Constraints honored:**
- FastAPI (Python 3.12) with async support
- MongoDB Atlas with Motor and Pydantic v2 models
- No Docker deployment
- Frontend-driven manual testing through UI flows
- Single branch `main` workflow with commit/push after successful sprints
- API base path `/api/v1/*`
- Minimal, scalable design focused on current frontend needs

**Sprint count:** Dynamic (S0-S6) to fully cover all discovered frontend features.

## 2) In-scope & Success Criteria

**In-scope features:**
- User authentication (signup, login, logout) with JWT tokens
- User profile management with dietary restrictions, preferences, and family members
- Virtual pantry management with receipt-based item addition
- Recipe storage and management (AI-generated, community, photo-analysis)
- AI meal planning with shopping list generation
- Community posts and interactions (recipes, tips, savings stories)
- Receipt processing simulation and meal photo analysis
- Shopping list creation and management
- Leftover management suggestions
- Subscription tier management (free, basic, premium)

**Success criteria:**
- Full coverage of all frontend features identified in component analysis
- Each sprint passes manual UI testing before pushing to `main`
- Backend supports all frontend data models and user flows
- Scalable foundation for future AI integrations

## 3) API Design

**Conventions:**
- Base path: `/api/v1`
- Consistent JSON error envelope: `{"error": "message", "code": "ERROR_CODE"}`
- RESTful endpoints with standard HTTP methods
- Async request/response handling
- JWT-based authentication for protected routes

**Endpoints:**

**Health & System:**
- `GET /healthz` - Health check with DB connectivity status

**Authentication:**
- `POST /api/v1/auth/signup` - User registration
- `POST /api/v1/auth/login` - User login, returns JWT token
- `POST /api/v1/auth/logout` - User logout (token invalidation)
- `GET /api/v1/auth/me` - Get current user info

**User Profile:**
- `GET /api/v1/profile` - Get user profile
- `PUT /api/v1/profile` - Update user profile
- `POST /api/v1/profile/family-members` - Add family member
- `PUT /api/v1/profile/family-members/{id}` - Update family member
- `DELETE /api/v1/profile/family-members/{id}` - Remove family member

**Pantry Management:**
- `GET /api/v1/pantry` - Get all pantry items
- `POST /api/v1/pantry` - Add pantry item manually
- `PUT /api/v1/pantry/{id}` - Update pantry item
- `DELETE /api/v1/pantry/{id}` - Remove pantry item

**Receipt Processing:**
- `POST /api/v1/receipts/process` - Process receipt image, returns identified items
- `POST /api/v1/receipts/confirm` - Confirm processed items and add to pantry
- `GET /api/v1/receipts` - Get user's receipt history

**Recipe Management:**
- `GET /api/v1/recipes` - Get user's recipes with filtering by source/tags
- `POST /api/v1/recipes` - Create new recipe
- `GET /api/v1/recipes/{id}` - Get specific recipe
- `PUT /api/v1/recipes/{id}` - Update recipe
- `DELETE /api/v1/recipes/{id}` - Delete recipe
- `POST /api/v1/recipes/from-photo` - Analyze meal photo and generate recipe
- `POST /api/v1/recipes/from-link` - Extract recipe from URL

**Meal Planning:**
- `GET /api/v1/meal-plans` - Get user's meal plans
- `POST /api/v1/meal-plans/generate` - Generate AI meal plan based on pantry/preferences
- `GET /api/v1/meal-plans/{id}` - Get specific meal plan
- `PUT /api/v1/meal-plans/{id}` - Update meal plan
- `DELETE /api/v1/meal-plans/{id}` - Delete meal plan

**Shopping Lists:**
- `GET /api/v1/shopping-lists` - Get user's shopping lists
- `POST /api/v1/shopping-lists` - Create shopping list
- `GET /api/v1/shopping-lists/{id}` - Get specific shopping list
- `PUT /api/v1/shopping-lists/{id}` - Update shopping list
- `DELETE /api/v1/shopping-lists/{id}` - Delete shopping list
- `PUT /api/v1/shopping-lists/{id}/items/{item_id}` - Mark item as purchased

**Community:**
- `GET /api/v1/community/posts` - Get community posts with filtering by type
- `POST /api/v1/community/posts` - Create community post
- `GET /api/v1/community/posts/{id}` - Get specific post
- `PUT /api/v1/community/posts/{id}/like` - Like/unlike post
- `POST /api/v1/community/posts/{id}/comments` - Add comment to post

**Leftovers:**
- `POST /api/v1/leftovers/suggestions` - Get leftover recipe suggestions based on ingredients

## 4) Data Model (MongoDB Atlas)

**Collections:**

**users:**
- `_id: ObjectId` - MongoDB document ID
- `email: str` - User email (unique)
- `name: str` - User display name
- `password_hash: str` - Argon2 hashed password
- `subscription: str` - Subscription tier (free, basic, premium)
- `trial_ends_at: datetime` - Trial expiration (optional)
- `monthly_usage: dict` - Usage tracking (receipt_scans, meal_plans, community_posts)
- `created_at: datetime` - Account creation timestamp
- `updated_at: datetime` - Last update timestamp

Example: `{"_id": ObjectId("..."), "email": "user@example.com", "name": "John Doe", "subscription": "basic", "created_at": "2025-01-01T00:00:00Z"}`

**profiles:**
- `_id: ObjectId` - MongoDB document ID
- `user_id: ObjectId` - Reference to users collection
- `dietary_restrictions: list[str]` - List of dietary restrictions
- `allergies: list[str]` - List of allergies
- `taste_preferences: list[str]` - Preferred cuisines/flavors
- `meal_preferences: list[str]` - Meal type preferences
- `kitchen_equipment: list[str]` - Available kitchen equipment
- `weekly_budget: float` - Weekly grocery budget
- `zip_code: str` - Location for store deals
- `family_members: list[dict]` - Embedded family member objects
- `preferred_grocers: list[str]` - Preferred grocery stores
- `created_at: datetime` - Profile creation timestamp
- `updated_at: datetime` - Last update timestamp

Example: `{"user_id": ObjectId("..."), "weekly_budget": 150.0, "dietary_restrictions": ["vegetarian"], "family_members": [{"name": "Jane", "age": 8, "allergies": ["nuts"]}]}`

**pantry_items:**
- `_id: ObjectId` - MongoDB document ID
- `user_id: ObjectId` - Reference to users collection
- `name: str` - Item name
- `quantity: float` - Quantity available
- `unit: str` - Unit of measurement
- `expiration_date: datetime` - Expiration date (optional)
- `source: str` - Source (receipt, manual)
- `added_at: datetime` - When item was added
- `updated_at: datetime` - Last update timestamp

Example: `{"user_id": ObjectId("..."), "name": "Chicken breast", "quantity": 2.0, "unit": "lbs", "source": "receipt", "added_at": "2025-01-01T00:00:00Z"}`

**recipes:**
- `_id: ObjectId` - MongoDB document ID
- `user_id: ObjectId` - Reference to users collection (optional for community recipes)
- `title: str` - Recipe title
- `description: str` - Recipe description
- `ingredients: list[dict]` - Ingredient objects with name, quantity, unit
- `instructions: list[str]` - Step-by-step instructions
- `prep_time: int` - Preparation time in minutes
- `cook_time: int` - Cooking time in minutes
- `servings: int` - Number of servings
- `difficulty: str` - Difficulty level (easy, medium, hard)
- `tags: list[str]` - Recipe tags
- `nutrition_info: dict` - Nutritional information (optional)
- `source: str` - Recipe source (ai-generated, community, photo-analysis)
- `created_at: datetime` - Recipe creation timestamp
- `updated_at: datetime` - Last update timestamp

Example: `{"title": "Quick Stir Fry", "ingredients": [{"name": "chicken", "quantity": 1, "unit": "lb"}], "prep_time": 15, "cook_time": 20, "source": "ai-generated"}`

**meal_plans:**
- `_id: ObjectId` - MongoDB document ID
- `user_id: ObjectId` - Reference to users collection
- `week_starting: datetime` - Start date of the week
- `meals: list[dict]` - Planned meal objects with day, meal_type, recipe_id, servings
- `shopping_list: list[dict]` - Shopping list items with name, quantity, price, store
- `total_estimated_cost: float` - Total estimated cost
- `created_at: datetime` - Plan creation timestamp
- `updated_at: datetime` - Last update timestamp

Example: `{"user_id": ObjectId("..."), "week_starting": "2025-01-06T00:00:00Z", "meals": [{"day": "Monday", "meal_type": "dinner", "recipe_id": ObjectId("..."), "servings": 4}], "total_estimated_cost": 85.50}`

**receipts:**
- `_id: ObjectId` - MongoDB document ID
- `user_id: ObjectId` - Reference to users collection
- `image_url: str` - Stored image URL/path
- `items: list[dict]` - Processed receipt items
- `total: float` - Receipt total amount
- `store: str` - Store name
- `date: datetime` - Receipt date
- `processed: bool` - Processing status
- `created_at: datetime` - Upload timestamp

Example: `{"user_id": ObjectId("..."), "store": "Kroger", "total": 45.67, "items": [{"name": "Milk", "quantity": 1, "price": 3.29}], "processed": true}`

**community_posts:**
- `_id: ObjectId` - MongoDB document ID
- `user_id: ObjectId` - Reference to users collection
- `user_name: str` - Display name of poster
- `title: str` - Post title
- `content: str` - Post content
- `type: str` - Post type (recipe, tip, savings-story)
- `likes: int` - Number of likes
- `comments: list[dict]` - Embedded comment objects
- `created_at: datetime` - Post creation timestamp
- `updated_at: datetime` - Last update timestamp

Example: `{"user_id": ObjectId("..."), "title": "Saved $50 this week!", "type": "savings-story", "likes": 23, "comments": [{"user_name": "Jane", "content": "Great tip!", "created_at": "2025-01-01T00:00:00Z"}]}`

**shopping_lists:**
- `_id: ObjectId` - MongoDB document ID
- `user_id: ObjectId` - Reference to users collection
- `name: str` - List name
- `items: list[dict]` - Shopping list items with name, quantity, unit, estimated_price, store, category, purchased
- `created_at: datetime` - List creation timestamp
- `updated_at: datetime` - Last update timestamp

Example: `{"user_id": ObjectId("..."), "name": "Weekly Groceries", "items": [{"name": "Bread", "quantity": 2, "unit": "loaves", "estimated_price": 4.98, "store": "Walmart", "purchased": false}]}`

## 5) Frontend Audit & Feature Map

**Authentication Flow ([`AuthForm.tsx`](frontend/src/components/AuthForm.tsx:1)):**
- Route: `/` (when not authenticated)
- Purpose: User signup/login with email/password or Google OAuth simulation
- Backend capability: [`POST /api/v1/auth/signup`](Backend-dev-plan.md:67), [`POST /api/v1/auth/login`](Backend-dev-plan.md:68)
- Auth requirement: None (public)
- Notes: Supports both new user (plan selection flow) and existing user (direct to dashboard)

**Dashboard ([`Dashboard.tsx`](frontend/src/components/Dashboard.tsx:1)):**
- Route: `/` (when authenticated)
- Purpose: Main hub showing pantry stats, recent recipes, meal plans, quick actions
- Backend capability: [`GET /api/v1/pantry`](Backend-dev-plan.md:76), [`GET /api/v1/recipes`](Backend-dev-plan.md:85), [`GET /api/v1/meal-plans`](Backend-dev-plan.md:93), [`GET /healthz`](Backend-dev-plan.md:63)
- Auth requirement: JWT required
- Notes: Central navigation point to all other features

**Profile Management ([`Profile.tsx`](frontend/src/components/Profile.tsx:1), [`ProfileSetup.tsx`](frontend/src/components/ProfileSetup.tsx:1)):**
- Route: Profile setup flow and `/profile`
- Purpose: User profile configuration with dietary restrictions, family members, budget
- Backend capability: [`GET /api/v1/profile`](Backend-dev-plan.md:72), [`PUT /api/v1/profile`](Backend-dev-plan.md:73), family member CRUD
- Auth requirement: JWT required
- Notes: Supports subscription tier selection (free, basic, premium)

**Receipt Processing ([`ReceiptScan.tsx`](frontend/src/components/ReceiptScan.tsx:1)):**
- Route: `/receipt-scan`
- Purpose: Upload receipt images, AI processing, review items, add to pantry
- Backend capability: [`POST /api/v1/receipts/process`](Backend-dev-plan.md:81), [`POST /api/v1/receipts/confirm`](Backend-dev-plan.md:82)
- Auth requirement: JWT required
- Notes: Multi-step flow with image upload and item confirmation

**Meal Photo Analysis ([`MealPhotoAnalysis.tsx`](frontend/src/components/MealPhotoAnalysis.tsx:1)):**
- Route: `/meal-photo`
- Purpose: Upload meal photos, AI analysis to generate recipes
- Backend capability: [`POST /api/v1/recipes/from-photo`](Backend-dev-plan.md:91)
- Auth requirement: JWT required
- Notes: AI-powered recipe reverse engineering

**Recipe Management ([`Recipes.tsx`](frontend/src/components/Recipes.tsx:1), [`RecipeDetail.tsx`](frontend/src/components/RecipeDetail.tsx:1), [`CreateRecipe.tsx`](frontend/src/components/CreateRecipe.tsx:1)):**
- Route: `/recipes`, `/recipe-detail`, `/create-recipe`
- Purpose: View, create, edit recipes from various sources
- Backend capability: Recipe CRUD endpoints, [`POST /api/v1/recipes/from-link`](Backend-dev-plan.md:92)
- Auth requirement: JWT required
- Notes: Supports multiple recipe sources (AI, manual, photo, link)

**Meal Planning ([`MealPlanner.tsx`](frontend/src/components/MealPlanner.tsx:1)):**
- Route: `/meal-planner`
- Purpose: Generate AI-powered weekly meal plans with shopping lists
- Backend capability: [`POST /api/v1/meal-plans/generate`](Backend-dev-plan.md:94), meal plan CRUD
- Auth requirement: JWT required
- Notes: Complex multi-step flow with pantry analysis and cost estimation

**Pantry Management ([`Pantry.tsx`](frontend/src/components/Pantry.tsx:1)):**
- Route: `/pantry`
- Purpose: View and manage virtual pantry items
- Backend capability: Pantry CRUD endpoints
- Auth requirement: JWT required
- Notes: Items sourced from receipts or manual entry

**Shopping Lists ([`ShoppingListManager.tsx`](frontend/src/components/ShoppingListManager.tsx:1), [`ShoppingListBuilder.tsx`](frontend/src/components/ShoppingListBuilder.tsx:1)):**
- Route: `/shopping-lists`, `/create-shopping-list`
- Purpose: Create and manage shopping lists with store organization
- Backend capability: Shopping list CRUD endpoints
- Auth requirement: JWT required
- Notes: Supports multiple lists and item purchase tracking

**Community Features ([`Community.tsx`](frontend/src/components/Community.tsx:1)):**
- Route: `/community`
- Purpose: Share recipes, tips, savings stories with other users
- Backend capability: Community post CRUD, like/comment functionality
- Auth requirement: JWT required
- Notes: Different post types with engagement features

**Leftover Management ([`LeftoverManager.tsx`](frontend/src/components/LeftoverManager.tsx:1)):**
- Route: `/leftovers`
- Purpose: Get suggestions for using leftover ingredients
- Backend capability: [`POST /api/v1/leftovers/suggestions`](Backend-dev-plan.md:109)
- Auth requirement: JWT required
- Notes: AI-powered suggestions based on available ingredients

**Family Members ([`FamilyMembers.tsx`](frontend/src/components/FamilyMembers.tsx:1)):**
- Route: `/family-members`
- Purpose: Manage family member profiles with dietary restrictions
- Backend capability: Family member CRUD within profile endpoints
- Auth requirement: JWT required
- Notes: Embedded within user profile data model

## 6) Configuration & ENV Vars (core only)

- `APP_ENV` - Environment name (development, production)
- `PORT` - HTTP server port (default: 8000)
- `MONGODB_URI` - MongoDB Atlas connection string
- `JWT_SECRET` - JWT token signing secret key
- `JWT_EXPIRES_IN` - Access token lifetime in seconds (default: 86400)
- `CORS_ORIGINS` - Allowed CORS origins (frontend URL)

## 7) Testing Strategy (Manual via Frontend)

**Policy:** Validate all functionality through the frontend UI by navigating screens, submitting forms, and observing expected behavior. Use browser DevTools Network tab to verify API calls and responses.

**Per-sprint Manual Test Checklist (Frontend):** Each sprint includes specific UI test steps and expected outcomes.

**User Test Prompt:** Copy-pasteable instructions for human testers to verify functionality through the UI.

**Post-sprint:** After successful manual testing, commit all changes and push to GitHub `main` branch.

## 8) Dynamic Sprint Plan & Backlog (S0-S6)

### S0 - Environment Setup & Frontend Connection

**Objectives:**
- Create FastAPI skeleton with health check endpoint
- Establish MongoDB Atlas connection
- Enable CORS for frontend
- Initialize Git repository and GitHub setup
- Wire frontend to backend with live health check

**User Stories:**
- As a developer, I need a working FastAPI server so I can build API endpoints
- As a developer, I need database connectivity so I can store application data
- As a user, I need the frontend to connect to the backend so I can use live data

**Tasks:**
- Set up FastAPI project structure with async support
- Create [`/healthz`](Backend-dev-plan.md:63) endpoint with MongoDB ping check
- Configure CORS middleware for frontend origin
- Set up MongoDB Atlas connection with Motor
- Create basic Pydantic models for health check response
- Initialize Git repository with `.gitignore`
- Create GitHub repository and set `main` as default branch
- Update frontend API configuration to use backend URL
- Replace at least one frontend dummy call with real backend call

**Definition of Done:**
- FastAPI server runs on specified port
- [`/healthz`](Backend-dev-plan.md:63) endpoint returns JSON with DB connectivity status
- Frontend successfully calls backend health check
- Repository exists on GitHub with initial commit on `main` branch
- CORS allows frontend requests

**Manual Test Checklist (Frontend):**
- Start backend server and verify it runs without errors
- Open frontend application
- Navigate to a page that triggers health check call
- Verify successful API response in browser Network tab
- Confirm health check shows database connectivity

**User Test Prompt:**
"Open the EZ Eatin' app. You should see the dashboard load successfully. Open browser DevTools > Network tab and refresh the page. Look for a successful call to '/healthz' endpoint showing the backend is connected."

**Post-sprint:**
- Commit all setup files and initial configuration
- Push to GitHub `main` branch

### S1 - Basic Authentication (signup, login, logout)

**Objectives:**
- Implement user registration and login with JWT tokens
- Create user data model and storage
- Protect at least one API endpoint with authentication
- Enable frontend authentication flow

**User Stories:**
- As a new user, I can create an account so I can access the application
- As a returning user, I can log in so I can access my data
- As a user, I can log out so I can secure my account
- As a user, I need protected access so my data remains private

**Tasks:**
- Create User Pydantic model matching frontend types
- Implement password hashing with Argon2
- Create users MongoDB collection with indexes
- Build auth endpoints: [`signup`](Backend-dev-plan.md:67), [`login`](Backend-dev-plan.md:68), [`logout`](Backend-dev-plan.md:69)
- Implement JWT token generation and validation
- Create authentication middleware for protected routes
- Protect [`/api/v1/auth/me`](Backend-dev-plan.md:70) endpoint as test case
- Update frontend to handle JWT tokens in requests
- Implement token storage and automatic inclusion in API calls

**Definition of Done:**
- Users can successfully sign up through frontend
- Users can log in and receive JWT token
- Protected endpoints require valid JWT token
- Frontend stores and uses JWT for authenticated requests
- Users can log out and token is invalidated

**Manual Test Checklist (Frontend):**
- Navigate to signup form and create new account
- Verify successful account creation and automatic login
- Log out and attempt to log back in with same credentials
- Try accessing a protected page without being logged in
- Verify unauthorized access is properly blocked
- Check that user session persists across browser refresh

**User Test Prompt:**
"Go to the EZ Eatin' login page. Click 'Sign Up' and create a new account with your email and a password. After signup, you should be automatically logged in and see the dashboard. Click 'Profile' in the header, then log out. Try to access the dashboard - you should be redirected to login. Log back in with your credentials."

**Post-sprint:**
- Commit authentication implementation
- Push to GitHub `main` branch

### S2 - User Profile Management

**Objectives:**
- Implement user profile creation and updates
- Support dietary restrictions, preferences, and family members
- Enable profile setup flow for new users
- Create subscription tier management

**User Stories:**
- As a new user, I can set up my profile so the app can personalize recommendations
- As a user, I can update my dietary restrictions so recipes match my needs
- As a user, I can add family members so meal planning considers everyone
- As a user, I can set my budget so meal plans stay within my limits

**Tasks:**
- Create UserProfile Pydantic model with all frontend fields
- Create profiles MongoDB collection with user_id reference
- Implement profile CRUD endpoints
- Create family member management endpoints
- Support subscription tier updates (free, basic, premium)
- Handle profile setup flow for new users
- Implement profile validation and error handling
- Connect frontend profile forms to backend endpoints

**Definition of Done:**
- New users can complete profile setup flow
- Users can view and edit their profile information
- Family members can be added, updated, and removed
- Dietary restrictions and preferences are properly stored
- Subscription tiers are correctly managed

**Manual Test Checklist (Frontend):**
- Create new account and go through profile setup
- Test each step of profile setup (basic, medium, full plans)
- Edit profile information and verify changes persist
- Add, edit, and remove family members
- Verify dietary restrictions and preferences are saved
- Test subscription tier changes

**User Test Prompt:**
"Create a new account and follow the profile setup flow. Choose the 'medium' plan and fill out your dietary restrictions, add a family member, and set your weekly budget. Save the profile, then go to Profile settings and make some changes. Verify all your information is saved correctly."

**Post-sprint:**
- Commit profile management implementation
- Push to GitHub `main` branch

### S3 - Pantry & Receipt Processing

**Objectives:**
- Implement virtual pantry management
- Create receipt processing simulation
- Enable adding items from receipts to pantry
- Support manual pantry item management

**User Stories:**
- As a user, I can scan receipts so my pantry is automatically updated
- As a user, I can manually add pantry items so I track everything I have
- As a user, I can view my pantry so I know what ingredients are available
- As a user, I can edit pantry items so quantities stay accurate

**Tasks:**
- Create PantryItem and Receipt Pydantic models
- Create pantry_items and receipts MongoDB collections
- Implement pantry CRUD endpoints
- Create receipt processing simulation endpoints
- Build multi-step receipt flow (upload, process, confirm)
- Implement image handling for receipt uploads
- Connect frontend receipt scanner to backend
- Enable pantry item management through frontend

**Definition of Done:**
- Users can upload receipt images through frontend
- Receipt processing simulation returns mock item data
- Users can review and confirm receipt items
- Confirmed items are added to user's pantry
- Users can manually add, edit, and remove pantry items
- Pantry displays correctly on dashboard

**Manual Test Checklist (Frontend):**
- Navigate to receipt scanner and upload an image
- Wait for processing and review identified items
- Confirm items and verify they appear in pantry
- Manually add a new pantry item
- Edit an existing pantry item's quantity
- Delete a pantry item
- Check pantry count on dashboard updates correctly

**User Test Prompt:**
"Go to the dashboard and click 'Scan Receipt'. Upload any image file and wait for processing. Review the mock items found and click 'Add to Pantry'. Go to the Pantry page and verify the items appear. Add a manual item like 'Salt - 1 container'. Edit one item's quantity and delete another item."

**Post-sprint:**
- Commit pantry and receipt processing implementation
- Push to GitHub `main` branch

### S4 - Recipe Management & AI Features

**Objectives:**
- Implement recipe storage and management
- Create meal photo analysis simulation
- Support recipe creation from multiple sources
- Enable recipe CRUD operations

**User Stories:**
- As a user, I can save recipes so I can cook them later
- As a user, I can take photos of meals to get recipes
- As a user, I can create my own recipes
- As a user, I can add recipes from links
- As a user, I can organize and search my recipes

**Tasks:**
- Create Recipe Pydantic model with all frontend fields
- Create recipes MongoDB collection
- Implement recipe CRUD endpoints
- Create meal photo analysis simulation
- Build recipe-from-link extraction (mock)
- Support manual recipe creation
- Implement recipe filtering and search
- Connect all frontend recipe components to backend

**Definition of Done:**
- Users can view their saved recipes
- Meal photo analysis generates mock recipes
- Users can create recipes manually
- Recipe-from-link feature works with mock data
- Recipes can be edited and deleted
- Recipe detail view works correctly

**Manual Test Checklist (Frontend):**
- Navigate to meal photo analysis and upload an image
- Wait for processing and save the generated recipe
- Go to create recipe and manually add a new recipe
- Try the add-from-link feature with any URL
- View all recipes and click on one to see details
- Edit a recipe and verify changes save
- Delete a recipe and confirm it's removed

**User Test Prompt:**
"Go to 'Add Recipe' > 'Add from photo' and upload any image. Save the generated recipe. Then try 'Create my own' and make a simple recipe. Go to 'Recipes' page and verify both recipes appear. Click on one to view details, then edit it to change the title."

**Post-sprint:**
- Commit recipe management implementation
- Push to GitHub `main` branch

### S5 - Meal Planning & Shopping Lists

**Objectives:**
- Implement AI meal plan generation
- Create shopping list management
- Support weekly meal planning workflow
- Enable shopping list item tracking

**User Stories:**
- As a user, I can generate weekly meal plans so I know what to cook
- As a user, I can create shopping lists so I know what to buy
- As a user, I can see cost estimates so I stay within budget
- As a user, I can mark items as purchased so I track my shopping

**Tasks:**
- Create MealPlan and ShoppingList Pydantic models
- Create meal_plans and shopping_lists MongoDB collections
- Implement meal plan generation with mock AI logic
- Build meal plan CRUD endpoints
- Create shopping list CRUD endpoints
- Implement shopping list item purchase tracking
- Connect frontend meal planner to backend
- Enable shopping list management through frontend

**Definition of Done:**
- Users can generate weekly meal plans
- Meal plans include recipes and shopping lists
- Cost estimates are calculated and displayed
- Shopping lists can be created and managed
- Items can be marked as purchased
- Multiple shopping lists are supported

**Manual Test Checklist (Frontend):**
- Go to meal planner and generate a new meal plan
- Review the generated plan and shopping list
- Verify cost estimates are shown
- Go to shopping lists and create a new list
- Add items to the list and mark some as purchased
- Edit a shopping list and verify changes save

**User Test Prompt:**
"Navigate to 'Weekly Meal Plan' and click 'Generate New Meal Plan'. Wait for the AI to create your plan and review the meals and shopping list. Note the total cost. Then go to 'My Shopping Lists' and create a new list called 'Weekend Groceries'. Add a few items and mark one as purchased."

**Post-sprint:**
- Commit meal planning and shopping list implementation
- Push to GitHub `main` branch

### S6 - Community & Leftover Features

**Objectives:**
- Implement community post system
- Create leftover suggestion feature
- Support post interactions (likes, comments)
- Enable community engagement

**User Stories:**
- As a user, I can share recipes and tips with the community
- As a user, I can like and comment on community posts
- As a user, I can get suggestions for using leftovers
- As a user, I can browse community content for inspiration

**Tasks:**
- Create CommunityPost Pydantic model
- Create community_posts MongoDB collection
- Implement community post CRUD endpoints
- Build like and comment functionality
- Create leftover suggestion endpoint with mock logic
- Support different post types (recipe, tip, savings-story)
- Connect frontend community features to backend
- Implement leftover manager backend logic

**Definition of Done:**
- Users can create community posts of different types
- Posts can be liked and commented on
- Community feed displays posts correctly
- Leftover suggestions work based on pantry items
- Post interactions update in real-time

**Manual Test Checklist (Frontend):**
- Go to Community and create a new post (tip or savings story)
- Like and comment on existing posts
- Verify your post appears in the community feed
- Go to leftover manager and get suggestions
- Verify suggestions are based on your pantry items

**User Test Prompt:**
"Navigate to the Community page and create a new post sharing a cooking tip. Like a few existing posts and add comments. Then go to 'Use Leftovers' and see what suggestions you get based on your pantry items."

**Post-sprint:**
- Commit community and leftover features implementation
- Push to GitHub `main` branch
- Final deployment verification and documentation update