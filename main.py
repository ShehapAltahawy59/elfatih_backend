from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer

from db.database import engine, Base
from api.users import router as users_router
from api.auth import router as auth_router
from api.admin import router as admin_router

# Create database tables
Base.metadata.create_all(bind=engine)

# Create FastAPI app with OAuth2 security scheme for Swagger
app = FastAPI(
    title="Elfatih Backend API",
    description="""
    A FastAPI application with JWT authentication and role-based access control.
    
    ## 🔐 Authentication Steps
    1. **Login**: Use `POST /api/v1/auth/login` with your credentials
    2. **Copy Token**: Copy the `access_token` from the response
    3. **Authorize**: Click the 🔒 **Authorize** button and paste your token (no "Bearer" prefix needed)
    4. **Test**: All protected endpoints will now work!
    
    ## 👥 Test Accounts
    - **Admin**: username=`admin`, password=`admin123` (Full access)
    - **User**: username=`testuser`, password=`user123` (Limited access)
    
    ## 🎯 User Roles
    - **USER**: Regular user with limited access
    - **ADMIN**: Full access to all endpoints including admin panel
    """,
    version="1.0.0",
    # Add security scheme for Swagger UI
    openapi_tags=[
        {
            "name": "authentication",
            "description": "Authentication endpoints - login, token refresh, user profile"
        },
        {
            "name": "users", 
            "description": "User management endpoints - CRUD operations"
        },
        {
            "name": "admin",
            "description": "Admin panel endpoints - requires admin role"
        }
    ]
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
from api.posts import router as posts_router

app.include_router(auth_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")
app.include_router(posts_router, prefix="/api/v1")

@app.get("/", tags=["root"])
def read_root():
    """
    Welcome endpoint with API information
    """
    return {
        "message": "Welcome to Elfatih Backend API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "authentication": {
            "login_endpoint": "/api/v1/auth/login",
            "how_to_authenticate": "1. Login to get token, 2. Click Authorize button, 3. Enter 'Bearer your_token'"
        }
    }

@app.get("/health", tags=["root"])
def health_check():
    """
    Health check endpoint
    """
    return {"status": "healthy", "message": "API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
