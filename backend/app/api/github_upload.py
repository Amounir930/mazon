"""
GitHub & Cloudinary Image Upload API
Uploads images for use with Amazon listings.

Strategy:
  1. Cloudinary — fast, reliable, CDN-backed (primary)
  2. GitHub — fallback if Cloudinary not configured
"""
import os
import re
import base64
import uuid
from fastapi import APIRouter, UploadFile, File
from pydantic import BaseModel
import httpx
from loguru import logger

router = APIRouter()


class ImageUploadResponse(BaseModel):
    success: bool
    image_url: str = ""
    message: str = ""
    error: str = ""


# ==================== Cloudinary Upload ====================

async def _upload_to_cloudinary(content: bytes, filename: str) -> ImageUploadResponse:
    """
    Upload image to Cloudinary (unsigned preset).
    Returns the secure_url on success.
    """
    cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME", "").strip()
    upload_preset = os.getenv("CLOUDINARY_UPLOAD_PRESET", "").strip()

    if not cloud_name or not upload_preset:
        return ImageUploadResponse(success=False, error="Cloudinary not configured")

    # Cloudinary unsigned upload endpoint
    upload_url = f"https://api.cloudinary.com/v1_1/{cloud_name}/image/upload"

    try:
        # Generate unique public_id
        public_id = f"crazy_lister/{uuid.uuid4().hex[:12]}"

        data = {
            "upload_preset": upload_preset,  # Unsigned preset (no signature needed)
            "public_id": public_id,
        }

        files = {"file": (filename, content, "image/jpeg")}

        async with httpx.AsyncClient(timeout=httpx.Timeout(15.0, connect=15.0, read=120.0, write=120.0)) as client:
            resp = await client.post(upload_url, data=data, files=files)

        if resp.status_code == 200:
            result = resp.json()
            secure_url = result.get("secure_url", "")
            if secure_url:
                logger.info(f"✅ Cloudinary upload: {secure_url[:80]}")
                return ImageUploadResponse(
                    success=True,
                    image_url=secure_url,
                    message="تم رفع الصورة على Cloudinary",
                )
            return ImageUploadResponse(success=False, error="No URL returned from Cloudinary")
        else:
            try:
                error_msg = resp.json().get("error", {}).get("message", resp.text[:200])
            except Exception:
                error_msg = resp.text[:200]
            logger.error(f"❌ Cloudinary {resp.status_code}: {error_msg}")
            return ImageUploadResponse(success=False, error=f"Cloudinary error: {error_msg}")

    except httpx.ConnectTimeout:
        return ImageUploadResponse(success=False, error="Cloudinary connection timeout")
    except Exception as e:
        logger.error(f"Cloudinary upload failed: {e}")
        return ImageUploadResponse(success=False, error=str(e))


# ==================== GitHub Upload ====================

async def _upload_to_github(content: bytes, filename: str) -> ImageUploadResponse:
    """
    Upload image to GitHub repository via API.
    Uses UUID filename — no need to check if file exists first.
    """
    gh_token = os.getenv("GITHUB_TOKEN", "").strip()
    gh_owner = os.getenv("GITHUB_OWNER", "").strip()
    gh_repo = os.getenv("GITHUB_REPO", "").strip()
    gh_branch = os.getenv("GITHUB_BRANCH", "main").strip()

    if not all([gh_token, gh_owner, gh_repo]):
        return ImageUploadResponse(success=False, error="GitHub not configured")

    # Encode to base64
    img_base64 = base64.b64encode(content).decode('utf-8')

    # GitHub API URL
    gh_url = f"https://api.github.com/repos/{gh_owner}/{gh_repo}/contents/images/{filename}"

    # Build request body — branch always included
    body = {
        "message": f"Upload {filename} via Crazy Lister",
        "content": img_base64,
        "branch": gh_branch,
    }

    headers = {
        "Authorization": f"Bearer {gh_token}",
        "Accept": "application/vnd.github.v3+json",
    }

    try:
        # PUT directly — UUID filename guarantees no conflicts, no GET needed
        async with httpx.AsyncClient(timeout=httpx.Timeout(15.0, connect=15.0, read=180.0, write=180.0)) as client:
            resp = await client.put(gh_url, headers=headers, json=body)

        if resp.status_code in (200, 201):
            raw_url = f"https://raw.githubusercontent.com/{gh_owner}/{gh_repo}/{gh_branch}/images/{filename}"
            logger.info(f"✅ GitHub upload: {raw_url}")
            return ImageUploadResponse(
                success=True,
                image_url=raw_url,
                message="تم رفع الصورة على GitHub",
            )
        else:
            try:
                error_data = resp.json()
                error_msg = error_data.get("message", resp.text[:200])
            except Exception:
                error_msg = resp.text[:200]
            logger.error(f"❌ GitHub {resp.status_code}: {error_msg}")
            return ImageUploadResponse(success=False, error=f"GitHub error: {error_msg}")

    except httpx.ConnectTimeout:
        return ImageUploadResponse(success=False, error="GitHub connection timeout")
    except Exception as e:
        logger.error(f"GitHub upload failed: {e}")
        return ImageUploadResponse(success=False, error=str(e))


# ==================== Main Endpoint ====================

@router.post("/upload-to-github", response_model=ImageUploadResponse)
async def upload_image(file: UploadFile = File(...)):
    """
    رفع صورة — يحاول Cloudinary أولاً، ثم GitHub كـ fallback.
    Endpoint name kept as /upload-to-github for frontend compatibility.
    """
    # Validate file type
    allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp', 'image/gif', 'image/bmp']
    if file.content_type not in allowed_types:
        return ImageUploadResponse(
            success=False,
            error=f"نوع الملف غير مدعوم. المسموح: {', '.join(allowed_types)}",
        )

    # Read file content
    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        return ImageUploadResponse(success=False, error="حجم الملف يجب أن يكون أقل من 5MB")

    # Generate safe filename
    ext = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
    safe_ext = re.sub(r'[^a-zA-Z0-9]', '', ext).lower()
    filename = f"{uuid.uuid4().hex}.{safe_ext if safe_ext else 'jpg'}"

    logger.info(f"📤 Upload request: {filename} ({len(content):,} bytes)")

    # Strategy 1: Try Cloudinary first (faster, CDN-backed)
    result = await _upload_to_cloudinary(content, filename)
    if result.success:
        return result

    logger.warning(f"⚠️ Cloudinary failed ({result.error}), trying GitHub...")

    # Strategy 2: Fallback to GitHub
    result = await _upload_to_github(content, filename)
    return result
