from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum

class FeedbackTypeEnum(str, Enum):
    positive = "positive"
    negative = "negative"

class SectionTypeEnum(str, Enum):
    text = "text"
    image = "image"
    video = "video"

# Section Schemas
class PostSectionBase(BaseModel):
    section_type: SectionTypeEnum
    order_index: int = 0
    
    @validator('order_index')
    def validate_order_index(cls, v):
        if v < 0:
            raise ValueError('Order index must be non-negative')
        return v

class TextSectionCreate(PostSectionBase):
    section_type: SectionTypeEnum = SectionTypeEnum.text
    text_content: str
    
    @validator('text_content')
    def validate_text_content(cls, v):
        if not v or len(v.strip()) < 1:
            raise ValueError('Text content cannot be empty')
        if len(v) > 10000:
            raise ValueError('Text content must not exceed 10,000 characters')
        return v.strip()

class VideoSectionCreate(PostSectionBase):
    section_type: SectionTypeEnum = SectionTypeEnum.video
    video_url: Optional[str] = None
    
    @validator('video_url')
    def validate_video_url(cls, v):
        if v and len(v) > 500:
            raise ValueError('Video URL must not exceed 500 characters')
        return v

class PostSectionResponse(BaseModel):
    id: int
    section_type: SectionTypeEnum
    order_index: int
    text_content: Optional[str] = None
    image_url: Optional[str] = None
    image_filename: Optional[str] = None
    video_url: Optional[str] = None
    video_filename: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Post Schemas
class PostBase(BaseModel):
    header: str
    description: Optional[str] = None
    
    @validator('header')
    def validate_header(cls, v):
        if not v or len(v.strip()) < 3:
            raise ValueError('Header must be at least 3 characters long')
        if len(v) > 200:
            raise ValueError('Header must not exceed 200 characters')
        return v.strip()
    
    @validator('description')
    def validate_description(cls, v):
        if v is not None:
            if len(v.strip()) > 1000:
                raise ValueError('Description must not exceed 1000 characters')
            return v.strip()
        return v

class PostCreate(PostBase):
    """Schema for creating a post with sections"""
    sections: Optional[List[dict]] = []  # Will be handled separately via API

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
    description: Optional[str] = None
    sections: List[PostSectionResponse] = []
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
