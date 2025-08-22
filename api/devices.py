from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional, List
import io
import math

from db.database import get_db
from crud.device import DeviceCRUD
from schemas.device import (
    DeviceCreate, DeviceUpdate, DeviceResponse, DeviceListResponse, QRCodeResponse
)
from api.auth import get_current_user, get_current_admin_user
from models.user import User

router = APIRouter()


# Public endpoints
@router.get("/", response_model=DeviceListResponse, summary="Get all devices")
async def get_devices(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
    active_only: bool = Query(True, description="Show only active devices"),
    include_images: bool = Query(True, description="Include base64 image data in response"),
    db: Session = Depends(get_db)
):
    """Get all devices with pagination"""
    device_crud = DeviceCRUD(db)
    
    skip = (page - 1) * per_page
    devices = device_crud.get_all(skip=skip, limit=per_page, active_only=active_only)
    total = device_crud.get_total_count(active_only=active_only)
    total_pages = math.ceil(total / per_page)
    
    # Convert to response format
    device_responses = []
    for device in devices:
        device_dict = device_crud.convert_device_to_dict(device, include_image_data=include_images)
        device_responses.append(DeviceResponse(**device_dict))
    
    return DeviceListResponse(
        devices=device_responses,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages
    )


@router.get("/{device_id}", response_model=DeviceResponse, summary="Get device by ID")
async def get_device(
    device_id: int, 
    include_images: bool = Query(True, description="Include base64 image data in response"),
    db: Session = Depends(get_db)
):
    """Get specific device by ID"""
    device_crud = DeviceCRUD(db)
    device = device_crud.get_by_id(device_id)
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    device_dict = device_crud.convert_device_to_dict(device, include_image_data=include_images)
    return DeviceResponse(**device_dict)


@router.get("/{device_id}/image", summary="Get device image")
async def get_device_image(device_id: int, db: Session = Depends(get_db)):
    """Get device image"""
    device_crud = DeviceCRUD(db)
    image_data = device_crud.get_device_image(device_id)
    
    if not image_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device image not found"
        )
    
    image_bytes, content_type = image_data
    return StreamingResponse(
        io.BytesIO(image_bytes),
        media_type=content_type,
        headers={"Content-Disposition": f"inline; filename=device_{device_id}_image.jpg"}
    )


@router.get("/{device_id}/qr-code", summary="Get device QR code")
async def get_device_qr_code(device_id: int, db: Session = Depends(get_db)):
    """Get device QR code image"""
    device_crud = DeviceCRUD(db)
    qr_data = device_crud.get_qr_code(device_id)
    
    if not qr_data:
        # Generate QR code if it doesn't exist
        device = device_crud.get_by_id(device_id)
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found"
            )
        
        device_crud.generate_qr_code(device)
        qr_data = device_crud.get_qr_code(device_id)
        
        if not qr_data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate QR code"
            )
    
    qr_bytes, content_type = qr_data
    return StreamingResponse(
        io.BytesIO(qr_bytes),
        media_type=content_type,
        headers={"Content-Disposition": f"inline; filename=device_{device_id}_qr.png"}
    )


# Admin-only endpoints
@router.post("/", response_model=DeviceResponse, summary="Create device (Admin only)")
async def create_device(
    device_data: DeviceCreate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Create a new device (Admin only)"""
    device_crud = DeviceCRUD(db)
    
    # Check if device name already exists
    existing_device = device_crud.get_by_name(device_data.device_name)
    if existing_device:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Device with this name already exists"
        )
    
    device = device_crud.create(device_data)
    device_dict = device_crud.convert_device_to_dict(device, include_image_data=True)
    return DeviceResponse(**device_dict)


@router.post("/with-image", response_model=DeviceResponse, summary="Create device with image (Admin only)")
async def create_device_with_image(
    device_name: str = Form(..., description="Device name"),
    version: str = Form(..., description="Device version"),
    description: Optional[str] = Form(None, description="Device description"),
    image: Optional[UploadFile] = File(None, description="Device image"),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Create a new device with optional image (Admin only)"""
    device_crud = DeviceCRUD(db)
    
    # Check if device name already exists
    existing_device = device_crud.get_by_name(device_name)
    if existing_device:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Device with this name already exists"
        )
    
    # Create device data
    device_data = DeviceCreate(
        device_name=device_name,
        version=version,
        description=description
    )
    
    device = await device_crud.create_with_image(device_data, image)
    device_dict = device_crud.convert_device_to_dict(device, include_image_data=True)
    return DeviceResponse(**device_dict)


