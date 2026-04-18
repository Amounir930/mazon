#!/usr/bin/env python3
"""
اختبار نظام الأتمتة والقواعس
============================
هذا السكريبت يختبر محرك الأتمتة والقواعس
"""

import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.services.rules_engine import RulesEngine
from app.services.automation_engine import AutomationEngine


def test_rules_engine():
    """اختبار محرك القواعس"""
    print("\n" + "="*60)
    print("🧪 اختبار محرك القواعس (RulesEngine)")
    print("="*60)
    
    try:
        engine = RulesEngine()
        print("✅ تم تحميل محرك القواعس بنجاح")
        
        # اختبار الحصول على معلومات الفئة
        category_info = engine.get_category_info("HOME_KITCHEN")
        print(f"\n📦 معلومات فئة 'أدوات المطبخ':")
        print(f"   - اسم عربي: {category_info.get('arabic_name')}")
        print(f"   - الحد الأدنى للهامش: {category_info.get('min_margin_percent')}%")
        print(f"   - النقاط النموذجية: {len(category_info.get('typical_bullet_points', []))} نقطة")
        
        # اختبار التحقق من منتج
        test_product = {
            'sku': 'TEST-001',
            'name': 'كوب قهوة',
            'price': 50,
            'product_type': 'HOME_KITCHEN',
            'condition': 'New',
            'fulfillment_channel': 'MFN',
            'main_image': 'image.jpg',
        }
        
        print(f"\n🔍 اختبار تطبيق القيم الافتراضية:")
        product_with_defaults, applied = engine.apply_defaults(test_product.copy())
        print(f"   - عدد القيم الافتراضية المطبقة: {len(applied)}")
        for field, value in applied.items():
            print(f"     • {field} = {value}")
        
        print(f"\n✔️ اختبار التحقق من المنتج:")
        result = engine.validate_product(product_with_defaults)
        print(f"   - المنتج صالح: {result.valid}")
        print(f"   - عدد الأخطاء: {len(result.errors)}")
        print(f"   - عدد التحذيرات: {len(result.warnings)}")
        
        if result.warnings:
            print(f"\n   ⚠️  التحذيرات:")
            for warn in result.warnings[:3]:
                print(f"      - {warn.field}: {warn.message}")
        
        return True
        
    except Exception as e:
        print(f"❌ خطأ: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_automation_engine():
    """اختبار محرك الأتمتة"""
    print("\n" + "="*60)
    print("🤖 اختبار محرك الأتمتة (AutomationEngine)")
    print("="*60)
    
    try:
        engine = AutomationEngine()
        print("✅ تم تحميل محرك الأتمتة بنجاح")
        
        # منتج اختبار
        test_product = {
            'sku': 'TEST-ENHANCE-001',
            'name': 'حقيبة يد',
            'price': 100,
            'cost': 70,
            'product_type': 'APPAREL',
            'condition': 'New',
            'fulfillment_channel': 'MFN',
            'main_image': 'image.jpg',
            'description': 'حقيبة جميلة',
            'bullet_points': [],
        }
        
        print(f"\n🔧 اختبار التحسين التلقائي:")
        enhancement = engine.enhance_product(test_product.copy(), auto_apply=False)
        print(f"   - عدد التغييرات المقترحة: {len(enhancement.changes)}")
        
        if enhancement.changes:
            print(f"   📝 التغييرات:")
            for field, change in enhancement.changes.items():
                print(f"      • {field}:")
                print(f"        - القديم: {str(change['old'])[:50]}...")
                print(f"        - الجديد: {str(change['new'])[:50]}...")
        
        print(f"\n✔️ نتيجة التحقق بعد التحسين:")
        print(f"   - صالح: {enhancement.validation_result.valid}")
        print(f"   - أخطاء: {len(enhancement.validation_result.errors)}")
        print(f"   - تحذيرات: {len(enhancement.validation_result.warnings)}")
        
        print(f"\n📊 الاقتراحات الإضافية:")
        if enhancement.suggestions:
            for field, suggestion in enhancement.suggestions.items():
                print(f"      • {field}: {suggestion.get('reason', 'N/A')}")
        else:
            print(f"   لا توجد اقتراحات إضافية")
        
        return True
        
    except Exception as e:
        print(f"❌ خطأ: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_readiness_check():
    """اختبار فحص الجاهزية"""
    print("\n" + "="*60)
    print("📋 اختبار فحص جاهزية الإرسال")
    print("="*60)
    
    try:
        engine = AutomationEngine()
        
        # منتج ناقص
        incomplete_product = {
            'sku': 'TEST-READY-001',
            'name': 'ساعة',
            'price': 200,
            'product_type': 'ELECTRONICS',
            'condition': 'New',
            'fulfillment_channel': 'MFN',
            # ناقص: main_image و description و bullet_points
        }
        
        print(f"\n🔎 فحص المنتج الناقص:")
        result = engine.check_ready_for_submission(incomplete_product)
        
        print(f"   - جاهز للإرسال: {result['ready']}")
        print(f"   - عدد المشاكل: {len(result['issues'])}")
        
        if result['issues']:
            print(f"\n   🚫 المشاكل الموجودة:")
            for issue in result['issues'][:5]:
                print(f"      - [{issue['type'].upper()}] {issue['field']}: {issue['message']}")
        
        return True
        
    except Exception as e:
        print(f"❌ خطأ: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n" + "🎯 "*20)
    print("اختبار شامل لنظام الأتمتة والقواعس")
    print("🎯 "*20)
    
    results = {
        "Rules Engine": test_rules_engine(),
        "Automation Engine": test_automation_engine(),
        "Readiness Check": test_readiness_check(),
    }
    
    print("\n" + "="*60)
    print("📊 نتائج الاختبارات:")
    print("="*60)
    
    for test_name, passed in results.items():
        status = "✅ نجح" if passed else "❌ فشل"
        print(f"   {status:15} - {test_name}")
    
    print("\n" + "="*60)
    total_passed = sum(1 for v in results.values() if v)
    print(f"✨ النتيجة النهائية: {total_passed}/{len(results)} اختبارات نجحت")
    print("="*60 + "\n")
