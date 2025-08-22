from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import List, Optional

from db.database import get_db
from crud.post import PostCRUD
from schemas.post import PostCreate, PostUpdate, PostResponse, FeedbackCreate, PostWithUserFeedback, FeedbackTypeEnum
from api.auth import get_current_active_user, get_current_admin_user

router = APIRouter(prefix="/posts", tags=["posts"])

# Public endpoints (read-only)
@router.get("/")
def get_posts(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all active posts (public endpoint)"""
    try:
        post_crud = PostCRUD(db)
        posts = post_crud.get_active_posts(skip=skip, limit=limit)
        
        # Convert posts to dict to avoid serialization issues
        posts_data = []
        for post in posts:
            posts_data.append(post_crud.convert_post_to_dict(post))
        
        return {
            "posts": posts_data,
            "count": len(posts_data),
            "skip": skip,
            "limit": limit
        }
        
    except Exception as e:
        return {
            "error": "Failed to get posts",
            "details": str(e),
            "debug": "Exception in GET /posts/"
        }

@router.get("/with-feedback")
def get_posts_with_user_feedback(
    skip: int = 0,
    limit: int = 100,
    include_images: bool = False,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Get posts with current user's feedback status"""
    try:
        post_crud = PostCRUD(db)
        posts_with_feedback = post_crud.get_posts_with_user_feedback(
            user_id=current_user.get("user_id"),
            skip=skip,
            limit=limit,
            include_images=include_images
        )
        
        # Convert datetime objects to ISO format
        for post in posts_with_feedback:
            if post.get("created_at"):
                post["created_at"] = post["created_at"].isoformat()
            if post.get("updated_at"):
                post["updated_at"] = post["updated_at"].isoformat()
        
        return {
            "posts": posts_with_feedback,
            "count": len(posts_with_feedback),
            "skip": skip,
            "limit": limit
        }
        
    except Exception as e:
        return {
            "error": "Failed to get posts with feedback",
            "details": str(e),
            "debug": "Exception in GET /posts/with-feedback"
        }

@router.get("/{post_id}")
def get_post(
    post_id: int,
    include_image_data: bool = False,
    db: Session = Depends(get_db)
):
    """Get a specific post by ID"""
    try:
        post_crud = PostCRUD(db)
        post = post_crud.get_by_id(post_id)
        
        if not post:
            return {
                "error": "Post not found",
                "post_id": post_id
            }
        
        return post_crud.convert_post_to_dict(post, include_image_data=include_image_data)
        
    except Exception as e:
        return {
            "error": "Failed to get post",
            "details": str(e),
            "post_id": post_id
        }

@router.get("/{post_id}/image")
def get_post_image(
    post_id: int,
    db: Session = Depends(get_db)
):
    """Get post image as binary response"""
    try:
        post_crud = PostCRUD(db)
        image_data = post_crud.get_post_image(post_id)
        
        if not image_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Image not found"
            )
        
        image_bytes, content_type, filename = image_data
        
        return Response(
            content=image_bytes,
            media_type=content_type,
            headers={
                "Content-Disposition": f"inline; filename={filename}",
                "Cache-Control": "public, max-age=3600"  # Cache for 1 hour
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get image: {str(e)}"
        )

# User feedback endpoints
@router.post("/{post_id}/feedback")
def add_feedback(
    post_id: int,
    feedback_data: FeedbackCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Add or update feedback for a post (one feedback per user per post)"""
    try:
        post_crud = PostCRUD(db)
        
        # Check if post exists and is active
        post = post_crud.get_by_id(post_id)
        if not post:
            return {
                "error": "Post not found",
                "post_id": post_id
            }
        
        if not post.is_active:
            return {
                "error": "Cannot give feedback to inactive post",
                "post_id": post_id
            }
        
        feedback = post_crud.add_feedback(
            post_id=post_id,
            user_id=current_user.get("user_id"),
            feedback_data=feedback_data
        )
        
        if not feedback:
            return {
                "error": "Failed to add feedback",
                "post_id": post_id
            }
        
        return {
            "message": "Feedback added successfully",
            "feedback": {
                "id": feedback.id,
                "post_id": feedback.post_id,
                "user_id": feedback.user_id,
                "feedback_type": feedback.feedback_type.value,
                "created_at": feedback.created_at.isoformat() if feedback.created_at else None,
                "updated_at": feedback.updated_at.isoformat() if feedback.updated_at else None
            }
        }
        
    except Exception as e:
        return {
            "error": "Failed to add feedback",
            "details": str(e),
            "post_id": post_id
        }

@router.get("/{post_id}/feedback/check")
def check_user_feedback(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Check if current user has given feedback for this post"""
    try:
        post_crud = PostCRUD(db)
        
        # Check if post exists
        post = post_crud.get_by_id(post_id)
        if not post:
            return {
                "error": "Post not found",
                "post_id": post_id,
                "has_feedback": False
            }
        
        # Check if user has feedback for this post
        user_feedback = post_crud.get_user_feedback(
            post_id=post_id,
            user_id=current_user.get("user_id")
        )
        
        return {
            "post_id": post_id,
            "user_id": current_user.get("user_id"),
            "has_feedback": user_feedback is not None,
            "feedback_type": user_feedback.feedback_type.value if user_feedback else None,
            "feedback_date": user_feedback.created_at.isoformat() if user_feedback else None
        }
        
    except Exception as e:
        return {
            "error": "Failed to check feedback",
            "details": str(e),
            "post_id": post_id,
            "has_feedback": False
        }

@router.delete("/{post_id}/feedback")
def remove_feedback(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Remove user's feedback from a post"""
    try:
        post_crud = PostCRUD(db)
        
        success = post_crud.remove_feedback(
            post_id=post_id,
            user_id=current_user.get("user_id")
        )
        
        if success:
            return {
                "message": "Feedback removed successfully",
                "post_id": post_id
            }
        else:
            return {
                "error": "No feedback found to remove",
                "post_id": post_id
            }
            
    except Exception as e:
        return {
            "error": "Failed to remove feedback",
            "details": str(e),
            "post_id": post_id
        }

# Admin endpoints
@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_post(
    header: str = Form(...),
    description: str = Form(...),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin_user)
):
    """Admin only: Create a new post with optional image"""
    try:
        # Create PostCreate object from form data
        post_data = PostCreate(header=header, description=description)
        
        post_crud = PostCRUD(db)
        post = await post_crud.create_with_image(post_data, image)
        
        return {
            "message": "Post created successfully",
            "post": post_crud.convert_post_to_dict(post)
        }
        
    except Exception as e:
        return {
            "error": "Failed to create post",
            "details": str(e),
            "debug": "Exception in POST /posts/"
        }

@router.put("/{post_id}")
def update_post(
    post_id: int,
    post_data: PostUpdate,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin_user)
):
    """Admin only: Update a post (text fields only)"""
    try:
        post_crud = PostCRUD(db)
        post = post_crud.update(post_id, post_data)
        
        if not post:
            return {
                "error": "Post not found",
                "post_id": post_id
            }
        
        return {
            "message": "Post updated successfully",
            "post": post_crud.convert_post_to_dict(post)
        }
        
    except Exception as e:
        return {
            "error": "Failed to update post",
            "details": str(e),
            "post_id": post_id
        }

@router.put("/{post_id}/image")
async def update_post_image(
    post_id: int,
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin_user)
):
    """Admin only: Update post image"""
    try:
        post_crud = PostCRUD(db)
        post = await post_crud.update_image(post_id, image)
        
        if not post:
            return {
                "error": "Post not found",
                "post_id": post_id
            }
        
        return {
            "message": "Post image updated successfully",
            "post": post_crud.convert_post_to_dict(post)
        }
        
    except Exception as e:
        return {
            "error": "Failed to update post image",
            "details": str(e),
            "post_id": post_id
        }

@router.delete("/{post_id}/image")
def remove_post_image(
    post_id: int,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin_user)
):
    """Admin only: Remove post image"""
    try:
        post_crud = PostCRUD(db)
        post = post_crud.remove_image(post_id)
        
        if not post:
            return {
                "error": "Post not found",
                "post_id": post_id
            }
        
        return {
            "message": "Post image removed successfully",
            "post": post_crud.convert_post_to_dict(post)
        }
        
    except Exception as e:
        return {
            "error": "Failed to remove post image",
            "details": str(e),
            "post_id": post_id
        }

@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin_user)
):
    """Admin only: Delete a post"""
    try:
        post_crud = PostCRUD(db)
        success = post_crud.delete(post_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post not found"
            )
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete post: {str(e)}"
        )