@router.put("/{device_id}", response_model=DeviceResponse, summary="Update device (Admin only)")
async def update_device(
    device_id: int,
    device_update: DeviceUpdate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Update device (Admin only)"""
    device_crud = DeviceCRUD(db)
    
    # Check if device name already exists (if updating name)
    if device_update.device_name:
        existing_device = device_crud.get_by_name(device_update.device_name)
        if existing_device and existing_device.id != device_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Device with this name already exists"
            )
    
    device = device_crud.update(device_id, device_update)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    device_dict = device_crud.convert_device_to_dict(device, include_image_data=True)
    return DeviceResponse(**device_dict)


@router.put("/{device_id}/image", response_model=DeviceResponse, summary="Update device image (Admin only)")
async def update_device_image(
    device_id: int,
    image: UploadFile = File(..., description="New device image"),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Update device image (Admin only)"""
    device_crud = DeviceCRUD(db)
    
    device = await device_crud.update_device_image(device_id, image)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    device_dict = device_crud.convert_device_to_dict(device, include_image_data=True)
    return DeviceResponse(**device_dict)


@router.delete("/{device_id}/image", response_model=DeviceResponse, summary="Remove device image (Admin only)")
async def remove_device_image(
    device_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Remove device image (Admin only)"""
    device_crud = DeviceCRUD(db)
    
    device = device_crud.remove_device_image(device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    device_dict = device_crud.convert_device_to_dict(device, include_image_data=True)
    return DeviceResponse(**device_dict)


@router.post("/{device_id}/regenerate-qr", response_model=DeviceResponse, summary="Regenerate QR code (Admin only)")
async def regenerate_qr_code(
    device_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Regenerate QR code for device (Admin only)"""
    device_crud = DeviceCRUD(db)
    
    device = device_crud.regenerate_qr_code(device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    device_dict = device_crud.convert_device_to_dict(device, include_image_data=True)
    return DeviceResponse(**device_dict)


@router.post("/{device_id}/activate", response_model=DeviceResponse, summary="Activate device (Admin only)")
async def activate_device(
    device_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Activate device (Admin only)"""
    device_crud = DeviceCRUD(db)
    
    device = device_crud.activate(device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    device_dict = device_crud.convert_device_to_dict(device, include_image_data=True)
    return DeviceResponse(**device_dict)


@router.delete("/{device_id}", summary="Deactivate device (Admin only)")
async def deactivate_device(
    device_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Deactivate device (soft delete) (Admin only)"""
    device_crud = DeviceCRUD(db)
    
    success = device_crud.delete(device_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    return {"message": "Device deactivated successfully"}


@router.delete("/{device_id}/hard-delete", summary="Hard delete device (Admin only)")
async def hard_delete_device(
    device_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Permanently delete device from database (Admin only)"""
    device_crud = DeviceCRUD(db)
    
    success = device_crud.hard_delete(device_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    return {"message": "Device permanently deleted"}


@router.get("/name/{device_name}", response_model=DeviceResponse, summary="Get device by name")
async def get_device_by_name(
    device_name: str, 
    include_images: bool = Query(True, description="Include base64 image data in response"),
    db: Session = Depends(get_db)
):
    """Get device by name"""
    device_crud = DeviceCRUD(db)
    device = device_crud.get_by_name(device_name)
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    device_dict = device_crud.convert_device_to_dict(device, include_image_data=include_images)
    return DeviceResponse(**device_dict)
