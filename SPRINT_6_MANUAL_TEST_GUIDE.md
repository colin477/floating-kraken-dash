# Sprint 6 Manual Testing Guide
## Personal Execution Checklist for Community Features & Leftover Suggestions

**Important:** Complete each task fully before moving to the next. Mark each task as ✅ when completed.

---

## Prerequisites Setup

### Task 1: Environment Verification
**Objective:** Ensure your testing environment is ready

**Steps to Complete:**
1. [ ] Verify backend server is running on `http://localhost:8000`
2. [ ] Open browser and navigate to `http://localhost:8000/docs`
3. [ ] Confirm Swagger UI loads with all API endpoints visible
4. [ ] Check that you can see both "community" and "leftovers" endpoint groups
5. [ ] Verify database connection by visiting `http://localhost:8000/healthz`
6. [ ] Confirm response shows `"database_connected": true`

**Expected Result:** Server running, API docs accessible, database connected
**Mark Complete:** [ ] ✅ Task 1 Complete

---

### Task 2: Authentication Setup
**Objective:** Set up test user for authenticated requests

**Steps to Complete:**
1. [ ] In Swagger UI, find `POST /api/v1/auth/signup` endpoint
2. [ ] Click "Try it out"
3. [ ] Use this test data:
   ```json
   {
     "email": "sprint6test@example.com",
     "password": "testpassword123",
     "full_name": "Sprint 6 Tester"
   }
   ```
4. [ ] Click "Execute" and verify 201 Created response
5. [ ] Find `POST /api/v1/auth/login` endpoint
6. [ ] Login with the same credentials
7. [ ] Copy the `access_token` from the response
8. [ ] Click "Authorize" button at top of Swagger UI
9. [ ] Enter: `Bearer YOUR_ACCESS_TOKEN_HERE`
10. [ ] Click "Authorize" then "Close"

**Expected Result:** Successfully authenticated in Swagger UI
**Mark Complete:** [ ] ✅ Task 2 Complete

---

## Community Features Testing

### Task 3: Community Post Management
**Objective:** Test core post creation and retrieval

**Steps to Complete:**
1. [ ] Find `POST /api/v1/community/posts/` endpoint
2. [ ] Click "Try it out"
3. [ ] Use this test data:
   ```json
   {
     "title": "My First Sprint 6 Test Post",
     "content": "Testing community features manually for Sprint 6 validation",
     "post_type": "general",
     "tags": ["sprint6", "manual-test", "community"]
   }
   ```
