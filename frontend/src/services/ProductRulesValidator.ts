/**
 * Product Rules Validation Service
 * ===================================
 * فحص القواعس الصارمة الإلزامية للمنتجات
 */

export interface ValidationIssue {
  field: string;
  isValid: boolean;
  message: string;
  wordCount?: number;
  minRequired?: number;
  severity: 'error' | 'warning' | 'success';
}

export class ProductRulesValidator {
  /**
   * فحص رقم الموديل - يجب أن يكون "Generic"
   */
  static validateModelNumber(modelNumber: string | undefined): ValidationIssue {
    if (!modelNumber || modelNumber.trim() === '') {
      return {
        field: 'model_number',
        isValid: false,
        message: 'رقم الموديل مطلوب - يجب أن يكون: Generic',
        severity: 'error',
      };
    }

    if (modelNumber.trim() !== 'Generic') {
      return {
        field: 'model_number',
        isValid: false,
        message: `رقم الموديل يجب أن يكون "Generic"، والحالي: "${modelNumber}"`,
        severity: 'error',
      };
    }

    return {
      field: 'model_number',
      isValid: true,
      message: '✅ رقم الموديل صحيح',
      severity: 'success',
    };
  }

  /**
   * فحص الوصف - يجب أن يكون 40+ كلمة
   */
  static validateDescription(description: string | undefined, field: string = 'description'): ValidationIssue {
    if (!description || description.trim() === '') {
      return {
        field: field,
        isValid: false,
        message: 'الوصف مطلوب',
        wordCount: 0,
        minRequired: 40,
        severity: 'error',
      };
    }

    const wordCount = description.trim().split(/\s+/).length;
    const isValid = wordCount >= 40;

    return {
      field: field,
      isValid,
      message: isValid 
        ? `✅ الوصف صحيح (${wordCount} كلمة)`
        : `❌ الوصف قصير جداً: ${wordCount} كلمة (المطلوب: 40+)`,
      wordCount,
      minRequired: 40,
      severity: isValid ? 'success' : 'error',
    };
  }

  /**
   * فحص نقاط البيع - كل نقطة يجب أن تكون 15+ كلمة بدون ترقيم
   */
  static validateBulletPoint(point: string | undefined, index: number): ValidationIssue {
    if (!point || point.trim() === '') {
      return {
        field: `bullet_point_${index}`,
        isValid: false,
        message: `نقطة البيع ${index + 1} مطلوبة`,
        wordCount: 0,
        minRequired: 15,
        severity: 'error',
      };
    }

    // إزالة الترقيم إذا كان موجوداً
    const cleanedPoint = point.replace(/^\s*نقطة\s+\d+:\s*/i, '').trim();

    // فحص وجود ترقيم
    const hasNumbering = /^\s*نقطة\s+\d+:\s*/i.test(point);

    const wordCount = cleanedPoint.split(/\s+/).length;
    const isValid = wordCount >= 15;

    if (hasNumbering) {
      return {
        field: `bullet_point_${index}`,
        isValid: false,
        message: `❌ نقطة البيع ${index + 1}: إزالة الترقيم - اكتب الجملة مباشرة`,
        wordCount: 0,
        minRequired: 15,
        severity: 'error',
      };
    }

    if (!isValid) {
      return {
        field: `bullet_point_${index}`,
        isValid: false,
        message: `❌ نقطة البيع ${index + 1}: ${wordCount} كلمة (المطلوب: 15+)`,
        wordCount,
        minRequired: 15,
        severity: 'error',
      };
    }

    return {
      field: `bullet_point_${index}`,
      isValid: true,
      message: `✅ نقطة البيع ${index + 1} صحيحة (${wordCount} كلمة)`,
      wordCount,
      minRequired: 15,
      severity: 'success',
    };
  }

