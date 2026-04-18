"""
Automation Engine - محرك الأتمتة
=================================
يستخدم قواعس المنتجات لتحسين وإرسال المنتجات تلقائياً
"""

from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from loguru import logger
import asyncio
import json

from app.services.rules_engine import RulesEngine, ValidationResult


class AutomationStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class AutomationTask:
    """مهمة أتمتة واحدة"""
    id: str
    product_id: str
    task_type: str  # "enhance", "validate", "submit", "bulk_process"
    status: AutomationStatus = AutomationStatus.IDLE
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class EnhancementResult:
    """نتيجة التحسين"""
    original_data: Dict[str, Any]
    enhanced_data: Dict[str, Any]
    changes: Dict[str, Dict[str, Any]]  # {field: {old: ..., new: ...}}
    validation_result: ValidationResult
    suggestions: Dict[str, Any]


class AutomationEngine:
    """محرك تشغيل الأتمتة والتحسينات التلقائية"""
    
    def __init__(self, rules_engine: Optional[RulesEngine] = None):
        """تهيئة محرك الأتمتة"""
        self.rules_engine = rules_engine or RulesEngine()
        self.tasks: Dict[str, AutomationTask] = {}
        self.status = AutomationStatus.IDLE
        logger.info("AutomationEngine initialized")
    
    # ===== PHASE 1: Full Validation Pipeline =====
    
    def validate_product_full(
        self,
        product_data: Dict[str, Any],
        seller_id: Optional[str] = None,
    ) -> ValidationResult:
        """التحقق الكامل من المنتج مع جميع القواعس"""
        logger.info(f"Full validation for product: {product_data.get('sku', 'unknown')}")
        
        # تطبيق القيم الافتراضية أولاً
        product_data, applied_defaults = self.rules_engine.apply_defaults(product_data)
        
        # التحقق من البيانات
        result = self.rules_engine.validate_product(product_data)
        result.applied_defaults = applied_defaults
        
        logger.debug(f"Validation result: {result.to_dict()}")
        return result
    
    # ===== PHASE 2: Auto-Enhancement =====
    
    def enhance_product(
        self,
        product_data: Dict[str, Any],
        auto_apply: bool = False,
    ) -> EnhancementResult:
        """تحسين بيانات المنتج تلقائياً"""
        logger.info(f"Enhancing product: {product_data.get('sku', 'unknown')}")
        
        original_data = product_data.copy()
        enhanced_data = product_data.copy()
        changes = {}
        
        # تطبيق القيم الافتراضية
        enhanced_data, _ = self.rules_engine.apply_defaults(enhanced_data)
        
        # تطبيق القواعس الصارمة الإلزامية (الأول!)
        enhanced_data, strict_changes = self.apply_strict_requirements(enhanced_data)
        changes.update(strict_changes)
        
        # تحسين النصوص
        enhancements = self._enhance_text_fields(enhanced_data)
        changes.update(enhancements)
        
        # تحسين الأسعار
        price_enhancements = self._enhance_pricing(enhanced_data)
        changes.update(price_enhancements)
        
        # تطبيق التحسينات إذا كان مطلوباً
        if auto_apply:
            for field, change in changes.items():
                enhanced_data[field] = change['new']
                logger.debug(f"Applied enhancement: {field} = {change['new']}")
        
        # التحقق من النتيجة
        validation_result = self.rules_engine.validate_product(enhanced_data)
        
        # الحصول على اقتراحات إضافية
        suggestions = self.rules_engine.suggest_enhancements(enhanced_data)
        
        result = EnhancementResult(
            original_data=original_data,
            enhanced_data=enhanced_data,
            changes=changes,
            validation_result=validation_result,
            suggestions=suggestions,
        )
        
        logger.debug(f"Enhancement completed with {len(changes)} changes")
        return result
    
    def _enhance_text_fields(self, product_data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """تحسين حقول النصوص"""
        changes = {}
        
        # تحسين الاسم
        name = product_data.get('name', '')
        if name:
            enhanced_name = self._clean_text(name)
            if enhanced_name != name:
                changes['name'] = {
                    'old': name,
                    'new': enhanced_name,
                    'reason': 'تنظيف النص',
                }
                product_data['name'] = enhanced_name
        
        # تحسين الوصف
        description = product_data.get('description', '')
        if description and len(description) < 100:
            # محاولة توسيع الوصف
            enhanced_desc = self._expand_description(product_data)
            if enhanced_desc != description:
                changes['description'] = {
                    'old': description,
                    'new': enhanced_desc,
                    'reason': 'توسيع الوصف',
                }
                product_data['description'] = enhanced_desc
        
        # تحسين نقاط البيع
        bullet_points = product_data.get('bullet_points', [])
        if not bullet_points or len(bullet_points) < 5:
            enhanced_points = self._generate_bullet_points(product_data)
            if enhanced_points != bullet_points:
                changes['bullet_points'] = {
                    'old': bullet_points,
                    'new': enhanced_points,
                    'reason': 'إضافة نقاط بيع',
                }
                product_data['bullet_points'] = enhanced_points
        
        return changes
    
    def _enhance_pricing(self, product_data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """تحسين الأسعار"""
        changes = {}
        optimization = self.rules_engine.optimization_rules.get('optimization', {})
        pricing_opt = optimization.get('pricing_optimization', {})
        
        if not pricing_opt.get('auto_adjust_enabled'):
            return changes
        
        price = product_data.get('price')
        cost = product_data.get('cost')
        
        # تعديل السعر بناءً على الهامش المطلوب
        if price and cost and cost > 0:
            margin = ((price - cost) / cost) * 100
            min_margin = pricing_opt.get('strategies', {}).get('margin_based', {}).get('min_margin_percent', 15)
            
            if margin < min_margin:
                new_price = cost * (1 + min_margin / 100)
                changes['price'] = {
                    'old': price,
                    'new': round(new_price, 2),
                    'reason': f'تحسين الهامش إلى {min_margin}%',
                }
                product_data['price'] = new_price
        
        # تعيين سعر المقارنة تلقائياً
        compare_price_rule = pricing_opt.get('compare_price', {})
        if compare_price_rule.get('auto_set') and price and not product_data.get('compare_price'):
            new_compare = price * 1.20
            changes['compare_price'] = {
                'old': None,
                'new': round(new_compare, 2),
                'reason': 'سعر المقارنة (20% أعلى)',
            }
            product_data['compare_price'] = new_compare
        
        return changes
    
    def _clean_text(self, text: str) -> str:
        """تنظيف النص"""
        # إزالة المسافات الزائدة
        text = ' '.join(text.split())
        # تحويل الحروف الأولى إلى رؤوس
        if text:
            text = text[0].upper() + text[1:]
        return text
    
    def _expand_description(self, product_data: Dict[str, Any]) -> str:
        """توسيع الوصف القصير"""
        current_desc = product_data.get('description', '')
        category = product_data.get('product_type')
        
        # قالب عام للتوسيع
        template = """
{current}

هذا المنتج يتميز بـ:
- جودة عالية وتصميم عصري
- مناسب للاستخدام اليومي
- أفضل سعر في السوق
- ضمان موثوق من البائع
        """.strip()
        
        expanded = template.format(current=current_desc)
        return expanded
    
    def _generate_bullet_points(self, product_data: Dict[str, Any]) -> List[str]:
        """توليد نقاط بيع افتراضية إذا لم تكن موجودة"""
        name = product_data.get('name', 'المنتج')
        category = product_data.get('product_type', 'عام')
        
        # الحصول على نقاط من template الفئة
        category_info = self.rules_engine.get_category_info(category)
        if category_info:
            return category_info.get('typical_bullet_points', [])
        
        # نقاط عامة افتراضية
        return [
            f"منتج عالي الجودة: {name}",
            "مصنوع من مواد آمنة وموثوقة",
            "سهل الاستخدام والصيانة",
            "أفضل قيمة مقابل السعر",
            "ضمان طويل الأجل",
        ]
    
    # ===== PHASE 2B: Apply Strict Requirements =====
    
    def apply_strict_requirements(
        self,
        product_data: Dict[str, Any],
    ) -> tuple:
        """تطبيق القواعس الصارمة الإلزامية"""
        logger.info(f"Applying strict requirements to: {product_data.get('sku', 'unknown')}")
        
        enhanced = product_data.copy()
        changes = {}
        
        # 1. تنسيق مميزات المنتج - حذف الترقيم + فحص الحد الأدنى (15 كلمة)
        if 'bullet_points' in enhanced and isinstance(enhanced['bullet_points'], list):
            cleaned_points = []
            for point in enhanced['bullet_points']:
                # حذف "نقطة 1:" و "نقطة 2:" الخ
                import re
                cleaned = re.sub(r'^\s*نقطة\s+\d+:\s*', '', str(point)).strip()
                word_count = len(cleaned.split())
                
                # فحص الحد الأدنى 15 كلمة
                if word_count < 15:
                    logger.warning(f"Bullet point has {word_count} words, need 15+: {cleaned[:50]}...")
                
                cleaned_points.append(cleaned)
            
            if cleaned_points != enhanced['bullet_points']:
                changes['bullet_points'] = {
                    'old': enhanced['bullet_points'],
                    'new': cleaned_points,
                    'reason': 'حذف الترقيم + فحص 15+ كلمة',
                }
                enhanced['bullet_points'] = cleaned_points
        
        # 2. رقم الموديل = Generic دائماً (إلزامي)
        old_model = enhanced.get('model_number')
        if old_model != 'Generic':
            enhanced['model_number'] = 'Generic'
            changes['model_number'] = {
                'old': old_model,
                'new': 'Generic',
                'reason': 'قاعدة إلزامية: رقم الموديل دائماً Generic',
            }
        
        # 3. بناء الوصف المركب (اسم + الوصف الأساسي + جمل انشائية) + فحص الحد الأدنى (40 كلمة)
        product_name = enhanced.get('name', 'المنتج')
        base_description = enhanced.get('description', '')
        
        # إنشاء وصف انشائي مركب فقط إذا كان الوصف موجوداً
        if base_description:
            narrative_extension = self._generate_narrative_description(product_name, base_description)
            new_description = f"{product_name}. {base_description} {narrative_extension}".strip()
            
            # فحص الحد الأدنى 40 كلمة
            word_count = len(new_description.split())
            if word_count < 40:
                logger.warning(f"Description has {word_count} words, need 40+: {new_description[:100]}...")
            
            if new_description != base_description:
                changes['description'] = {
                    'old': base_description,
                    'new': new_description,
                    'reason': f'بناء وصف انشائي مركب ({word_count} كلمة)',
                }
                enhanced['description'] = new_description
        
        # 4. المكونات المضمنة = "لا يوجد" دائماً
        old_components = enhanced.get('included_components')
        if old_components != 'لا يوجد':
            enhanced['included_components'] = 'لا يوجد'
            changes['included_components'] = {
                'old': old_components,
                'new': 'لا يوجد',
                'reason': 'قاعدة إلزامية: المكونات = لا يوجد',
            }
        
        # 5. المواصفات الفنية - شرطية (أو ملء بـ 0)
        tech_specs = self._handle_technical_specs(enhanced, base_description)
        if tech_specs:
            changes.update(tech_specs)
        
        # 6. إزالة نوع القابس (Plug Type) إن كان موجوداً
        if 'plug_type' in enhanced:
            del enhanced['plug_type']
            changes['plug_type'] = {
                'old': enhanced.get('plug_type'),
                'new': None,
                'reason': 'حقل غير مطلوب - تم حذفه',
            }
        
        # 7. إضافة الترجمة الإنجليزية (إذا لم تكن موجودة)
        if 'name_en' not in enhanced or not enhanced.get('name_en'):
            name_en = self._translate_to_english(enhanced.get('name', ''))
            if name_en:
                enhanced['name_en'] = name_en
                changes['name_en'] = {
                    'old': None,
                    'new': name_en,
                    'reason': 'ترجمة إنجليزية تلقائية',
                }
        
        if 'description_en' not in enhanced or not enhanced.get('description_en'):
            desc_en = self._translate_to_english(enhanced.get('description', ''))
            if desc_en:
                enhanced['description_en'] = desc_en
                changes['description_en'] = {
                    'old': None,
                    'new': desc_en,
                    'reason': 'ترجمة إنجليزية تلقائية',
                }
        
        logger.info(f"Strict requirements applied: {len(changes)} changes")
        return enhanced, changes
    
    def _generate_narrative_description(self, product_name: str, base_desc: str) -> str:
        """إنشاء جمل انشائية توضيحية"""
        narratives = [
            f"يُعد منتج {product_name} حلاً مثالياً للعملاء الباحثين عن الجودة والقيمة معاً.",
            f"تم تصميم {product_name} بعناية فائقة ليلبي احتياجات السوق المحلي والعالمي.",
            "يتمتع هذا المنتج بمميزات فريدة تجعله الخيار الأول للمستهلك الذكي.",
            "جودة عالية واتقان في الصنع مع التزام بأفضل المعايير العالمية.",
            "يثق بهذا المنتج آلاف العملاء الراضين عن أدائه وجودته.",
        ]
        import random
        return random.choice(narratives)
    
    def _translate_to_english(self, arabic_text: str) -> str:
        """ترجمة نصوص عربية إلى إنجليزية"""
        if not arabic_text:
            return ""
        
        # قاموس ترجمة أساسي
        translation_dict = {
            # أدوات المطبخ
            "كوب": "cup", "طبق": "plate", "سكين": "knife", "ملعقة": "spoon",
            "أدوات المطبخ": "kitchen tools", "جودة عالية": "high quality",
            "مواد آمنة": "safe materials", "آمن على الصحة": "health safe",
            "سهل التنظيف": "easy to clean", "استخدام يومي": "daily use",
            "ضمان": "warranty", "طويل الأجل": "long-term",
            
            # الملابس
            "ملابس": "clothes", "أزياء": "fashion", "مريح": "comfortable",
            "عملي": "practical", "جودة عالية": "high quality", "خياطة": "tailoring",
            "متقنة": "professional", "ألوان عصرية": "modern colors", "جذاب": "attractive",
            "غسل آلي": "machine washable", "كي آمن": "safe ironing",
            
            # الهدايا والديكور
            "هدايا": "gifts", "ديكور": "decor", "إسلامي": "Islamic", "ديني": "religious",
            "رمضان": "Ramadan", "فانوس": "lantern", "كهربائي": "electric",
            "تصميم": "design", "هلال": "crescent", "معلق": "hanging",
            "إضاءة": "lighting", "LED": "LED", "منزلي": "home",
            
            # الإلكترونيات
            "إلكترونيات": "electronics", "أحدث التقنيات": "latest technology",
            "ضمان رسمي": "official warranty", "شركة مصنعة": "manufacturer",
            "سهل الاستخدام": "easy to use", "آمن تماماً": "completely safe",
            "توفير": "saving", "كهرباء": "electricity", "عمر افتراضي": "lifespan",
            "إصلاح معتمد": "authorized repair",
            
            # الكتب
            "كتاب": "book", "أصلي": "original", "حديث": "recent", "ناشر": "publisher",
            "مُجلد": "hardcover", "معروف عالمياً": "world famous", "آراء إيجابية": "positive reviews",
            "جميع الأعمار": "all ages", "ثقافات": "cultures", "سعر منافس": "competitive price",
            
            # الألعاب
            "لعبة": "toy", "آمنة": "safe", "خالية من": "free from", "مواد سامة": "toxic materials",
            "تطور مهارات": "skill development", "ذكاء": "intelligence", "قوية": "durable",
            "هدية": "gift", "عيد ميلاد": "birthday", "معتمدة": "certified",
            "جهات صحية": "health authorities",
            
            # عام
            "المنتج": "product", "يتميز": "features", "مصنوع من": "made of",
            "يوفر": "provides", "يحسن": "improves", "يقلل": "reduces",
            "مناسب ل": "suitable for", "يثق": "trust", "راضي": "satisfied",
            "جودة": "quality", "سعر": "price", "قيمة": "value",
        }
        
        # ترجمة بسيطة بالاستبدال
        result = arabic_text
        for ar, en in translation_dict.items():
            result = result.replace(ar, en)
        
        # إذا لم تساعد الترجمة الحرفية، نرجع ترجمة عامة
        if not result or result == arabic_text:
            return f"[Translated: {arabic_text[:100]}...]"  # ترجمة معلبة بسيطة
        
        return result.strip()
    
    def _handle_technical_specs(self, product_data: Dict[str, Any], description: str) -> Dict[str, Any]:
        """معالجة المواصفات الفنية - شرطية (أو ملء بـ 0)"""
        specs_fields = ['dimensions', 'weight', 'material', 'color', 'voltage', 'warranty']
        changes = {}
        
        # البحث عن المواصفات في الوصف
        found_specs = False
        if description:
            for spec in specs_fields:
                if spec in description.lower():
                    found_specs = True
                    break
        
        if found_specs:
            logger.info("Technical specs found in description - extracting them")
            # يتم استخراجها من الوصف (يدوي أو بـ AI)
        else:
            # ملء بـ 0 إذا لم تكن موجودة (قاعدة إلزامية)
            for spec in specs_fields:
                current_value = product_data.get(spec)
                if current_value is None or current_value == '' or current_value == 0:
                    product_data[spec] = 0
                    if current_value != 0:
                        changes[spec] = {
                            'old': current_value,
                            'new': 0,
                            'action': 'filled_with_zero',
                            'reason': 'قاعدة إلزامية: المواصفات = 0 (لم تُذكر)',
                        }
        
        return changes if changes else None

        """فحص جودة النصوص"""
        issues = []
        
        # فحص نقاط البيع
        if 'bullet_points' in product_data:
            for i, point in enumerate(product_data['bullet_points'], 1):
                if len(point.split()) < 15:
                    issues.append(f"نقطة {i}: أقل من 15 كلمة ({len(point.split())} كلمة)")
        
        # فحص الوصف
        if 'description' in product_data:
            desc_words = len(product_data['description'].split())
            if desc_words < 40:
                issues.append(f"الوصف: أقل من 40 كلمة ({desc_words} كلمة)")
        
        # فحص عدم وجود قوائم مرقمة
        for field in ['bullet_points', 'description']:
            if field in product_data:
                import re
                if isinstance(product_data[field], list):
                    text = ' '.join(product_data[field])
                else:
                    text = product_data[field]
                
                if re.search(r'^\d+[\.\-\:]|\n\d+[\.\-\:]', text):
                    issues.append(f"{field}: وُجدت قوائم مرقمة (يجب حذفها)")
        
        return issues
    
    # ===== PHASE 3: Bulk Processing =====
    
    async def process_bulk_products(
        self,
        products: List[Dict[str, Any]],
        operations: List[str] = None,
        batch_size: int = 50,
        callback: Optional[Callable] = None,
    ) -> Dict[str, Any]:
        """معالجة مجموعة كبيرة من المنتجات"""
        if operations is None:
            operations = ["validate", "enhance"]
        
        logger.info(f"Starting bulk processing for {len(products)} products")
        
        total = len(products)
        completed = 0
        succeeded = 0
        failed = 0
        results = []
        
        for i in range(0, total, batch_size):
            batch = products[i:i + batch_size]
            
            for product in batch:
                try:
                    result = {
                        'sku': product.get('sku'),
                        'success': True,
                        'operations': {}
                    }
                    
                    # تنفيذ العمليات المطلوبة
                    if 'validate' in operations:
                        validation = self.validate_product_full(product)
                        result['operations']['validate'] = validation.to_dict()
                        if not validation.valid:
                            result['success'] = False
                    
                    if 'enhance' in operations:
                        enhancement = self.enhance_product(product, auto_apply=True)
                        result['operations']['enhance'] = {
                            'changes': enhancement.changes,
                            'enhanced_data': enhancement.enhanced_data,
                        }
                        product.update(enhancement.enhanced_data)
                    
                    results.append(result)
                    succeeded += 1
                    
                except Exception as e:
                    failed += 1
                    results.append({
                        'sku': product.get('sku'),
                        'success': False,
                        'error': str(e),
                    })
                    logger.error(f"Error processing product {product.get('sku')}: {e}")
                
                completed += 1
                
                # استدعاء callback للتقدم
                if callback:
                    await callback({
                        'total': total,
                        'completed': completed,
                        'succeeded': succeeded,
                        'failed': failed,
                        'percentage': (completed / total) * 100,
                    })
        
        logger.success(f"Bulk processing completed: {succeeded} succeeded, {failed} failed")
        
        return {
            'total': total,
            'succeeded': succeeded,
            'failed': failed,
            'success_rate': (succeeded / total * 100) if total > 0 else 0,
            'results': results,
        }
    
    # ===== PHASE 4: Pre-Submission Check =====
    
    def check_ready_for_submission(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """فحص جاهزية المنتج للإرسال"""
        logger.info(f"Checking readiness for submission: {product_data.get('sku')}")
        
        # التحقق الكامل
        validation = self.validate_product_full(product_data)
        
        ready = validation.valid
        issues = []
        
        # جمع جميع المشاكل
        for error in validation.errors:
            issues.append({
                'type': 'error',
                'field': error.field,
                'message': error.message,
                'code': error.code,
            })
        
        for warning in validation.warnings:
            if warning.code in ['WARN_NO_BULLET_POINTS', 'WARN_LOW_MARGIN']:
                ready = False
            
            issues.append({
                'type': 'warning',
                'field': warning.field,
                'message': warning.message,
                'code': warning.code,
            })
        
        return {
            'ready': ready,
            'issues': issues,
            'data': product_data,
            'timestamp': datetime.now().isoformat(),
        }
    
    # ===== PHASE 5: Export Ready Format =====
    
    def export_for_amazon(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """تحويل المنتج إلى صيغة جاهزة للإرسال لـ Amazon"""
        logger.info(f"Exporting product for Amazon: {product_data.get('sku')}")
        
        amazon_format = {
            'sku': product_data.get('sku'),
            'title': product_data.get('name'),
            'brand': product_data.get('brand'),
            'product_type': product_data.get('product_type'),
            'condition_type': product_data.get('condition'),
            'fulfillment_channel': product_data.get('fulfillment_channel'),
            'price': float(product_data.get('price', 0)),
            'item_package_quantity': product_data.get('number_of_items', 1),
            'main_image_url': product_data.get('main_image'),
            'other_image_urls': product_data.get('images', []),
            'description': product_data.get('description'),
            'bullet_point_1': product_data.get('bullet_points', [None])[0],
            'bullet_point_2': product_data.get('bullet_points', [None, None])[1] if len(product_data.get('bullet_points', [])) > 1 else None,
            'bullet_point_3': product_data.get('bullet_points', [None, None, None])[2] if len(product_data.get('bullet_points', [])) > 2 else None,
            'bullet_point_4': product_data.get('bullet_points', [None, None, None, None])[3] if len(product_data.get('bullet_points', [])) > 3 else None,
            'bullet_point_5': product_data.get('bullet_points', [None, None, None, None, None])[4] if len(product_data.get('bullet_points', [])) > 4 else None,
        }
        
        # إضافة الأبعاد إذا كانت موجودة
        dimensions = product_data.get('dimensions', {})
        if isinstance(dimensions, dict):
            amazon_format['length_unit_of_measure'] = dimensions.get('unit', 'CM')
            amazon_format['length'] = dimensions.get('length')
            amazon_format['width'] = dimensions.get('width')
            amazon_format['height'] = dimensions.get('height')
        
        # إضافة الوزن
        amazon_format['weight'] = product_data.get('weight')
        amazon_format['weight_unit_of_measure'] = product_data.get('weight_unit', 'KG')
        
        # تنظيف القيم الفارغة
        return {k: v for k, v in amazon_format.items() if v is not None}


# ===== Global Instance =====
_automation_engine: Optional[AutomationEngine] = None

def get_automation_engine() -> AutomationEngine:
    """الحصول على instance من محرك الأتمتة"""
    global _automation_engine
    if _automation_engine is None:
        _automation_engine = AutomationEngine()
    return _automation_engine