4. [ ] Click "Execute" and verify 201 Created response
5. [ ] Copy the `id` from the response (you'll need this later)
6. [ ] Find `GET /api/v1/community/posts/` endpoint
7. [ ] Execute it and verify your post appears in the list
8. [ ] Find `GET /api/v1/community/posts/{id}` endpoint
9. [ ] Enter your post ID and execute
10. [ ] Verify you get the complete post details

**Expected Result:** Post created successfully and retrievable
**Mark Complete:** [ ] ✅ Task 3 Complete - Post ID: _______________

---

### Task 4: Comment System Testing
**Objective:** Test comment creation and nested replies

**Steps to Complete:**
1. [ ] Find `POST /api/v1/community/posts/{post_id}/comments/` endpoint
2. [ ] Enter your post ID from Task 3
3. [ ] Click "Try it out"
4. [ ] Use this test data:
   ```json
   {
     "content": "This is my first test comment on this post!"
   }
   ```
5. [ ] Execute and verify 201 Created response
6. [ ] Copy the comment `id` from the response
7. [ ] Find `GET /api/v1/community/posts/{post_id}/comments/` endpoint
8. [ ] Enter your post ID and execute
9. [ ] Verify your comment appears in the list
10. [ ] Find `POST /api/v1/community/comments/{comment_id}/replies/` endpoint
11. [ ] Enter your comment ID
12. [ ] Use this test data:
    ```json
    {
      "content": "This is a reply to my own comment!"
    }
    ```
13. [ ] Execute and verify 201 Created response
14. [ ] Find `GET /api/v1/community/comments/{comment_id}/replies/` endpoint
15. [ ] Enter your comment ID and verify the reply appears

**Expected Result:** Comments and replies working correctly
**Mark Complete:** [ ] ✅ Task 4 Complete - Comment ID: _______________

---

### Task 5: Like System Testing
**Objective:** Test like/unlike functionality

**Steps to Complete:**
1. [ ] Find `POST /api/v1/community/comments/{comment_id}/like` endpoint
2. [ ] Enter your comment ID from Task 4
3. [ ] Execute and verify 200 OK response
4. [ ] Find `GET /api/v1/community/comments/{comment_id}/likes` endpoint
5. [ ] Enter your comment ID and execute
6. [ ] Verify the response shows 1 like
7. [ ] Find `DELETE /api/v1/community/comments/{comment_id}/like` endpoint
8. [ ] Enter your comment ID and execute
9. [ ] Verify 200 OK response
10. [ ] Repeat step 5 and verify the like count is now 0

**Expected Result:** Like/unlike functionality working correctly
**Mark Complete:** [ ] ✅ Task 5 Complete

---

### Task 6: Community Statistics
**Objective:** Test community stats endpoint

**Steps to Complete:**
1. [ ] Find `GET /api/v1/community/stats/overview` endpoint
2. [ ] Execute the endpoint
3. [ ] Verify 200 OK response
4. [ ] Check that stats show at least 1 post and 1 comment
5. [ ] Note the exact numbers: Posts: _____ Comments: _____

**Expected Result:** Statistics accurately reflect your test data
**Mark Complete:** [ ] ✅ Task 6 Complete

---

## Leftover Suggestions Testing

### Task 7: Basic Leftover Suggestions
**Objective:** Test core leftover suggestion functionality

**Steps to Complete:**
1. [ ] Find `GET /api/v1/leftovers/suggestions` endpoint
2. [ ] Click "Try it out"
3. [ ] Execute with default parameters
4. [ ] Note the response structure (should be 200 OK)
5. [ ] Check the response fields:
   - [ ] `suggestions` array (may be empty)
   - [ ] `total_suggestions` number
   - [ ] `user_id` matches your user
   - [ ] `pantry_items_count` number
   - [ ] `recipes_analyzed` number
   - [ ] `generated_at` timestamp
   - [ ] `filters_applied` object
   - [ ] `performance_metrics` object
6. [ ] Record the values: Pantry Items: _____ Recipes Analyzed: _____

**Expected Result:** Endpoint responds with proper structure
**Mark Complete:** [ ] ✅ Task 7 Complete

---

### Task 8: Filtered Leftover Suggestions
**Objective:** Test suggestion filtering parameters

**Steps to Complete:**
1. [ ] Find `GET /api/v1/leftovers/suggestions` endpoint
2. [ ] Click "Try it out"
3. [ ] Set these parameters:
   - `max_suggestions`: 5
   - `min_match_percentage`: 0.5
   - `difficulty_level`: easy
   - `include_expiring`: true
   - `exclude_expired`: true
4. [ ] Execute and verify 200 OK response
5. [ ] Check that `filters_applied` in response matches your parameters
6. [ ] Verify `max_suggestions` is respected in the response

**Expected Result:** Filtering parameters properly applied
**Mark Complete:** [ ] ✅ Task 8 Complete

---

### Task 9: Custom Suggestion Filters
**Objective:** Test custom filter object endpoint

**Steps to Complete:**
1. [ ] Find `POST /api/v1/leftovers/suggestions/custom` endpoint
2. [ ] Click "Try it out"
3. [ ] Use this test data:
   ```json
   {
     "max_suggestions": 8,
     "min_match_percentage": 0.4,
     "max_prep_time": 30,
     "max_cook_time": 45,
     "difficulty_levels": ["easy", "medium"],
     "meal_types": ["dinner"],
     "dietary_restrictions": ["vegetarian"],
     "exclude_expired": true,
     "prioritize_expiring": true,
     "include_substitutes": true
   }
   ```
4. [ ] Execute and verify 200 OK response
5. [ ] Check that all your custom filters appear in `filters_applied`

**Expected Result:** Custom filters properly processed
**Mark Complete:** [ ] ✅ Task 9 Complete

---

### Task 10: Debug Information
**Objective:** Test debug endpoint for detailed information

**Steps to Complete:**
1. [ ] Find `GET /api/v1/leftovers/suggestions/debug` endpoint
2. [ ] Click "Try it out"
3. [ ] Set parameters:
   - `max_suggestions`: 3
   - `min_match_percentage`: 0.3
4. [ ] Execute and verify 200 OK response
5. [ ] Check for additional debug fields in response:
   - [ ] `debug_info` object present
   - [ ] Processing time information
   - [ ] Algorithm version information

**Expected Result:** Debug information provided
**Mark Complete:** [ ] ✅ Task 10 Complete

---

### Task 11: Available Ingredients
**Objective:** Test pantry ingredients endpoint

**Steps to Complete:**
1. [ ] Find `GET /api/v1/leftovers/ingredients` endpoint
2. [ ] Execute the endpoint
3. [ ] Note the response (may be 404 if no pantry items, or 200 with ingredient list)
4. [ ] If 200 OK, verify ingredient structure includes:
   - [ ] `name` field
   - [ ] `normalized_name` field
   - [ ] `category` field
   - [ ] `quantity` and `unit` fields
   - [ ] Expiration information

**Expected Result:** Endpoint responds appropriately based on pantry data
**Mark Complete:** [ ] ✅ Task 11 Complete

---

## Authentication & Security Testing

### Task 12: Unauthenticated Access Testing
**Objective:** Verify endpoints properly require authentication

**Steps to Complete:**
1. [ ] Click "Authorize" button in Swagger UI
2. [ ] Click "Logout" to clear your token
3. [ ] Try `POST /api/v1/community/posts/` without authentication
4. [ ] Verify you get 401 Unauthorized or 403 Forbidden
5. [ ] Try `GET /api/v1/leftovers/suggestions` without authentication
6. [ ] Verify you get 401 Unauthorized or 403 Forbidden
7. [ ] Re-authenticate using your token from Task 2

**Expected Result:** Protected endpoints reject unauthenticated requests
**Mark Complete:** [ ] ✅ Task 12 Complete

---

### Task 13: Invalid Token Testing
**Objective:** Test handling of invalid authentication tokens

**Steps to Complete:**
1. [ ] Click "Authorize" button in Swagger UI
2. [ ] Enter: `Bearer invalid-token-12345`
3. [ ] Click "Authorize" then "Close"
4. [ ] Try `POST /api/v1/community/posts/` with invalid token
5. [ ] Verify you get 401 Unauthorized
6. [ ] Re-authenticate with your valid token

**Expected Result:** Invalid tokens properly rejected
**Mark Complete:** [ ] ✅ Task 13 Complete

---

## Error Handling Testing

### Task 14: Invalid Data Testing
**Objective:** Test validation and error handling

**Steps to Complete:**
1. [ ] Find `POST /api/v1/community/posts/` endpoint
2. [ ] Try creating a post with empty title:
   ```json
   {
     "title": "",
     "content": "Test content",
     "post_type": "general"
   }
   ```
3. [ ] Verify you get 422 Unprocessable Entity
4. [ ] Try creating a comment with empty content:
   ```json
   {
     "content": ""
   }
   ```
5. [ ] Verify you get 422 Unprocessable Entity
6. [ ] Try accessing a non-existent post: `GET /api/v1/community/posts/507f1f77bcf86cd799439011`
7. [ ] Verify you get 404 Not Found

**Expected Result:** Proper validation errors and status codes
**Mark Complete:** [ ] ✅ Task 14 Complete

---

## Performance Testing

### Task 15: Response Time Testing
**Objective:** Verify acceptable performance

**Steps to Complete:**
1. [ ] Find `GET /api/v1/community/posts/` endpoint
2. [ ] Set parameters: `skip`: 0, `limit`: 50
3. [ ] Execute and note the response time (should be < 5 seconds)
4. [ ] Response time: _____ seconds
5. [ ] Execute `GET /api/v1/leftovers/suggestions` 3 times
6. [ ] Note response times: _____ , _____ , _____ seconds
7. [ ] All should be under 10 seconds

**Expected Result:** All responses within acceptable time limits
**Mark Complete:** [ ] ✅ Task 15 Complete

---

## Integration Testing

### Task 16: Cross-System Testing
**Objective:** Verify both systems work together without conflicts

**Steps to Complete:**
1. [ ] Create a new community post about leftovers:
   ```json
   {
     "title": "Great Leftover Recipe Ideas",
     "content": "I love using the leftover suggestions feature!",
     "post_type": "recipe_share",
     "tags": ["leftovers", "recipes", "suggestions"]
   }
   ```
2. [ ] Immediately after, get leftover suggestions
3. [ ] Then add a comment to your post
4. [ ] Then get leftover suggestions again
5. [ ] Verify all operations work without interference
6. [ ] Check that both community stats and leftover suggestions still work

**Expected Result:** No conflicts between systems
**Mark Complete:** [ ] ✅ Task 16 Complete

---

## Final Validation

### Task 17: End-to-End Workflow Test
**Objective:** Complete realistic user workflow

**Steps to Complete:**
1. [ ] Create a post asking for recipe suggestions
2. [ ] Add a comment to your own post
3. [ ] Like your comment
4. [ ] Get leftover suggestions with custom filters
5. [ ] Create another post sharing a "recipe" you "found"
6. [ ] Check community stats to see updated numbers
7. [ ] Get debug information from leftover suggestions
8. [ ] Unlike your comment
9. [ ] Verify all operations completed successfully

**Expected Result:** Complete workflow executes without errors
**Mark Complete:** [ ] ✅ Task 17 Complete

---

## Test Results Summary

### Task 18: Document Your Results
**Objective:** Record your testing outcomes

**Complete this summary:**

**Community Features Results:**
- [ ] Post creation: ✅ Working / ❌ Issues: ________________
- [ ] Comment system: ✅ Working / ❌ Issues: ________________
- [ ] Like system: ✅ Working / ❌ Issues: ________________
- [ ] Statistics: ✅ Working / ❌ Issues: ________________

**Leftover Suggestions Results:**
- [ ] Basic suggestions: ✅ Working / ❌ Issues: ________________
- [ ] Filtered suggestions: ✅ Working / ❌ Issues: ________________
- [ ] Custom filters: ✅ Working / ❌ Issues: ________________
- [ ] Debug info: ✅ Working / ❌ Issues: ________________

**Authentication & Security:**
- [ ] Authentication required: ✅ Working / ❌ Issues: ________________
- [ ] Invalid token handling: ✅ Working / ❌ Issues: ________________

**Error Handling:**
- [ ] Validation errors: ✅ Working / ❌ Issues: ________________
- [ ] Not found errors: ✅ Working / ❌ Issues: ________________

**Performance:**
- [ ] Response times acceptable: ✅ Yes / ❌ No: ________________

**Integration:**
- [ ] Systems work together: ✅ Yes / ❌ No: ________________

**Overall Assessment:**
- [ ] ✅ Sprint 6 Ready for Production
- [ ] ⚠️ Sprint 6 Ready with Minor Issues
- [ ] ❌ Sprint 6 Needs Fixes Before Production

**Issues Found:** ________________________________________________

**Mark Complete:** [ ] ✅ Task 18 Complete

---

## Completion Checklist

Mark each major section when fully completed:

- [ ] ✅ Prerequisites Setup (Tasks 1-2)
- [ ] ✅ Community Features Testing (Tasks 3-6)
- [ ] ✅ Leftover Suggestions Testing (Tasks 7-11)
- [ ] ✅ Authentication & Security Testing (Tasks 12-13)
- [ ] ✅ Error Handling Testing (Task 14)
- [ ] ✅ Performance Testing (Task 15)
- [ ] ✅ Integration Testing (Task 16)
- [ ] ✅ Final Validation (Tasks 17-18)

**FINAL RESULT:** [ ] ✅ Sprint 6 Manual Testing Complete

---

**Notes:**
- Complete each task fully before moving to the next
- Record any issues or unexpected behavior immediately
- If any task fails, note the details and continue with remaining tests
- This comprehensive test should take 45-60 minutes to complete thoroughly