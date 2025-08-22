from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from db.database import get_db
from crud.user import UserCRUD
from schemas.user import Token, UserResponse, UserTypeEnum, UserLogin
from auth.jwt_utils import create_access_token, get_user_from_token, ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter(prefix="/auth", tags=["authentication"])

# HTTP Bearer scheme for Swagger UI - simpler token input
security = HTTPBearer(scheme_name="Bearer Token")

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Get current user data from JWT token only"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    user_data = get_user_from_token(credentials.credentials)
    if user_data is None:
        raise credentials_exception
    
    return user_data

def get_current_active_user(current_user: dict = Depends(get_current_user)) -> dict:
    """Get current active user"""
    if not current_user.get("is_active", True):
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def get_current_admin_user(current_user: dict = Depends(get_current_active_user)) -> dict:
    """Get current admin user - requires admin role"""
    if current_user.get("user_type") != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

def require_admin_or_self(user_id: int, current_user: dict = Depends(get_current_active_user)) -> dict:
    """Require admin role or accessing own data"""
    if current_user.get("user_type") != "ADMIN" and current_user.get("user_id") != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required or can only access own data"
        )
    return current_user

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Login endpoint - returns JWT token"""
    user_crud = UserCRUD(db)
    user = user_crud.authenticate_user(form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": user.username, 
            "user_id": user.id,
            "user_type": user.user_type.value,
            "is_active": user.is_active
        }, 
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/test-token")
def test_token_authentication(current_user: dict = Depends(get_current_active_user)):
    """
    Test endpoint to verify JWT token authentication is working
    
    Use this endpoint to test if your token is valid after clicking the Authorize button.
    """
    return {
        "message": "Token authentication successful!",
        "user_info": {
            "username": current_user.get("username"),
            "user_id": current_user.get("user_id"),
            "user_type": current_user.get("user_type"),
            "is_active": current_user.get("is_active")
        },
        "instructions": "Your token is working correctly. You can now access protected endpoints."
    }

@router.get("/me")
def read_users_me(current_user: dict = Depends(get_current_active_user)):
    """Get current user information from JWT token"""
    # Return user info directly from token (no database lookup needed)
    return {
        "message": "Current user information",
        "user": {
            "username": current_user.get("username"),
            "user_id": current_user.get("user_id"),
            "user_type": current_user.get("user_type"),
            "is_active": current_user.get("is_active")
        }
    }

@router.post("/refresh", response_model=Token)
def refresh_token(current_user: dict = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """Refresh JWT token with fresh user data"""
    # Get fresh user data from database for token refresh
    user_crud = UserCRUD(db)
    user = user_crud.get_by_username(current_user["username"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": user.username, 
            "user_id": user.id,
            "user_type": user.user_type.value,
            "is_active": user.is_active
        }, 
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}
