# Comprehensive Manual Testing Guide for EZ Eatin' Backend
## Sprint S0 (Environment Setup) & Sprint S1 (Basic Authentication)

This guide provides step-by-step instructions to manually verify that your backend infrastructure and authentication system are fully functional and production-ready.

## Prerequisites

- Backend server running on `http://localhost:8000` (currently active)
- MongoDB Atlas database connected
- Web browser with developer tools
- Optional: API testing tool like Postman, Insomnia, or curl command line tool

---

## 🏗️ Sprint S0 Testing: Environment Setup

### Test 1: Server Health Check with Database

**Objective**: Verify the server is running and connected to MongoDB Atlas.

#### Browser Test:
1. Open your web browser
2. Navigate to: `http://localhost:8000/healthz`
3. **Expected Response**:
   ```json
   {
     "status": "healthy",
     "message": "API is running and database is connected",
     "database_connected": true,
     "timestamp": "2025-01-XX..."
   }
   ```
4. **Success Criteria**: 
   - Status code: `200 OK`
   - `status` field shows `"healthy"`
   - `database_connected` shows `true`
   - Response includes current timestamp

#### curl Test (if available):
```bash
curl -X GET http://localhost:8000/healthz
```

**Troubleshooting**:
- If `database_connected: false`, check MongoDB Atlas connection string in `.env` file
- If server doesn't respond, verify uvicorn is running on port 8000

---

### Test 2: Root Endpoint

**Objective**: Verify basic API functionality.

#### Browser Test:
1. Navigate to: `http://localhost:8000/`
2. **Expected Response**:
   ```json
   {
     "message": "EZ Eatin' API is running",
     "version": "1.0.0"
   }
   ```
3. **Success Criteria**: Status code `200 OK` with correct message

---

### Test 3: API Documentation Access

**Objective**: Verify FastAPI's automatic documentation is accessible.

#### Browser Test:
1. Navigate to: `http://localhost:8000/docs`
2. **Expected Result**: Interactive Swagger UI documentation loads
3. **Success Criteria**:
   - Page loads without errors
   - Shows "EZ Eatin' API" title
   - Lists all available endpoints organized by tags
   - Authentication endpoints are visible under "authentication" tag

#### Alternative Documentation:
1. Navigate to: `http://localhost:8000/redoc`
2. **Expected Result**: ReDoc documentation interface loads

---

### Test 4: CORS Configuration

**Objective**: Verify Cross-Origin Resource Sharing is properly configured.

#### Browser Developer Tools Test:
1. Open browser developer tools (F12)
2. Go to Console tab
3. Navigate to `http://localhost:8000/docs`
4. Execute this JavaScript in the console:
   ```javascript
   fetch('http://localhost:8000/healthz', {
     method: 'GET',
     headers: {
       'Content-Type': 'application/json',
     }
   })
   .then(response => response.json())
   .then(data => console.log('CORS test successful:', data))
   .catch(error => console.error('CORS test failed:', error));
   ```
5. **Success Criteria**: No CORS errors in console, successful response logged

---

### Test 5: Error Handling

**Objective**: Verify proper error responses for invalid endpoints.

#### Browser Test:
1. Navigate to: `http://localhost:8000/nonexistent-endpoint`
2. **Expected Response**:
   ```json
   {
     "detail": "Not Found"
   }
   ```
3. **Success Criteria**: Status code `404 Not Found`

---

## 🔐 Sprint S1 Testing: Basic Authentication

### Test 6: User Registration (Signup)

**Objective**: Verify user registration with validation works correctly.

#### Using FastAPI Docs (Recommended):
1. Navigate to `http://localhost:8000/docs`
2. Find the `POST /api/v1/auth/signup` endpoint
3. Click "Try it out"
4. Use this test payload:
   ```json
   {
     "email": "test@example.com",
     "password": "testpassword123",
     "full_name": "Test User"
   }
   ```
