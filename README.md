# Elfatih Backend - FastAPI Application

A comprehensive FastAPI backend application with flexible posts system, user management, and JWT authentication.

## Project Structure

```
elfatih_backend/
├── api/                    # API route handlers
│   ├── __init__.py
│   ├── auth.py            # Authentication endpoints
│   ├── users.py           # User management endpoints
│   ├── posts.py           # Posts and sections endpoints
│   └── admin.py           # Admin-only endpoints
├── auth/                  # Authentication utilities
│   ├── __init__.py
│   └── jwt_utils.py       # JWT token handling
├── crud/                  # CRUD operations
│   ├── __init__.py
│   ├── user.py           # User CRUD operations
│   └── post.py           # Posts and sections CRUD
├── db/                    # Database configuration
│   ├── __init__.py
│   └── database.py       # Database setup and connection
├── models/                # SQLAlchemy models
│   ├── __init__.py
│   ├── user.py           # User model with roles
│   └── post.py           # Posts, sections, and feedback models
├── schemas/               # Pydantic schemas
│   ├── __init__.py
│   ├── user.py           # User validation schemas
│   └── post.py           # Post and section schemas
├── utils/                 # Utility functions
│   ├── __init__.py
│   └── image_utils.py    # Image processing utilities
├── config.py             # Configuration settings
├── main.py               # FastAPI application entry point
├── run_server.py         # Server startup script
└── requirements.txt      # Python dependencies
```

## Database Configuration

The application connects to MySQL using the following connection string:
```
mysql+mysqlconnector://elfatih_user:123456@173.212.251.191:3306/elfatih_backend
```

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

### Option 1: Using main.py
```bash
python main.py
```

### Option 2: Using run_server.py
```bash
python run_server.py
```

### Option 3: Using uvicorn directly
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The application will be available at:
- API: http://localhost:8000
- Interactive API docs: http://localhost:8000/docs
- Alternative docs: http://localhost:8000/redoc

## 🔑 Default Credentials

### Admin Account
- **Username**: `admin`
- **Password**: `admin123`
- **Role**: ADMIN (full access to all endpoints)

### Test User Account
- **Username**: `testuser`
- **Password**: `user123`
- **Role**: USER (limited access)

## API Endpoints

### 🔐 Authentication
- `POST /api/v1/auth/login` - User login (get JWT token)
- `GET /api/v1/auth/me` - Get current user profile
- `POST /api/v1/auth/refresh` - Refresh JWT token
- `GET /api/v1/auth/test-token` - Test token validity

### 👥 Users
- `POST /api/v1/users/` - Create a new user (public registration)
- `GET /api/v1/users/` - Get all users (admin only)
- `GET /api/v1/users/{user_id}` - Get user by ID
- `GET /api/v1/users/me` - Get current user profile
- `PUT /api/v1/users/me` - Update current user profile
- `DELETE /api/v1/users/me` - Delete current user account
- `GET /api/v1/users/phone/{phone}` - Get user by phone number

### 📝 Posts System
#### Public Endpoints
- `GET /api/v1/posts/` - Get all active posts
- `GET /api/v1/posts/{id}` - Get specific post with sections
- `GET /api/v1/posts/{id}/image` - Get main post image
- `GET /api/v1/posts/sections/{id}/image` - Get section image
- `GET /api/v1/posts/with-feedback` - Get posts with user feedback status (auth required)

#### User Feedback
- `POST /api/v1/posts/{id}/feedback` - Add/update feedback (auth required)
- `DELETE /api/v1/posts/{id}/feedback` - Remove feedback (auth required)
- `GET /api/v1/posts/{id}/feedback/check` - Check if user gave feedback (auth required)

#### Admin Only - Post Management
- `POST /api/v1/posts/complete` - **Create complete post with sections** ⭐
- `POST /api/v1/posts/` - Create basic post
- `PUT /api/v1/posts/{id}` - Update post
- `DELETE /api/v1/posts/{id}` - Delete post
- `PUT /api/v1/posts/{id}/image` - Update main post image
- `DELETE /api/v1/posts/{id}/image` - Remove main post image

