from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from db.database import get_db
from crud.user import UserCRUD
from schemas.user import UserCreate, UserUpdate, UserResponse, UserTypeEnum, UserRegister
from api.auth import get_current_active_user, get_current_admin_user, require_admin_or_self

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    user_data: UserRegister,
    db: Session = Depends(get_db)
):
    """Public user registration - creates regular user only (no user_type field needed)"""
    user_crud = UserCRUD(db)
    
    # Check if username already exists
    existing_user = user_crud.get_by_username(user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email already exists
    existing_email = user_crud.get_by_email(user_data.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if phone already exists (if phone is provided)
    if user_data.phone:
        existing_phone = user_crud.get_by_phone(user_data.phone)
        if existing_phone:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone number already registered"
            )
    
    # Convert UserRegister to UserCreate with default USER type
    user_create_data = UserCreate(
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        phone=user_data.phone,
        password=user_data.password,
        user_type=UserTypeEnum.USER,  # Always USER for public registration
        is_active=True
    )
    
    return user_crud.create(user_create_data)

# /me endpoints - MUST come before /{user_id} routes to avoid conflicts
@router.get("/me")
def get_my_profile(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Get your own profile using token only (no ID needed)"""
    try:
        user_crud = UserCRUD(db)
        user = user_crud.get_by_id(current_user.get("user_id"))
        if not user:
            return {
                "error": "User not found",
                "user_id": current_user.get("user_id"),
                "debug": "User exists in token but not in database"
            }
        
        # Return user data manually to avoid serialization issues
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "phone": user.phone,
            "user_type": user.user_type.value if user.user_type else None,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None
        }
    except Exception as e:
        return {
            "error": "Internal server error",
            "details": str(e),
            "user_id": current_user.get("user_id"),
            "debug": "Exception occurred in /users/me endpoint"
        }

@router.put("/me", response_model=UserResponse)
def update_my_profile(
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Update your own profile using token only (no ID needed)"""
    # Regular users cannot change their own user_type
    if current_user.get("user_type") != "ADMIN" and user_data.user_type is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot change your own user type"
        )
    
    user_crud = UserCRUD(db)
    user = user_crud.update(current_user.get("user_id"), user_data)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_my_account(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Delete your own account using token only (no ID needed)"""
    # Prevent admins from deleting themselves (optional safety check)
    if current_user.get("user_type") == "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admins cannot delete their own account. Use admin panel or contact another admin."
        )
    
    user_crud = UserCRUD(db)
    success = user_crud.delete(current_user.get("user_id"))
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

# Regular endpoints with parameters
@router.get("/{user_id}")
def get_user(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Get user by ID"""
    try:
        user_crud = UserCRUD(db)
        user = user_crud.get_by_id(user_id)
        if not user:
            return {
                "error": "User not found",
                "user_id": user_id
            }
        
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "phone": user.phone,
            "user_type": user.user_type.value if user.user_type else None,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None
        }
    except Exception as e:
        return {
            "error": "Failed to get user",
            "details": str(e),
            "user_id": user_id
        }

@router.get("/phone/{phone}", response_model=UserResponse)
def get_user_by_phone(
    phone: str,
    db: Session = Depends(get_db)
):
    """Get user by phone number"""
    user_crud = UserCRUD(db)
    user = user_crud.get_by_phone(phone)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

@router.get("/")
def get_users(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Get all users with pagination - regular users only see active users"""
    try:
        user_crud = UserCRUD(db)
        
        # Regular users can only see active users, admins can see all
        if current_user.get("user_type") == "ADMIN" and not active_only:
            users = user_crud.get_all(skip=skip, limit=limit)
        else:
            users = user_crud.get_active_users(skip=skip, limit=limit)
        
        # Convert users to dict to avoid serialization issues
        users_data = []
        for user in users:
            users_data.append({
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "phone": user.phone,
                "user_type": user.user_type.value if user.user_type else None,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "updated_at": user.updated_at.isoformat() if user.updated_at else None
            })
        
        return {
            "users": users_data,
            "count": len(users_data),
            "skip": skip,
            "limit": limit,
            "active_only": active_only
        }
        
    except Exception as e:
        return {
            "error": "Failed to get users",
            "details": str(e),
            "debug": "Exception in GET /users/"
        }

@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Update user - admins can update anyone, users can only update themselves"""
    # Check if user can update this record
    if current_user.get("user_type") != "ADMIN" and current_user.get("user_id") != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only update your own profile or admin access required"
        )
    
    # Regular users cannot change user_type
    if current_user.get("user_type") != "ADMIN" and user_data.user_type is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can change user type"
        )
    
    user_crud = UserCRUD(db)
    user = user_crud.update(user_id, user_data)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin_user)
):
    """Delete user"""
    user_crud = UserCRUD(db)
    success = user_crud.delete(user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return None
