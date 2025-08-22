import qrcode
import io
from PIL import Image
from typing import Tuple


def generate_qr_code(data: str, size: int = 10, border: int = 4) -> Tuple[bytes, str]:
    """
    Generate QR code image from data
    
    Args:
        data: The data to encode in QR code
        size: Size of QR code (default 10)
        border: Border size (default 4)
    
    Returns:
        Tuple of (image_bytes, content_type)
    """
    # Create QR code instance
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=size,
        border=border,
    )
    
    # Add data and make QR code
    qr.add_data(data)
    qr.make(fit=True)
    
    # Create image
    qr_image = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to bytes
    img_buffer = io.BytesIO()
    qr_image.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    
    return img_buffer.getvalue(), "image/png"


def generate_device_qr_data(device_id: int, device_name: str, version: str) -> str:
    """
    Generate QR code data for a device
    
    Args:
        device_id: Device ID
        device_name: Device name
        version: Device version
    
    Returns:
        JSON string to be encoded in QR code
    """
    import json
    from datetime import datetime
    
    qr_data = {
        "device_id": device_id,
        "device_name": device_name,
        "version": version,
        "type": "device",
        "generated_at": str(datetime.utcnow().isoformat())
    }
    
    return json.dumps(qr_data)


def create_device_qr_code(device_id: int, device_name: str, version: str) -> Tuple[bytes, str, str]:
    """
    Create QR code for a device
    
    Args:
        device_id: Device ID
        device_name: Device name  
        version: Device version
    
    Returns:
        Tuple of (qr_image_bytes, content_type, qr_data_string)
    """
    from datetime import datetime
    import json
    
    # Generate QR data
    qr_data = generate_device_qr_data(device_id, device_name, version)
    
    # Generate QR code image
    qr_image_bytes, content_type = generate_qr_code(qr_data)
    
    return qr_image_bytes, content_type, qr_data
