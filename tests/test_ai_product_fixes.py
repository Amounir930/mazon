import pytest
from app.services.ai_product_assistant import AIProductAssistant

@pytest.mark.asyncio
async def test_no_cross_product_contamination():
    """تأكد أن منتج 'خلاط' لا يحتوي على كلمات 'فانوس رمضان'"""
    assistant = AIProductAssistant()
    result = await assistant.generate_products(
        name="خلاط كهربائي 300 واط",
        specs="5 سرعات، ستانلس ستيل، سهل التنظيف",
        copies=2
    )

    # Check base product
    all_text_ar = " ".join(result.base_product.bullet_points_ar).lower()
    assert "فانوس" not in all_text_ar, "Found Ramadan lantern content in blender product!"
    assert "رمضان" not in all_text_ar

    # Check variants
    for variant in result.variants:
        assert "فانوس" not in variant.description_ar.lower()
        assert "رمضان" not in variant.description_ar.lower()

    # Check specs fidelity
    assert "ستانلس ستيل" in all_text_ar or "stainless steel" in " ".join(result.base_product.bullet_points_en).lower()

@pytest.mark.asyncio
async def test_translation_quality():
    """تأكد أن الترجمة الإنجليزية دقيقة ولا تحتوي على 'Translation of'"""
    assistant = AIProductAssistant()
    result = await assistant.generate_products(
        name="منظم ملابس",
        specs="قماش غير منسوج، 6 رفوف، قابل للطي",
        copies=1
    )

    variant = result.variants[0]
    assert not variant.name_en.startswith("Translation of"), f"Bad name translation: {variant.name_en}"
    assert not variant.description_en.startswith("Translation of"), f"Bad desc translation: {variant.description_en}"
    assert len(variant.description_en.split()) >= 50, "Description too short"