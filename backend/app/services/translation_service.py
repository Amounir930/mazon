"""
Centralized Translation Service with LLM Fallback
"""
from typing import Optional
from loguru import logger


class TranslationService:
    """Unified translation service with caching and LLM fallback"""

    def __init__(self, llm_provider):
        self.llm = llm_provider
        self._cache = {}
        # Common terms dictionary for fast fallback
        self._common_terms = {
            'كهربائي': 'electric', 'ستانلس ستيل': 'stainless steel',
            'سهل التنظيف': 'easy to clean', 'عالي الجودة': 'high quality',
            '5 سرعات': '5 speed settings', 'وات': 'watt', 'لتر': 'liter',
        }

    async def translate(self, text: str, from_lang: str, to_lang: str,
                       context: str = "", max_tokens: int = 150) -> str:
        """Translate with context preservation, caching, and LLM fallback"""
        if not text or not text.strip():
            return ""

        cache_key = f"{text}:{from_lang}:{to_lang}:{hash(context)}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        # Try simple dictionary first (fast path)
        if from_lang == 'ar' and to_lang == 'en':
            simple = self._simple_ar_to_en(text)
            if simple != text and len(simple.split()) >= 3:
                self._cache[cache_key] = simple
                return simple

        # Fallback to LLM for complex translations
        try:
            prompt = self._build_translation_prompt(text, from_lang, to_lang, context)
            result = await self.llm.generate_text(prompt, max_tokens=max_tokens, temperature=0.3)
            translation = result.strip().strip('"').strip("'")
            if translation and not translation.startswith('Translation of'):
                self._cache[cache_key] = translation
                return translation
        except Exception as e:
            logger.warning(f"LLM translation failed: {e}")

        # Last resort: return original with warning
        logger.warning(f"Translation fallback for: {text[:50]}...")
        return text

    def _simple_ar_to_en(self, text: str) -> str:
        """Simple dictionary-based translation for common terms"""
        result = text
        for ar_term, en_term in self._common_terms.items():
            result = result.replace(ar_term, en_term)
        return result if result != text else text

    def _build_translation_prompt(self, text: str, from_lang: str, to_lang: str, context: str) -> str:
        """Build optimized prompt for translation task"""
        return f"""Translate this {from_lang} product text to {to_lang}.
Product context: {context or 'General e-commerce product'}
Text to translate: "{text}"
Rules:
- Preserve all technical specs, numbers, and units exactly
- Use professional e-commerce language
- Output ONLY the translation, no explanations
- Keep it concise and marketing-friendly"""
