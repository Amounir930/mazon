"""
AI Product Assistant
=====================
Async AI-powered product data generator using Qwen AI.

Implements Base + Delta Pattern:
- 1 request generates all data
- base_product: shared fields (brand, price, bullets, keywords, etc.)
- variants: per-product differences (name, description, SKU)

Saves 84% of tokens compared to generating each product separately.
"""
from typing import Dict, Any
from loguru import logger

from app.core.llm_provider import QwenProvider
from app.schemas.ai import AIProductResponse


class AIProductAssistant:
    """
    AI-powered product data generator.
    
    Usage:
        assistant = AIProductAssistant()
        result = await assistant.generate_products(
            name="خلاط كهربائي 300 واط",
            specs="5 سرعات، ستانلس ستيل، سهل التنظيف",
            copies=3
        )
        
        # result.base_product → shared data
        # result.variants → 3 variants with different names/descriptions
    """
    
    def __init__(self):
        self.llm = QwenProvider()
    
    async def generate_products(
        self,
        name: str,
        specs: str,
        copies: int = 1,
        learned_fields: list[str] = None,
    ) -> AIProductResponse:
        """
        Generate N product variants in a SINGLE request (Base + Delta Pattern).
        
        Args:
            name: Product base name
            specs: Product specifications
            copies: Number of variants (1-10)
            learned_fields: Fields learned from previous rejection errors
        """
        # Build system prompt with learned fields
        system_prompt = self._build_system_prompt(learned_fields)
        
        # Build user prompt
        user_prompt = self._build_user_prompt(name, specs, copies)
        
        logger.info(f"Generating {copies} product variant(s): {name}")
        
        # Call Qwen AI (async — non-blocking)
        raw_result = await self.llm.generate_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )
        
        # Validate with Pydantic
        try:
            # FIX: AI sometimes generates >5 or <5 bullet points — ensure exactly 5
            if 'base_product' in raw_result:
                bp = raw_result['base_product']
                for key in ['bullet_points_ar', 'bullet_points_en']:
                    if key in bp:
                        items = bp[key][:5]  # Truncate to 5
                        while len(items) < 5:  # Pad if less than 5
                            items.append("")
                        bp[key] = items

            result = AIProductResponse(**raw_result)
            logger.info(
                f"✅ Generated {len(result.variants)} variant(s) — "
                f"base: brand={result.base_product.brand}, "
                f"type={result.base_product.product_type}"
            )
            return result
        except Exception as e:
            logger.error(f"Pydantic validation failed: {e}\nRaw data: {raw_result}")
            raise ValueError(f"AI generated invalid product data: {e}")
    
    def _build_system_prompt(self, learned_fields: list[str] = None) -> str:
        """Build system prompt with Amazon listing best practices"""
        base_prompt = """
أنت مساعد ذكاء اصطناعي متخصص في تحسين قوائم المنتجات على Amazon.
مهمتك: توليد بيانات منتج كاملة من وصف مختصر.

⚠️ قواعد إجبارية:
1. الباركود EAN: إجباري - ولّد رقم EAN صحيح من 13 رقم في كل مرة
   - استخدم صيغة: ابدأ بـ 628 أو 629 (مصر) أو 690 (الصين) ثم 10 أرقام عشوائية
   - مثال: 6281234567890
2. التسعير والكمية: اتركها فارغة (null) - المستخدم يملأها بنفسه
3. المكونات المرفقة: اكتب كلمة واحدة فقط (مثال: "خلاط" أو "جهاز")
4. الوصف (عربي + إنجليزي): لازم يكون وصف شامل - 3 سطور كاملة على الأقل
   - يشرح المميزات + الاستخدامات + الفوائد
   - مثال عربي: "هذا الخلاط الكهربائي بقوة 500 واط يأتي مع 5 سرعات مختلفة لتناسب جميع احتياجاتك في المطبخ. مصنوع من مواد عالية الجودة تضمن له المتانة والاستخدام الطويل. مثالي لخلط العجين، تحضير العصائر، وفرم المكونات المختلفة بسهولة تامة."
5. النقاط البيعية (5 نقاط): إجباري - كل نقطة سطر كامل يشرح ميزة مهمة
   - كل نقطة 20 حرف على الأقل
   - تركز على الفوائد للمشتري

معايير Amazon:
- اسم المنتج: max 200 حرف، يتضمن العلامة + الموديل + المواصفات الأساسية
- الوصف: max 2000 حرف، شامل المميزات + الاستخدام
- Bullet Points: 5 نقاط، كل نقطة max 500 حرف، تركز على الفوائد
- Keywords: max 250 حرف، SEO optimized
- SKU: يجب أن يكون فريد وقابل للقراءة (مثال: MIX-300W-001)

⚠️ مهم جداً:
- ارجع JSON فقط بدون أي نص إضافي
- لا تضيف markdown code blocks (```)
- لا تضيف JSON Schema أو type definitions
- ارجع القيم مباشرة كما في المثال أدناه
""".strip()

        # Add learned fields section
        if learned_fields:
            learned_section = f"""

⚠️ حقول سبق رفضها من Amazon (مطلوب تضمينها في base_product):
{chr(10).join(f'- {field}' for field in learned_fields)}

تأكد من تضمين كل هذه الحقول في base_product.
""".strip()
            return base_prompt + "\n" + learned_section

        return base_prompt
    
    def _build_user_prompt(self, name: str, specs: str, copies: int) -> str:
        """Build user prompt for product generation"""
        variants_instruction = ""
        if copies > 1:
            variants_instruction = f"""
ولّد {copies} منتجات مختلفة — كل منتج يجب أن يكون له:
- اسم مختلف (عربي + إنجليزي) يركز على زاوية تسويقية مختلفة
- وصف مختلف (عربي + إنجليزي) يبرز مميزات مختلفة
- SKU فريد (مثال: MIX-300W-001, MIX-300W-002, ...)
""".strip()
        else:
            variants_instruction = "ولّد منتج واحد ببيانات كاملة."

        # Use strict JSON format with clear example - avoid YAML-like indentation
        return f"""
المطلوب: توليد بيانات منتج كامل. أخرج JSON صالح فقط.

اسم المنتج: {name}
المواصفات: {specs}
عدد النسخ: {copies}

{variants_instruction}

التنسيق المطلوب (JSON فقط):
{{"base_product": {{"brand": "اسم البراند", "manufacturer": "اسم المصنع", "product_type": "نوع المنتج", "price": null, "ean": "6281234567890", "upc": "", "bullet_points_ar": ["نقطة بيعية كاملة 1 - سطر يشرح ميزة مهمة", "نقطة بيعية كاملة 2 - سطر يشرح فائدة", "نقطة بيعية كاملة 3 - سطر يشرح ميزة", "نقطة بيعية كاملة 4 - سطر يشرح فائدة", "نقطة بيعية كاملة 5 - سطر يشرح ميزة"], "bullet_points_en": ["Full selling point 1 - line describing feature", "Full selling point 2 - line describing benefit", "Full selling point 3 - line describing feature", "Full selling point 4 - line describing benefit", "Full selling point 5 - line describing feature"], "keywords": ["كلمة1", "كلمة2"], "material": "المادة", "target_audience": "الفئة", "condition": "New", "fulfillment_channel": "MFN", "country_of_origin": "CN", "model_number": "MOD-001", "included_components": "كلمة واحدة"}}, "variants": [{{"variant_number": 1, "name_ar": "الاسم بالعربي", "name_en": "English Name", "description_ar": "وصف شامل 3 سطور - يشرح المميزات والاستخدامات والفوائد بشكل تفصيلي. هذا المنتج مصنوع من مواد عالية الجودة. مثالي للاستخدام اليومي.", "description_en": "Full 3-line description describing features, benefits and uses in detail. Made from high quality materials. Perfect for daily use.", "suggested_sku": "SKU-001"}}]}}

قواعد مهمة:
- الباركود EAN: إجباري - ولّد 13 رقم صحيح (مثال: 628xxxxxxxxx)
- التسعير (price): اتركه null - لا تكتب رقم
- المكونات المرفقة (included_components): كلمة واحدة فقط
- الوصف: 3 سطور كاملة على الأقل
- النقاط البيعية: 5 نقاط كاملة - كل نقطة 20 حرف على الأقل
- استبدل القيم الافتراضية ببيانات حقيقية مناسبة للمنتج
- أخرج JSON فقط بدون أي نص إضافي
- لا تضيف ```json أو ``` في البداية أو النهاية
- لا تضيف "type": "object" أو أي JSON Schema
- استخدم double quotes فقط (لا تستخدم single quotes)
- تأكد من إغلاق جميع الأقواس {{}} و []
- لا تستخدم YAML format (لا تستخدم indentation بدل الأقواس)
""".strip()