5. Click "Execute"
6. **Expected Response** (Status `201 Created`):
   ```json
   {
     "id": "507f1f77bcf86cd799439011",
     "email": "test@example.com",
     "full_name": "Test User",
     "created_at": "2025-01-XX...",
     "updated_at": "2025-01-XX...",
     "is_active": true
   }
   ```

#### Using curl:
```bash
curl -X POST "http://localhost:8000/api/v1/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpassword123",
    "full_name": "Test User"
  }'
```

**Success Criteria**:
- Status code: `201 Created`
- Response includes user ID, email, full_name, timestamps
- Password is NOT included in response
- `is_active` is `true`

---

### Test 7: Registration Validation

**Objective**: Verify input validation works correctly.

#### Test Invalid Email:
1. In FastAPI docs, try signup with:
   ```json
   {
     "email": "invalid-email",
     "password": "testpassword123",
     "full_name": "Test User"
   }
   ```
2. **Expected**: Status `422 Unprocessable Entity` with validation error

#### Test Short Password:
1. Try signup with:
   ```json
   {
     "email": "test2@example.com",
     "password": "short",
     "full_name": "Test User"
   }
   ```
2. **Expected**: Status `422 Unprocessable Entity` with password length error

#### Test Duplicate Email:
1. Try to register the same email again:
   ```json
   {
     "email": "test@example.com",
     "password": "anotherpassword123",
     "full_name": "Another User"
   }
   ```
2. **Expected**: Status `400 Bad Request` with "Email already registered" message

---

### Test 8: User Login

**Objective**: Verify user authentication and JWT token generation.

#### Using FastAPI Docs:
1. Navigate to `POST /api/v1/auth/login`
2. Click "Try it out"
3. Use credentials from Test 6:
   ```json
   {
     "email": "test@example.com",
     "password": "testpassword123"
   }
   ```
4. Click "Execute"
5. **Expected Response** (Status `200 OK`):
   ```json
   {
     "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
     "token_type": "bearer",
     "expires_in": 86400,
     "user": {
       "id": "507f1f77bcf86cd799439011",
       "email": "test@example.com",
       "full_name": "Test User",
       "created_at": "2025-01-XX...",
       "updated_at": "2025-01-XX...",
       "is_active": true
     }
   }
   ```

**Success Criteria**:
- Status code: `200 OK`
- Response includes `access_token` (JWT string)
- `token_type` is "bearer"
- `expires_in` shows token lifetime in seconds (86400 = 24 hours)
- User information is included

**⚠️ Important**: Copy the `access_token` value for the next tests!

---

### Test 9: Invalid Login Attempts

**Objective**: Verify proper handling of authentication failures.

#### Test Wrong Password:
1. Try login with:
   ```json
   {
     "email": "test@example.com",
     "password": "wrongpassword"
   }
   ```
2. **Expected**: Status `401 Unauthorized` with "Incorrect email or password"

#### Test Non-existent User:
1. Try login with:
   ```json
   {
     "email": "nonexistent@example.com",
     "password": "anypassword"
   }
   ```
2. **Expected**: Status `401 Unauthorized` with "Incorrect email or password"

---

### Test 10: Protected Route Access

**Objective**: Verify JWT token authentication for protected endpoints.

#### Using FastAPI Docs:
1. Navigate to `GET /api/v1/auth/me`
2. Click "Try it out"
3. **First, test without authentication**:
   - Click "Execute" without adding authorization
   - **Expected**: Status `401 Unauthorized`

4. **Now test with authentication**:
   - Click the "Authorize" button at the top of the docs page
   - In the "HTTPBearer" field, enter: `Bearer YOUR_ACCESS_TOKEN_FROM_TEST_8`
   - Click "Authorize" then "Close"
   - Try the `/api/v1/auth/me` endpoint again
   - **Expected Response** (Status `200 OK`):
     ```json
     {
       "id": "507f1f77bcf86cd799439011",
       "email": "test@example.com",
       "full_name": "Test User",
       "created_at": "2025-01-XX...",
       "updated_at": "2025-01-XX...",
       "is_active": true
     }
     ```

