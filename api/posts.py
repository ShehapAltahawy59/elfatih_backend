from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import List, Optional

from db.database import get_db
from crud.post import PostCRUD
from models.post import Post
from schemas.post import PostCreate, PostUpdate, PostResponse, FeedbackCreate, PostWithUserFeedback, FeedbackTypeEnum, TextSectionCreate, VideoSectionCreate, SectionTypeEnum
from api.auth import get_current_active_user, get_current_admin_user

router = APIRouter(prefix="/posts", tags=["posts"])

# Public endpoints (read-only)
@router.get("/")
def get_posts(
    skip: int = 0,
    limit: int = 100,
    include_images: bool = False,
    db: Session = Depends(get_db)
):
    """Get all active posts (public endpoint)"""
    try:
        post_crud = PostCRUD(db)
        posts = post_crud.get_active_posts(skip=skip, limit=limit)
        
        # Convert posts to dict to avoid serialization issues
        posts_data = []
        for post in posts:
            posts_data.append(post_crud.convert_post_to_dict(post, include_image_data=include_images))
        
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
    """Get main post image as binary response"""
    try:
        post_crud = PostCRUD(db)
        image_data = post_crud.get_post_image(post_id)
        
        if not image_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post image not found"
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
            detail=f"Failed to get post image: {str(e)}"
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

# Section endpoints
@router.get("/sections/{section_id}/image")
def get_section_image(
    section_id: int,
    db: Session = Depends(get_db)
):
    """Get section image as binary response"""
    try:
        post_crud = PostCRUD(db)
        image_data = post_crud.get_section_image(section_id)
        
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
                "Cache-Control": "public, max-age=3600"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get section image: {str(e)}"
        )

@router.post("/{post_id}/sections/text")
def add_text_section(
    post_id: int,
    section_data: TextSectionCreate,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin_user)
):
    """Admin only: Add a text section to a post"""
    try:
        post_crud = PostCRUD(db)
        
        # Check if post exists
        post = post_crud.get_by_id(post_id)
        if not post:
            return {
                "error": "Post not found",
                "post_id": post_id
            }
        
        section = post_crud.create_text_section(post_id, section_data)
        if not section:
            return {
                "error": "Failed to create text section",
                "post_id": post_id
            }
        
        return {
            "message": "Text section added successfully",
            "section": {
                "id": section.id,
                "section_type": section.section_type.value,
                "order_index": section.order_index,
                "text_content": section.text_content,
                "created_at": section.created_at.isoformat() if section.created_at else None
            }
        }
        
    except Exception as e:
        return {
            "error": "Failed to add text section",
            "details": str(e),
            "post_id": post_id
        }

@router.post("/{post_id}/sections/image")
async def add_image_section(
    post_id: int,
    order_index: int = Form(0),
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin_user)
):
    """Admin only: Add an image section to a post"""
    try:
        post_crud = PostCRUD(db)
        
        # Check if post exists
        post = post_crud.get_by_id(post_id)
        if not post:
            return {
                "error": "Post not found",
                "post_id": post_id
            }
        
        section = await post_crud.create_image_section(post_id, order_index, image)
        if not section:
            return {
                "error": "Failed to create image section",
                "post_id": post_id
            }
        
        return {
            "message": "Image section added successfully",
            "section": {
                "id": section.id,
                "section_type": section.section_type.value,
                "order_index": section.order_index,
                "image_url": f"/api/v1/posts/sections/{section.id}/image",
                "image_filename": section.image_filename,
                "created_at": section.created_at.isoformat() if section.created_at else None
            }
        }
        
    except Exception as e:
        return {
            "error": "Failed to add image section",
            "details": str(e),
            "post_id": post_id
        }

@router.post("/{post_id}/sections/video")
def add_video_section(
    post_id: int,
    section_data: VideoSectionCreate,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin_user)
):
    """Admin only: Add a video section to a post"""
    try:
        post_crud = PostCRUD(db)
        
        # Check if post exists
        post = post_crud.get_by_id(post_id)
        if not post:
            return {
                "error": "Post not found",
                "post_id": post_id
            }
        
        section = post_crud.create_video_section(post_id, section_data)
        if not section:
            return {
                "error": "Failed to create video section",
                "post_id": post_id
            }
        
        return {
            "message": "Video section added successfully",
            "section": {
                "id": section.id,
                "section_type": section.section_type.value,
                "order_index": section.order_index,
                "video_url": section.video_url,
                "created_at": section.created_at.isoformat() if section.created_at else None
            }
        }
        
    except Exception as e:
        return {
            "error": "Failed to add video section",
            "details": str(e),
            "post_id": post_id
        }

@router.put("/sections/{section_id}/order")
def update_section_order(
    section_id: int,
    new_order: int,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin_user)
):
    """Admin only: Update the order of a section"""
    try:
        post_crud = PostCRUD(db)
        section = post_crud.update_section_order(section_id, new_order)
        
        if not section:
            return {
                "error": "Section not found",
                "section_id": section_id
            }
        
        return {
            "message": "Section order updated successfully",
            "section": {
                "id": section.id,
                "order_index": section.order_index
            }
        }
        
    except Exception as e:
        return {
            "error": "Failed to update section order",
            "details": str(e),
            "section_id": section_id
        }

@router.delete("/sections/{section_id}")
def delete_section(
    section_id: int,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin_user)
):
    """Admin only: Delete a section"""
    try:
        post_crud = PostCRUD(db)
        success = post_crud.delete_section(section_id)
        
        if success:
            return {
                "message": "Section deleted successfully",
                "section_id": section_id
            }
        else:
            return {
                "error": "Section not found",
                "section_id": section_id
            }
        
    except Exception as e:
        return {
            "error": "Failed to delete section",
            "details": str(e),
            "section_id": section_id
        }

