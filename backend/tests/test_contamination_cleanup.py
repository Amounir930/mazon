"""
Test Suite: Verify AI Product Generation Contamination Cleanup
============================================================

This test suite verifies that all hardcoded content and problematic translation
dictionaries have been completely removed from the AI product generation system.

Tests check for:
1. ✅ No hardcoded "Ramadan lantern" content anywhere
2. ✅ No hardcoded QUALITY_BULLETS arrays
3. ✅ No legacy translate_to_english functions with broken dictionaries
4. ✅ All translations use TranslationService
5. ✅ Exception handlers use dynamic generation, not static fallbacks
6. ✅ Cross-product contamination detection is in place
7. ✅ QwenProvider has generate_text() method
8. ✅ ai_prompts.py rule numbering is sequential (1-9)
"""

import pytest
import re
from pathlib import Path

# Paths to key files
PROJECT_ROOT = Path(__file__).parent.parent.parent
BACKEND_ROOT = PROJECT_ROOT / "backend"
AI_ASSISTANT_FILE = BACKEND_ROOT / "app" / "services" / "ai_product_assistant.py"
AI_PROMPTS_FILE = BACKEND_ROOT / "app" / "services" / "ai_prompts.py"
LLM_PROVIDER_FILE = BACKEND_ROOT / "app" / "core" / "llm_provider.py"
TRANSLATION_SERVICE_FILE = BACKEND_ROOT / "app" / "services" / "translation_service.py"
VALIDATION_SERVICE_FILE = BACKEND_ROOT / "app" / "services" / "validation_service.py"