#### Using curl:
```bash
# Without token (should fail)
curl -X GET "http://localhost:8000/api/v1/auth/me"

# With token (should succeed)
curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE"
```

---

### Test 11: Invalid Token Handling

**Objective**: Verify proper handling of invalid or malformed tokens.

#### Test Invalid Token:
1. In FastAPI docs, authorize with: `Bearer invalid-token-string`
2. Try accessing `/api/v1/auth/me`
3. **Expected**: Status `401 Unauthorized` with "Could not validate credentials"

#### Test Malformed Authorization Header:
Using curl:
```bash
# Missing "Bearer" prefix
curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: just-the-token"
```
**Expected**: Status `401 Unauthorized`

---

### Test 12: User Logout

**Objective**: Verify logout functionality.

#### Using FastAPI Docs:
1. Ensure you're still authorized from Test 10
2. Navigate to `POST /api/v1/auth/logout`
3. Click "Try it out" and "Execute"
4. **Expected Response** (Status `200 OK`):
   ```json
   {
     "message": "Successfully logged out",
     "data": {
       "user_id": "507f1f77bcf86cd799439011"
     }
   }
   ```

**Success Criteria**:
- Status code: `200 OK`
- Success message returned
- User ID included in response data

---

### Test 13: Password Security Verification

**Objective**: Verify passwords are properly hashed and secured.

#### Database Check (MongoDB Atlas):
1. Connect to your MongoDB Atlas cluster via MongoDB Compass or web interface
2. Navigate to the `ez_eatin` database
3. Query the `users` collection to find your test user
4. **Success Criteria**:
   - `password_hash` field exists (not `password`)
   - Hash starts with `$argon2id$` (Argon2 algorithm)
   - Original password is not visible anywhere

#### API Response Check:
1. Review all previous API responses
2. **Success Criteria**: No API response should ever contain plain text passwords or password hashes

---

### Test 14: Token Expiration Testing

**Objective**: Verify JWT token expiration is properly configured.

#### Check Token Payload:
1. Copy your JWT token from Test 8
2. Go to https://jwt.io/
3. Paste your token in the "Encoded" section
4. **Verify in the payload**:
   - `exp` field shows expiration timestamp
   - `sub` field contains user ID
   - `email` field contains user email

#### Manual Expiration Test (Optional):
1. Wait for token to expire (24 hours by default) OR
2. Modify `JWT_EXPIRES_IN` in `.env` to a shorter time (e.g., 60 seconds) and restart server
3. Try accessing protected route after expiration
4. **Expected**: Status `401 Unauthorized`

---

## 🔍 Advanced Testing with Browser Developer Tools

### Network Tab Analysis

1. Open browser developer tools (F12)
2. Go to Network tab
3. Perform login test (Test 8)
4. **Verify**:
   - Request shows `POST /api/v1/auth/login`
   - Request headers include `Content-Type: application/json`
   - Response headers include appropriate CORS headers
   - Response time is reasonable (< 2 seconds)

### Security Headers Check

1. In Network tab, examine response headers for any endpoint
2. **Look for**:
   - CORS headers (`Access-Control-Allow-Origin`, etc.)
   - No sensitive information in headers
   - Proper `Content-Type` headers

---

## 📋 Success Checklist

Mark each item as complete after successful testing:

### Sprint S0 - Environment Setup:
- [ ] Health check endpoint responds correctly with database connected
- [ ] Root endpoint returns proper message
- [ ] API documentation is accessible at `/docs` and `/redoc`
- [ ] CORS is properly configured (no browser errors)
- [ ] 404 errors are handled gracefully
- [ ] Database connectivity is confirmed

