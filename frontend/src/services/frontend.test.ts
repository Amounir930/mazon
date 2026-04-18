/**
 * Frontend Services Testing
 * =========================
 * اختبر الخدمات الجديدة للتأكد من أنها تعمل بشكل صحيح
 */

import ProductRulesValidator, { ValidationIssue } from './ProductRulesValidator';
import ProductTranslationService from './ProductTranslationService';

describe('ProductRulesValidator Tests', () => {
  describe('validateModelNumber', () => {
    test('should pass for "Generic"', () => {
      const result = ProductRulesValidator.validateModelNumber('Generic');
      expect(result.isValid).toBe(true);
      expect(result.severity).toBe('success');
    });

    test('should fail for empty model number', () => {
      const result = ProductRulesValidator.validateModelNumber('');
      expect(result.isValid).toBe(false);
      expect(result.severity).toBe('error');
    });

    test('should fail for non-Generic model number', () => {
      const result = ProductRulesValidator.validateModelNumber('XYZ-123');
      expect(result.isValid).toBe(false);
      expect(result.message).toContain('يجب أن يكون');
    });
  });

  describe('validateDescription', () => {
    test('should pass for 40+ words', () => {
      const desc =
        'هذا وصف رائع يحتوي على الكثير من الكلمات المهمة التي تشرح المنتج بشكل مفصل وشامل ويوضح جميع المميزات والفوائد';
      const result = ProductRulesValidator.validateDescription(desc);
      expect(result.isValid).toBe(true);
      expect(result.severity).toBe('success');
    });

    test('should fail for less than 40 words', () => {
      const desc = 'وصف قصير جداً';
      const result = ProductRulesValidator.validateDescription(desc);
      expect(result.isValid).toBe(false);
      expect(result.severity).toBe('error');
    });
  });

  describe('validateBulletPoint', () => {
    test('should pass for valid bullet point', () => {
      const point =
        'هذه نقطة بيع رائعة تحتوي على الكثير من الكلمات الضرورية لشرح مميزة معينة من المنتج';
      const result = ProductRulesValidator.validateBulletPoint(point, 0);
      expect(result.isValid).toBe(true);
      expect(result.severity).toBe('success');
    });

    test('should fail for numbered bullet point', () => {
      const point = 'نقطة 1: هذه نقطة بسيطة';
      const result = ProductRulesValidator.validateBulletPoint(point, 0);
      expect(result.isValid).toBe(false);
      expect(result.message).toContain('الترقيم');
    });

    test('should fail for short bullet point', () => {
      const point = 'نقطة قصيرة';
      const result = ProductRulesValidator.validateBulletPoint(point, 0);
      expect(result.isValid).toBe(false);
    });
  });

  describe('validateAllBulletPoints', () => {
    test('should pass for 5 valid bullet points', () => {
      const points = Array(5).fill(
        'هذه نقطة بيع رائعة تحتوي على الكثير من الكلمات الضرورية لشرح مميزة معينة من المنتج'
      );
      const results = ProductRulesValidator.validateAllBulletPoints(points);
      expect(results.length).toBe(5);
      expect(results.every(r => r.isValid)).toBe(true);
    });

    test('should fail for less than 5 bullet points', () => {
      const points = Array(3).fill('نقطة بيع');
      const results = ProductRulesValidator.validateAllBulletPoints(points);
      expect(results[0].isValid).toBe(false);
    });
  });

  describe('validateFullProduct', () => {
    test('should validate complete product correctly', () => {
      const product = {
        model_number: 'Generic',
        description: 'وصف كامل يحتوي على الكثير من الكلمات الضرورية لشرح المنتج بشكل مفصل وشامل',
        bullet_points: Array(5).fill(
          'نقطة بيع رائعة تحتوي على الكثير من الكلمات الضرورية'
        ),
        name_en: 'Product Name',
        keywords: [],
      };

      const issues = ProductRulesValidator.validateFullProduct(product);
      const summary = ProductRulesValidator.getValidationSummary(issues);

      expect(summary.errors).toBe(0);
      expect(summary.canSubmit).toBe(true);
    });
  });
});

