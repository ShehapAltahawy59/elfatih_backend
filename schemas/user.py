from pydantic import BaseModel, EmailStr, validator
from datetime import datetime
from typing import Optional
from enum import Enum
import re

class UserTypeEnum(str, Enum):
    USER = "USER"
    ADMIN = "ADMIN"

class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: str
    phone: Optional[str] = None
    user_type: UserTypeEnum = UserTypeEnum.USER
    is_active: bool = True
    
    @validator('username')
    def validate_username(cls, v):
        if not v or len(v.strip()) < 3:
            raise ValueError('Username must be at least 3 characters long')
        if len(v) > 50:
            raise ValueError('Username must not exceed 50 characters')
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Username can only contain letters, numbers, and underscores')
        return v.strip()
    
    @validator('full_name')
    def validate_full_name(cls, v):
        if not v or len(v.strip()) < 2:
            raise ValueError('Full name must be at least 2 characters long')
        if len(v) > 100:
            raise ValueError('Full name must not exceed 100 characters')
        return v.strip()
    
    @validator('phone')
    def validate_phone(cls, v):
        if v is None:
            return v
        # Remove all non-digit characters except +
        phone_clean = re.sub(r'[^\d+]', '', v)
        
        # Check if it's a valid phone number format
        if not re.match(r'^\+?[1-9]\d{7,14}$', phone_clean):
            raise ValueError('Phone number must be 8-15 digits, optionally starting with +')
        
        return phone_clean

class UserCreate(UserBase):
    password: str
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')
        if len(v) > 100:
            raise ValueError('Password must not exceed 100 characters')
        return v

# Public registration schema - no user_type field
class UserRegister(BaseModel):
    model_config = {"extra": "forbid"}  # Reject any extra fields
    username: str
    email: EmailStr
    full_name: str
    phone: Optional[str] = None
    password: str
    
    @validator('username')
    def validate_username(cls, v):
        if not v or len(v.strip()) < 3:
            raise ValueError('Username must be at least 3 characters long')
        if len(v) > 50:
            raise ValueError('Username must not exceed 50 characters')
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Username can only contain letters, numbers, and underscores')
        return v.strip()
    
    @validator('full_name')
    def validate_full_name(cls, v):
        if not v or len(v.strip()) < 2:
            raise ValueError('Full name must be at least 2 characters long')
        if len(v) > 100:
            raise ValueError('Full name must not exceed 100 characters')
        return v.strip()
    
    @validator('phone')
    def validate_phone(cls, v):
        if v is None:
            return v
        # Remove all non-digit characters except +
        phone_clean = re.sub(r'[^\d+]', '', v)
        
        # Check if it's a valid phone number format
        if not re.match(r'^\+?[1-9]\d{7,14}$', phone_clean):
            raise ValueError('Phone number must be 8-15 digits, optionally starting with +')
        
        return phone_clean
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')
        if len(v) > 100:
            raise ValueError('Password must not exceed 100 characters')
        return v

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None
    password: Optional[str] = None
    user_type: Optional[UserTypeEnum] = None
    is_active: Optional[bool] = None
    
    @validator('username')
    def validate_username(cls, v):
        if v is None:
            return v
        if len(v.strip()) < 3:
            raise ValueError('Username must be at least 3 characters long')
        if len(v) > 50:
            raise ValueError('Username must not exceed 50 characters')
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Username can only contain letters, numbers, and underscores')
        return v.strip()
    
    @validator('full_name')
    def validate_full_name(cls, v):
        if v is None:
            return v
        if len(v.strip()) < 2:
            raise ValueError('Full name must be at least 2 characters long')
        if len(v) > 100:
            raise ValueError('Full name must not exceed 100 characters')
        return v.strip()
    
    @validator('phone')
    def validate_phone(cls, v):
        if v is None:
            return v
        # Remove all non-digit characters except +
        phone_clean = re.sub(r'[^\d+]', '', v)
        
        # Check if it's a valid phone number format
        if not re.match(r'^\+?[1-9]\d{7,14}$', phone_clean):
            raise ValueError('Phone number must be 8-15 digits, optionally starting with +')
        
        return phone_clean
    
    @validator('password')
    def validate_password(cls, v):
        if v is None:
            return v
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')
        if len(v) > 100:
            raise ValueError('Password must not exceed 100 characters')
        return v

class UserResponse(UserBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Authentication schemas
class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# Admin-specific schemas
class AdminUserUpdate(BaseModel):
    """Admin can update user_type and other sensitive fields"""
    username: Optional[str] = None
    email: Optional[str] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None
    password: Optional[str] = None
    user_type: Optional[UserTypeEnum] = None
    is_active: Optional[bool] = None