### Sprint S1 - Authentication:
- [ ] User registration works with valid data
- [ ] Input validation prevents invalid registrations
- [ ] Duplicate email registration is properly rejected
- [ ] User login generates valid JWT tokens
- [ ] Invalid login attempts are properly rejected
- [ ] Protected routes require authentication
- [ ] Valid JWT tokens grant access to protected routes
- [ ] Invalid/malformed tokens are properly rejected
- [ ] Logout endpoint functions correctly
- [ ] Passwords are securely hashed with Argon2
- [ ] JWT tokens contain proper payload and expiration
- [ ] No sensitive data is exposed in API responses

---

## 🚨 Common Issues & Troubleshooting

### Database Connection Issues:
- **Symptom**: `database_connected: false` in health check
- **Solution**: Check MongoDB Atlas connection string in `.env` file
- **Check**: Ensure IP address is whitelisted in MongoDB Atlas

### CORS Errors:
- **Symptom**: Browser console shows CORS policy errors
- **Solution**: Verify frontend URL is in CORS origins list in `.env`

### JWT Token Issues:
- **Symptom**: `401 Unauthorized` with valid token
- **Solution**: Check token format includes "Bearer " prefix
- **Check**: Verify token hasn't expired

### Validation Errors:
- **Symptom**: `422 Unprocessable Entity` responses
- **Solution**: Verify request payload matches expected schema
- **Check**: Email format, password length (min 8 chars), full_name not empty

### Server Not Responding:
- **Symptom**: Connection refused errors
- **Solution**: Confirm uvicorn server is running on port 8000
- **Check**: Look for server restart after `.env` changes

### MongoDB Atlas Issues:
- **Symptom**: Database connection timeouts
- **Solution**: Check network connectivity and Atlas cluster status
- **Check**: Verify database user permissions

---

## 🎯 Final Verification

After completing all tests successfully, you should be confident that:

1. **Infrastructure is solid**: Server runs reliably with proper error handling
2. **Database integration works**: MongoDB Atlas connection is stable and functional  
3. **Authentication is secure**: Passwords are hashed with Argon2, JWT tokens work correctly
4. **API is well-documented**: Interactive documentation is accessible and functional
5. **CORS is configured**: Frontend integration will work smoothly
6. **Error handling is robust**: Invalid requests are handled gracefully
7. **Security is implemented**: Protected routes require proper authentication
8. **Token management works**: JWT creation, validation, and expiration function correctly
9. **Input validation works**: Malformed requests are properly rejected
10. **Database operations work**: User creation, authentication, and retrieval function correctly

Your backend is now ready for Sprint S2 development! 🚀

---

## 📝 Test Results Template

Use this template to record your test results:

```
## Test Results - [Date]

### Sprint S0 - Environment Setup
- [ ] Test 1: Health Check - Status: _____ Notes: _____
- [ ] Test 2: Root Endpoint - Status: _____ Notes: _____
- [ ] Test 3: API Docs - Status: _____ Notes: _____
- [ ] Test 4: CORS - Status: _____ Notes: _____
- [ ] Test 5: Error Handling - Status: _____ Notes: _____

### Sprint S1 - Authentication  
- [ ] Test 6: User Registration - Status: _____ Notes: _____
- [ ] Test 7: Registration Validation - Status: _____ Notes: _____
- [ ] Test 8: User Login - Status: _____ Notes: _____
- [ ] Test 9: Invalid Login - Status: _____ Notes: _____
- [ ] Test 10: Protected Routes - Status: _____ Notes: _____
- [ ] Test 11: Invalid Tokens - Status: _____ Notes: _____
- [ ] Test 12: User Logout - Status: _____ Notes: _____
- [ ] Test 13: Password Security - Status: _____ Notes: _____
- [ ] Test 14: Token Expiration - Status: _____ Notes: _____

### Overall Assessment
- Sprint S0 Status: [PASS/FAIL]
- Sprint S1 Status: [PASS/FAIL]
- Ready for Sprint S2: [YES/NO]
- Notes: _____