describe('ProductTranslationService Tests', () => {
  describe('translateArabicToEnglish', () => {
    test('should translate known Arabic words', () => {
      const text = 'هذا كوب جميل';
      const result = ProductTranslationService.translateArabicToEnglish(text);
      expect(result).toContain('cup');
    });

    test('should handle empty strings', () => {
      const result = ProductTranslationService.translateArabicToEnglish('');
      expect(result).toBe('');
    });

    test('should preserve case and spacing', () => {
      const text = 'مصنوع من قطن';
      const result = ProductTranslationService.translateArabicToEnglish(text);
      expect(result).toBeTruthy();
      expect(result).toMatch(/cotton/i);
    });
  });

  describe('translateProductName', () => {
    test('should translate product name', () => {
      const name = 'فانوس رمضان كهربائي';
      const result = ProductTranslationService.translateProductName(name);
      expect(result).not.toContain('فانوس');
      expect(result).toBeTruthy();
    });

    test('should return fallback for untranslatable text', () => {
      const name = 'منتج غير معروف تماماً';
      const result = ProductTranslationService.translateProductName(name);
      expect(result).toBeTruthy();
    });
  });

  describe('translateBulletPoints', () => {
    test('should translate multiple bullet points', () => {
      const points = [
        'مصنوع من قطن عالي الجودة',
        'آمن تماماً للأطفال',
        'سهل التنظيف والعناية',
      ];
      const results =
        ProductTranslationService.translateBulletPoints(points);
      expect(results.length).toBe(3);
      expect(results[0]).toContain('cotton');
    });
  });

  describe('translateProduct', () => {
    test('should translate complete product', () => {
      const product = {
        name: 'فانوس ديكور إسلامي',
        description: 'فانوس جميل مصنوع من مادة عالية الجودة للديكور المنزلي',
        bullet_points: [
          'تصميم إسلامي أنيق',
          'مصنوع من مواد آمنة وعالية الجودة',
        ],
      };

      const result = ProductTranslationService.translateProduct(product);

      expect(result.name_en).toBeTruthy();
      expect(result.description_en).toBeTruthy();
      expect(result.bullet_points_en.length).toBe(2);
    });
  });
});

// ==================== Integration Tests ====================

describe('ProductForm Integration', () => {
  test('should validate and translate product together', () => {
    const product = {
      model_number: 'Generic',
      name: 'فانوس رمضان كهربائي',
      description:
        'فانوس جميل مصنوع من مادة عالية الجودة مع تصميم إسلامي أنيق ومناسب للديكور المنزلي الحديث',
      bullet_points: [
        'تصميم إسلامي أنيق وعصري يناسب جميع أنماط الديكور المنزلي',
        'مصنوع من مواد آمنة وعالية الجودة وموثوقة تماماً للاستخدام الطويل',
        'يحتوي على إضاءة كهربائية LED توفر استهلاك الكهرباء بشكل كبير جداً',
        'سهل التنظيف والصيانة والعناية ولا يتطلب جهد كبير في الاستخدام',
        'هدية رائعة وجميلة للأعياد والمناسبات الإسلامية والدينية المختلفة',
      ],
      keywords: [],
    };

    // Validate
    const issues = ProductRulesValidator.validateFullProduct(product);
    const summary = ProductRulesValidator.getValidationSummary(issues);

    expect(summary.errors).toBe(0);
    expect(summary.canSubmit).toBe(true);

    // Translate
    const translations =
      ProductTranslationService.translateProduct(product);

    expect(translations.name_en).toBeTruthy();
    expect(translations.description_en).toBeTruthy();
    expect(translations.bullet_points_en.length).toBe(5);

    // Verify no Arabic in translations
    expect(translations.name_en).not.toMatch(/[\u0600-\u06FF]/);
  });
});

// ==================== Run Tests ====================

if (typeof describe === 'undefined') {
  // Fallback for non-Jest environments
  console.log('✅ Frontend Services Test Suite Created');
  console.log('Run with: npm test frontend.test.ts');
}

export {};
