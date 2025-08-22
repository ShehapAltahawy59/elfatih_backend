import io
from typing import Optional, Tuple
from fastapi import UploadFile, HTTPException
from PIL import Image
import base64

# Configuration
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
ALLOWED_CONTENT_TYPES = {
    "image/jpeg", "image/jpg", "image/png", 
    "image/gif", "image/webp"
}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB for database storage
MAX_IMAGE_WIDTH = 1200
MAX_IMAGE_HEIGHT = 800

def validate_image_file(file: UploadFile) -> bool:
    """Validate uploaded image file"""
    # Check content type
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        return False
    
    # Check filename extension if provided
    if file.filename:
        from pathlib import Path
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            return False
    
    return True

def resize_image_if_needed(image_data: bytes) -> bytes:
    """Resize image if it exceeds maximum dimensions and return optimized bytes"""
    try:
        # Open image from bytes
        with Image.open(io.BytesIO(image_data)) as img:
            width, height = img.size
            
            # Check if resize is needed
            if width <= MAX_IMAGE_WIDTH and height <= MAX_IMAGE_HEIGHT:
                # Still optimize the image
                output = io.BytesIO()
                
                # Convert to RGB if necessary (for JPEG)
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                
                # Save with optimization
                img.save(output, format='JPEG', optimize=True, quality=85)
                return output.getvalue()
            
            # Calculate new dimensions maintaining aspect ratio
            ratio = min(MAX_IMAGE_WIDTH / width, MAX_IMAGE_HEIGHT / height)
            new_width = int(width * ratio)
            new_height = int(height * ratio)
            
            # Resize image
            resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Convert to RGB if necessary
            if resized_img.mode in ('RGBA', 'LA', 'P'):
                resized_img = resized_img.convert('RGB')
            
            # Save to bytes
            output = io.BytesIO()
            resized_img.save(output, format='JPEG', optimize=True, quality=85)
            return output.getvalue()
            
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to process image: {str(e)}"
        )

async def process_uploaded_image(file: UploadFile) -> Tuple[bytes, str, str]:
    """Process uploaded image and return (image_data, filename, content_type)"""
    try:
        # Validate file
        if not validate_image_file(file):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_CONTENT_TYPES)}"
            )
        
        # Read file content
        image_data = await file.read()
        
        # Check file size
        if len(image_data) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB"
            )
        
        # Process and resize image
        processed_image_data = resize_image_if_needed(image_data)
        
        # Get filename (use original or generate default)
        filename = file.filename or "uploaded_image.jpg"
        
        # Set content type (force JPEG after processing)
        content_type = "image/jpeg"
        
        return processed_image_data, filename, content_type
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process image: {str(e)}"
        )

def image_to_base64(image_data: bytes, content_type: str) -> str:
    """Convert image data to base64 data URL for frontend display"""
    if not image_data:
        return ""
    
    base64_data = base64.b64encode(image_data).decode('utf-8')
    return f"data:{content_type};base64,{base64_data}"

def get_image_info(image_data: bytes) -> dict:
    """Get image information like dimensions and size"""
    try:
        if not image_data:
            return {"width": 0, "height": 0, "size": 0}
        
        with Image.open(io.BytesIO(image_data)) as img:
            return {
                "width": img.width,
                "height": img.height,
                "size": len(image_data),
                "format": img.format
            }
    except Exception:
        return {"width": 0, "height": 0, "size": len(image_data) if image_data else 0}