  /**
   * فحص جميع نقاط البيع
   */
  static validateAllBulletPoints(bulletPoints: string[] | undefined): ValidationIssue[] {
    if (!bulletPoints || bulletPoints.length === 0) {
      return [{
        field: 'bullet_points',
        isValid: false,
        message: 'يجب إضافة 5 نقاط بيع',
        severity: 'error',
      }];
    }

    if (bulletPoints.length !== 5) {
      return [{
        field: 'bullet_points',
        isValid: false,
        message: `يجب أن تكون 5 نقاط، والحالي: ${bulletPoints.length}`,
        severity: 'error',
      }];
    }

    return bulletPoints.map((point, idx) => 
      this.validateBulletPoint(point, idx)
    );
  }

  /**
   * فحص الترجمة الإنجليزية - يجب أن لا تكون فارغة
   */
  static validateEnglishName(name_en: string | undefined, field: string = 'name_en'): ValidationIssue {
    if (!name_en || name_en.trim() === '') {
      return {
        field: field,
        isValid: false,
        message: 'اسم المنتج بالإنجليزية مطلوب',
        severity: 'error',
      };
    }

    // فحص أن الترجمة ليست عربية
    if (/[\u0600-\u06FF]/.test(name_en)) {
      return {
        field: field,
        isValid: false,
        message: '❌ الاسم يجب أن يكون بالإنجليزية فقط',
        severity: 'error',
      };
    }

    return {
      field: field,
      isValid: true,
      message: '✅ الترجمة الإنجليزية موجودة',
      severity: 'success',
    };
  }

  /**
   * فحص الكلمات المفتاحية - لا تكون "كلمة 1" و "كلمة 2"
   */
  static validateKeywords(keywords: string[] | undefined): ValidationIssue {
    if (!keywords || keywords.length === 0) {
      return {
        field: 'keywords',
        isValid: true,
        message: '✅ الكلمات المفتاحية اختيارية',
        severity: 'success',
      };
    }

    // فحص القيم الافتراضية الخاطئة
    const invalidKeywords = keywords.filter(k => 
      k.match(/^كلمة\s+\d+$|^keyword\s+\d+$/i)
    );

    if (invalidKeywords.length > 0) {
      return {
        field: 'keywords',
        isValid: false,
        message: `❌ الكلمات المفتاحية غير صحيحة: ${invalidKeywords.join(', ')} - أضف كلمات حقيقية`,
        severity: 'warning',
      };
    }

    return {
      field: 'keywords',
      isValid: true,
      message: `✅ الكلمات المفتاحية موجودة (${keywords.length})`,
      severity: 'success',
    };
  }

  /**
   * فحص شامل لكل المنتج
   */
  static validateFullProduct(product: any): ValidationIssue[] {
    const issues: ValidationIssue[] = [];

    // 1. رقم الموديل
    issues.push(this.validateModelNumber(product.model_number));

    // 2. الوصف العربي
    if (product.description_ar) {
      issues.push(this.validateDescription(product.description_ar, 'description_ar'));
    }

    // 3. الوصف الإنجليزي
    if (product.description_en) {
      issues.push(this.validateDescription(product.description_en, 'description_en'));
    }

    // 4. الاسم العربي
    if (product.name_ar) {
      issues.push(this.validateEnglishName(product.name_ar, 'name_ar'));
    }

    // 5. الاسم الإنجليزي
    if (product.name_en) {
      issues.push(this.validateEnglishName(product.name_en, 'name_en'));
    }

    // 6. نقاط البيع
    if (product.bullet_points && Array.isArray(product.bullet_points)) {
      issues.push(...this.validateAllBulletPoints(product.bullet_points));
    }

    // 7. الكلمات المفتاحية
    if (product.keywords) {
      issues.push(this.validateKeywords(product.keywords));
    }

    return issues;
  }

  /**
   * معلومات عن الأخطاء الحالية
   */
  static getValidationSummary(issues: ValidationIssue[]): {
    errors: number;
    warnings: number;
    success: number;
    canSubmit: boolean;
  } {
    const errors = issues.filter(i => i.severity === 'error').length;
    const warnings = issues.filter(i => i.severity === 'warning').length;
    const success = issues.filter(i => i.severity === 'success').length;

    return {
      errors,
      warnings,
      success,
      canSubmit: errors === 0,
    };
  }
}

export default ProductRulesValidator;
