"""
Bulk Upload API
CSV/Excel file uploads
"""
import os
import io
import json
from pathlib import Path
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from loguru import logger
import pandas as pd

from app.database import get_db
from app.models.product import Product
from app.config import get_settings

router = APIRouter()
settings = get_settings()


@router.post("/upload")
async def bulk_upload_products(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload CSV or Excel file"""
    if not file.filename or not file.filename.endswith(('.csv', '.xlsx')):
        raise HTTPException(status_code=400, detail="Only CSV and Excel files are supported")

    # Save file to uploads folder
    upload_dir = Path(settings.UPLOAD_DIR)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = upload_dir / f"bulk_{timestamp}_{file.filename}"

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    try:
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(content))
        else:
            df = pd.read_excel(io.BytesIO(content))

        required = ['sku', 'name', 'price']
        missing = [col for col in required if col not in df.columns]
        if missing:
            raise HTTPException(status_code=400, detail=f"Missing columns: {', '.join(missing)}")

        created_count = 0
        errors = []

        for index, row in df.iterrows():
            try:
                product = Product(
                    sku=str(row['sku']),
                    name=str(row['name']),
                    price=float(row['price']),
                    quantity=int(row.get('quantity', 0)),
                    category=str(row.get('category', '')),
                    brand=str(row.get('brand', '')),
                    description=str(row.get('description', '')),
                    bullet_points=json.dumps([]),
                    images=json.dumps([]),
                    attributes=json.dumps({}),
                )
                db.add(product)
                created_count += 1
            except Exception as e:
                errors.append(f"Row {index + 1}: {str(e)}")

        db.commit()
        logger.info(f"Bulk uploaded {created_count} products")

        return {
            "message": f"Uploaded {created_count} products",
            "created_count": created_count,
            "errors": errors[:10],
            "file_path": str(file_path),
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Bulk upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