# Admin endpoints
@router.post("/complete", status_code=status.HTTP_201_CREATED)
async def create_complete_post(
    header: str = Form(...),
    description: Optional[str] = Form(None),
    sections: str = Form(...),  # JSON string describing all sections with their types and order
    # Main post image (featured/cover image)
    main_image: Optional[UploadFile] = File(None),
    # For image sections - multiple files can be uploaded
    images: Optional[List[UploadFile]] = File(None),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin_user)
):
    """
    Admin only: Create a complete post with flexible sections
    
    sections format:
    [
        {"type": "text", "order_index": 0, "content": "Introduction text..."},
        {"type": "image", "order_index": 1, "content": "image_file_1"},
        {"type": "text", "order_index": 2, "content": "More text..."},
        {"type": "video", "order_index": 3, "content": "https://youtube.com/watch?v=..."},
        {"type": "image", "order_index": 4, "content": "image_file_2"}
    ]
    
    Note: For image sections, the "content" field should match the filename of uploaded images
    """
    try:
        import json
        post_crud = PostCRUD(db)
        
        # Parse sections data
        try:
            sections_data = json.loads(sections)
        except json.JSONDecodeError as e:
            return {"error": f"Invalid sections JSON: {str(e)}"}
        
        # Create the basic post with main image
        post_data = PostCreate(header=header, description=description)
        db_post = await post_crud.create_with_image(post_data, main_image)
        
        created_sections = []
        
        # Process each section based on its type
        for section_info in sections_data:
            section_type = section_info.get("type")
            order_index = section_info.get("order_index", 0)
            content = section_info.get("content", "")
            
            if section_type == "text":
                # Create text section
                section_data = TextSectionCreate(
                    order_index=order_index,
                    text_content=content
                )
                section = post_crud.create_text_section(db_post.id, section_data)
                if section:
                    created_sections.append({
                        "id": section.id,
                        "type": "text",
                        "order_index": section.order_index,
                        "content": section.text_content[:100] + "..." if len(section.text_content) > 100 else section.text_content
                    })
            
            elif section_type == "image":
                # Create image section - find image by filename in content
                image_filename = content
                if images:
                    # Find the uploaded image that matches the content filename
                    matching_image = None
                    for image_file in images:
                        if image_file.filename == image_filename:
                            matching_image = image_file
                            break
                    
                    if matching_image:
                        section = await post_crud.create_image_section(db_post.id, order_index, matching_image)
                        if section:
                            created_sections.append({
                                "id": section.id,
                                "type": "image",
                                "order_index": section.order_index,
                                "filename": section.image_filename,
                                "image_url": f"/api/v1/posts/sections/{section.id}/image"
                            })
                    else:
                        return {"error": f"Image file '{image_filename}' not found in uploaded images"}
                else:
                    return {"error": f"No images uploaded but image section requires '{image_filename}'"}
            
            elif section_type == "video":
                # Create video section
                section_data = VideoSectionCreate(
                    order_index=order_index,
                    video_url=content
                )
                section = post_crud.create_video_section(db_post.id, section_data)
                if section:
                    created_sections.append({
                        "id": section.id,
                        "type": "video",
                        "order_index": section.order_index,
                        "video_url": section.video_url
                    })
            
            else:
                return {"error": f"Invalid section type: {section_type}. Must be 'text', 'image', or 'video'"}
        
        # Get the complete post with all sections
        complete_post = post_crud.get_by_id(db_post.id)
        
        return {
            "message": "Complete post created successfully",
            "post": post_crud.convert_post_to_dict(complete_post, include_image_data=False),
            "sections_created": len(created_sections),
            "created_sections": created_sections
        }
        
    except Exception as e:
        return {
            "error": "Failed to create complete post",
            "details": str(e),
            "debug": "Exception in POST /posts/complete"
        }

@router.post("/", status_code=status.HTTP_201_CREATED)
def create_post(
    post_data: PostCreate,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin_user)
):
    """Admin only: Create a basic post (sections added separately)"""
    try:
        post_crud = PostCRUD(db)
        
        # Create basic post without sections
        db_post = Post(
            header=post_data.header,
            description=post_data.description,
            positive_feedbacks=0,
            negative_feedbacks=0,
            is_active=True
        )
        
        post_crud.db.add(db_post)
        post_crud.db.commit()
        post_crud.db.refresh(db_post)
        
        return {
            "message": "Post created successfully",
            "post": post_crud.convert_post_to_dict(db_post, include_image_data=False),
            "instructions": "Use the section endpoints to add content: /posts/{id}/sections/text, /posts/{id}/sections/image, /posts/{id}/sections/video"
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
            "post": post_crud.convert_post_to_dict(post, include_image_data=False)
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
    """Admin only: Update main post image"""
    try:
        post_crud = PostCRUD(db)
        post = await post_crud.update_post_image(post_id, image)
        
        if not post:
            return {
                "error": "Post not found",
                "post_id": post_id
            }
        
        return {
            "message": "Main post image updated successfully",
            "post": post_crud.convert_post_to_dict(post, include_image_data=False)
        }
        
    except Exception as e:
        return {
            "error": "Failed to update main post image",
            "details": str(e),
            "post_id": post_id
        }

@router.delete("/{post_id}/image")
def remove_post_image(
    post_id: int,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin_user)
):
    """Admin only: Remove main post image"""
    try:
        post_crud = PostCRUD(db)
        post = post_crud.remove_post_image(post_id)
        
        if not post:
            return {
                "error": "Post not found",
                "post_id": post_id
            }
        
        return {
            "message": "Main post image removed successfully",
            "post": post_crud.convert_post_to_dict(post, include_image_data=False)
        }
        
    except Exception as e:
        return {
            "error": "Failed to remove main post image",
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
