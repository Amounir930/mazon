"""
Automation API Routes
=====================
APIs لتشغيل نظام الأتمتة والتحسينات التلقائية
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional, List
import json

from app.database import get_db
from app.models.product import Product
from app.models.seller import Seller
from app.services.automation_engine import get_automation_engine, AutomationEngine, AutomationStatus
from app.services.rules_engine import get_rules_engine
from loguru import logger

router = APIRouter(prefix="/api/v1/automation", tags=["automation"])


# ===== Validation Endpoints =====

@router.post("/validate/{product_id}")
async def validate_product(
    product_id: str,
    db: Session = Depends(get_db),
    engine: AutomationEngine = Depends(get_automation_engine),
):
    """
    التحقق الكامل من منتج واحد
    
    Returns:
        - valid: هل المنتج صالح
        - errors: قائمة الأخطاء (ترفع الإرسال)
        - warnings: قائمة التحذيرات (إنصاحات)
        - applied_defaults: القيم الافتراضية المطبقة
    """
    try:
        # الحصول على المنتج
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # تحويل البيانات
        product_data = {
            'sku': product.sku,
            'name': product.name,
            'price': float(product.price) if product.price else None,
            'cost': float(product.cost) if product.cost else None,
            'product_type': product.product_type,
            'condition': product.condition,
            'fulfillment_channel': product.fulfillment_channel,
            'description': product.description,
            'brand': product.brand,
            'bullet_points': product.bullet_points if isinstance(product.bullet_points, list) else [],
            'main_image': product.main_image,
            'images': product.images if isinstance(product.images, list) else [],
        }
        
        # التحقق
        result = engine.validate_product_full(product_data)
        
        logger.info(f"Validation completed for product {product_id}: valid={result.valid}")
        
        return result.to_dict()
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating product {product_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate-batch")
async def validate_batch(
    product_ids: List[str],
    db: Session = Depends(get_db),
    engine: AutomationEngine = Depends(get_automation_engine),
):
    """
    التحقق من مجموعة من المنتجات
    """
    results = {}
    
    for product_id in product_ids:
        try:
            product = db.query(Product).filter(Product.id == product_id).first()
            if product:
                product_data = {
                    'sku': product.sku,
                    'name': product.name,
                    'price': float(product.price) if product.price else None,
                    'cost': float(product.cost) if product.cost else None,
                    'product_type': product.product_type,
                    'condition': product.condition,
                    'fulfillment_channel': product.fulfillment_channel,
                }
                
                result = engine.validate_product_full(product_data)
                results[product_id] = {
                    'valid': result.valid,
                    'error_count': len(result.errors),
                    'warning_count': len(result.warnings),
                }
        except Exception as e:
            results[product_id] = {'error': str(e)}
    
    return {
        'total': len(product_ids),
        'results': results,
    }


# ===== Enhancement Endpoints =====

@router.post("/enhance/{product_id}")
async def enhance_product(
    product_id: str,
    auto_apply: bool = False,
    db: Session = Depends(get_db),
    engine: AutomationEngine = Depends(get_automation_engine),
):
    """
    تحسين منتج واحد تلقائياً
    
    Parameters:
        - auto_apply: هل يتم حفظ التحسينات فوراً
    
    Returns:
        - changes: التغييرات المقترحة/المطبقة
        - enhanced_data: البيانات بعد التحسين
        - validation_result: نتيجة التحقق بعد التحسين
    """
    try:
        # الحصول على المنتج
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # تحويل البيانات
        product_data = {
            'sku': product.sku,
            'name': product.name,
            'price': float(product.price) if product.price else None,
            'cost': float(product.cost) if product.cost else None,
            'product_type': product.product_type,
            'condition': product.condition,
            'fulfillment_channel': product.fulfillment_channel,
            'description': product.description,
            'brand': product.brand,
            'bullet_points': product.bullet_points if isinstance(product.bullet_points, list) else [],
            'main_image': product.main_image,
            'images': product.images if isinstance(product.images, list) else [],
            'number_of_items': product.number_of_items,
        }
        
        # التحسين
        result = engine.enhance_product(product_data, auto_apply=auto_apply)
        
        # إذا كان auto_apply، حفظ التغييرات
        if auto_apply:
            for field, value in result.enhanced_data.items():
                if hasattr(product, field):
                    setattr(product, field, value)
            
            db.commit()
            logger.info(f"Enhanced product {product_id} and saved changes")
        
        return {
            'changes': {k: v for k, v in result.changes.items()},
            'enhanced_data': result.enhanced_data,
            'validation': result.validation_result.to_dict(),
            'applied': auto_apply,
            'changes_count': len(result.changes),
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error enhancing product {product_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/enhance-batch")
async def enhance_batch(
    product_ids: List[str],
    auto_apply: bool = False,
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
    engine: AutomationEngine = Depends(get_automation_engine),
):
    """
    تحسين مجموعة من المنتجات
    """
    results = {
        'total': len(product_ids),
        'succeeded': 0,
        'failed': 0,
        'changes': [],
    }
    
    for product_id in product_ids:
        try:
            product = db.query(Product).filter(Product.id == product_id).first()
            if product:
                product_data = {
                    'sku': product.sku,
                    'name': product.name,
                    'price': float(product.price) if product.price else None,
                    'cost': float(product.cost) if product.cost else None,
                    'product_type': product.product_type,
                    'condition': product.condition,
                    'fulfillment_channel': product.fulfillment_channel,
                    'description': product.description,
                    'brand': product.brand,
                    'bullet_points': product.bullet_points if isinstance(product.bullet_points, list) else [],
                    'main_image': product.main_image,
                    'images': product.images if isinstance(product.images, list) else [],
                }
                
                enhancement = engine.enhance_product(product_data, auto_apply=auto_apply)
                
                if auto_apply and enhancement.changes:
                    for field, value in enhancement.enhanced_data.items():
                        if hasattr(product, field):
                            setattr(product, field, value)
                    db.commit()
                
                results['succeeded'] += 1
                results['changes'].append({
                    'sku': product.sku,
                    'changes_count': len(enhancement.changes),
                    'changes': enhancement.changes,
                })
        
        except Exception as e:
            results['failed'] += 1
            logger.error(f"Error enhancing product {product_id}: {e}")
    
    return results


# ===== Readiness Check Endpoints =====

@router.get("/check-ready/{product_id}")
async def check_ready_for_submission(
    product_id: str,
    db: Session = Depends(get_db),
    engine: AutomationEngine = Depends(get_automation_engine),
):
    """
    فحص جاهزية المنتج للإرسال
    
    Returns:
        - ready: هل المنتج جاهز للإرسال
        - issues: المشاكل التي تحتاج حل
        - suggestions: الإجراءات المقترحة
    """
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        product_data = {
            'sku': product.sku,
            'name': product.name,
            'price': float(product.price) if product.price else None,
            'cost': float(product.cost) if product.cost else None,
            'product_type': product.product_type,
            'condition': product.condition,
            'fulfillment_channel': product.fulfillment_channel,
            'description': product.description,
            'brand': product.brand,
            'bullet_points': product.bullet_points if isinstance(product.bullet_points, list) else [],
            'main_image': product.main_image,
            'images': product.images if isinstance(product.images, list) else [],
        }
        
        result = engine.check_ready_for_submission(product_data)
        
        logger.info(f"Readiness check for product {product_id}: ready={result['ready']}")
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking readiness for product {product_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===== Export Endpoints =====

@router.get("/export/{product_id}/amazon-format")
async def export_for_amazon(
    product_id: str,
    db: Session = Depends(get_db),
    engine: AutomationEngine = Depends(get_automation_engine),
):
    """
    تحويل المنتج إلى صيغة جاهزة للإرسال لـ Amazon
    """
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        product_data = {
            'sku': product.sku,
            'name': product.name,
            'price': float(product.price) if product.price else None,
            'product_type': product.product_type,
            'condition': product.condition,
            'fulfillment_channel': product.fulfillment_channel,
            'description': product.description,
            'brand': product.brand,
            'bullet_points': product.bullet_points if isinstance(product.bullet_points, list) else [],
            'main_image': product.main_image,
            'images': product.images if isinstance(product.images, list) else [],
            'number_of_items': product.number_of_items,
            'dimensions': product.dimensions if isinstance(product.dimensions, dict) else {},
            'weight': float(product.weight) if product.weight else None,
            'weight_unit': product.weight_unit or 'KG',
        }
        
        amazon_format = engine.export_for_amazon(product_data)
        
        return amazon_format
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting product {product_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===== Rules Info Endpoints =====

@router.get("/rules/product-types")
async def get_product_types(
    rules_engine = Depends(get_rules_engine),
):
    """
    الحصول على قائمة أنواع المنتجات المدعومة
    """
    categories = rules_engine.category_rules.get('categories', {})
    
    return {
        'total': len(categories),
        'categories': [
            {
                'id': cat_id,
                'name': cat_info.get('arabic_name'),
                'required_attributes': cat_info.get('required_attributes', []),
            }
            for cat_id, cat_info in categories.items()
        ]
    }


@router.get("/rules/category/{category_id}")
async def get_category_rules(
    category_id: str,
    rules_engine = Depends(get_rules_engine),
):
    """
    الحصول على قواعس فئة معينة
    """
    category_info = rules_engine.get_category_info(category_id)
    
    if not category_info:
        raise HTTPException(status_code=404, detail="Category not found")
    
    return {
        'category_id': category_id,
        'arabic_name': category_info.get('arabic_name'),
        'required_attributes': category_info.get('required_attributes', []),
        'optional_attributes': category_info.get('optional_attributes', []),
        'typical_bullet_points': category_info.get('typical_bullet_points', []),
        'min_margin_percent': category_info.get('min_margin_percent'),
        'price_range': category_info.get('price_range_egp'),
    }


@router.get("/rules/validation-errors")
async def get_validation_errors(
    rules_engine = Depends(get_rules_engine),
):
    """
    الحصول على قائمة أنواع أخطاء التحقق الممكنة
    """
    errors = rules_engine.validation_rules['validation']['blocking_errors']
    
    return {
        'total': len(errors),
        'errors': [
            {
                'field': err['field'],
                'rule': err['rule'],
                'message': err['message'],
                'code': err['code'],
            }
            for err in errors
        ]
    }


# ===== Automation Status Endpoint =====

@router.get("/status")
async def get_automation_status(
    engine: AutomationEngine = Depends(get_automation_engine),
):
    """
    الحصول على حالة محرك الأتمتة
    """
    return {
        'status': engine.status.value,
        'tasks_count': len(engine.tasks),
        'active_tasks': sum(1 for t in engine.tasks.values() if t.status == AutomationStatus.RUNNING),
    }
