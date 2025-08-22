from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional, Tuple
from fastapi import UploadFile
from models.post import Post, PostSection, PostFeedback, FeedbackType, SectionType
from schemas.post import PostCreate, PostUpdate, FeedbackCreate, TextSectionCreate, VideoSectionCreate, SectionTypeEnum
from utils.image_utils import process_uploaded_image, image_to_base64, get_image_info

class PostCRUD:
    def __init__(self, db: Session):
        self.db = db

    def create(self, post_data: PostCreate) -> Post:
        """Create a new post"""
        # Create post data
        db_post = Post(
            header=post_data.header,
            description=post_data.description,
            positive_feedbacks=0,
            negative_feedbacks=0,
            is_active=True
        )
        
        self.db.add(db_post)
        self.db.commit()
        self.db.refresh(db_post)
        return db_post

    async def create_with_image(self, post_data: PostCreate, image_file: Optional[UploadFile] = None) -> Post:
        """Create a new post with optional main image"""
        # Create post data
        db_post = Post(
            header=post_data.header,
            description=post_data.description,
            positive_feedbacks=0,
            negative_feedbacks=0,
            is_active=True
        )
        
        # Process main post image if provided
        if image_file:
            try:
                image_data, filename, content_type = await process_uploaded_image(image_file)
                db_post.image_data = image_data
                db_post.image_filename = filename
                db_post.image_content_type = content_type
            except Exception as e:
                print(f"Error processing main post image: {e}")
        
        self.db.add(db_post)
        self.db.commit()
        self.db.refresh(db_post)
        return db_post

    async def update_post_image(self, post_id: int, image_file: UploadFile) -> Optional[Post]:
        """Update main post image"""
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
            print(f"Error updating main post image: {e}")
            return None

    def remove_post_image(self, post_id: int) -> Optional[Post]:
        """Remove main post image"""
        db_post = self.get_by_id(post_id)
        if not db_post:
            return None

        db_post.image_data = None
        db_post.image_filename = None
        db_post.image_content_type = None
        
        self.db.commit()
        self.db.refresh(db_post)
        return db_post

    def get_post_image(self, post_id: int) -> Optional[Tuple[bytes, str, str]]:
        """Get main post image data, content type, and filename"""
        db_post = self.get_by_id(post_id)
        if not db_post or not db_post.image_data:
            return None
        
        return db_post.image_data, db_post.image_content_type, db_post.image_filename

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

    # Section CRUD methods
    def create_text_section(self, post_id: int, section_data: TextSectionCreate) -> Optional[PostSection]:
        """Create a text section for a post"""
        try:
            db_section = PostSection(
                post_id=post_id,
                section_type=SectionType.text,
                order_index=section_data.order_index,
                text_content=section_data.text_content
            )
            self.db.add(db_section)
            self.db.commit()
            self.db.refresh(db_section)
            return db_section
        except Exception as e:
            self.db.rollback()
            print(f"Error creating text section: {e}")
            return None

    async def create_image_section(self, post_id: int, order_index: int, image_file: UploadFile) -> Optional[PostSection]:
        """Create an image section for a post"""
        try:
            # Process the uploaded image
            image_data, filename, content_type = await process_uploaded_image(image_file)
            
            db_section = PostSection(
                post_id=post_id,
                section_type=SectionType.image,
                order_index=order_index,
                image_data=image_data,
                image_filename=filename,
                image_content_type=content_type
            )
            self.db.add(db_section)
            self.db.commit()
            self.db.refresh(db_section)
            return db_section
        except Exception as e:
            self.db.rollback()
            print(f"Error creating image section: {e}")
            return None

    def create_video_section(self, post_id: int, section_data: VideoSectionCreate) -> Optional[PostSection]:
        """Create a video section for a post"""
        try:
            db_section = PostSection(
                post_id=post_id,
                section_type=SectionType.video,
                order_index=section_data.order_index,
                video_url=section_data.video_url
            )
            self.db.add(db_section)
            self.db.commit()
            self.db.refresh(db_section)
            return db_section
        except Exception as e:
            self.db.rollback()
            print(f"Error creating video section: {e}")
            return None

    def get_post_sections(self, post_id: int) -> List[PostSection]:
        """Get all sections for a post, ordered by order_index"""
        return self.db.query(PostSection).filter(
            PostSection.post_id == post_id
        ).order_by(PostSection.order_index).all()

    def get_section_by_id(self, section_id: int) -> Optional[PostSection]:
        """Get a specific section by ID"""
        return self.db.query(PostSection).filter(PostSection.id == section_id).first()

    def update_section_order(self, section_id: int, new_order: int) -> Optional[PostSection]:
        """Update the order of a section"""
        section = self.get_section_by_id(section_id)
        if section:
            section.order_index = new_order
            self.db.commit()
            self.db.refresh(section)
        return section

    def delete_section(self, section_id: int) -> bool:
        """Delete a section"""
        section = self.get_section_by_id(section_id)
        if section:
            self.db.delete(section)
            self.db.commit()
            return True
        return False

    def get_section_image(self, section_id: int) -> Optional[Tuple[bytes, str, str]]:
        """Get section image data, content type, and filename"""
        section = self.get_section_by_id(section_id)
        if section and section.section_type == SectionType.image and section.image_data:
            return section.image_data, section.image_content_type, section.image_filename
        return None

    def convert_post_to_dict(self, post: Post, include_sections: bool = True, include_image_data: bool = False) -> dict:
        """Convert Post object to dictionary with sections and optional image data"""
        import base64
        
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
        
        # Include base64 encoded main post image data if requested
        if include_image_data and post.image_data:
            try:
                image_b64 = base64.b64encode(post.image_data).decode('utf-8')
                post_dict["image_data"] = f"data:{post.image_content_type or 'image/jpeg'};base64,{image_b64}"
            except Exception as e:
                print(f"Error encoding post image data: {e}")
                post_dict["image_data"] = None
        else:
            post_dict["image_data"] = None
        
        if include_sections:
            sections = []
            for section in post.sections:
                section_dict = {
                    "id": section.id,
                    "section_type": section.section_type.value,
                    "order_index": section.order_index,
                    "text_content": section.text_content,
                    "image_url": f"/api/v1/posts/sections/{section.id}/image" if section.image_data else None,
                    "image_filename": section.image_filename,
                    "video_url": section.video_url,
                    "video_filename": section.video_filename,
                    "created_at": section.created_at.isoformat() if section.created_at else None,
                    "updated_at": section.updated_at.isoformat() if section.updated_at else None
                }
                
                # Include base64 encoded section image data if requested
                if include_image_data and section.image_data:
                    try:
                        section_image_b64 = base64.b64encode(section.image_data).decode('utf-8')
                        section_dict["image_data"] = f"data:{section.image_content_type or 'image/jpeg'};base64,{section_image_b64}"
                    except Exception as e:
                        print(f"Error encoding section image data: {e}")
                        section_dict["image_data"] = None
                else:
                    section_dict["image_data"] = None
                
                sections.append(section_dict)
            post_dict["sections"] = sections
        
        return post_dict