#### Admin Only - Section Management
- `POST /api/v1/posts/{id}/sections/text` - Add text section
- `POST /api/v1/posts/{id}/sections/image` - Add image section
- `POST /api/v1/posts/{id}/sections/video` - Add video section
- `PUT /api/v1/posts/sections/{id}/order` - Update section order
- `DELETE /api/v1/posts/sections/{id}` - Delete section

### 🔧 Admin Panel
- `GET /api/v1/admin/users` - Get all users (admin only)
- `POST /api/v1/admin/users` - Create user (admin only)
- `PUT /api/v1/admin/users/{id}` - Update any user (admin only)
- `POST /api/v1/admin/users/{id}/make-admin` - Promote to admin
- `POST /api/v1/admin/users/{id}/remove-admin` - Remove admin role
- `POST /api/v1/admin/users/{id}/activate` - Activate user
- `POST /api/v1/admin/users/{id}/deactivate` - Deactivate user
- `GET /api/v1/admin/stats` - Get system statistics

### 🏠 System
- `GET /` - Root endpoint with API information
- `GET /health` - Health check endpoint

## 🎯 Posts System - Complete Post Creation

### Overview
The posts system supports flexible content creation with multiple section types. Each post can have:
- **Main Post Image**: Featured/cover image for the post
- **Multiple Sections**: Text, image, and video sections in any order
- **User Feedback**: Positive/negative feedback system (one per user per post)

### 🚀 Using the Complete Post Endpoint

The **`POST /api/v1/posts/complete`** endpoint allows creating a full post with all sections in one request.

#### 📋 Swagger UI Usage (Recommended)

1. **Get Admin Token**:
   - Go to http://localhost:8000/docs
   - Use `/auth/login` with admin credentials
   - Copy the `access_token`

2. **Authorize**:
   - Click "Authorize" button in Swagger UI
   - Paste the token (without "Bearer" prefix)

3. **Use Complete Post Endpoint**:
   - Find `POST /api/v1/posts/complete`
   - Click "Try it out"
   - Fill the form:

**Form Fields:**
```
header: "My Amazing Article"
description: "Brief description of the article"
main_image: [Upload cover image file]
sections: [Paste JSON below]
images: [Upload content image files]
```

**Sections JSON Format:**
```json
[
  {
    "type": "text",
    "order_index": 0,
    "content": "This is the introduction paragraph of our article."
  },
  {
    "type": "image",
    "order_index": 1,
    "content": "photo1.jpg"
  },
  {
    "type": "text",
    "order_index": 2,
    "content": "After the image, here's more detailed content."
  },
  {
    "type": "video",
    "order_index": 3,
    "content": "https://www.youtube.com/watch?v=abc123"
  },
  {
    "type": "image",
    "order_index": 4,
    "content": "photo2.jpg"
  },
  {
    "type": "text",
    "order_index": 5,
    "content": "Finally, here's the conclusion paragraph."
  }
]
```

**Important Notes:**
- For image sections, the `content` field must match uploaded filenames exactly
- Upload all referenced images in the `images` field
- The `main_image` is separate from section images

#### 📊 Response Structure
```json
{
  "message": "Complete post created successfully",
  "post": {
    "id": 1,
    "header": "My Amazing Article",
    "description": "Brief description of the article",
    "image_url": "/api/v1/posts/1/image",
    "image_filename": "cover.jpg",
    "sections": [
      {
        "id": 1,
        "section_type": "text",
        "order_index": 0,
        "text_content": "This is the introduction paragraph..."
      },
      {
        "id": 2,
        "section_type": "image",
        "order_index": 1,
        "image_url": "/api/v1/posts/sections/2/image",
        "image_filename": "photo1.jpg"
      },
      {
        "id": 3,
        "section_type": "video",
        "order_index": 3,
        "video_url": "https://www.youtube.com/watch?v=abc123"
      }
    ],
    "positive_feedbacks": 0,
    "negative_feedbacks": 0,
    "is_active": true
  },
  "sections_created": 6
}
```

