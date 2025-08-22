from sqlalchemy.orm import Session
from sqlalchemy import desc
from models.device import Device
from schemas.device import DeviceCreate, DeviceUpdate
from utils.image_utils import process_uploaded_image
from utils.qr_utils import create_device_qr_code
from fastapi import UploadFile
from typing import Optional, List, Tuple


class DeviceCRUD:
    def __init__(self, db: Session):
        self.db = db

    def create(self, device_data: DeviceCreate) -> Device:
        """Create a new device"""
        db_device = Device(
            device_name=device_data.device_name,
            version=device_data.version,
            description=device_data.description,
            is_active=True
        )
        self.db.add(db_device)
        self.db.commit()
        self.db.refresh(db_device)
        
        # Generate QR code after device is created (so we have the ID)
        self.generate_qr_code(db_device)
        
        return db_device

    async def create_with_image(self, device_data: DeviceCreate, image_file: Optional[UploadFile] = None) -> Device:
        """Create a new device with optional image"""
        db_device = Device(
            device_name=device_data.device_name,
            version=device_data.version,
            description=device_data.description,
            is_active=True
        )
        
        # Process image if provided
        if image_file:
            try:
                image_data, filename, content_type = await process_uploaded_image(image_file)
                db_device.image_data = image_data
                db_device.image_filename = filename
                db_device.image_content_type = content_type
            except Exception as e:
                print(f"Error processing device image: {e}")
        
        self.db.add(db_device)
        self.db.commit()
        self.db.refresh(db_device)
        
        # Generate QR code after device is created
        self.generate_qr_code(db_device)
        
        return db_device

    def get_by_id(self, device_id: int) -> Optional[Device]:
        """Get device by ID"""
        return self.db.query(Device).filter(Device.id == device_id).first()

    def get_by_name(self, device_name: str) -> Optional[Device]:
        """Get device by name"""
        return self.db.query(Device).filter(Device.device_name == device_name).first()

    def get_all(self, skip: int = 0, limit: int = 100, active_only: bool = True) -> List[Device]:
        """Get all devices with pagination"""
        query = self.db.query(Device)
        if active_only:
            query = query.filter(Device.is_active == True)
        return query.order_by(desc(Device.created_at)).offset(skip).limit(limit).all()

    def get_total_count(self, active_only: bool = True) -> int:
        """Get total count of devices"""
        query = self.db.query(Device)
        if active_only:
            query = query.filter(Device.is_active == True)
        return query.count()

    def update(self, device_id: int, device_update: DeviceUpdate) -> Optional[Device]:
        """Update device"""
        db_device = self.get_by_id(device_id)
        if not db_device:
            return None

        # Update fields that are provided
        update_data = device_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_device, field, value)

        self.db.commit()
        self.db.refresh(db_device)
        
        # Regenerate QR code if name or version changed
        if 'device_name' in update_data or 'version' in update_data:
            self.generate_qr_code(db_device)

        return db_device

    async def update_device_image(self, device_id: int, image_file: UploadFile) -> Optional[Device]:
        """Update device image"""
        db_device = self.get_by_id(device_id)
        if not db_device:
            return None

        try:
            image_data, filename, content_type = await process_uploaded_image(image_file)
            db_device.image_data = image_data
            db_device.image_filename = filename
            db_device.image_content_type = content_type
            
            self.db.commit()
            self.db.refresh(db_device)
            return db_device
        except Exception as e:
            print(f"Error updating device image: {e}")
            return None

    def remove_device_image(self, device_id: int) -> Optional[Device]:
        """Remove device image"""
        db_device = self.get_by_id(device_id)
        if not db_device:
            return None

        db_device.image_data = None
        db_device.image_filename = None
        db_device.image_content_type = None
        
        self.db.commit()
        self.db.refresh(db_device)
        return db_device

    def get_device_image(self, device_id: int) -> Optional[Tuple[bytes, str]]:
        """Get device image data"""
        db_device = self.get_by_id(device_id)
        if not db_device or not db_device.image_data:
            return None
        return db_device.image_data, db_device.image_content_type or "image/jpeg"

    def delete(self, device_id: int) -> bool:
        """Soft delete device (set inactive)"""
        db_device = self.get_by_id(device_id)
        if not db_device:
            return False

        db_device.is_active = False
        self.db.commit()
        return True

    def hard_delete(self, device_id: int) -> bool:
        """Hard delete device from database"""
        db_device = self.get_by_id(device_id)
        if not db_device:
            return False

        self.db.delete(db_device)
        self.db.commit()
        return True

    def activate(self, device_id: int) -> Optional[Device]:
        """Activate device"""
        db_device = self.get_by_id(device_id)
        if not db_device:
            return None

        db_device.is_active = True
        self.db.commit()
        self.db.refresh(db_device)
        return db_device

    def generate_qr_code(self, device: Device) -> Device:
        """Generate and save QR code for device"""
        try:
            qr_image_bytes, content_type, qr_data = create_device_qr_code(
                device.id, device.device_name, device.version
            )
            device.qr_code_data = qr_image_bytes
            self.db.commit()
            self.db.refresh(device)
        except Exception as e:
            print(f"Error generating QR code: {e}")
        
        return device

    def get_qr_code(self, device_id: int) -> Optional[Tuple[bytes, str]]:
        """Get QR code image data"""
        db_device = self.get_by_id(device_id)
        if not db_device or not db_device.qr_code_data:
            return None
        return db_device.qr_code_data, "image/png"

    def regenerate_qr_code(self, device_id: int) -> Optional[Device]:
        """Regenerate QR code for device"""
        db_device = self.get_by_id(device_id)
        if not db_device:
            return None
        
        return self.generate_qr_code(db_device)

    def convert_device_to_dict(self, device: Device, include_image_data: bool = True) -> dict:
        """Convert device model to dictionary for API response"""
        import base64
        
        device_dict = {
            "id": device.id,
            "device_name": device.device_name,
            "version": device.version,
            "description": device.description,
            "image_url": f"/api/v1/devices/{device.id}/image" if device.image_data else None,
            "image_filename": device.image_filename,
            "qr_code_url": f"/api/v1/devices/{device.id}/qr-code" if device.qr_code_data else None,
            "is_active": device.is_active,
            "created_at": device.created_at,
            "updated_at": device.updated_at
        }
        
        # Include base64 encoded image data if requested and available
        if include_image_data and device.image_data:
            try:
                image_b64 = base64.b64encode(device.image_data).decode('utf-8')
                device_dict["image_data"] = f"data:{device.image_content_type or 'image/jpeg'};base64,{image_b64}"
            except Exception as e:
                print(f"Error encoding image data: {e}")
                device_dict["image_data"] = None
        else:
            device_dict["image_data"] = None
        
        # Include base64 encoded QR code data if available
        if device.qr_code_data:
            try:
                qr_b64 = base64.b64encode(device.qr_code_data).decode('utf-8')
                device_dict["qr_code_data"] = f"data:image/png;base64,{qr_b64}"
            except Exception as e:
                print(f"Error encoding QR code data: {e}")
                device_dict["qr_code_data"] = None
        else:
            device_dict["qr_code_data"] = None
        
        return device_dict
