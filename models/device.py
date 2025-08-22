from sqlalchemy import Column, Integer, String, Text, LargeBinary, Boolean, DateTime
from sqlalchemy.sql import func
from db.database import Base


class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    device_name = Column(String(200), nullable=False, index=True)
    version = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    
    # Device image stored as binary data
    image_data = Column(LargeBinary, nullable=True)
    image_filename = Column(String(255), nullable=True)
    image_content_type = Column(String(100), nullable=True)
    
    # QR code data
    qr_code_data = Column(LargeBinary, nullable=True)  # Generated QR code image
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Device(id={self.id}, name={self.device_name}, version={self.version})>"
