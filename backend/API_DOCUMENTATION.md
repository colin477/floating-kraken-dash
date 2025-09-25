# EZ Eatin' API Documentation

## Community API Endpoints

### Create a new post
- **Endpoint**: `POST /api/v1/community/posts/`
- **Authentication**: Required
- **Request Body**:
  ```json
  {
    "title": "My Favorite Recipe",
    "content": "This is a great recipe for...",
    "tags": ["recipe", "dinner"]
  }
  ```
- **Response**:
  ```json
  {
    "id": "post_id",
    "title": "My Favorite Recipe",
    "content": "This is a great recipe for...",
    "author_id": "user_id",
    "created_at": "2025-09-24T23:26:28.131Z",
    "likes": 0,
    "comments": []
  }
  ```

### Get all posts
- **Endpoint**: `GET /api/v1/community/posts/`
- **Authentication**: Not Required
- **Response**: A list of post objects.

### Get a single post
- **Endpoint**: `GET /api/v1/community/posts/{post_id}`
- **Authentication**: Not Required
- **Response**: A single post object.

### Update a post
- **Endpoint**: `PUT /api/v1/community/posts/{post_id}`
- **Authentication**: Required (must be post author)
- **Request Body**:
  ```json
  {
    "title": "My Updated Favorite Recipe",
    "content": "This is an updated recipe..."
  }
  ```
- **Response**: The updated post object.

### Delete a post
- **Endpoint**: `DELETE /api/v1/community/posts/{post_id}`
- **Authentication**: Required (must be post author)
- **Response**: `204 No Content`

### Like a post
- **Endpoint**: `POST /api/v1/community/posts/{post_id}/like`
- **Authentication**: Required
- **Response**: The updated post object with the new like count.

### Add a comment to a post
- **Endpoint**: `POST /api/v1/community/posts/{post_id}/comments/`
- **Authentication**: Required
- **Request Body**:
  ```json
  {
    "content": "This is a great comment!"
  }
  ```- **Response**: The newly created comment object.

### Update a comment
- **Endpoint**: `PUT /api/v1/community/comments/{comment_id}`
- **Authentication**: Required (must be comment author)
- **Request Body**:
  ```json
  {
    "content": "This is an updated comment."
  }
  ```
- **Response**: The updated comment object.

### Delete a comment
- **Endpoint**: `DELETE /api/v1/community/comments/{comment_id}`
- **Authentication**: Required (must be comment author)
- **Response**: `204 No Content`

### Like a comment
- **Endpoint**: `POST /api/v1/community/comments/{comment_id}/like`
- **Authentication**: Required
- **Response**: The updated comment object with the new like count.

## Leftover Suggestions API Endpoints

### Get recipe suggestions for leftovers
- **Endpoint**: `POST /api/v1/leftovers/suggestions`
- **Authentication**: Required
- **Request Body**:
  ```json
  {
    "ingredients": ["chicken", "rice", "carrots"]
  }
  ```
- **Response**: A list of recipe suggestion objects, ranked by a matching score.