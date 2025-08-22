from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum, LargeBinary
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.database import Base
import enum

class FeedbackType(enum.Enum):
    positive = "positive"
    negative = "negative"

class SectionType(enum.Enum):
    text = "text"
    image = "image"
    video = "video"

class Post(Base):
    __tablename__ = "posts"
    
    id = Column(Integer, primary_key=True, index=True)
    header = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)  # Optional post description
    
    # Main post image (featured/cover image)
    image_data = Column(LargeBinary, nullable=True)  # Main post image as binary data
    image_filename = Column(String(255), nullable=True)  # Original filename
    image_content_type = Column(String(100), nullable=True)  # MIME type
    
    positive_feedbacks = Column(Integer, default=0, nullable=False)
    negative_feedbacks = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    sections = relationship("PostSection", back_populates="post", cascade="all, delete-orphan", order_by="PostSection.order_index")
    feedbacks = relationship("PostFeedback", back_populates="post", cascade="all, delete-orphan")

class PostSection(Base):
    __tablename__ = "post_sections"
    
    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False)
    section_type = Column(Enum(SectionType), nullable=False)
    order_index = Column(Integer, nullable=False, default=0)  # For ordering sections
    
    # Content fields - only one will be used based on section_type
    text_content = Column(Text, nullable=True)  # For text sections
    image_data = Column(LargeBinary, nullable=True)  # For image sections
    image_filename = Column(String(255), nullable=True)
    image_content_type = Column(String(100), nullable=True)
    video_url = Column(String(500), nullable=True)  # For video sections (YouTube, Vimeo, etc.)
    video_filename = Column(String(255), nullable=True)  # For uploaded videos
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship
    post = relationship("Post", back_populates="sections")

class PostFeedback(Base):
    __tablename__ = "post_feedbacks"
    
    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    feedback_type = Column(Enum(FeedbackType), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    post = relationship("Post", back_populates="feedbacks")
    user = relationship("User")
    
    # Ensure one feedback per user per post
    __table_args__ = (
        {"mysql_engine": "InnoDB"},
    )
