from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from db.database import get_db
from crud.user import UserCRUD
from schemas.user import UserResponse, AdminUserUpdate, UserTypeEnum, UserCreate
from api.auth import get_current_admin_user

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/users")
def admin_get_all_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin_user)
):
    """Admin only: Get all users including inactive ones"""
    try:
        user_crud = UserCRUD(db)
        users = user_crud.get_all(skip=skip, limit=limit)
        
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
            "limit": limit
        }
        
    except Exception as e:
        return {
            "error": "Failed to get users",
            "details": str(e),
            "debug": "Exception in GET /admin/users"
        }

@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def admin_create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin_user)
):
    """Admin only: Create a user with any role (including admin)"""
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
    
    # Admin can create users with any role (including admin)
    return user_crud.create(user_data)

@router.put("/users/{user_id}", response_model=UserResponse)
def admin_update_user(
    user_id: int,
    user_data: AdminUserUpdate,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin_user)
):
    """Admin only: Update any user including user_type"""
    user_crud = UserCRUD(db)
    user = user_crud.update(user_id, user_data)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

@router.post("/users/{user_id}/make-admin", response_model=UserResponse)
def make_user_admin(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin_user)
):
    """Admin only: Make a user an admin"""
    user_crud = UserCRUD(db)
    
    # Create update data to make user admin
    admin_update = AdminUserUpdate(user_type=UserTypeEnum.ADMIN)
    user = user_crud.update(user_id, admin_update)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

@router.post("/users/{user_id}/remove-admin", response_model=UserResponse)
def remove_user_admin(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin_user)
):
    """Admin only: Remove admin privileges from a user"""
    user_crud = UserCRUD(db)
    
    # Prevent removing admin from self
    if user_id == current_admin.get("user_id"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove admin privileges from yourself"
        )
    
    # Create update data to make user regular user
    user_update = AdminUserUpdate(user_type=UserTypeEnum.USER)
    user = user_crud.update(user_id, user_update)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

@router.post("/users/{user_id}/activate", response_model=UserResponse)
def activate_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin_user)
):
    """Admin only: Activate a user"""
    user_crud = UserCRUD(db)
    user_update = AdminUserUpdate(is_active=True)
    user = user_crud.update(user_id, user_update)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

@router.post("/users/{user_id}/deactivate", response_model=UserResponse)
def deactivate_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin_user)
):
    """Admin only: Deactivate a user"""
    user_crud = UserCRUD(db)
    
    # Prevent deactivating self
    if user_id == current_admin.get("user_id"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate yourself"
        )
    
    user_update = AdminUserUpdate(is_active=False)
    user = user_crud.update(user_id, user_update)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

@router.get("/stats")
def admin_get_stats(
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin_user)
):
    """Admin only: Get user statistics"""
    user_crud = UserCRUD(db)
    
    total_users = len(user_crud.get_all())
    active_users = len(user_crud.get_active_users())
    inactive_users = total_users - active_users
    
    # Count admins
    all_users = user_crud.get_all()
    admin_users = len([u for u in all_users if u.user_type.value == "ADMIN"])
    regular_users = total_users - admin_users
    
    return {
        "total_users": total_users,
        "active_users": active_users,
        "inactive_users": inactive_users,
        "admin_users": admin_users,
        "regular_users": regular_users
    }