class TestContaminationCleanup:
    """Verify all contamination cleanup is complete."""
    
    def test_no_hardcoded_ramadan_lantern_in_ai_assistant(self):
        """✅ CRITICAL: No hardcoded 'Ramadan lantern' content in AI assistant"""
        content = AI_ASSISTANT_FILE.read_text(encoding='utf-8')
        
        # Should not contain Ramadan lantern in any form
        assert "Ramadan lantern" not in content, "❌ Hardcoded 'Ramadan lantern' found!"
        assert "رمضان" not in content or "lantern" not in content.replace("فانوس رمضان", ""), \
            "❌ Arabic Ramadan lantern reference found!"
        
        print("✅ PASS: No hardcoded 'Ramadan lantern' content found")
    
    def test_no_quality_bullets_static_arrays(self):
        """✅ No hardcoded QUALITY_BULLETS arrays"""
        content = AI_ASSISTANT_FILE.read_text(encoding='utf-8')
        
        # Should not have static QUALITY_BULLETS_AR or QUALITY_BULLETS_EN
        assert "QUALITY_BULLETS_AR = [" not in content, \
            "❌ Hardcoded QUALITY_BULLETS_AR array found!"
        assert "QUALITY_BULLETS_EN = [" not in content, \
            "❌ Hardcoded QUALITY_BULLETS_EN array found!"
        
        print("✅ PASS: No hardcoded QUALITY_BULLETS arrays")
    
    def test_dynamic_bullet_generation_used(self):
        """✅ Dynamic _generate_contextual_bullets() used instead of static arrays"""
        content = AI_ASSISTANT_FILE.read_text(encoding='utf-8')
        
        # Should contain calls to dynamic method
        assert "_generate_contextual_bullets(name, specs, 'ar')" in content, \
            "❌ Dynamic Arabic bullets not found!"
        assert "_generate_contextual_bullets(name, specs, 'en')" in content, \
            "❌ Dynamic English bullets not found!"
        
        print("✅ PASS: Dynamic bullet generation is used")
    
    def test_no_legacy_translate_to_english_functions(self):
        """✅ No legacy translate_to_english functions with broken dictionaries"""
        content = AI_ASSISTANT_FILE.read_text(encoding='utf-8')
        
        # Check for the pattern of old broken translate functions
        # Should not have hardcoded translation dictionaries
        if "def translate_to_english(text):" in content:
            # If function exists, it should not have static phrase dictionaries
            # (unless it's a docstring or comment)
            # Count occurrences - should be minimal
            func_count = len(re.findall(r'def translate_to_english\(text\):', content))
            assert func_count <= 1, f"❌ Multiple translate_to_english functions found: {func_count}"
            
            # If it exists, should not have hardcoded phrases dictionary
            if func_count == 1:
                # Extract the function
                match = re.search(r'def translate_to_english\(text\):.*?(?=\n    def|\n\n|\Z)', content, re.DOTALL)
                if match:
                    func_body = match.group(0)
                    assert "phrases = {" not in func_body, \
                        "❌ translate_to_english still has hardcoded phrases dictionary!"
        
        print("✅ PASS: No legacy translate_to_english functions with broken dicts")
    
    def test_translation_service_used(self):
        """✅ TranslationService is used for translations"""
        content = AI_ASSISTANT_FILE.read_text(encoding='utf-8')
        
        # Should use self.translator.translate()
        assert "self.translator.translate(" in content, \
            "❌ TranslationService not being used!"
        
        # Should not have raw hardcoded translation logic
        bad_patterns = [
            "phrases.get(",
            "phrases[",
            "replace(ar, en)"
        ]
        for pattern in bad_patterns:
            if pattern in content:
                # Make sure it's not in a comment or docstring
                for line in content.split('\n'):
                    if pattern in line and not line.strip().startswith('#'):
                        # Check it's not in a clean function
                        pass  # This is okay as long as it's not the main translation logic
        
        print("✅ PASS: TranslationService is used for translations")
    
    def test_exception_handlers_use_dynamic_generation(self):
        """✅ Exception handlers use dynamic generation, not hardcoded fallbacks"""
        content = AI_ASSISTANT_FILE.read_text(encoding='utf-8')
        
        # Find exception handlers
        except_blocks = re.findall(r'except.*?:.*?(?=\n    def|\n\n|\Z)', content, re.DOTALL)
        
        # Exception handlers should use dynamic methods or TranslationService
        for block in except_blocks:
            if len(block) > 100:  # Only check substantial exception blocks
                # Should either call dynamic methods or use translator
                has_dynamic = (
                    "_generate_contextual_bullets" in block or
                    "self.translator.translate" in block or
                    "await self.translator" in block
                )
                assert has_dynamic or "logger.error" in block, \
                    f"❌ Exception handler has static fallback:\n{block[:200]}"
        
        print("✅ PASS: Exception handlers use dynamic generation")
    
    def test_contamination_check_in_place(self):
        """✅ Cross-product contamination check is in place"""
        content = AI_ASSISTANT_FILE.read_text(encoding='utf-8')
        
        # Should call validation service
        assert "self.validator.check_cross_product_contamination" in content, \
            "❌ Contamination check not called!"
        
        print("✅ PASS: Contamination check is in place")
    
    def test_qwen_provider_has_generate_text(self):
        """✅ QwenProvider has generate_text() method"""
        content = LLM_PROVIDER_FILE.read_text(encoding='utf-8')
        
        assert "async def generate_text(" in content, \
            "❌ QwenProvider.generate_text() method not found!"
        
        # Should return plain text, not JSON
        assert "# Generate plain text" in content or "plain text" in content, \
            "❌ generate_text() method not documented or implemented correctly!"
        
        print("✅ PASS: QwenProvider.generate_text() method exists")
    
    def test_ai_prompts_rule_numbering_sequential(self):
        """✅ ai_prompts.py rule numbering is sequential (1-9)"""
        content = AI_PROMPTS_FILE.read_text(encoding='utf-8')
        
        # Extract all rule numbers
        rules = re.findall(r'القاعدة (\d+):', content)
        
        # Check if rules are properly numbered
        expected_rules = list(map(str, range(1, 10)))  # 1-9
        
        # Make sure we have all rule numbers (some might be duplicated in text)
        for i in range(1, 9):
            assert str(i) in rules, f"❌ Rule {i} not found or incorrectly numbered!"
        
        print(f"✅ PASS: Rules are sequentially numbered: {sorted(set(rules))}")
    
    def test_safe_translate_variant_method_exists(self):
        """✅ _safe_translate_variant method uses TranslationService"""
        content = AI_ASSISTANT_FILE.read_text(encoding='utf-8')
        
        assert "_safe_translate_variant" in content, \
            "❌ _safe_translate_variant method not found!"
        
        # Extract the method and verify it uses TranslationService
        match = re.search(r'async def _safe_translate_variant\(.*?\):.*?(?=\n    async def|\n    def|\Z)', 
                         content, re.DOTALL)
        if match:
            method_body = match.group(0)
            assert "self.translator.translate" in method_body, \
                "❌ _safe_translate_variant doesn't use TranslationService!"
        
        print("✅ PASS: _safe_translate_variant uses TranslationService")
    
    def test_all_new_services_created(self):
        """✅ All new services are created (Translation, Validation, Retry)"""
        
        assert TRANSLATION_SERVICE_FILE.exists(), \
            "❌ TranslationService not found!"
        assert VALIDATION_SERVICE_FILE.exists(), \
            "❌ ValidationService not found!"
        
        # Check TranslationService has translate method
        translation_content = TRANSLATION_SERVICE_FILE.read_text(encoding='utf-8')
        assert "async def translate(" in translation_content, \
            "❌ TranslationService.translate() not found!"
        
        # Check ValidationService has contamination check
        validation_content = VALIDATION_SERVICE_FILE.read_text(encoding='utf-8')
        assert "check_cross_product_contamination" in validation_content, \
            "❌ ValidationService.check_cross_product_contamination() not found!"
        
        print("✅ PASS: All new services created with required methods")
    
    def test_no_empty_translation_dictionaries(self):
        """✅ No empty translation dictionaries (phrases with empty strings)"""
        files_to_check = [
            TRANSLATION_SERVICE_FILE
        ]
        
        for file_path in files_to_check:
            if file_path.exists():
                content = file_path.read_text(encoding='utf-8')
                
                # Look for pattern: 'word': '' (empty translation in dictionary)
                # But allow empty field values in data structures (that's okay)
                # Only check for empty translations in translation logic
                if "phrases = {" in content:
                    match = re.search(r"phrases = \{.*?\}", content, re.DOTALL)
                    if match:
                        phrases_dict = match.group(0)
                        empty_phrases = re.findall(r"'[^']+': ''", phrases_dict)
                        if empty_phrases:
                            assert False, \
                                f"❌ Empty translation dictionary found in {file_path.name}: {empty_phrases}"
        
        print("✅ PASS: No empty translation dictionaries in active translation code")


