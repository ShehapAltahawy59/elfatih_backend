from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional, Tuple
from fastapi import UploadFile
from models.post import Post, PostFeedback, FeedbackType
from schemas.post import PostCreate, PostUpdate, FeedbackCreate
from utils.image_utils import process_uploaded_image, image_to_base64, get_image_info

class PostCRUD:
    def __init__(self, db: Session):
        self.db = db

    def create(self, post_data: PostCreate, image_file: Optional[UploadFile] = None) -> Post:
        """Create a new post with optional image"""
        # Create post data
        db_post = Post(
            header=post_data.header,
            description=post_data.description,
            positive_feedbacks=0,
            negative_feedbacks=0,
            is_active=True
        )
        
        # Process image if provided
        if image_file:
            try:
                # This should be called in an async context
                # For now, we'll handle it in the API layer
                pass
            except Exception as e:
                print(f"Error processing image: {e}")
        
        self.db.add(db_post)
        self.db.commit()
        self.db.refresh(db_post)
        return db_post

    async def create_with_image(self, post_data: PostCreate, image_file: Optional[UploadFile] = None) -> Post:
        """Create a new post with optional image (async version)"""
        # Create post data
        db_post = Post(
            header=post_data.header,
            description=post_data.description,
            positive_feedbacks=0,
            negative_feedbacks=0,
            is_active=True
        )
        
        # Process image if provided
        if image_file:
            try:
                image_data, filename, content_type = await process_uploaded_image(image_file)
                db_post.image_data = image_data
                db_post.image_filename = filename
                db_post.image_content_type = content_type
            except Exception as e:
                print(f"Error processing image: {e}")
        
        self.db.add(db_post)
        self.db.commit()
        self.db.refresh(db_post)
        return db_post

    def get_by_id(self, post_id: int) -> Optional[Post]:
        """Get post by ID"""
        return self.db.query(Post).filter(Post.id == post_id).first()

    def get_all(self, skip: int = 0, limit: int = 100, active_only: bool = True) -> List[Post]:
        """Get all posts with pagination"""
        query = self.db.query(Post)
        if active_only:
            query = query.filter(Post.is_active == True)
        return query.offset(skip).limit(limit).all()

    def get_active_posts(self, skip: int = 0, limit: int = 100) -> List[Post]:
        """Get only active posts"""
        return self.db.query(Post).filter(Post.is_active == True).offset(skip).limit(limit).all()

    def update(self, post_id: int, post_data: PostUpdate) -> Optional[Post]:
        """Update a post (text fields only)"""
        db_post = self.get_by_id(post_id)
        if not db_post:
            return None

        update_data = post_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_post, field, value)

        self.db.commit()
        self.db.refresh(db_post)
        return db_post

    async def update_image(self, post_id: int, image_file: UploadFile) -> Optional[Post]:
        """Update post image"""
        db_post = self.get_by_id(post_id)
        if not db_post:
            return None

        try:
            image_data, filename, content_type = await process_uploaded_image(image_file)
            db_post.image_data = image_data
            db_post.image_filename = filename
            db_post.image_content_type = content_type
            
            self.db.commit()
            self.db.refresh(db_post)
            return db_post
        except Exception as e:
            print(f"Error updating image: {e}")
            return None

    def remove_image(self, post_id: int) -> Optional[Post]:
        """Remove image from post"""
        db_post = self.get_by_id(post_id)
        if not db_post:
            return None

        db_post.image_data = None
        db_post.image_filename = None
        db_post.image_content_type = None
        
        self.db.commit()
        self.db.refresh(db_post)
        return db_post

    def delete(self, post_id: int) -> bool:
        """Delete a post"""
        db_post = self.get_by_id(post_id)
        if not db_post:
            return False

        self.db.delete(db_post)
        self.db.commit()
        return True

    def get_post_image(self, post_id: int) -> Optional[Tuple[bytes, str, str]]:
        """Get post image data, content type, and filename"""
        db_post = self.get_by_id(post_id)
        if not db_post or not db_post.image_data:
            return None
        
        return db_post.image_data, db_post.image_content_type, db_post.image_filename

    def add_feedback(self, post_id: int, user_id: int, feedback_data: FeedbackCreate) -> Optional[PostFeedback]:
        """Add or update user feedback for a post"""
        # Check if user already has feedback for this post
        existing_feedback = self.db.query(PostFeedback).filter(
            and_(PostFeedback.post_id == post_id, PostFeedback.user_id == user_id)
        ).first()

        # Get the post
        post = self.get_by_id(post_id)
        if not post:
            return None

        if existing_feedback:
            # Update existing feedback
            old_feedback_type = existing_feedback.feedback_type
            existing_feedback.feedback_type = FeedbackType(feedback_data.feedback_type.value)
            
            # Update counters
            if old_feedback_type == FeedbackType.positive:
                post.positive_feedbacks = max(0, post.positive_feedbacks - 1)
            else:
                post.negative_feedbacks = max(0, post.negative_feedbacks - 1)
                
            if existing_feedback.feedback_type == FeedbackType.positive:
                post.positive_feedbacks += 1
            else:
                post.negative_feedbacks += 1
                
            self.db.commit()
            self.db.refresh(existing_feedback)
            return existing_feedback
        else:
            # Create new feedback
            db_feedback = PostFeedback(
                post_id=post_id,
                user_id=user_id,
                feedback_type=FeedbackType(feedback_data.feedback_type.value)
            )
            self.db.add(db_feedback)
            
            # Update counters
            if db_feedback.feedback_type == FeedbackType.positive:
                post.positive_feedbacks += 1
            else:
                post.negative_feedbacks += 1
                
            self.db.commit()
            self.db.refresh(db_feedback)
            return db_feedback

    def remove_feedback(self, post_id: int, user_id: int) -> bool:
        """Remove user feedback from a post"""
        feedback = self.db.query(PostFeedback).filter(
            and_(PostFeedback.post_id == post_id, PostFeedback.user_id == user_id)
        ).first()

        if not feedback:
            return False

        # Get the post and update counters
        post = self.get_by_id(post_id)
        if post:
            if feedback.feedback_type == FeedbackType.positive:
                post.positive_feedbacks = max(0, post.positive_feedbacks - 1)
            else:
                post.negative_feedbacks = max(0, post.negative_feedbacks - 1)

        self.db.delete(feedback)
        self.db.commit()
        return True

    def get_user_feedback(self, post_id: int, user_id: int) -> Optional[PostFeedback]:
        """Get user's feedback for a specific post"""
        return self.db.query(PostFeedback).filter(
            and_(PostFeedback.post_id == post_id, PostFeedback.user_id == user_id)
        ).first()

    def get_posts_with_user_feedback(self, user_id: int, skip: int = 0, limit: int = 100, include_images: bool = False) -> List[dict]:
        """Get posts with user's feedback status"""
        posts = self.get_active_posts(skip=skip, limit=limit)
        result = []
        
        for post in posts:
            user_feedback = self.get_user_feedback(post.id, user_id)
            post_dict = {
                "id": post.id,
                "header": post.header,
                "description": post.description,
                "image_url": f"/api/v1/posts/{post.id}/image" if post.image_data else None,
                "image_filename": post.image_filename,
                "positive_feedbacks": post.positive_feedbacks,
                "negative_feedbacks": post.negative_feedbacks,
                "is_active": post.is_active,
                "created_at": post.created_at,
                "updated_at": post.updated_at,
                "user_feedback": user_feedback.feedback_type.value if user_feedback else None
            }
            
            # Include base64 image data if requested
            if include_images and post.image_data and post.image_content_type:
                post_dict["image_data"] = image_to_base64(post.image_data, post.image_content_type)
                post_dict["image_info"] = get_image_info(post.image_data)
            
            result.append(post_dict)
            
        return result

    def convert_post_to_dict(self, post: Post, include_image_data: bool = False) -> dict:
        """Convert Post object to dictionary with proper image handling"""
        post_dict = {
            "id": post.id,
            "header": post.header,
            "description": post.description,
            "image_url": f"/api/v1/posts/{post.id}/image" if post.image_data else None,
            "image_filename": post.image_filename,
            "positive_feedbacks": post.positive_feedbacks,
            "negative_feedbacks": post.negative_feedbacks,
            "is_active": post.is_active,
            "created_at": post.created_at.isoformat() if post.created_at else None,
            "updated_at": post.updated_at.isoformat() if post.updated_at else None
        }
        
        # Include base64 image data if requested
        if include_image_data and post.image_data and post.image_content_type:
            post_dict["image_data"] = image_to_base64(post.image_data, post.image_content_type)
            post_dict["image_info"] = get_image_info(post.image_data)
        
        return post_dict
