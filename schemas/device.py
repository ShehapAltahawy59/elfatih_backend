from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
import re


class DeviceBase(BaseModel):
    device_name: str = Field(..., min_length=1, max_length=200, description="Device name")
    version: str = Field(..., min_length=1, max_length=50, description="Device version")
    description: Optional[str] = Field(None, max_length=1000, description="Device description")
    
    @validator('device_name')
    def validate_device_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Device name cannot be empty')
        # Allow letters, numbers, spaces, hyphens, underscores
        if not re.match(r'^[a-zA-Z0-9\s\-_]+$', v.strip()):
            raise ValueError('Device name can only contain letters, numbers, spaces, hyphens, and underscores')
        return v.strip()
    
    @validator('version')
    def validate_version(cls, v):
        if not v or not v.strip():
            raise ValueError('Version cannot be empty')
        # Allow version patterns like 1.0, v1.2.3, 2.0.1-beta, etc.
        if not re.match(r'^[vV]?[\d]+\.[\d]+(?:\.[\d]+)?(?:[-\w]*)?$', v.strip()):
            raise ValueError('Version must follow format like 1.0, v1.2.3, or 2.0.1-beta')
        return v.strip()


class DeviceCreate(DeviceBase):
    """Schema for creating a new device"""
    pass


class DeviceUpdate(BaseModel):
    """Schema for updating a device"""
    device_name: Optional[str] = Field(None, min_length=1, max_length=200)
    version: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=1000)
    is_active: Optional[bool] = None
    
    @validator('device_name')
    def validate_device_name(cls, v):
        if v is not None:
            if not v or not v.strip():
                raise ValueError('Device name cannot be empty')
            if not re.match(r'^[a-zA-Z0-9\s\-_]+$', v.strip()):
                raise ValueError('Device name can only contain letters, numbers, spaces, hyphens, and underscores')
            return v.strip()
        return v
    
    @validator('version')
    def validate_version(cls, v):
        if v is not None:
            if not v or not v.strip():
                raise ValueError('Version cannot be empty')
            if not re.match(r'^[vV]?[\d]+\.[\d]+(?:\.[\d]+)?(?:[-\w]*)?$', v.strip()):
                raise ValueError('Version must follow format like 1.0, v1.2.3, or 2.0.1-beta')
            return v.strip()
        return v


class DeviceResponse(DeviceBase):
    """Schema for device response"""
    id: int
    image_url: Optional[str] = None
    image_filename: Optional[str] = None
    image_data: Optional[str] = None  # Base64 encoded image data
    qr_code_url: Optional[str] = None
    qr_code_data: Optional[str] = None  # Base64 encoded QR code data
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class DeviceListResponse(BaseModel):
    """Schema for device list response"""
    devices: list[DeviceResponse]
    total: int
    page: int
    per_page: int
    total_pages: int


class QRCodeResponse(BaseModel):
    """Schema for QR code response"""
    device_id: int
    qr_code_url: str
    qr_code_data: str  # The data encoded in QR code
