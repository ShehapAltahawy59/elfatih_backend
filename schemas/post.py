from pydantic import BaseModel, validator
from typing import Optional
from datetime import datetime
from enum import Enum

class FeedbackTypeEnum(str, Enum):
    positive = "positive"
    negative = "negative"

class PostBase(BaseModel):
    header: str
    description: str
    
    @validator('header')
    def validate_header(cls, v):
        if not v or len(v.strip()) < 3:
            raise ValueError('Header must be at least 3 characters long')
        if len(v) > 200:
            raise ValueError('Header must not exceed 200 characters')
        return v.strip()
    
    @validator('description')
    def validate_description(cls, v):
        if not v or len(v.strip()) < 10:
            raise ValueError('Description must be at least 10 characters long')
        if len(v) > 5000:
            raise ValueError('Description must not exceed 5000 characters')
        return v.strip()

class PostCreate(PostBase):
    """Schema for creating a post (without image, image handled separately)"""
    pass

class PostUpdate(BaseModel):
    header: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    
    @validator('header')
    def validate_header(cls, v):
        if v is not None:
            if len(v.strip()) < 3:
                raise ValueError('Header must be at least 3 characters long')
            if len(v) > 200:
                raise ValueError('Header must not exceed 200 characters')
            return v.strip()
        return v
    
    @validator('description')
    def validate_description(cls, v):
        if v is not None:
            if len(v.strip()) < 10:
                raise ValueError('Description must be at least 10 characters long')
            if len(v) > 5000:
                raise ValueError('Description must not exceed 5000 characters')
            return v.strip()
        return v

class PostResponse(BaseModel):
    id: int
    header: str
    description: str
    image_url: Optional[str] = None  # This will contain the image URL endpoint or None
    image_filename: Optional[str] = None
    positive_feedbacks: int
    negative_feedbacks: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class PostWithImage(PostResponse):
    """Extended response that includes base64 image data"""
    image_data: Optional[str] = None  # Base64 encoded image
    image_info: Optional[dict] = None  # Image metadata

class FeedbackCreate(BaseModel):
    feedback_type: FeedbackTypeEnum

class FeedbackResponse(BaseModel):
    id: int
    post_id: int
    user_id: int
    feedback_type: FeedbackTypeEnum
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class PostWithUserFeedback(PostResponse):
    user_feedback: Optional[FeedbackTypeEnum] = None
    
    class Config:
        from_attributes = True
