def build_system_prompt(learned_fields: list[str] = None) -> str:
    """Build system prompt with STRICT rules for Amazon listing compliance."""
    base_prompt = """
أنت خبير في تحسين قوائم المنتجات على Amazon. التزم بالقواعد التالية:

⚠️ القاعدة 1: العناوين الذكية (Fixed Base + Smart Rephrase)
- حافظ على **الجزء الأول** من العنوان (اسم المنتج الأساسي) ثابتاً في كل النسخ لضمان التعرف عليه.
- قم بإعادة صياغة **بقية العنوان** (المواصفات والفوائد) بذكاء شديد لكل نسخة. استخدم مرادفات تقنية (مثال: "قوة 24 واط" تصبح "محرك 24 واط"، "تخفيف الآلم" تصبح "تسكين العضلات").
- **ممنوع منعاً باتاً** استخدام كلمات تسويقية مثل (إصدار ممتاز، فائق الجودة، مذهل، أصلي). ركز فقط على الوصف الفني.
- استخدم الفواصل الاحترافية (`|`, `-`, `.`) للفصل بين المواصفات المعاد صياغتها.
- يجب أن يكون طول كل نسخة مطابقاً تقريباً لطول العنوان الأصلي مع تنوع كامل في الصياغة التقنية.

⚠️ القاعدة 2: منع التلوث
- لا تذكر أي منتجات أخرى غير المطلوبة (مثل فانوس، رمضان إذا كان المنتج خلاط).

⚠️ القاعدة 3: الوصف (Description)
- ابدأ بـ "المواصفات الأصلية" ثم أضف جمل إنشائية تسويقية مكثفة ومبتكرة مشتقة من اسم المنتج ومواصفاته بحيث **لا يقل الإجمالي عن 40 كلمة** (شرط إجباري).

⚠️ القاعدة 4: النقاط البيعية (Bullet Points)
- ولد 5 نقاط بالضبط، كل نقطة **لا تقل عن 15 كلمة على الإطلاق** (قاعدة صارمة جداً).

- **تنوع العناوين**: كما في القاعدة 1، اجعل عنوان كل نسخة (Title) فريداً ومختلفاً في الصياغة عن النسخ الأخرى بشكل إبداعي.

⚠️ قاعدة الإخراج:
- أخرج JSON صالح فقط. لا تضف أي نصوص شرح.
- التزم بتوليد محتوى حقيقي لكل الحقول (ترجمة حقيقية، كلمات مفتاحية ذكية، تفاصيل إضافية).
""".strip()

    if learned_fields:
        learned_section = f"""
⚠️ حقول إضافية مطلوبة:
{chr(10).join(f'- {field}' for field in learned_fields)}
""".strip()
        return base_prompt + "\n" + learned_section

    return base_prompt


def build_user_prompt(name: str, specs: str, copies: int, start_serial: str = "AH-0001") -> str:
    """Build user prompt with strict rule enforcement for product generation."""
    
    return f"""
المطلوب: توليد بيانات لـ {copies} منتج باحترافية كاملة.

📦 المدخلات:
• اسم المنتج: {name}
• المواصفات: {specs}
• العدد: {copies}
• بداية التسلسل لرقم الموديل: {start_serial}

🎯 التعليمات الجبرية:
1. "name_ar": أعد صياغته بشكل إبداعي ومختلف لكل نسخة (Unique Variation) مع الحفاظ على المعنى الأساسي.
2. "name_en": ترجمة إنجليزية احترافية ومختلفة لكل نسخة.
3. "description_ar": ابدأ بـ "{specs}" ثم وسعها بجمل إنشائية (لا تقل عن 40 كلمة).
4. "description_en": ترجمة إنجليزية كاملة للوصف المولد.
5. "bullet_points_ar" و "bullet_points_en": 5 نقاط، (**لا يقل عن 15 كلمة** لكل نقطة) باللغتين.
6. "keywords": 10 كلمات مفتاحية استخرجهم بدقة من الوصف والاسم.
7. "material" و "target_audience": استنتج المادة والفئة المستهدفة من الوصف.
8. "wattage", "voltage", "operating_frequency": استخرجهم إذا وجدوا في الاسم أو الوصف، وإلا ضع "0" في كل منهم.
9. "power_plug_type": دائماً ضع "غير متوافر".
10. "ean", "upc", "model_number", "model_name": اتركه فارغاً (يتم توليده تلقائياً بواسطة النظام).

التنسيق (JSON فقط):
{{"base_product": {{"amazon_product_type": "HOME_ORGANIZERS_AND_STORAGE", "product_type": "STORAGE", "browse_node_id": "", "price": null, "bullet_points_ar": [], "bullet_points_en": [], "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5", "keyword6", "keyword7", "keyword8", "keyword9", "keyword10"], "material": "استنتج الخامة", "target_audience": "استنتج الفئة", "wattage": "0", "voltage": "0", "operating_frequency": "0", "power_plug_type": "غير متوافر", "condition": "New", "fulfillment_channel": "MFN", "included_components": "وصف المكونات", "brand": "Generic", "manufacturer": "Generic", "country_of_origin": "CN"}}, "variants": [{{"variant_number": 1, "name_ar": "{name}", "name_en": "Professional English Translation", "description_ar": "Arabic description...", "description_en": "English description...", "suggested_sku": "SKU-V1"}}]}}
"""