### 🎨 Section Types

#### 1. Text Sections
```json
{
  "type": "text",
  "order_index": 0,
  "content": "Your text content here..."
}
```

#### 2. Image Sections
```json
{
  "type": "image",
  "order_index": 1,
  "content": "filename.jpg"
}
```
- Must upload the image file in the `images` field
- `content` must match the uploaded filename exactly

#### 3. Video Sections
```json
{
  "type": "video",
  "order_index": 2,
  "content": "https://youtube.com/watch?v=abc123"
}
```
- Supports YouTube, Vimeo, or any video URL

### 💾 Image Storage
- **Main Post Images**: Stored in `posts.image_data` (LONGBLOB)
- **Section Images**: Stored in `post_sections.image_data` (LONGBLOB)
- **Processing**: Auto-resized (max 1200x800px), optimized JPEG
- **Size Limit**: 5MB per image
- **Formats**: JPEG, PNG, GIF, WebP

### 👍 Feedback System
- Users can give positive or negative feedback
- One feedback per user per post (database constraint)
- Real-time counter updates
- Users can change or remove their feedback

## Features

- **FastAPI Framework**: Modern, fast web framework for building APIs
- **MySQL Integration**: Using SQLAlchemy ORM with MySQL connector
- **JWT Authentication**: Secure token-based authentication
- **Role-Based Access**: USER and ADMIN roles with proper permissions
- **Flexible Posts System**: Rich content with text, images, and videos
- **Image Processing**: Automatic resize and optimization
- **Database Storage**: Images stored as BLOB data in database
- **User Feedback**: Positive/negative feedback system
- **CRUD Operations**: Complete Create, Read, Update, Delete operations
- **Data Validation**: Comprehensive Pydantic schemas with validators
- **Auto Documentation**: Swagger UI and ReDoc integration
- **CORS Support**: Cross-Origin Resource Sharing enabled

## 🔧 Troubleshooting

### Common Issues

#### 1. Complete Post Creation Errors
**Error**: `Image file 'photo1.jpg' not found in uploaded images`
- **Solution**: Ensure the filename in sections JSON exactly matches uploaded file names
- **Check**: File extensions are case-sensitive (`.jpg` vs `.JPG`)

**Error**: `401 Unauthorized`
- **Solution**: Get a fresh admin token from `/auth/login`
- **Check**: Token is pasted correctly in Swagger UI (without "Bearer" prefix)

**Error**: `Invalid sections JSON`
- **Solution**: Validate JSON format using a JSON validator
- **Check**: All quotes are double quotes, no trailing commas

#### 2. Image Display Issues
**Error**: Images not loading from URLs
- **Solution**: Check if database tables are created with LONGBLOB columns
- **Check**: Run the database migration scripts

#### 3. Database Connection Issues
**Error**: `Can't connect to MySQL server`
- **Solution**: Verify database credentials in `config.py`
- **Check**: Database server is accessible from your network

#### 4. Authentication Issues
**Error**: `Invalid credentials`
- **Solution**: Use default credentials: `admin` / `admin123`
- **Check**: User exists in database (run user creation scripts)

### Quick Tests

#### Test Server Status
```bash
curl http://localhost:8000/
```

#### Test Authentication
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"
```

#### Test Posts Endpoint
```bash
curl http://localhost:8000/api/v1/posts/
```

### Database Setup

If you need to recreate the database tables, run these SQL scripts:
1. `add_post_sections.sql` - Creates post_sections table
2. `add_main_image_to_posts.sql` - Adds image fields to posts table

## Development

The project is structured following FastAPI best practices:
- Separation of concerns with dedicated folders for different components
- Dependency injection for database sessions and CRUD operations
- Proper error handling with HTTP status codes
- Type hints throughout the codebase
- JWT-based authentication with role-based access control
- Comprehensive data validation with Pydantic schemas
- Database storage for images (BLOB data)
- RESTful API design principles
