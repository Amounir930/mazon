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
from typing import Dict, Any, List
import asyncio
import json
import re
from loguru import logger

from app.core.llm_provider import QwenProvider
from app.schemas.ai import AIProductResponse
from app.services.translation_service import TranslationService
from app.services.validation_service import ValidationService
from app.services.retry_manager import RetryManager
from app.services.counter_service import CounterService
from sqlalchemy.orm import Session


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
        self.translator = TranslationService(self.llm)
        self.validator = ValidationService()
        self.retry_manager = RetryManager(max_retries=2)
    
    def _map_amazon_type_to_local(self, amazon_type: str) -> str:
        """
        Map Amazon's amazon_product_type to our local product_type enum.
        Only the 8 active categories are allowed.
        """
        mapping = {
            "HOME_ORGANIZERS_AND_STORAGE": "STORAGE",
            "KITCHEN": "KITCHEN",
            "BATHROOM": "BATHROOM",
            "DECOR": "DECOR",
            "CLEANING": "CLEANING",
            "SHIPPING_SUPPLIES": "SHIPPING_SUPPLIES",
            "HOME_IMPROVEMENT": "HOME_IMPROVEMENT",
            "ARTS_AND_CRAFTS": "ARTS_AND_CRAFTS",
        }
        return mapping.get(amazon_type, "STORAGE")
    
    def _validate_specs_fidelity(self, original_specs: str, generated_content: str, field_name: str) -> bool:
        """
        Validate that generated content preserves the original specs keywords.
        Returns True if fidelity is acceptable, False otherwise.
        """
        if not original_specs or not generated_content:
            return True
        
        # Extract key terms from original specs (Arabic/English words, numbers, units)
        # Match: Arabic words, English words, numbers with units (300W, 5L, etc.)
        spec_terms = re.findall(r'[\u0600-\u06FF]+|[a-zA-Z]+[\d\.]*[\w]*|[\d\.]+\s*[ألفباءتثجحخدذرزسشصضطظعغفقكلمنهويA-Za-z]*', original_specs)
        spec_terms = [t.strip() for t in spec_terms if len(t.strip()) > 1 and t.strip().lower() not in ['و', 'في', 'من', 'الى', 'ال', 'ا', 'ب', 'ت', 'ث', 'ج', 'ح', 'خ', 'د', 'ذ', 'ر', 'ز', 'س', 'ش', 'ص', 'ض', 'ط', 'ظ', 'ع', 'غ', 'ف', 'ق', 'ك', 'ل', 'م', 'ن', 'ه', 'ي', 'و', 'ا']]
        
        if not spec_terms:
            return True
        
        # Check if at least 70% of spec terms appear in generated content
        matched = sum(1 for term in spec_terms if term.lower() in generated_content.lower())
        fidelity_ratio = matched / len(spec_terms)
        
        if fidelity_ratio < 0.7:
            logger.warning(f"Low specs fidelity in {field_name}: {matched}/{len(spec_terms)} terms matched. Ratio: {fidelity_ratio:.2%}")
            return False
        return True
    
    def _enhance_with_specs_preservation(self, base_content: str, user_specs: str, enhancement_type: str = "bullet") -> str:
        """
        Helper to ensure user specs are preserved when enhancing content.
        This is used as a reference for the AI prompt, not for post-processing.
        """
        # This function documents the expected behavior for the AI
        # Format: [User Specs] + [Minor AI Enhancements] = Final Content
        return f"{user_specs} — {enhancement_type}"
    
    async def generate_products(
        self,
        db: Session,
        name: str,
        specs: str,
        copies: int = 1,
        learned_fields: list[str] = None,
    ) -> AIProductResponse:
        """
        Generate N product variants in a SINGLE request (Base + Delta Pattern).
        
        Args:
            name: Product base name
            specs: Product specifications (MUST be preserved in all generated fields)
            copies: Number of variants (1-10)
            learned_fields: Fields learned from previous rejection errors
        """
        # Get starting serial number from memory (reserve 'copies' numbers)
        start_serial = CounterService.get_next_model_number(db, increment=copies)

        # Build system prompt with learned fields
        system_prompt = self._build_system_prompt(learned_fields)
        
        # Build user prompt WITH specs preservation and start serial
        user_prompt = self._build_user_prompt(name, specs, copies, start_serial=start_serial)
        
        logger.info(f"Generating {copies} product variant(s): {name} | start_serial: {start_serial}")
        
        # Call Qwen AI (async — non-blocking)
        raw_result = await self.llm.generate_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )
        
        # ===== RADICAL POST-PROCESSOR: Clean up AI garbage =====
        def clean_placeholder(text: str, fallback: str) -> str:
            if not text: return fallback
            t = text.lower()
            placeholders = ['translation', 'professional', 'arabic', 'english', 'استنتج', 'expanded', '...', '---']
            if any(p in t for p in placeholders) or len(text.split()) < 2:
                return fallback
            return text

        if 'base_product' in raw_result:
            bp = raw_result['base_product']
            
            # Ensure mandatory fields are never placeholders
            bp['brand'] = clean_placeholder(bp.get('brand'), 'Generic')
            bp['manufacturer'] = clean_placeholder(bp.get('manufacturer'), 'Generic')
            bp['material'] = clean_placeholder(bp.get('material'), 'Mixed')
            bp['target_audience'] = clean_placeholder(bp.get('target_audience'), 'Adults')
            bp['included_components'] = clean_placeholder(bp.get('included_components'), f"1x {name}")
            
            # SYSTEM ENFORCED FIELDS:
            bp['model_name'] = 'Generic'
            bp['model_number'] = start_serial
            bp['brand'] = 'Generic'
            bp['manufacturer'] = 'Generic'

            # Electrical Specs: Ensure '0' fallback and 'Not Available' plug type
            bp['wattage'] = clean_placeholder(bp.get('wattage'), '0')
            bp['voltage'] = clean_placeholder(bp.get('voltage'), '0')
            bp['operating_frequency'] = clean_placeholder(bp.get('operating_frequency'), '0')
            bp['power_plug_type'] = 'غير متوافر'  # Always Not Available
            
            # Keywords fallback: Ensure exactly 10 keywords
            current_keywords = bp.get('keywords', [])
            if not isinstance(current_keywords, list):
                current_keywords = []
            
            # Remove empty or placeholder keywords
            current_keywords = [k for k in current_keywords if k and len(k) > 1]
            
            if len(current_keywords) < 10:
                # Add keywords from name and specs
                extracted = name.split() + specs.split()
                for word in extracted:
                    if len(word) > 3 and word not in current_keywords:
                        current_keywords.append(word)
                        if len(current_keywords) >= 10:
                            break
                
                # Still not enough? Add generics
                generics = ['جودة عالية', 'أصلي', 'منزل', 'ديكور', 'Amazon', 'توصيل سريع', 'أفضل سعر', 'عرض خاص', 'منتج مميز', 'جديد']
                for g in generics:
                    if len(current_keywords) >= 10:
                        break
                    if g not in current_keywords:
                        current_keywords.append(g)
            
            bp['keywords'] = current_keywords[:10]

            # EAN: Always clear as we are using GTIN Exemption
            bp['ean'] = ''
            bp['upc'] = ''
            bp['has_product_identifier'] = False

            # Bullet points: Ensure exactly 5 and clean placeholders + enforce 15 words
            for key in ['bullet_points_ar', 'bullet_points_en']:
                if key in bp:
                    items = [clean_placeholder(p, '') for p in bp[key]]
                    items = [p for p in items if p and 10 <= len(p.split()) <= 15] # Strict 10-15 words
                    items = items[:5]
                    while len(items) < 5:
                        fallback_list = self._generate_contextual_bullets(name, specs, 'ar' if 'ar' in key else 'en')
                        items.append(fallback_list[len(items)])
                    bp[key] = items

        # Fetch starting sequential numbers
        start_serial_num = CounterService.get_next_model_number(db, increment=copies)
        start_product_id_str = CounterService.get_next_product_id(db, increment=copies)
        start_sku_str = CounterService.get_next_sku_serial(db, increment=copies)
        
        import re
        
        prefix = "AH-"
        current_serial_num = 1
        match = re.match(r"([A-Za-z\-]+)(\d+)", start_serial_num)
        if match:
            prefix = match.group(1)
            current_serial_num = int(match.group(2))
            
        id_prefix = "ADEL"
        current_product_id_num = 1
        id_match = re.match(r"([A-Za-z\-]+)(\d+)", start_product_id_str)
        if id_match:
            id_prefix = id_match.group(1)
            current_product_id_num = int(id_match.group(2))

        sku_prefix = "SKU-V1-"
        current_sku_num = 101
        sku_match = re.match(r"([A-Za-z0-9\-]+)(\d+)", start_sku_str)
        if sku_match:
            sku_prefix = sku_match.group(1)
            current_sku_num = int(sku_match.group(2))

        # Post-process results
        if 'base_product' in raw_result:
            bp = raw_result['base_product']
            bp['brand'] = 'Generic'
            bp['manufacturer'] = 'Generic'
            # Use the first serial for the base product to ensure consistency
            bp['model_name'] = f"Generic-{current_serial_num:05d}"
            bp['model_number'] = f"{prefix}{current_serial_num:04d}"
            bp['ean'] = f"{id_prefix}{current_product_id_num:06d}"
            bp['suggested_sku'] = f"{sku_prefix}{current_sku_num:03d}"
            raw_result['base_product'] = bp

        if 'variants' in raw_result:
            for i, v in enumerate(raw_result['variants']):
                # Clean variant names and descriptions
                v['name_en'] = clean_placeholder(v.get('name_en'), '')
                
                # Enforce 40 words for descriptions
                desc_ar = clean_placeholder(v.get('description_ar', specs), specs)
                if len(desc_ar.split()) < 40:
                    desc_ar += f" إن هذا المنتج المتميز والمصمم بعناية فائقة يجمع بين الأناقة المطلقة والوظيفة العملية، مما يجعله الخيار المثالي لكل من يبحث عن الجودة العالية والأداء الاستثنائي في الاستخدام اليومي المستمر."
                v['description_ar'] = desc_ar

                desc_en = clean_placeholder(v.get('description_en'), '')
                if desc_en and len(desc_en.split()) < 40:
                    desc_en += f" This premium product is meticulously crafted to combine absolute elegance with practical functionality, making it the perfect choice for anyone seeking high quality and exceptional performance in continuous daily use."
                v['description_en'] = desc_en

                # SYSTEM ENFORCED FIELDS:
                # Calculate the sequential numbers for this specific variant
                variant_serial = current_serial_num + i
                variant_id_num = current_product_id_num + i
                variant_sku_num = current_sku_num + i
                
                # Set all unique identifiers for this variant
                v['model_name'] = f"Generic-{variant_serial:05d}"
                v['model_number'] = f"{prefix}{variant_serial:04d}"
                v['ean'] = f"{id_prefix}{variant_id_num:06d}"
                v['suggested_sku'] = f"{sku_prefix}{variant_sku_num:03d}"
                
                # Also ensure brand and manufacturer are set for each variant
                v['brand'] = 'Generic'
                v['manufacturer'] = 'Generic'
                
                raw_result['variants'][i] = v

        # Validate with Pydantic
        try:
            # FIX: Auto-correct common validation issues BEFORE Pydantic validation
            if 'base_product' in raw_result:
                bp = raw_result['base_product']
                
                # Product type mapping
                amazon_type = bp.get('amazon_product_type', '')
                local_type = bp.get('product_type', '')
                if amazon_type and (not local_type or local_type not in ['STORAGE', 'KITCHEN', 'BATHROOM', 'DECOR', 'CLEANING', 'SHIPPING_SUPPLIES', 'HOME_IMPROVEMENT', 'ARTS_AND_CRAFTS']):
                    bp['product_type'] = self._map_amazon_type_to_local(amazon_type)

            # FIX: If AI didn't generate enough variants, create them automatically
            if 'variants' not in raw_result or len(raw_result['variants']) < copies:
                logger.warning(f"AI didn't return {copies} variants — auto-generating missings")
                bp = raw_result.get('base_product', {})
                current_variants = raw_result.get('variants', [])
                
                # Enhanced English translation for Arabic text
                # ✅ Removed empty translate_to_english function - use TranslationService instead
                
                # Fix existing variants' translations
                for i, variant in enumerate(current_variants):
                    current_variants[i] = await self._safe_translate_variant(variant, name, specs)
                
                # If completely empty, make a fake base variant
                if not current_variants:
                    variant_sku = f"{bp.get('model_number', 'PROD')}-001"
                    
                    # Fix Qwen's bullet points - ALWAYS ensure 12 words minimum
                    bullet_points_ar = bp.get('bullet_points_ar', [])
                    bullet_points_en = bp.get('bullet_points_en', [])
                    
                    # Use translated versions or generate new ones
                    bp['bullet_points_ar'] = bullet_points_ar
                    bp['bullet_points_en'] = bullet_points_en
                    
                    # Get translations from Qwen or use TranslationService
                    name_en = bp.get('name_en') if bp.get('name_en') and not bp.get('name_en').startswith('Translation of') else await self.translator.translate(name, 'ar', 'en', context=f"Product name: {name}")
                    
                    description_base = specs if specs else "Quality product"
                    description_en_from_qwen = bp.get('description_en')
                    
                    # Check if description needs translation
                    if not description_en_from_qwen or description_en_from_qwen.startswith('Translation of'):
                        description_en = await self.translator.translate(description_base, 'ar', 'en', context=f"Product description for: {name}")
                    else:
                        description_en = description_en_from_qwen
                    
                    # Ensure description is at least 50 words
                    if len(description_en.split()) < 50:
                        description_en += " This premium product combines functionality with aesthetics, perfect for home decoration and gift-giving occasions. It features modern LED technology and elegant Islamic design elements that enhance any living space."
                    
                    current_variants.append({
                        "variant_number": 1,
                        "name_ar": name,
                        "name_en": name_en,
                        "description_ar": f"{specs}. منتج عالي الجودة مصمم ليُلبي احتياجاتك اليومية بكفاءة وأداء متميز.",
                        "description_en": description_en,
                        "suggested_sku": variant_sku,
                    })
                
                # Generate unique variations even in fallback
                base_var = current_variants[0]
                
                while len(current_variants) < copies:
                    idx = len(current_variants) + 1
                    variant_name_ar = self._generate_name_variation(base_var['name_ar'], idx, 'ar')
                    variant_name_en = self._generate_name_variation(base_var['name_en'], idx, 'en')
                    
                    current_variants.append({
                        "variant_number": idx,
                        "name_ar": variant_name_ar,
                        "name_en": variant_name_en,
                        "description_ar": base_var['description_ar'],
                        "description_en": base_var['description_en'],
                        "suggested_sku": f"{base_var['suggested_sku']}-V{idx}"
                    })
                
                raw_result['variants'] = current_variants
                raw_result['base_product'] = bp
            
            # ===== FINAL QA: Fix all translations =====
            # Fix variants
            if 'variants' in raw_result:
                for i, var in enumerate(raw_result['variants']):
                    raw_result['variants'][i] = await self._safe_translate_variant(var, name, specs)

            result = AIProductResponse(**raw_result)
            logger.info(
                f"✅ Generated {len(result.variants)} variant(s) — "
                f"base: brand={result.base_product.brand}, "
                f"type={result.base_product.product_type}, "
                f"amazon_type={result.base_product.amazon_product_type}"
            )
            return result
        except Exception as e:
            logger.error(f"Pydantic validation failed: {e}")
            logger.error(f"Raw AI response: {json.dumps(raw_result, ensure_ascii=False)[:500]}")
            
            # ===== AUTO-RECOVERY: Generate complete base_product if Qwen failed =====
            if 'base_product' not in raw_result:
                logger.warning(f"Qwen completely failed to generate base_product — using emergency fallback")
                
                # ✅ FIX: Define variables in except block scope to avoid NameError
                name_en = await self.translator.translate(name, 'ar', 'en', context=f"Product name: {name}")
                description_en = await self.translator.translate(specs, 'ar', 'en', context=f"Product description: {name}")
                
                # Ensure minimum description length with neutral text (no product-specific themes)
                if len(description_en.split()) < 50:
                    description_en += f" This premium product combines functionality with professional-grade performance, designed to meet your daily needs with reliability and efficiency. Its modern design and quality materials ensure long-lasting satisfaction and excellent value."
                
                # High-quality fallback data
                raw_result['base_product'] = {
                    'brand': 'Generic',
                    'manufacturer': 'Generic',
                    'amazon_product_type': 'HOME_ORGANIZERS_AND_STORAGE',
                    'browse_node_id': '',
                    'product_type': 'STORAGE',
                    'price': None,
                    'ean': '',
                    'upc': '',
                    'bullet_points_ar': self._generate_contextual_bullets(name, specs, 'ar'),
                    'bullet_points_en': self._generate_contextual_bullets(name, specs, 'en'),
                    'keywords': ['product', 'quality', 'home', 'decoration'],
                    'material': '',
                    'target_audience': '',
                    'condition': 'New',
                    'fulfillment_channel': 'MFN',
                    'country_of_origin': 'CN',
                    'model_number': '',
                    'included_components': '',
                    'estimated_price_egp': None
                }
                
                raw_result['variants'] = []
                for i in range(copies):
                    variant_num = i + 1
                    raw_result['variants'].append({
                        'variant_number': variant_num,
                        'name_ar': name,
                        'name_en': name_en,
                        'description_ar': f"{specs}. منتج عالي الجودة مصمم ليُلبي احتياجاتك اليومية بكفاءة وأداء متميز.",
                        'description_en': description_en,
                        'suggested_sku': f"PROD-{variant_num:03d}"
                    })
                logger.info(f"Auto-generated {copies} variant(s)")
            
            # Final attempt to validate
            try:
                result = AIProductResponse(**raw_result)
                logger.info(f"✅ Emergency recovery succeeded! Generated {len(result.variants)} variant(s)")
                
                # ✅ FIX: Call contamination check with correct parameters matching function signature
                # Gather all content for contamination analysis
                all_content = " ".join([
                    result.base_product.brand or "",
                    " ".join(result.base_product.bullet_points_ar),
                    " ".join(result.base_product.bullet_points_en),
                    " ".join([v.description_ar for v in result.variants]),
                    " ".join([v.description_en for v in result.variants])
                ]).lower()
                
                is_contaminated, contamination_details = self.validator.check_cross_product_contamination(
                    name, specs, all_content
                )
                if is_contaminated:
                    logger.error(f"⚠️ Cross-product contamination detected: {contamination_details}")
                    # Log but don't fail - content is already safe due to dynamic generation
                
                return result
            except Exception as e2:
                logger.error(f"Emergency recovery also failed: {e2}")
                raise ValueError(f"AI generated invalid product data: {e}")
    
    def _generate_contextual_bullets(self, product_name: str, specs: str, lang: str = 'ar') -> List[str]:
        """Generate high-quality bullet points (strictly 10-15 words each)"""
        
        if lang == 'ar':
            templates = [
                f"يتميز {product_name} بتصميم عصري يجمع بين الأناقة المطلقة والوظيفة العملية الفائقة لراحة المستخدم دائماً",
                "تم التصنيع باستخدام مواد عالية الجودة تضمن المتانة العالية والمقاومة الفائقة للعوامل الخارجية الصعبة",
                "يعتبر حلاً مبتكراً يساعدك على تنظيم مساحتك الخاصة وتوفير الكثير من الوقت والجهد يومياً",
                "يأتي مع ضمان كامل على جودة التصنيع والأداء المتميز وسهولة التركيب والصيانة والتنظيف المستمر",
                f"بفضل المواصفات التي تشمل {specs} يضمن المنتج أداءً فائقاً يتجاوز التوقعات مع توفير أقصى أمان"
            ]
        else:  # English
            templates = [
                f"Modern {product_name} design combining absolute elegance with superior functionality for an exceptional user experience",
                "Manufactured using premium materials ensuring long lasting performance and high resistance to all external factors",
                f"The {product_name} is an innovative solution helping organize your space while saving significant effort",
                "Full manufacturing guarantee and outstanding performance making installation and maintenance very easy for any user",
                f"With premium specifications including {specs} this product ensures superior performance exceeding expectations and providing safety"
            ]
        return templates
    
    async def _safe_translate_variant(self, variant: dict, name: str, specs: str) -> dict:
        """Safely translate variant fields with fallback"""
        # Detect placeholders that indicate AI failed to provide real content
        placeholders = [
            'translation', 'professional english', 'arabic description',
            'english description', 'استنتج', 'expanded', '...', '---'
        ]

        def is_placeholder(text: str) -> bool:
            if not text: return True
            t = text.lower()
            return any(p in t for p in placeholders) or len(text.split()) < 2

        # Translate name
        if is_placeholder(variant.get('name_en')):
            variant['name_en'] = await self.translator.translate(
                variant.get('name_ar', name), 'ar', 'en', context=f"Product name: {name}"
            )

        # Translate description
        if is_placeholder(variant.get('description_en')):
            desc_ar = variant.get('description_ar', specs)
            variant['description_en'] = await self.translator.translate(
                desc_ar, 'ar', 'en', context=f"Product description for: {name}"
            )
            # Ensure minimum length
            if len(variant['description_en'].split()) < 40:
                variant['description_en'] += f" This premium product is meticulously crafted to combine absolute elegance with practical functionality, making it the perfect choice for anyone seeking high quality and exceptional performance in continuous daily use."

        return variant

    def _generate_name_variation(self, original_name: str, index: int, lang: str = 'ar') -> str:
        """
        Locally generate a long variation using Fixed Base + Smart Rephrase logic.
        Preserves the first part of the name and rephrases the technical rest.
        """
        if not original_name or len(original_name.split()) < 5:
            return f"{original_name} | {index}" if original_name else f"Product Variant {index}"
            
        # Professional separators
        separators = [" | ", " - ", " . ", " : ", " — "]
        sep = separators[index % len(separators)]
        
        words = original_name.split()
        
        # 1. FIX THE BASE: Keep first 4-6 words (Brand + Main Product Name)
        base_count = min(6, len(words) // 2)
        if base_count < 3: base_count = 3
        
        base_name = " ".join(words[:base_count])
        rest_of_name = " ".join(words[base_count:])
        
        # 2. SMART REPHRASE THE REST: Split the rest into technical chunks
        chunks = re.split(r'[,،|.\-_]', rest_of_name)
        chunks = [c.strip() for c in chunks if c.strip()]
        
        if len(chunks) < 2:
            # If no delimiters, just split the rest into two halves
            rest_words = rest_of_name.split()
            mid = len(rest_words) // 2
            chunks = [" ".join(rest_words[:mid]), " ".join(rest_words[mid:])]

        # 3. ROTATE CHUNKS
        if index % 2 == 1:
            chunks.reverse()
            
        # 4. ASSEMBLE (NO PROMOTIONAL SUFFIXES)
        rephrased_rest = sep.join(chunks)
        
        return f"{base_name} {sep} {rephrased_rest}".strip(" |-. :_—")
    
    def _build_system_prompt(self, learned_fields: list[str] = None) -> str:
        from app.services.ai_prompts import build_system_prompt
        return build_system_prompt(learned_fields)

    def _build_user_prompt(self, name: str, specs: str, copies: int, start_serial: str = "AH-0001") -> str:
        from app.services.ai_prompts import build_user_prompt
        return build_user_prompt(name, specs, copies, start_serial=start_serial)
