"""
Rules Engine - محرك تطبيق القواعس
====================================
يقرأ ملفات YAML ويطبق القواعس على المنتجات تلقائياً
"""

import yaml
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from loguru import logger
from decimal import Decimal

# ===== Data Models =====

class SeverityLevel(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationIssue:
    """مشكلة تحقق واحدة"""
    field: str
    message: str
    code: str
    severity: SeverityLevel
    value: Any = None
    suggestion: Optional[str] = None


@dataclass
class ValidationResult:
    """نتيجة التحقق الكاملة"""
    valid: bool = True
    errors: List[ValidationIssue] = field(default_factory=list)
    warnings: List[ValidationIssue] = field(default_factory=list)
    applied_defaults: Dict[str, Any] = field(default_factory=dict)
    
    def is_blocking(self) -> bool:
        """هل هناك أخطاء توقف الإرسال؟"""
        return len(self.errors) > 0
    
    def to_dict(self) -> Dict:
        return {
            "valid": self.valid,
            "blocking": self.is_blocking(),
            "errors": [
                {
                    "field": e.field,
                    "message": e.message,
                    "code": e.code,
                    "severity": e.severity.value,
                    "suggestion": e.suggestion,
                }
                for e in self.errors
            ],
            "warnings": [
                {
                    "field": e.field,
                    "message": e.message,
                    "code": e.code,
                    "severity": e.severity.value,
                    "suggestion": e.suggestion,
                }
                for e in self.warnings
            ],
            "applied_defaults": self.applied_defaults,
        }


# ===== Rules Engine =====

class RulesEngine:
    """محرك تطبيق القواعس - يقرأ ملفات YAML ويطبقها على المنتجات"""
    
    def __init__(self, rules_dir: Optional[Path] = None):
        """تحميل ملفات القواعس من المجلد"""
        if rules_dir is None:
            rules_dir = Path(__file__).parent.parent.parent.parent / "rules"
        
        self.rules_dir = rules_dir
        logger.info(f"Loading rules from: {self.rules_dir}")
        
        # تحميل ملفات القواعس
        self.product_rules = self._load_yaml("product_rules.yaml")
        self.validation_rules = self._load_yaml("validation_rules.yaml")
        self.optimization_rules = self._load_yaml("optimization_rules.yaml")
        self.category_rules = self._load_yaml("category_rules.yaml")
        
        logger.success("Rules loaded successfully")
    
    def _load_yaml(self, filename: str) -> Dict[str, Any]:
        """قراءة ملف YAML"""
        path = self.rules_dir / filename
        if not path.exists():
            raise FileNotFoundError(f"Rules file not found: {path}")
        
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            logger.debug(f"Loaded rules file: {filename}")
            return data
    
    # ===== PHASE 1: Apply Defaults =====
    
    def apply_defaults(self, product_data: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """تطبيق القيم الافتراضية على البيانات الناقصة"""
        applied = {}
        product_copy = product_data.copy()
        
        defaults = self.product_rules['product_creation']['defaults']
        
        for field, default_value in defaults.items():
            if field not in product_copy or product_copy[field] is None or product_copy[field] == "":
                product_copy[field] = default_value
                applied[field] = default_value
                logger.debug(f"Applied default: {field} = {default_value}")
        
        return product_copy, applied
    
    # ===== PHASE 2: Validate =====
    
    def validate_product(self, product_data: Dict[str, Any]) -> ValidationResult:
        """التحقق من بيانات المنتج بناءً على القواعس"""
        result = ValidationResult()
        
        # تحقق من الحقول المطلوبة
        required = self.product_rules['product_creation']['required_fields']
        for field in required:
            if field not in product_data or product_data.get(field) is None:
                result.errors.append(
                    ValidationIssue(
                        field=field,
                        message=f"الحقل '{field}' مطلوب ولم يتم تحديده",
                        code=f"ERR_MISSING_{field.upper()}",
                        severity=SeverityLevel.ERROR,
                    )
                )
        
        # تحقق من حدود الحقول
        self._validate_field_limits(product_data, result)
        
        # تحقق من القيم المسموحة
        self._validate_enums(product_data, result)
        
        # تحقق من الأسعار
        self._validate_pricing(product_data, result)
        
        # تحقق من الصور
        self._validate_images(product_data, result)
        
        # تحذيرات إضافية
        self._check_warnings(product_data, result)
        
        result.valid = len(result.errors) == 0
        return result
    
    def _validate_field_limits(self, product_data: Dict, result: ValidationResult):
        """التحقق من حدود الحقول (الطول، الطول، إلخ)"""
        limits = self.product_rules['product_creation']['field_limits']
        
        for field, limit_config in limits.items():
            if field not in product_data:
                continue
            
            value = product_data.get(field)
            
            # Check string length
            if isinstance(value, str):
                if 'min_length' in limit_config and len(value) < limit_config['min_length']:
                    result.errors.append(
                        ValidationIssue(
                            field=field,
                            message=f"الحد الأدنى للطول: {limit_config['min_length']} أحرف",
                            code=f"ERR_{field.upper()}_TOO_SHORT",
                            severity=SeverityLevel.ERROR,
                            value=value,
                        )
                    )
                
                if 'max_length' in limit_config and len(value) > limit_config['max_length']:
                    result.errors.append(
                        ValidationIssue(
                            field=field,
                            message=f"الحد الأقصى للطول: {limit_config['max_length']} حرف",
                            code=f"ERR_{field.upper()}_TOO_LONG",
                            severity=SeverityLevel.ERROR,
                            value=value,
                        )
                    )
                
                # Check pattern if exists
                if 'pattern' in limit_config:
                    if not re.match(limit_config['pattern'], value):
                        result.errors.append(
                            ValidationIssue(
                                field=field,
                                message=f"الصيغة غير صحيحة. يجب أن تتطابق مع: {limit_config['pattern']}",
                                code=f"ERR_{field.upper()}_INVALID_FORMAT",
                                severity=SeverityLevel.ERROR,
                                value=value,
                            )
                        )
            
            # Check numeric ranges
            if isinstance(value, (int, float)):
                if 'min_value' in limit_config and value < limit_config['min_value']:
                    result.errors.append(
                        ValidationIssue(
                            field=field,
                            message=f"القيمة الدنيا: {limit_config['min_value']}",
                            code=f"ERR_{field.upper()}_TOO_LOW",
                            severity=SeverityLevel.ERROR,
                            value=value,
                        )
                    )
                
                if 'max_value' in limit_config and value > limit_config['max_value']:
                    result.errors.append(
                        ValidationIssue(
                            field=field,
                            message=f"القيمة العليا: {limit_config['max_value']}",
                            code=f"ERR_{field.upper()}_TOO_HIGH",
                            severity=SeverityLevel.ERROR,
                            value=value,
                        )
                    )
    
    def _validate_enums(self, product_data: Dict, result: ValidationResult):
        """التحقق من القيم المسموحة"""
        valid_values = self.validation_rules['validation']['valid_values']
        
        # Check condition
        if 'condition' in product_data:
            if product_data['condition'] not in valid_values.get('condition', []):
                result.errors.append(
                    ValidationIssue(
                        field='condition',
                        message=f"حالة المنتج غير صحيحة. المسموح: {', '.join(valid_values['condition'])}",
                        code="ERR_INVALID_CONDITION",
                        severity=SeverityLevel.ERROR,
                        value=product_data['condition'],
                    )
                )
        
        # Check fulfillment channel
        if 'fulfillment_channel' in product_data:
            if product_data['fulfillment_channel'] not in valid_values.get('fulfillment_channel', []):
                result.errors.append(
                    ValidationIssue(
                        field='fulfillment_channel',
                        message="قناة الشحن يجب أن تكون: MFN أو AFN",
                        code="ERR_INVALID_FULFILLMENT",
                        severity=SeverityLevel.ERROR,
                        value=product_data['fulfillment_channel'],
                    )
                )
    
    def _validate_pricing(self, product_data: Dict, result: ValidationResult):
        """التحقق من الأسعار"""
        price = product_data.get('price')
        cost = product_data.get('cost')
        
        if price is None or price <= 0:
            result.errors.append(
                ValidationIssue(
                    field='price',
                    message="السعر يجب أن يكون موجب وأكبر من صفر",
                    code="ERR_INVALID_PRICE",
                    severity=SeverityLevel.ERROR,
                    value=price,
                )
            )
        
        # Check margin
        if cost and cost > 0:
            margin = ((price - cost) / cost) * 100
            min_margin = self.product_rules['product_creation']['pricing_rules']['min_margin_percent']
            
            if margin < min_margin:
                result.warnings.append(
                    ValidationIssue(
                        field='price',
                        message=f"الهامش منخفض جداً ({margin:.1f}%). الحد الأدنى الموصى به: {min_margin}%",
                        code="WARN_LOW_MARGIN",
                        severity=SeverityLevel.WARNING,
                        value=price,
                        suggestion=f"اجعل السعر: {cost * (1 + min_margin/100):.2f}",
                    )
                )
    
    def _validate_images(self, product_data: Dict, result: ValidationResult):
        """التحقق من الصور"""
        images = product_data.get('images', [])
        main_image = product_data.get('main_image')
        
        if not main_image:
            result.errors.append(
                ValidationIssue(
                    field='main_image',
                    message="الصورة الرئيسية مطلوبة",
                    code="ERR_NO_MAIN_IMAGE",
                    severity=SeverityLevel.ERROR,
                )
            )
        
        image_limits = self.product_rules['product_creation']['field_limits']['images']
        
        if images and len(images) > image_limits['max_count']:
            result.warnings.append(
                ValidationIssue(
                    field='images',
                    message=f"عدد الصور أكثر من المسموح ({image_limits['max_count']})",
                    code="WARN_TOO_MANY_IMAGES",
                    severity=SeverityLevel.WARNING,
                )
            )
    
    def _check_warnings(self, product_data: Dict, result: ValidationResult):
        """فحص التحذيرات الإضافية"""
        warnings = self.validation_rules['validation']['warnings']
        
        for warn_config in warnings:
            field = warn_config['field']
            rule = warn_config['rule']
            value = product_data.get(field)
            
            # Missing field
            if rule == 'missing' and (value is None or value == "" or value == []):
                result.warnings.append(
                    ValidationIssue(
                        field=field,
                        message=warn_config['message'],
                        code=warn_config['code'],
                        severity=SeverityLevel.WARNING,
                    )
                )
            
            # Too short
            if rule == 'too_short' and value:
                threshold = warn_config.get('threshold', 100)
                word_count = len(str(value).split())
                if word_count < threshold:
                    result.warnings.append(
                        ValidationIssue(
                            field=field,
                            message=warn_config['message'],
                            code=warn_config['code'],
                            severity=SeverityLevel.WARNING,
                            value=f"{word_count} كلمة",
                        )
                    )
            
            # Few images
            if rule == 'too_few':
                images = product_data.get('images', [])
                threshold = warn_config.get('threshold', 1)
                if len(images) <= threshold:
                    result.warnings.append(
                        ValidationIssue(
                            field=field,
                            message=warn_config['message'],
                            code=warn_config['code'],
                            severity=SeverityLevel.WARNING,
                            value=f"{len(images)} صورة",
                        )
                    )
    
    # ===== PHASE 3: Get Category Info =====
    
    def get_category_info(self, product_type: str) -> Optional[Dict[str, Any]]:
        """الحصول على معلومات الفئة"""
        categories = self.category_rules.get('categories', {})
        return categories.get(product_type)
    
    # ===== PHASE 4: Auto-Enhancements (Preview) =====
    
    def suggest_enhancements(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """اقتراح تحسينات تلقائية بدون تطبيقها"""
        suggestions = {}
        
        # Suggest price adjustment
        price = product_data.get('price')
        cost = product_data.get('cost')
        if price and cost and cost > 0:
            margin = ((price - cost) / cost) * 100
            if margin < 15:
                suggested_price = cost * 1.15
                suggestions['price'] = {
                    'current': price,
                    'suggested': suggested_price,
                    'reason': 'تحسين الهامش إلى 15%',
                }
        
        # Suggest compare price
        if price and not product_data.get('compare_price'):
            suggestions['compare_price'] = {
                'current': None,
                'suggested': price * 1.20,
                'reason': 'تحديد سعر المقارنة (20% أعلى)',
            }
        
        return suggestions


# ===== Helper Functions =====

def _enhance_text(text: str) -> str:
    """تحسين نص بسيط"""
    # Remove extra spaces
    text = ' '.join(text.split())
    # Capitalize first letter
    if text:
        text = text[0].upper() + text[1:]
    return text


# ===== Global Instance =====
_engine: Optional[RulesEngine] = None

def get_rules_engine() -> RulesEngine:
    """الحصول على instance من محرك القواعس"""
    global _engine
    if _engine is None:
        _engine = RulesEngine()
    return _engine
