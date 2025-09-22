# EZ Eatin' Backend API

AI-driven meal planning and recipe management backend built with FastAPI and MongoDB Atlas.

## Overview

EZ Eatin' is a comprehensive meal planning application that helps families reduce grocery costs and meal planning time through AI-powered features including:

- Receipt processing and virtual pantry management
- Meal photo analysis for recipe generation
- Personalized meal planning with budget optimization
- Community features for sharing recipes and tips
- Shopping list generation and management

## Technology Stack

- **Framework**: FastAPI (Python 3.12)
- **Database**: MongoDB Atlas with Motor (async driver)
- **Authentication**: JWT tokens with Argon2 password hashing
- **Data Validation**: Pydantic v2
- **ASGI Server**: Uvicorn

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── database.py          # MongoDB connection and configuration
│   ├── models/              # Pydantic models
│   │   ├── __init__.py
│   │   └── responses.py     # API response models
│   └── routers/             # API route handlers
│       ├── __init__.py
│       ├── auth.py          # Authentication endpoints
│       ├── profile.py       # User profile management
│       ├── pantry.py        # Pantry management
│       ├── receipts.py      # Receipt processing
│       ├── recipes.py       # Recipe management
│       ├── meal_plans.py    # Meal planning
│       ├── shopping_lists.py # Shopping list management
│       ├── community.py     # Community features
│       └── leftovers.py     # Leftover suggestions
├── main.py                  # FastAPI application entry point
├── requirements.txt         # Python dependencies
├── .env.example            # Environment variables template
├── .gitignore              # Git ignore rules
└── README.md               # This file
```

## Setup Instructions

### Prerequisites

- Python 3.12+
- MongoDB Atlas account (or local MongoDB instance)
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd floating-kraken-dash/backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your MongoDB URI and other configuration
   ```

5. **Run the application**
   ```bash
   python main.py
   ```

   Or using uvicorn directly:
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `APP_ENV` | Application environment | `development` |
| `PORT` | HTTP server port | `8000` |
| `MONGODB_URI` | MongoDB connection string | Required |
| `DATABASE_NAME` | MongoDB database name | `ez_eatin` |
| `JWT_SECRET` | JWT signing secret | Required |
| `JWT_EXPIRES_IN` | Token expiration (seconds) | `86400` |
| `CORS_ORIGINS` | Allowed CORS origins | Frontend URLs |

## API Endpoints

### Health Check
- `GET /healthz` - Health check with database connectivity

### Authentication (`/api/v1/auth`)
- `POST /signup` - User registration
- `POST /login` - User login
- `POST /logout` - User logout
- `GET /me` - Get current user info

### User Profile (`/api/v1/profile`)
- `GET /` - Get user profile
- `PUT /` - Update user profile
- `POST /family-members` - Add family member
- `PUT /family-members/{id}` - Update family member
- `DELETE /family-members/{id}` - Remove family member

### Pantry Management (`/api/v1/pantry`)
- `GET /` - Get all pantry items
- `POST /` - Add pantry item
- `PUT /{id}` - Update pantry item
- `DELETE /{id}` - Remove pantry item

### Receipt Processing (`/api/v1/receipts`)
- `POST /process` - Process receipt image
- `POST /confirm` - Confirm processed items
- `GET /` - Get receipt history

### Recipe Management (`/api/v1/recipes`)
- `GET /` - Get user recipes
- `POST /` - Create new recipe
- `GET /{id}` - Get specific recipe
- `PUT /{id}` - Update recipe
- `DELETE /{id}` - Delete recipe
- `POST /from-photo` - Generate recipe from meal photo
- `POST /from-link` - Extract recipe from URL

### Meal Planning (`/api/v1/meal-plans`)
- `GET /` - Get meal plans
- `POST /generate` - Generate AI meal plan
- `GET /{id}` - Get specific meal plan
- `PUT /{id}` - Update meal plan
- `DELETE /{id}` - Delete meal plan

### Shopping Lists (`/api/v1/shopping-lists`)
- `GET /` - Get shopping lists
- `POST /` - Create shopping list
- `GET /{id}` - Get specific shopping list
- `PUT /{id}` - Update shopping list
- `DELETE /{id}` - Delete shopping list
- `PUT /{id}/items/{item_id}` - Mark item as purchased

### Community (`/api/v1/community`)
- `GET /posts` - Get community posts
- `POST /posts` - Create community post
- `GET /posts/{id}` - Get specific post
- `PUT /posts/{id}/like` - Like/unlike post
- `POST /posts/{id}/comments` - Add comment

### Leftovers (`/api/v1/leftovers`)
- `POST /suggestions` - Get leftover recipe suggestions

## Development

### Running Tests
```bash
pytest
```

### Code Style
The project follows PEP 8 style guidelines. Use tools like `black` and `flake8` for formatting and linting.

### Database Schema
The application uses MongoDB with the following collections:
- `users` - User accounts and authentication
- `profiles` - User profiles and preferences
- `pantry_items` - Virtual pantry management
- `recipes` - Recipe storage and management
- `meal_plans` - Weekly meal plans
- `receipts` - Receipt processing history
- `community_posts` - Community posts and interactions
- `shopping_lists` - Shopping list management

## Deployment

The application is designed to run without Docker. For production deployment:

1. Set `APP_ENV=production` in environment variables
2. Use a production ASGI server like Gunicorn with Uvicorn workers
3. Configure proper MongoDB Atlas connection with authentication
4. Set secure JWT secrets and CORS origins
5. Enable proper logging and monitoring

## Contributing

1. Follow the sprint-based development approach outlined in Backend-dev-plan.md
2. Test all changes through the frontend UI before committing
3. Commit and push to the `main` branch after successful sprint completion
4. Maintain API compatibility with the existing frontend components

## License

[License information to be added]