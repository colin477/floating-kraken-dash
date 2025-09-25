# EZ Eatin' Developer Documentation

## Overview

EZ Eatin' is a full-stack meal planning application built with modern web technologies. This documentation provides comprehensive guidance for developers working on the project, including setup, architecture, coding standards, and contribution guidelines.

## Table of Contents

1. [Project Architecture](#project-architecture)
2. [Development Environment Setup](#development-environment-setup)
3. [Backend Development](#backend-development)
4. [Frontend Development](#frontend-development)
5. [Database Schema](#database-schema)
6. [API Development](#api-development)
7. [Testing Guidelines](#testing-guidelines)
8. [Code Style & Standards](#code-style--standards)
9. [Git Workflow](#git-workflow)
10. [Deployment Process](#deployment-process)
11. [Performance Guidelines](#performance-guidelines)
12. [Security Considerations](#security-considerations)
13. [Troubleshooting](#troubleshooting)

---

## Project Architecture

### High-Level Architecture

```mermaid
graph TB
    subgraph "Frontend Layer"
        REACT[React + TypeScript]
        VITE[Vite Build Tool]
        TAILWIND[Tailwind CSS]
        SHADCN[Shadcn/ui Components]
    end
    
    subgraph "Backend Layer"
        FASTAPI[FastAPI + Python 3.11]
        PYDANTIC[Pydantic Models]
        MOTOR[Motor MongoDB Driver]
        JWT[JWT Authentication]
    end
    
    subgraph "Database Layer"
        MONGODB[(MongoDB Atlas)]
        INDEXES[Database Indexes]
        AGGREGATION[Aggregation Pipelines]
    end
    
    subgraph "External Services"
        RENDER[Render Hosting]
        GITHUB[GitHub Actions CI/CD]
        ATLAS[MongoDB Atlas]
    end
    
    REACT --> FASTAPI
    FASTAPI --> MONGODB
    GITHUB --> RENDER
    RENDER --> FASTAPI
    RENDER --> REACT
```

### Technology Stack

#### Backend
- **Framework**: FastAPI 0.104.1
- **Language**: Python 3.11
- **Database**: MongoDB with Motor (async driver)
- **Authentication**: JWT with Argon2 password hashing
- **Validation**: Pydantic v2
- **Server**: Uvicorn ASGI server
- **Testing**: Pytest with async support

#### Frontend
- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite 6.3.4
- **Styling**: Tailwind CSS + Shadcn/ui components
- **State Management**: React Query + Context API
- **Routing**: React Router DOM
- **Testing**: Vitest + Playwright for E2E

#### Infrastructure
- **Hosting**: Render (backend + frontend)
- **Database**: MongoDB Atlas
- **CI/CD**: GitHub Actions
- **Monitoring**: Built-in health checks

---

## Development Environment Setup

### Prerequisites

- **Node.js**: 18+ (for frontend)
- **Python**: 3.11+ (for backend)
- **MongoDB**: Local instance or Atlas connection
- **Git**: Version control
- **VS Code**: Recommended IDE with extensions

### Initial Setup

1. **Clone Repository**
   ```bash
   git clone <repository-url>
   cd floating-kraken-dash
   ```

2. **Backend Setup**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   cp .env.example .env
   # Edit .env with your MongoDB URI and JWT secret
   ```

3. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   # or
   pnpm install
   ```

4. **Database Setup**
   - Create MongoDB Atlas cluster or use local MongoDB
   - Update connection string in backend/.env
   - Run initial database setup if needed

### Running the Application

#### Development Mode

**Backend** (Terminal 1):
```bash
cd backend
python main.py
# Server runs on http://localhost:8000
```

**Frontend** (Terminal 2):
```bash
cd frontend
npm run dev
# App runs on http://localhost:5173
```

#### Production Mode

**Backend**:
```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

**Frontend**:
```bash
cd frontend
npm run build
npm run preview
```

### Environment Variables

#### Backend (.env)
```bash
# Application
APP_ENV=development
PORT=8000

# Database
MONGODB_URI=mongodb://localhost:27017/ez_eatin_dev
DATABASE_NAME=ez_eatin_dev

# Authentication
JWT_SECRET=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRES_IN=86400

# CORS
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# Features
DEMO_MODE_ENABLED=true
```

#### Frontend (.env)
```bash
# API Configuration
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_APP_ENV=development

# Features
VITE_DEMO_MODE_ENABLED=true
VITE_DEBUG_MODE=true
```

---

## Backend Development

### Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── database.py              # MongoDB connection
│   ├── models/                  # Pydantic models
│   │   ├── auth.py             # Authentication models
│   │   ├── pantry.py           # Pantry models
│   │   ├── recipes.py          # Recipe models
│   │   ├── meal_plans.py       # Meal planning models
│   │   ├── shopping_lists.py   # Shopping list models
│   │   ├── community.py        # Community models
│   │   └── responses.py        # Response models
│   ├── routers/                # API route handlers
│   │   ├── auth.py             # Authentication endpoints
│   │   ├── profile.py          # User profile endpoints
│   │   ├── pantry.py           # Pantry management
│   │   ├── recipes.py          # Recipe management
│   │   ├── meal_plans.py       # Meal planning
│   │   ├── shopping_lists.py   # Shopping lists
│   │   ├── receipts.py         # Receipt processing
│   │   ├── community.py        # Community features
│   │   └── leftovers.py        # Leftover suggestions
│   ├── crud/                   # Database operations
│   │   ├── users.py            # User CRUD operations
│   │   ├── pantry.py           # Pantry CRUD operations
│   │   └── ...                 # Other CRUD modules
│   ├── utils/                  # Utility functions
│   │   ├── auth.py             # Authentication utilities
│   │   └── validation.py       # Validation helpers
│   └── middleware/             # Custom middleware
│       ├── security.py         # Security middleware
│       └── performance.py      # Performance middleware
├── tests/                      # Test files
├── main.py                     # Application entry point
├── requirements.txt            # Python dependencies
└── .env.example               # Environment template
```

### Adding New Endpoints

1. **Create Pydantic Models** (if needed)
   ```python
   # app/models/new_feature.py
   from pydantic import BaseModel, Field
   from typing import Optional
   from datetime import datetime

   class NewFeatureCreate(BaseModel):
       name: str = Field(..., min_length=1, max_length=200)
       description: Optional[str] = None

   class NewFeatureResponse(BaseModel):
       id: str
       name: str
       description: Optional[str]
       created_at: datetime
       updated_at: datetime

       model_config = {"from_attributes": True}
   ```

2. **Create CRUD Operations**
   ```python
   # app/crud/new_feature.py
   from motor.motor_asyncio import AsyncIOMotorDatabase
   from bson import ObjectId
   from typing import List, Optional

   async def create_item(db: AsyncIOMotorDatabase, user_id: str, item_data: dict) -> dict:
       item_data["user_id"] = user_id
       item_data["created_at"] = datetime.utcnow()
       item_data["updated_at"] = datetime.utcnow()
       
       result = await db.new_feature_collection.insert_one(item_data)
       created_item = await db.new_feature_collection.find_one({"_id": result.inserted_id})
       created_item["id"] = str(created_item["_id"])
       return created_item

   async def get_user_items(db: AsyncIOMotorDatabase, user_id: str) -> List[dict]:
       cursor = db.new_feature_collection.find({"user_id": user_id})
       items = await cursor.to_list(length=None)
       for item in items:
           item["id"] = str(item["_id"])
       return items
   ```

3. **Create Router**
   ```python
   # app/routers/new_feature.py
   from fastapi import APIRouter, Depends, HTTPException, status
   from app.models.new_feature import NewFeatureCreate, NewFeatureResponse
   from app.crud import new_feature as crud
   from app.utils.auth import get_current_active_user
   from app.database import get_database

   router = APIRouter(prefix="/new-feature", tags=["new-feature"])

   @router.post("/", response_model=NewFeatureResponse, status_code=status.HTTP_201_CREATED)
   async def create_item(
       item_data: NewFeatureCreate,
       current_user: dict = Depends(get_current_active_user),
       db = Depends(get_database)
   ):
       try:
           created_item = await crud.create_item(db, current_user["id"], item_data.dict())
           return NewFeatureResponse(**created_item)
       except Exception as e:
           raise HTTPException(status_code=500, detail=str(e))

   @router.get("/", response_model=List[NewFeatureResponse])
   async def get_items(
       current_user: dict = Depends(get_current_active_user),
       db = Depends(get_database)
   ):
       items = await crud.get_user_items(db, current_user["id"])
       return [NewFeatureResponse(**item) for item in items]
   ```

4. **Register Router in main.py**
   ```python
   from app.routers import new_feature

   app.include_router(new_feature.router, prefix="/api/v1")
   ```

### Database Operations

#### Connection Management
```python
# app/database.py
from motor.motor_asyncio import AsyncIOMotorClient
import os

class Database:
    client: AsyncIOMotorClient = None
    database = None

db = Database()

async def connect_to_mongo():
    db.client = AsyncIOMotorClient(os.getenv("MONGODB_URI"))
    db.database = db.client[os.getenv("DATABASE_NAME")]

async def close_mongo_connection():
    if db.client:
        db.client.close()

async def get_database():
    return db.database
```

#### Common Patterns
```python
# Pagination
async def get_paginated_items(db, user_id: str, page: int = 1, page_size: int = 20):
    skip = (page - 1) * page_size
    cursor = db.collection.find({"user_id": user_id}).skip(skip).limit(page_size)
    items = await cursor.to_list(length=page_size)
    total_count = await db.collection.count_documents({"user_id": user_id})
    
    return {
        "items": items,
        "total_count": total_count,
        "page": page,
        "page_size": page_size,
        "total_pages": (total_count + page_size - 1) // page_size
    }

# Aggregation Pipeline
async def get_user_statistics(db, user_id: str):
    pipeline = [
        {"$match": {"user_id": user_id}},
        {"$group": {
            "_id": "$category",
            "count": {"$sum": 1},
            "total_value": {"$sum": "$estimated_value"}
        }},
        {"$sort": {"count": -1}}
    ]
    
    result = await db.collection.aggregate(pipeline).to_list(length=None)
    return result
```

### Authentication & Authorization

#### JWT Token Handling
```python
# app/utils/auth.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
import os

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(
            credentials.credentials,
            os.getenv("JWT_SECRET"),
            algorithms=[os.getenv("JWT_ALGORITHM", "HS256")]
        )
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return {"id": user_id, "email": payload.get("email")}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_active_user(current_user: dict = Depends(get_current_user)):
    # Add additional checks if needed (user active status, etc.)
    return current_user
```

---

## Frontend Development

### Project Structure

```
frontend/
├── src/
│   ├── components/             # React components
│   │   ├── ui/                # Shadcn/ui base components
│   │   ├── AuthForm.tsx       # Authentication forms
│   │   ├── Dashboard.tsx      # Main dashboard
│   │   ├── Pantry.tsx         # Pantry management
│   │   ├── Recipes.tsx        # Recipe management
│   │   ├── MealPlanner.tsx    # Meal planning
│   │   └── ...                # Other feature components
│   ├── contexts/              # React contexts
│   │   └── AuthContext.tsx    # Authentication context
│   ├── hooks/                 # Custom React hooks
│   ├── lib/                   # Utility libraries
│   │   ├── utils.ts           # General utilities
│   │   ├── api.ts             # API client
│   │   └── storage.ts         # Local storage utilities
│   ├── pages/                 # Page components
│   │   └── Index.tsx          # Main page
│   ├── services/              # API services
│   │   └── api.ts             # API service layer
│   ├── types/                 # TypeScript type definitions
│   │   └── index.ts           # Type definitions
│   ├── utils/                 # Utility functions
│   └── main.tsx               # Application entry point
├── public/                    # Static assets
├── tests/                     # Test files
├── package.json               # Dependencies and scripts
├── vite.config.ts            # Vite configuration
├── tailwind.config.ts        # Tailwind configuration
└── tsconfig.json             # TypeScript configuration
```

### Component Development

#### Component Structure
```typescript
// components/NewFeature.tsx
import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useAuth } from '@/contexts/AuthContext';
import { apiService } from '@/services/api';

interface NewFeatureProps {
  className?: string;
  onUpdate?: () => void;
}

interface FeatureItem {
  id: string;
  name: string;
  description?: string;
  created_at: string;
}

export const NewFeature: React.FC<NewFeatureProps> = ({ className, onUpdate }) => {
  const [items, setItems] = useState<FeatureItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { user } = useAuth();

  useEffect(() => {
    loadItems();
  }, []);

  const loadItems = async () => {
    try {
      setLoading(true);
      const response = await apiService.get('/new-feature/');
      setItems(response.data);
      setError(null);
    } catch (err) {
      setError('Failed to load items');
      console.error('Error loading items:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (data: { name: string; description?: string }) => {
    try {
      await apiService.post('/new-feature/', data);
      await loadItems();
      onUpdate?.();
    } catch (err) {
      setError('Failed to create item');
      console.error('Error creating item:', err);
    }
  };

  if (loading) {
    return <div className="flex justify-center p-4">Loading...</div>;
  }

  if (error) {
    return <div className="text-red-500 p-4">{error}</div>;
  }

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle>New Feature</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {items.map((item) => (
            <div key={item.id} className="border p-3 rounded">
              <h3 className="font-semibold">{item.name}</h3>
              {item.description && (
                <p className="text-gray-600 text-sm">{item.description}</p>
              )}
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
};
```

#### API Service Layer
```typescript
// services/api.ts
import axios, { AxiosInstance, AxiosResponse } from 'axios';

class ApiService {
  private api: AxiosInstance;

  constructor() {
    this.api = axios.create({
      baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor to add auth token
    this.api.interceptors.request.use((config) => {
      const token = localStorage.getItem('auth_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });

    // Response interceptor for error handling
    this.api.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          // Handle unauthorized - redirect to login
          localStorage.removeItem('auth_token');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  async get<T = any>(url: string, params?: any): Promise<AxiosResponse<T>> {
    return this.api.get(url, { params });
  }

  async post<T = any>(url: string, data?: any): Promise<AxiosResponse<T>> {
    return this.api.post(url, data);
  }

  async put<T = any>(url: string, data?: any): Promise<AxiosResponse<T>> {
    return this.api.put(url, data);
  }

  async delete<T = any>(url: string): Promise<AxiosResponse<T>> {
    return this.api.delete(url);
  }
}

export const apiService = new ApiService();
```

#### Custom Hooks
```typescript
// hooks/useApi.ts
import { useState, useEffect } from 'react';
import { apiService } from '@/services/api';

interface UseApiOptions {
  immediate?: boolean;
  onSuccess?: (data: any) => void;
  onError?: (error: any) => void;
}

export function useApi<T = any>(
  url: string,
  options: UseApiOptions = {}
) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const execute = async (params?: any) => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiService.get(url, params);
      setData(response.data);
      options.onSuccess?.(response.data);
      return response.data;
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'An error occurred';
      setError(errorMessage);
      options.onError?.(err);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (options.immediate !== false) {
      execute();
    }
  }, [url]);

  return { data, loading, error, execute, refetch: execute };
}
```

### State Management

#### Authentication Context
```typescript
// contexts/AuthContext.tsx
import React, { createContext, useContext, useState, useEffect } from 'react';
import { apiService } from '@/services/api';

interface User {
  id: string;
  email: string;
  full_name: string;
}

interface AuthContextType {
  user: User | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  loading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async () => {
    try {
      const token = localStorage.getItem('auth_token');
      if (token) {
        const response = await apiService.get('/auth/me');
        setUser(response.data);
      }
    } catch (error) {
      localStorage.removeItem('auth_token');
    } finally {
      setLoading(false);
    }
  };

  const login = async (email: string, password: string) => {
    const response = await apiService.post('/auth/login', { email, password });
    const { access_token, user: userData } = response.data;
    
    localStorage.setItem('auth_token', access_token);
    setUser(userData);
  };

  const logout = () => {
    localStorage.removeItem('auth_token');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
```

---

## Database Schema

### Collections Overview

#### Users Collection
```javascript
{
  _id: ObjectId,
  email: String (unique),
  password_hash: String,
  full_name: String,
  created_at: Date,
  updated_at: Date,
  is_active: Boolean
}

// Indexes
db.users.createIndex({ "email": 1 }, { unique: true })
db.users.createIndex({ "created_at": 1 })
```

#### Profiles Collection
```javascript
{
  _id: ObjectId,
  user_id: ObjectId (ref: users),
  dietary_restrictions: [String],
  allergies: [String],
  family_members: [{
    id: String,
    name: String,
    age: Number,
    dietary_restrictions: [String],
    allergies: [String]
  }],
  preferences: {
    cuisine_types: [String],
    cooking_skill: String,
    meal_prep_time: Number,
    budget_per_week: Number
  },
  created_at: Date,
  updated_at: Date
}

// Indexes
db.profiles.createIndex({ "user_id": 1 }, { unique: true })
```

#### Pantry Items Collection
```javascript
{
  _id: ObjectId,
  user_id: ObjectId (ref: users),
  name: String,
  category: String,
  quantity: Number,
  unit: String,
  expiration_date: Date,
  purchase_date: Date,
  location: String,
  notes: String,
  estimated_value: Number,
  created_at: Date,
  updated_at: Date
}

// Indexes
db.pantry_items.createIndex({ "user_id": 1, "category": 1 })
db.pantry_items.createIndex({ "user_id": 1, "expiration_date": 1 })
db.pantry_items.createIndex({ "user_id": 1, "created_at": -1 })
```

#### Recipes Collection
```javascript
{
  _id: ObjectId,
  user_id: ObjectId (ref: users),
  title: String,
  description: String,
  ingredients: [{
    name: String,
    quantity: Number,
    unit: String,
    notes: String
  }],
  instructions: [String],
  prep_time: Number,
  cook_time: Number,
  servings: Number,
  difficulty: String,
  tags: [String],
  meal_types: [String],
  dietary_restrictions: [String],
  nutrition_info: {
    calories_per_serving: Number,
    protein_g: Number,
    carbs_g: Number,
    fat_g: Number
  },
  photo_url: String,
  source_url: String,
  created_at: Date,
  updated_at: Date
}

// Indexes
db.recipes.createIndex({ "user_id": 1 })
db.recipes.createIndex({ "tags": 1 })
db.recipes.createIndex({ "difficulty": 1, "prep_time": 1 })
```

### Database Initialization

```python
# scripts/init_database.py
async def initialize_database():
    """Initialize database with required indexes and collections"""
    
    # Create indexes for users collection
    await db.users.create_index([("email", 1)], unique=True)
    await db.users.create_index([("created_at", 1)])
    
    # Create indexes for profiles collection
    await db.profiles.create_index([("user_id", 1)], unique=True)
    
    # Create indexes for pantry_items collection
    await db.pantry_items.create_index([("user_id", 1), ("category", 1)])
    await db.pantry_items.create_index([("user_id", 1), ("expiration_date", 1)])
    await db.pantry_items.create_index([("user_id", 1), ("created_at", -1)])
    
    # Create indexes for recipes collection
    await db.recipes.create_index([("user_id", 1)])
    await db.recipes.create_index([("tags", 1)])
    await db.recipes.create_index([("difficulty", 1), ("prep_time", 1)])
    
    print("Database initialization completed!")
```

---

## API Development

### RESTful API Design

#### Endpoint Naming Conventions
- Use nouns for resources: `/api/v1/recipes`
- Use HTTP methods for actions: GET, POST, PUT, DELETE
- Use plural nouns: `/recipes` not `/recipe`
- Use nested resources: `/recipes/{id}/ingredients`
- Use query parameters for filtering: `/recipes?difficulty=easy`

#### Response Format Standards
```python
# Success Response
{
  "data": {...},
  "message": "Success",
  "timestamp": "2024-01-16T12:00:00Z"
}

# Error Response
{
  "detail": "Error message",
  "error_code": "VALIDATION_ERROR",
  "timestamp": "2024-01-16T12:00:00Z",
  "path": "/api/v1/recipes",
  "request_id": "req_123456789"
}

# Paginated Response
{
  "items": [...],
  "total_count": 100,
  "page": 1,
  "page_size": 20,
  "total_pages": 5
}
```

#### Error Handling
```python
from fastapi import HTTPException, status

# Custom exception handler
@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={
            "detail": str(exc),
            "error_code": "VALIDATION_ERROR",
            "timestamp": datetime.utcnow().isoformat(),
            "path": str(request.url.path)
        }
    )

# Standard error responses
def not_found_error(resource: str):
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"{resource} not found"
    )

def validation_error(message: str):
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=message
    )
```

### API Versioning

```python
# Version 1 routes
app.include_router(auth.router, prefix="/api/v1")
app.include_router(pantry.router, prefix="/api/v1")

# Future version 2 routes
# app.include_router(auth_v2.router, prefix="/api/v2")
```

---

## Testing Guidelines

### Backend Testing

#### Unit Tests
```python
# tests/test_pantry.py
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_create_pantry_item():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Login to get token
        login_response = await ac.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "testpassword"
        })
        token = login_response.json()["access_token"]
        
        # Create pantry item
        response = await ac.post(
            "/api/v1/pantry/",
            json={
                "name": "Test Item",
                "category": "produce",
                "quantity": 1,
                "unit": "piece"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Item"
        assert data["category"] == "produce"

@pytest.mark.asyncio
async def test_get_pantry_items():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Test with authentication
        response = await ac.get(
            "/api/v1/pantry/",
            headers={"Authorization": f"Bearer {valid_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "pantry_items" in data
        assert "total_count" in data
```

#### Integration Tests
```python
# tests/test_integration.py
@pytest.mark.asyncio
async def test_meal_planning_workflow():
    """Test complete meal planning workflow"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # 1. Login
        login_response = await ac.post("/api/v1/auth/login", json=login_data)
        token =
 login_response.json()["access_token"]
        
        # 2. Add pantry items
        pantry_response = await ac.post(
            "/api/v1/pantry/",
            json={"name": "Chicken", "category": "meat", "quantity": 2, "unit": "lbs"},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert pantry_response.status_code == 201
        
        # 3. Generate meal plan
        meal_plan_response = await ac.post(
            "/api/v1/meal-plans/generate",
            json={
                "week_starting": "2024-01-15",
                "budget_target": 50.0,
                "use_pantry_items": True
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        assert meal_plan_response.status_code == 201
        
        # 4. Create shopping list from meal plan
        meal_plan_id = meal_plan_response.json()["meal_plan_id"]
        shopping_response = await ac.post(
            f"/api/v1/shopping-lists/from-meal-plan/{meal_plan_id}",
            json={"title": "Weekly Shopping"},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert shopping_response.status_code == 201
```

### Frontend Testing

#### Component Tests
```typescript
// components/__tests__/Pantry.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import { Pantry } from '../Pantry';
import { AuthProvider } from '@/contexts/AuthContext';
import * as apiService from '@/services/api';

// Mock API service
vi.mock('@/services/api');
const mockApiService = vi.mocked(apiService);

const renderWithAuth = (component: React.ReactElement) => {
  return render(
    <AuthProvider>
      {component}
    </AuthProvider>
  );
};

describe('Pantry Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders pantry items', async () => {
    const mockItems = [
      { id: '1', name: 'Chicken', category: 'meat', quantity: 2, unit: 'lbs' },
      { id: '2', name: 'Tomatoes', category: 'produce', quantity: 5, unit: 'pieces' }
    ];

    mockApiService.apiService.get.mockResolvedValue({
      data: { pantry_items: mockItems, total_count: 2 }
    });

    renderWithAuth(<Pantry />);

    await waitFor(() => {
      expect(screen.getByText('Chicken')).toBeInTheDocument();
      expect(screen.getByText('Tomatoes')).toBeInTheDocument();
    });
  });

  it('handles adding new item', async () => {
    mockApiService.apiService.get.mockResolvedValue({
      data: { pantry_items: [], total_count: 0 }
    });
    mockApiService.apiService.post.mockResolvedValue({
      data: { id: '1', name: 'New Item', category: 'produce' }
    });

    renderWithAuth(<Pantry />);

    const addButton = screen.getByText('Add Item');
    fireEvent.click(addButton);

    // Fill form and submit
    const nameInput = screen.getByLabelText('Item Name');
    fireEvent.change(nameInput, { target: { value: 'New Item' } });

    const submitButton = screen.getByText('Save');
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockApiService.apiService.post).toHaveBeenCalledWith(
        '/pantry/',
        expect.objectContaining({ name: 'New Item' })
      );
    });
  });
});
```

#### E2E Tests
```typescript
// tests/e2e/meal-planning.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Meal Planning Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Login
    await page.goto('/');
    await page.fill('[data-testid="email"]', 'test@example.com');
    await page.fill('[data-testid="password"]', 'testpassword');
    await page.click('[data-testid="login-button"]');
    await expect(page).toHaveURL('/dashboard');
  });

  test('should create meal plan', async ({ page }) => {
    // Navigate to meal planning
    await page.click('[data-testid="meal-plans-nav"]');
    await expect(page).toHaveURL('/meal-plans');

    // Create new meal plan
    await page.click('[data-testid="create-meal-plan"]');
    await page.fill('[data-testid="meal-plan-title"]', 'Test Week Plan');
    await page.fill('[data-testid="budget-target"]', '50');
    await page.click('[data-testid="generate-plan"]');

    // Wait for generation
    await expect(page.locator('[data-testid="meal-plan-generated"]')).toBeVisible();
    
    // Verify meal plan created
    await expect(page.locator('text=Test Week Plan')).toBeVisible();
  });

  test('should create shopping list from meal plan', async ({ page }) => {
    // Assume meal plan exists
    await page.goto('/meal-plans');
    await page.click('[data-testid="meal-plan-item"]:first-child');
    
    // Create shopping list
    await page.click('[data-testid="create-shopping-list"]');
    await expect(page.locator('[data-testid="shopping-list-items"]')).toBeVisible();
    
    // Verify items are present
    const itemCount = await page.locator('[data-testid="shopping-item"]').count();
    expect(itemCount).toBeGreaterThan(0);
  });
});
```

### Test Configuration

#### Pytest Configuration
```ini
# pytest.ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --tb=short
    --cov=app
    --cov-report=html
    --cov-report=term-missing
    --asyncio-mode=auto
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow tests
    security: Security tests
```

#### Vitest Configuration
```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react-swc';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    coverage: {
      reporter: ['text', 'html', 'lcov'],
      exclude: [
        'node_modules/',
        'src/test/',
        '**/*.d.ts',
        '**/*.config.*',
      ],
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
});
```

---

## Code Style & Standards

### Python Code Style

#### Formatting with Black
```python
# pyproject.toml
[tool.black]
line-length = 88
target-version = ['py311']
include = '\.pyi?$'
extend-exclude = '''
/(
  # directories
  \.eggs
  | \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | build
  | dist
)/
'''
```

#### Linting with Flake8
```ini
# .flake8
[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude = .git,__pycache__,docs/source/conf.py,old,build,dist
```

#### Import Sorting with isort
```ini
# .isort.cfg
[settings]
profile = black
multi_line_output = 3
line_length = 88
```

#### Type Hints
```python
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel

# Function signatures
async def get_user_items(
    db: AsyncIOMotorDatabase,
    user_id: str,
    category: Optional[str] = None,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """Get user's pantry items with optional filtering."""
    pass

# Class definitions
class PantryItemCreate(BaseModel):
    name: str
    category: str
    quantity: float
    unit: str
    expiration_date: Optional[datetime] = None
    notes: Optional[str] = None
```

### TypeScript Code Style

#### ESLint Configuration
```json
// eslint.config.js
export default [
  {
    files: ['**/*.{ts,tsx}'],
    languageOptions: {
      parser: '@typescript-eslint/parser',
      parserOptions: {
        ecmaVersion: 'latest',
        sourceType: 'module',
        ecmaFeatures: {
          jsx: true,
        },
      },
    },
    plugins: {
      '@typescript-eslint': typescriptEslint,
      'react': react,
      'react-hooks': reactHooks,
    },
    rules: {
      '@typescript-eslint/no-unused-vars': 'error',
      '@typescript-eslint/explicit-function-return-type': 'off',
      'react/prop-types': 'off',
      'react-hooks/rules-of-hooks': 'error',
      'react-hooks/exhaustive-deps': 'warn',
    },
  },
];
```

#### Prettier Configuration
```json
// .prettierrc
{
  "semi": true,
  "trailingComma": "es5",
  "singleQuote": true,
  "printWidth": 80,
  "tabWidth": 2,
  "useTabs": false
}
```

#### TypeScript Standards
```typescript
// Use interfaces for object shapes
interface User {
  id: string;
  email: string;
  full_name: string;
}

// Use types for unions and computed types
type Status = 'loading' | 'success' | 'error';
type UserKeys = keyof User;

// Use generics for reusable components
interface ApiResponse<T> {
  data: T;
  message: string;
  timestamp: string;
}

// Use proper error handling
const handleApiCall = async (): Promise<User | null> => {
  try {
    const response = await apiService.get<User>('/auth/me');
    return response.data;
  } catch (error) {
    console.error('Failed to fetch user:', error);
    return null;
  }
};
```

### Documentation Standards

#### Python Docstrings
```python
def create_meal_plan(
    user_id: str,
    preferences: Dict[str, Any],
    pantry_items: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Create a personalized meal plan for a user.
    
    Args:
        user_id: The unique identifier for the user
        preferences: User preferences including dietary restrictions,
                    budget, and cuisine preferences
        pantry_items: List of available pantry items to incorporate
        
    Returns:
        Dict containing the generated meal plan with meals, shopping list,
        and cost estimates
        
    Raises:
        ValueError: If user_id is invalid or preferences are malformed
        DatabaseError: If database operation fails
        
    Example:
        >>> preferences = {"budget": 50, "dietary_restrictions": ["vegetarian"]}
        >>> pantry = [{"name": "tomatoes", "quantity": 3}]
        >>> plan = create_meal_plan("user123", preferences, pantry)
        >>> print(plan["total_estimated_cost"])
        45.50
    """
    pass
```

#### TypeScript JSDoc
```typescript
/**
 * Custom hook for managing API calls with loading and error states
 * 
 * @template T - The expected response data type
 * @param url - The API endpoint URL
 * @param options - Configuration options for the API call
 * @returns Object containing data, loading state, error state, and execute function
 * 
 * @example
 * ```typescript
 * const { data, loading, error, execute } = useApi<User[]>('/users');
 * 
 * // Manual execution
 * const handleRefresh = () => execute();
 * ```
 */
export function useApi<T = any>(
  url: string,
  options: UseApiOptions = {}
): UseApiResult<T> {
  // Implementation
}
```

---

## Git Workflow

### Branch Strategy

```
main
├── develop
│   ├── feature/user-authentication
│   ├── feature/meal-planning
│   ├── feature/community-features
│   └── hotfix/critical-bug-fix
└── release/v1.0.0
```

#### Branch Types
- **main**: Production-ready code
- **develop**: Integration branch for features
- **feature/**: New features and enhancements
- **hotfix/**: Critical bug fixes
- **release/**: Release preparation

### Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

#### Types
- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Code style changes (formatting, etc.)
- **refactor**: Code refactoring
- **test**: Adding or updating tests
- **chore**: Maintenance tasks

#### Examples
```
feat(pantry): add receipt scanning functionality

- Implement OCR processing for receipt images
- Add automatic item categorization
- Include expiration date estimation

Closes #123
```

```
fix(auth): resolve JWT token expiration handling

- Fix token refresh logic
- Add proper error handling for expired tokens
- Update frontend to handle 401 responses

Fixes #456
```

### Pull Request Process

1. **Create Feature Branch**
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b feature/new-feature
   ```

2. **Development**
   - Write code following style guidelines
   - Add tests for new functionality
   - Update documentation as needed

3. **Pre-PR Checklist**
   - [ ] All tests pass
   - [ ] Code follows style guidelines
   - [ ] Documentation updated
   - [ ] No merge conflicts with develop

4. **Create Pull Request**
   - Use descriptive title and description
   - Link related issues
   - Add screenshots for UI changes
   - Request appropriate reviewers

5. **Code Review**
   - Address reviewer feedback
   - Update code as needed
   - Ensure CI/CD checks pass

6. **Merge**
   - Squash commits if needed
   - Delete feature branch after merge

### Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.1.0
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: ["--profile", "black"]

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8

  - repo: https://github.com/pre-commit/mirrors-prettier
    rev: v3.0.0-alpha.4
    hooks:
      - id: prettier
        files: \.(js|ts|tsx|json|css|md)$
```

---

## Deployment Process

### Environment Setup

#### Development
```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py

# Frontend
cd frontend
npm install
npm run dev
```

#### Production (Render)

**Backend Service Configuration**:
```yaml
# render.yaml
services:
  - type: web
    name: ezeatin-backend
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: python main.py
    envVars:
      - key: APP_ENV
        value: production
      - key: MONGODB_URI
        sync: false  # Set in Render dashboard
      - key: JWT_SECRET
        sync: false  # Set in Render dashboard
```

**Frontend Service Configuration**:
```yaml
  - type: web
    name: ezeatin-frontend
    env: static
    buildCommand: npm ci && npm run build
    staticPublishPath: ./dist
    envVars:
      - key: VITE_API_BASE_URL
        value: https://ezeatin-backend.onrender.com/api/v1
```

### CI/CD Pipeline

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          
      - name: Install backend dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          
      - name: Run backend tests
        run: |
          cd backend
          pytest
          
      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '18'
          
      - name: Install frontend dependencies
        run: |
          cd frontend
          npm ci
          
      - name: Run frontend tests
        run: |
          cd frontend
          npm run test:run

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - name: Deploy to Render
        uses: render-deploy/github-action@v1
        with:
          service-id: ${{ secrets.RENDER_SERVICE_ID }}
          api-key: ${{ secrets.RENDER_API_KEY }}
```

---

## Performance Guidelines

### Backend Performance

#### Database Optimization
```python
# Use indexes for frequent queries
await db.pantry_items.create_index([("user_id", 1), ("expiration_date", 1)])

# Use aggregation pipelines for complex queries
pipeline = [
    {"$match": {"user_id": user_id}},
    {"$group": {
        "_id": "$category",
        "count": {"$sum": 1},
        "total_value": {"$sum": "$estimated_value"}
    }},
    {"$sort": {"count": -1}}
]

# Use projection to limit returned fields
items = await db.pantry_items.find(
    {"user_id": user_id},
    {"name": 1, "category": 1, "quantity": 1}
).to_list(length=100)
```

#### Caching Strategy
```python
from functools import lru_cache
import asyncio

# In-memory caching for expensive operations
@lru_cache(maxsize=128)
def get_recipe_suggestions(ingredients_hash: str) -> List[Dict]:
    # Expensive computation
    pass

# Async caching
_cache = {}

async def get_cached_user_preferences(user_id: str) -> Dict:
    if user_id not in _cache:
        _cache[user_id] = await fetch_user_preferences(user_id)
    return _cache[user_id]
```

#### Response Optimization
```python
# Use response models to control serialization
class PantryItemSummary(BaseModel):
    id: str
    name: str
    category: str
    quantity: float
    # Exclude heavy fields like notes, created_at for list views

# Implement pagination
@router.get("/", response_model=PaginatedPantryResponse)
async def get_pantry_items(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_active_user)
):
    skip = (page - 1) * page_size
    items = await db.pantry_items.find({"user_id": current_user["id"]}) \
                                 .skip(skip) \
                                 .limit(page_size) \
                                 .to_list(length=page_size)
    return paginated_response(items, page, page_size)
```

### Frontend Performance

#### Code Splitting
```typescript
// Lazy load components
import { lazy, Suspense } from 'react';

const Dashboard = lazy(() => import('./components/Dashboard'));
const Pantry = lazy(() => import('./components/Pantry'));
const Recipes = lazy(() => import('./components/Recipes'));

// Use Suspense for loading states
function App() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <Routes>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/pantry" element={<Pantry />} />
        <Route path="/recipes" element={<Recipes />} />
      </Routes>
    </Suspense>
  );
}
```

#### Memoization
```typescript
import { memo, useMemo, useCallback } from 'react';

// Memoize expensive components
const PantryItem = memo(({ item, onUpdate }) => {
  return (
    <div className="pantry-item">
      <h3>{item.name}</h3>
      <p>{item.category}</p>
    </div>
  );
});

// Memoize expensive calculations
const PantryList = ({ items, filters }) => {
  const filteredItems = useMemo(() => {
    return items.filter(item => 
      filters.category ? item.category === filters.category : true
    );
  }, [items, filters.category]);

  const handleItemUpdate = useCallback((itemId, updates) => {
    // Handle update
  }, []);

  return (
    <div>
      {filteredItems.map(item => (
        <PantryItem 
          key={item.id} 
          item={item} 
          onUpdate={handleItemUpdate}
        />
      ))}
    </div>
  );
};
```

#### Bundle Optimization
```typescript
// vite.config.ts
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          ui: ['@radix-ui/react-dialog', '@radix-ui/react-dropdown-menu'],
          utils: ['date-fns', 'clsx', 'tailwind-merge']
        }
      }
    },
    chunkSizeWarningLimit: 1000
  }
});
```

---

## Security Considerations

### Authentication Security

```python
# Strong password hashing
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
```

### Input Validation

```python
# Pydantic validation
class PantryItemCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, regex=r'^[a-zA-Z0-9\s\-_]+$')
    quantity: float = Field(..., gt=0, le=10000)
    
    @validator('name')
    def validate_name(cls, v):
        # Additional validation
        if any(char in v for char in ['<', '>', '&', '"', "'"]):
            raise ValueError('Name contains invalid characters')
        return v.strip()
```

### SQL Injection Prevention

```python
# MongoDB query safety
from bson import ObjectId

async def get_user_item(user_id: str, item_id: str):
    # Validate ObjectId format
    if not ObjectId.is_valid(item_id):
        raise ValueError("Invalid item ID format")
    
    # Use parameterized queries
    item = await db.pantry_items.find_one({
        "_id": ObjectId(item_id),
        "user_id": user_id  # Ensure user owns the item
    })
    return item
```

### CORS Configuration

```python
from fastapi.middleware.cors import CORSMiddleware

# Restrictive CORS for production
if os.getenv("APP_ENV") == "production":
    allowed_origins = [
        "https://ezeatin-frontend.onrender.com",
        "https://app.ezeatin.com"
    ]
else:
    allowed_origins = [
        "http://localhost:3000",
        "http://localhost:5173"
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

### Rate Limiting

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/v1/auth/login")
@limiter.limit("5/minute")
async def login(request: Request, user_credentials: UserLogin):
    # Login implementation
    pass
```

---

## Troubleshooting

### Common Development Issues

#### Backend Issues

**MongoDB Connection Problems**:
```python
# Debug connection
import logging
logging.basicConfig(level=logging.DEBUG)

# Check connection string format
MONGODB_URI = "mongodb://localhost:27017/ez_eatin_dev"
# or for Atlas:
MONGODB_URI = "mongodb+srv://user:pass@cluster.mongodb.net/ez_eatin_dev"
```

**Import Errors**:
```python
# Ensure proper Python path
import sys
sys.path.append('/path/to/project/backend')

# Use relative imports within app
from .models import pantry
from ..utils import auth
```

**Async/Await Issues**:
```python
# Ensure all database operations are awaited
items = await db.pantry_items.find({"user_id": user_id}).to_list(length=None)

# Use async context managers
async with AsyncIOMotorClient(uri) as client:
    db = client.database_name
    result = await db.collection.find_one({"_id": item_id})
```

#### Frontend Issues

**API Connection Problems**:
```typescript
// Check environment variables
console.log('API Base URL:', import.meta.env.VITE_API_BASE_URL);

// Add request/response interceptors for debugging
axios.interceptors.request.use(request => {
  console.log('Starting Request:', request);
  return request;
});

axios.interceptors.response.use(
  response => {
    console.log('Response:', response);
    return response;
  },
  error => {
    console.log('Response Error:', error.response);
    return Promise.reject(error);
  }
);
```

**Build Issues**:
```bash
# Clear node modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Check for TypeScript errors
npm run type-check

# Verify environment variables
npm run build -- --mode development
```

### Performance Debugging

#### Backend Performance
```python
import time
import logging

# Add timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    if process_time > 1.0:  # Log slow requests
        logging.warning(f"Slow request: {request.url} took {process_time:.2f}s")
    
    return response

# Database query profiling
async def profile_query():
    start_time = time.time()
    result = await db.collection.find(query).to_list(length=None)
    end_time = time.time()
    print(f"Query took {end_time - start_time:.2f}s")
    return result
```

#### Frontend Performance
```typescript
// React DevTools Profiler
import { Profiler } from 'react';

function onRenderCallback(id, phase, actualDuration) {
  console.log('Component:', id, 'Phase:', phase, 'Duration:', actualDuration);
}

<Profiler id="PantryList" onRender={onRenderCallback}>
  <PantryList items={items} />
</Profiler>

// Performance monitoring
const observer = new PerformanceObserver((list) => {
  for (const entry of list.getEntries()) {
    console.log('Performance entry:', entry);
  }
});
observer.observe({ entryTypes: ['navigation', 'resource'] });
```

### Debugging Tools

#### Backend Debugging
```python
# Use pdb for debugging
import pdb; pdb.set_trace()

# Or use ipdb for better interface
import ipdb; ipdb.set_trace()

# Logging configuration
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@router.get("/debug")
async def debug_endpoint():
    logger.debug("Debug endpoint called")
    # Debug logic here
```

#### Frontend Debugging
```typescript
// React Developer Tools
// Install browser extension for component inspection

// Console debugging
console.log('State:', state);
console.table(items);
console.group('API Call');
console.log('Request:', request);
console.log('Response:', response);
console.groupEnd();

// Performance debugging
console.time('Component Render');
// Component logic
console.timeEnd('Component Render');
```

---

## Contributing Guidelines

### Getting Started

1. **Fork the Repository**
2. **Clone Your Fork**
   ```bash
   git clone https://github.com/yourusername/ez-eatin.git
   cd ez-eatin
   ```
3. **Set Up Development Environment** (see setup instructions above)
4. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

### Development Process

1. **Follow Code Standards**
   - Use provided linting and formatting tools
   - Write tests for new functionality
   - Update documentation as needed

2. **Test Your Changes**
   ```bash
   # Backend tests
   cd backend && pytest
   
   # Frontend tests
   cd frontend && npm run test
   
   # E2E tests
   cd frontend && npm run test:e2e
   ```

3. **Commit Changes**
   ```bash
   git add .
   git commit -m "feat(pantry): add receipt scanning functionality"
   ```

4. **Push and Create PR**
   ```bash
   git push origin feature/your-feature-name
   # Create pull request on GitHub
   ```

### Code Review Process

1. **Automated Checks**
   - All tests must pass
   - Code coverage requirements met
   - Linting and formatting checks pass

2. **Manual Review**
   - Code quality and maintainability
   - Security considerations
   - Performance implications
   - Documentation completeness

3. **Approval and Merge**
   - At least one approval required
   - Squash commits before merge
   - Delete feature branch after merge

### Issue Reporting

When reporting bugs or requesting features:

1. **Use Issue Templates**
2. **Provide Detailed Information**
   - Steps to reproduce
   - Expected vs
 actual behavior
   - Environment details (OS, browser, versions)
   - Screenshots or error messages

3. **Label Appropriately**
   - Bug, enhancement, documentation, etc.
   - Priority level (low, medium, high, critical)

### Community Guidelines

1. **Be Respectful**
   - Constructive feedback only
   - Help newcomers learn
   - Acknowledge contributions

2. **Stay On Topic**
   - Keep discussions relevant
   - Use appropriate channels
   - Search before posting

3. **Quality Standards**
   - Test your code thoroughly
   - Write clear documentation
   - Follow established patterns

---

## Resources and References

### Documentation Links
- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **React Documentation**: https://react.dev/
- **MongoDB Documentation**: https://docs.mongodb.com/
- **Pydantic Documentation**: https://docs.pydantic.dev/
- **Tailwind CSS**: https://tailwindcss.com/docs

### Development Tools
- **VS Code Extensions**:
  - Python
  - TypeScript and JavaScript
  - Tailwind CSS IntelliSense
  - MongoDB for VS Code
  - GitLens
  - Prettier
  - ESLint

### Testing Resources
- **Pytest Documentation**: https://docs.pytest.org/
- **Vitest Documentation**: https://vitest.dev/
- **Playwright Documentation**: https://playwright.dev/
- **Testing Library**: https://testing-library.com/

### Deployment Resources
- **Render Documentation**: https://render.com/docs
- **MongoDB Atlas**: https://docs.atlas.mongodb.com/
- **GitHub Actions**: https://docs.github.com/en/actions

---

## Changelog and Versioning

### Version History

#### v1.0.0 (Current)
- Initial release with core features
- User authentication and profiles
- Pantry management with receipt scanning
- Recipe management and meal planning
- Shopping list generation
- Community features
- Leftover suggestions

#### Upcoming Features (v1.1.0)
- Advanced meal planning algorithms
- Integration with grocery delivery services
- Mobile app development
- Enhanced community features
- Advanced analytics and insights

### Semantic Versioning

We follow [Semantic Versioning](https://semver.org/):
- **MAJOR**: Incompatible API changes
- **MINOR**: New functionality (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Process

1. **Feature Freeze**: Stop adding new features
2. **Testing Phase**: Comprehensive testing and bug fixes
3. **Documentation Update**: Update all documentation
4. **Release Candidate**: Deploy to staging for final testing
5. **Production Release**: Deploy to production
6. **Post-Release**: Monitor and address any issues

---

## Support and Contact

### Getting Help

1. **Documentation**: Check this guide and API documentation
2. **GitHub Issues**: Search existing issues or create new ones
3. **Community Forum**: Ask questions and share knowledge
4. **Email Support**: development@ezeatin.com

### Reporting Security Issues

For security vulnerabilities:
- **Email**: security@ezeatin.com
- **Do not** create public GitHub issues
- Include detailed reproduction steps
- We'll respond within 24 hours

### Contributing to Documentation

Documentation improvements are always welcome:
1. Fork the repository
2. Update documentation files
3. Test your changes locally
4. Submit a pull request

---

## Conclusion

This developer documentation provides a comprehensive guide for working with the EZ Eatin' codebase. As the project evolves, this documentation will be updated to reflect new features, best practices, and lessons learned.

### Key Takeaways

1. **Follow Standards**: Consistent code style and patterns make the codebase maintainable
2. **Test Thoroughly**: Comprehensive testing prevents bugs and regressions
3. **Document Changes**: Keep documentation up-to-date with code changes
4. **Security First**: Always consider security implications of changes
5. **Performance Matters**: Write efficient code and monitor performance
6. **Community Focus**: Collaborate effectively and help others learn

### Next Steps

1. Set up your development environment
2. Explore the codebase and run tests
3. Pick up a beginner-friendly issue
4. Join our community discussions
5. Start contributing!

---

**Happy coding!** 🚀

*This documentation is maintained by the EZ Eatin' development team. Last updated: January 2024*