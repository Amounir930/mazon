/**
 * Product Translation Service
 * ============================
 * ترجمة النصوص العربية إلى الإنجليزية
 */

export class ProductTranslationService {
  // قاموس الترجمة الشامل
  private static readonly TRANSLATION_DICT: Record<string, string> = {
    // أدوات المطبخ
    'كوب': 'cup',
    'أكواب': 'cups',
    'طبق': 'plate',
    'أطباق': 'plates',
    'سكين': 'knife',
    'ملعقة': 'spoon',
    'شوكة': 'fork',
    'أدوات المطبخ': 'kitchen tools',
    'جودة عالية': 'high quality',
    'مواد آمنة': 'safe materials',
    'آمن على الصحة': 'health safe',
    'سهل التنظيف': 'easy to clean',
    'استخدام يومي': 'daily use',
    'ضمان': 'warranty',
    'طويل الأجل': 'long-term',

    // الملابس
    'ملابس': 'clothes',
    'أزياء': 'fashion',
    'مريح': 'comfortable',
    'عملي': 'practical',
    'خياطة': 'tailoring',
    'متقنة': 'professional',
    'ألوان عصرية': 'modern colors',
    'جذاب': 'attractive',
    'غسل آلي': 'machine washable',
    'كي آمن': 'safe ironing',
    'مادة': 'material',
    'قطن': 'cotton',
    'حرير': 'silk',

    // الهدايا والديكور
    'هدايا': 'gifts',
    'ديكور': 'decor',
    'إسلامي': 'Islamic',
    'ديني': 'religious',
    'رمضان': 'Ramadan',
    'فانوس': 'lantern',
    'كهربائي': 'electric',
    'تصميم': 'design',
    'هلال': 'crescent',
    'معلق': 'hanging',
    'إضاءة': 'lighting',
    'LED': 'LED',
    'منزلي': 'home',
    'زينة': 'decoration',

    // الإلكترونيات
    'إلكترونيات': 'electronics',
    'أحدث التقنيات': 'latest technology',
    'تقنية': 'technology',
    'ضمان رسمي': 'official warranty',
    'شركة مصنعة': 'manufacturer',
    'سهل الاستخدام': 'easy to use',
    'آمن تماماً': 'completely safe',
    'توفير': 'saving',
    'كهرباء': 'electricity',
    'عمر افتراضي': 'lifespan',
    'إصلاح معتمد': 'authorized repair',

    // الكتب
    'كتاب': 'book',
    'كتب': 'books',
    'أصلي': 'original',
    'حديث': 'recent',
    'ناشر': 'publisher',
    'مُجلد': 'hardcover',
    'معروف عالمياً': 'world famous',
    'آراء إيجابية': 'positive reviews',
    'جميع الأعمار': 'all ages',
    'ثقافات': 'cultures',
    'سعر منافس': 'competitive price',
    'مؤلف': 'author',

    // الألعاب
    'لعبة': 'toy',
    'لعب': 'toys',
    'آمنة': 'safe',
    'خالية من': 'free from',
    'مواد سامة': 'toxic materials',
    'تطور مهارات': 'skill development',
    'ذكاء': 'intelligence',
    'قوية': 'durable',
    'هدية': 'gift',
    'عيد ميلاد': 'birthday',
    'معتمدة': 'certified',
    'جهات صحية': 'health authorities',

    // عام
    'المنتج': 'product',
    'يتميز': 'features',
    'مصنوع من': 'made of',
    'يوفر': 'provides',
    'يحسن': 'improves',
    'يقلل': 'reduces',
    'مناسب ل': 'suitable for',
    'يثق': 'trust',
    'راضي': 'satisfied',
    'جودة': 'quality',
    'سعر': 'price',
    'قيمة': 'value',
    'تصميم': 'design',
    'عصري': 'modern',
    'احترافي': 'professional',
    'موثوق': 'reliable',
    'آمن': 'safe',
    'سهل': 'easy',
    'عملي': 'practical',
    'فعال': 'efficient',
  };

  /**
   * ترجمة نص عربي إلى إنجليزي
   */
  static translateArabicToEnglish(arabicText: string): string {
    if (!arabicText || arabicText.trim() === '') {
      return '';
    }

    let result = arabicText;

    // ترتيب الكلمات من الأطول للأقصر لتجنب استبدالات جزئية
    const sortedEntries = Object.entries(this.TRANSLATION_DICT).sort(
      (a, b) => b[0].length - a[0].length
    );

    for (const [arabic, english] of sortedEntries) {
      const regex = new RegExp(`\\b${arabic}\\b`, 'gi');
      result = result.replace(regex, english);
    }

    // تنظيف المسافات الزائدة
    result = result.replace(/\s+/g, ' ').trim();

    // تحويل الحرف الأول إلى كبير
    if (result.length > 0) {
      result = result.charAt(0).toUpperCase() + result.slice(1);
    }

    return result;
  }

  /**
   * ترجمة اسم المنتج مع التأكد من أنه إنجليزي
   */
  static translateProductName(arabicName: string): string {
    const translated = this.translateArabicToEnglish(arabicName);
    
    // إذا كانت الترجمة فارغة أو تحتوي على عربي، نرجع ترجمة معلبة
    if (!translated || /[\u0600-\u06FF]/.test(translated)) {
      return `Product: ${arabicName.substring(0, 50)}`;
    }

    return translated;
  }

  /**
   * ترجمة الوصف
   */
  static translateDescription(arabicDescription: string): string {
    if (!arabicDescription || arabicDescription.trim() === '') {
      return '';
    }

    return this.translateArabicToEnglish(arabicDescription);
  }

  /**
   * ترجمة نقاط البيع
   */
  static translateBulletPoints(arabicPoints: string[]): string[] {
    if (!arabicPoints || arabicPoints.length === 0) {
      return [];
    }

    return arabicPoints.map(point => this.translateArabicToEnglish(point));
  }

  /**
   * ترجمة شاملة للمنتج
   */
  static translateProduct(product: any): {
    name_en: string;
    description_en: string;
    bullet_points_en: string[];
  } {
    return {
      name_en: this.translateProductName(product.name),
      description_en: this.translateDescription(product.description),
      bullet_points_en: this.translateBulletPoints(product.bullet_points || []),
    };
  }
}

export default ProductTranslationService;
