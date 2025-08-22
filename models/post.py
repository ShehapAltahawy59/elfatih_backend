from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum, LargeBinary
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.database import Base
import enum

class FeedbackType(enum.Enum):
    positive = "positive"
    negative = "negative"

class Post(Base):
    __tablename__ = "posts"
    
    id = Column(Integer, primary_key=True, index=True)
    header = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    image_data = Column(LargeBinary, nullable=True)  # Store image as binary data
    image_filename = Column(String(255), nullable=True)  # Original filename
    image_content_type = Column(String(100), nullable=True)  # MIME type (image/jpeg, image/png, etc.)
    positive_feedbacks = Column(Integer, default=0, nullable=False)
    negative_feedbacks = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship to feedback
    feedbacks = relationship("PostFeedback", back_populates="post", cascade="all, delete-orphan")

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
