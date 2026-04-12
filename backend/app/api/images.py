"""
Image Upload API
Handles image uploads - saves locally and returns public URLs
"""
import os
import uuid
import base64
import re
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from loguru import logger

router = APIRouter()

# ==================== Configuration ====================

# مسار تخزين الصور
IMAGES_DIR = Path(__file__).parent.parent.parent.parent / "Data" / "images"
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

# Base URL للصور (هتتغير حسب الـ deployment)
BASE_URL = "/api/v1/images"


# ==================== Static Files Serving ====================

# خدمة الملفات الثابتة (هتتضاف في main.py)
def get_images_mount():
    """رجع mount للـ static files"""
    return StaticFiles(directory=str(IMAGES_DIR), name="images")


# ==================== Models ====================

class ImageUploadResponse(BaseModel):
    url: str
    filename: str
    size: int
    mime_type: str


# ==================== Helper Functions ====================

def _decode_base64_image(data: str) -> tuple:
    """
    يفك تشفير base64 image ويرجع (bytes, mime_type)
    
    Expected format: "data:image/jpeg;base64,AAAA..."
    """
    # Remove data URI prefix
    match = re.match(r'data:(image/\w+);base64,(.*)', data)
    if not match:
        raise ValueError("Invalid image format. Expected: data:image/TYPE;base64,...")
    
    mime_type = match.group(1)
    base64_data = match.group(2)
    
    try:
        image_bytes = base64.b64decode(base64_data)
    except Exception as e:
        raise ValueError(f"Invalid base64 data: {e}")
    
    return image_bytes, mime_type


def _get_extension(mime_type: str) -> str:
    """يرجع extension من MIME type"""
    extensions = {
        'image/jpeg': '.jpg',
        'image/jpg': '.jpg',
        'image/png': '.png',
        'image/webp': '.webp',
        'image/gif': '.gif',
        'image/bmp': '.bmp',
    }
    return extensions.get(mime_type, '.jpg')


# ==================== Endpoints ====================

@router.post("/upload", response_model=ImageUploadResponse)
async def upload_image(file: UploadFile = File(...)):
    """
    رفع صورة واحدة
    
    Request: POST /api/v1/images/upload
    Content-Type: multipart/form-data
    Body: file=<image_file>
    
    Response: {
        "url": "/api/v1/images/static/xxx.jpg",
        "filename": "xxx.jpg",
        "size": 12345,
        "mime_type": "image/jpeg"
    }
    """
    # Validate file type
    allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp', 'image/gif', 'image/bmp']
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_types)}"
        )
    
    # Validate file size (max 10MB)
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size must be less than 10MB")
    
    # Generate unique filename
    ext = _get_extension(file.content_type)
    filename = f"{uuid.uuid4().hex}{ext}"
    file_path = IMAGES_DIR / filename
    
    # Save file
    try:
        with open(file_path, 'wb') as f:
            f.write(content)
    except Exception as e:
        logger.error(f"Failed to save image: {e}")
        raise HTTPException(status_code=500, detail="Failed to save image")
    
    logger.info(f"Image uploaded: {filename} ({len(content)} bytes)")
    
    return ImageUploadResponse(
        url=f"{BASE_URL}/static/{filename}",
        filename=filename,
        size=len(content),
        mime_type=file.content_type,
    )


@router.post("/upload-base64", response_model=ImageUploadResponse)
async def upload_image_base64(data: dict):
    """
    رفع صورة بـ base64 data URL
    
    Request: POST /api/v1/images/upload-base64
    Content-Type: application/json
    Body: {"image": "data:image/jpeg;base64,AAAA..."}
    
    Response: {
        "url": "/api/v1/images/static/xxx.jpg",
        "filename": "xxx.jpg",
        "size": 12345,
        "mime_type": "image/jpeg"
    }
    """
    image_data = data.get("image", "")
    if not image_data:
        raise HTTPException(status_code=400, detail="No image data provided")
    
    try:
        image_bytes, mime_type = _decode_base64_image(image_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Validate file size
    if len(image_bytes) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Image size must be less than 10MB")
    
    # Generate unique filename
    ext = _get_extension(mime_type)
    filename = f"{uuid.uuid4().hex}{ext}"
    file_path = IMAGES_DIR / filename
    
    # Save file
    try:
        with open(file_path, 'wb') as f:
            f.write(image_bytes)
    except Exception as e:
        logger.error(f"Failed to save image: {e}")
        raise HTTPException(status_code=500, detail="Failed to save image")
    
    logger.info(f"Image uploaded (base64): {filename} ({len(image_bytes)} bytes)")
    
    return ImageUploadResponse(
        url=f"{BASE_URL}/static/{filename}",
        filename=filename,
        size=len(image_bytes),
        mime_type=mime_type,
    )


@router.delete("/static/{filename}")
async def delete_image(filename: str):
    """حذف صورة من التخزين المحلي"""
    # Security: prevent directory traversal
    if '..' in filename or '/' in filename or '\\' in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    file_path = IMAGES_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Image not found")
    
    try:
        file_path.unlink()
        logger.info(f"Image deleted: {filename}")
        return {"message": "Image deleted successfully"}
    except Exception as e:
        logger.error(f"Failed to delete image: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete image")


@router.get("/list")
async def list_images():
    """عرض كل الصور المخزنة محلياً"""
    images = []
    for file_path in IMAGES_DIR.glob("*"):
        if file_path.is_file():
            stat = file_path.stat()
            images.append({
                "filename": file_path.name,
                "url": f"{BASE_URL}/static/{file_path.name}",
                "size": stat.st_size,
                "created_at": stat.st_ctime,
            })
    return {"images": images, "total": len(images)}