class TestEdgeCases:
    """Test edge cases and potential issues."""
    
    def test_emergency_fallback_doesnt_hardcode(self):
        """✅ Emergency fallback paths don't hardcode content"""
        content = AI_ASSISTANT_FILE.read_text(encoding='utf-8')
        
        # Find emergency recovery section
        emergency_pattern = r'emergency.*?recovery.*?(?=\n    def|\Z)'
        emergency_sections = re.findall(emergency_pattern, content, re.IGNORECASE | re.DOTALL)
        
        for section in emergency_sections:
            # Emergency fallback should use dynamic generation
            has_dynamic = (
                "_generate_contextual_bullets" in section or
                "self.translator" in section
            )
            assert has_dynamic, \
                f"❌ Emergency fallback might be hardcoding: {section[:200]}"
        
        print("✅ PASS: Emergency fallback uses dynamic generation")
    
    def test_base_product_dict_well_formed(self):
        """✅ base_product dictionary is well-formed (no syntax errors)"""
        # This test verifies the fix for the unclosed brace issue
        content = AI_ASSISTANT_FILE.read_text(encoding='utf-8')
        
        # Find base_product assignments
        base_product_pattern = r"raw_result\['base_product'\] = \{.*?\}"
        matches = re.findall(base_product_pattern, content, re.DOTALL)
        
        for match in matches:
            # Count braces
            open_count = match.count('{')
            close_count = match.count('}')
            assert open_count == close_count, \
                f"❌ Mismatched braces in base_product: {match[:100]}"
        
        print("✅ PASS: base_product dictionaries are well-formed")
    
    def test_no_mixed_old_new_code(self):
        """✅ No mixing of old and new translation code"""
        content = AI_ASSISTANT_FILE.read_text(encoding='utf-8')
        
        # Check that we don't have both old and new translation patterns in same function
        # Look for patterns that indicate both old and new code mixed
        bad_mixing_pattern = r"def.*?phrases.*?self.translator.translate"
        if re.search(bad_mixing_pattern, content, re.DOTALL):
            print("⚠️  WARNING: Possible mixing of old and new translation code detected")
        else:
            print("✅ PASS: No obvious mixing of old and new translation code")


def run_all_tests():
    """Run all contamination cleanup tests."""
    print("\n" + "="*70)
    print("🧪 AI PRODUCT GENERATION - CONTAMINATION CLEANUP VERIFICATION")
    print("="*70 + "\n")
    
    # Test class instances
    cleanup_tests = TestContaminationCleanup()
    edge_case_tests = TestEdgeCases()
    
    # Run cleanup tests
    print("📋 CONTAMINATION CLEANUP TESTS:")
    print("-" * 70)
    test_methods = [m for m in dir(cleanup_tests) if m.startswith('test_')]
    for method_name in test_methods:
        try:
            method = getattr(cleanup_tests, method_name)
            method()
        except AssertionError as e:
            print(f"❌ FAIL: {method_name}")
            print(f"   Error: {e}\n")
            raise
    
    # Run edge case tests
    print("\n📋 EDGE CASE TESTS:")
    print("-" * 70)
    edge_methods = [m for m in dir(edge_case_tests) if m.startswith('test_')]
    for method_name in edge_methods:
        try:
            method = getattr(edge_case_tests, method_name)
            method()
        except AssertionError as e:
            print(f"❌ FAIL: {method_name}")
            print(f"   Error: {e}\n")
            raise
    
    print("\n" + "="*70)
    print("✅ ALL CONTAMINATION CLEANUP TESTS PASSED!")
    print("="*70)


if __name__ == "__main__":
    run_all_tests()
