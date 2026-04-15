"""
GitHub Image Upload API
Uploads images directly to GitHub repository for use with Amazon listings
"""
import os
import base64
import uuid
import time
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
import requests
from loguru import logger

router = APIRouter()


class GitHubUploadResponse(BaseModel):
    success: bool
    github_url: str = ""
    message: str = ""
    error: str = ""


@router.post("/upload-to-github", response_model=GitHubUploadResponse)
async def upload_image_to_github(file: UploadFile = File(...)):
    """
    رفع صورة مباشرة على GitHub repository
    """
    # GitHub config from environment
    gh_token = os.getenv("GITHUB_TOKEN", "")
    gh_owner = os.getenv("GITHUB_OWNER", "")
    gh_repo = os.getenv("GITHUB_REPO", "")
    gh_branch = os.getenv("GITHUB_BRANCH", "main")

    if not all([gh_token, gh_owner, gh_repo]):
        return GitHubUploadResponse(
            success=False,
            error="GitHub configuration missing. Check .env file.",
        )

    # Validate file type
    allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp', 'image/gif', 'image/bmp']
    if file.content_type not in allowed_types:
        return GitHubUploadResponse(
            success=False,
            error=f"Invalid file type. Allowed: {', '.join(allowed_types)}",
        )

    # Read file
    content = await file.read()
    if len(content) > 5 * 1024 * 1024:  # 5MB max
        return GitHubUploadResponse(
            success=False,
            error="File size must be less than 5MB",
        )

    # Generate unique filename
    ext = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
    filename = f"{uuid.uuid4().hex}.{ext}"
    
    # Encode to base64
    img_base64 = base64.b64encode(content).decode('utf-8')

    # Upload to GitHub API
    gh_url = f"https://api.github.com/repos/{gh_owner}/{gh_repo}/contents/images/{filename}"
    
    try:
        gh_resp = requests.put(
            gh_url,
            headers={
                "Authorization": f"Bearer {gh_token}",
                "Accept": "application/vnd.github.v3+json",
            },
            json={
                "message": f"Upload {filename} via Crazy Lister",
                "content": img_base64,
                "branch": gh_branch,
            },
            timeout=30,
        )

        if gh_resp.status_code in (200, 201):
            raw_url = f"https://raw.githubusercontent.com/{gh_owner}/{gh_repo}/{gh_branch}/images/{filename}"
            logger.info(f"✅ Image uploaded to GitHub: {raw_url}")
            return GitHubUploadResponse(
                success=True,
                github_url=raw_url,
                message="تم رفع الصورة بنجاح على GitHub",
            )
        else:
            return GitHubUploadResponse(
                success=False,
                error=f"GitHub API error: {gh_resp.status_code} - {gh_resp.text[:200]}",
            )

    except Exception as e:
        logger.error(f"GitHub upload failed: {e}")
        return GitHubUploadResponse(
            success=False,
            error=str(e),
        )
