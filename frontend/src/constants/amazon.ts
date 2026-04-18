/**
 * Amazon SP-API Constants
 * 
 * جميع الثوابت والقوائم المنسدلة المطلوبة لـ Amazon SP-API
 * مصدر واحد مركزي - ممنوع الـ Hardcoding في الـ Components
 */

// ==================== Product Type Categories ====================
// كل مجموعة لها browse nodes خاصة بها
// تم حذف// productType ثابت = HOME_ORGANIZERS_AND_STORAGE (أمازون مصر ترفض أي نوع آخر)
// الـ browse_node_id هو اللي يحدد الفئة الفعلية للمنتج

export const PRODUCT_TYPE_CATEGORIES = [
  { value: 'STORAGE', label: '📦 تخزين وتنظيم', icon: '📦', amazonType: 'HOME_ORGANIZERS_AND_STORAGE' },
  { value: 'KITCHEN', label: '🍳 أدوات المطبخ', icon: '🍳', amazonType: 'HOME_ORGANIZERS_AND_STORAGE' },
  { value: 'BATHROOM', label: '🛁 مستلزمات الحمام', icon: '🛁', amazonType: 'HOME_ORGANIZERS_AND_STORAGE' },
  { value: 'DECOR', label: '🎨 ديكور وزينة', icon: '🎨', amazonType: 'HOME_ORGANIZERS_AND_STORAGE' },
  { value: 'CLEANING', label: '🧹 تنظيف المنزل', icon: '🧹', amazonType: 'HOME_ORGANIZERS_AND_STORAGE' },
  { value: 'HOME_IMPROVEMENT', label: '🛠️ أدوات وتحسين المنزل', icon: '🛠️', amazonType: 'HOME_ORGANIZERS_AND_STORAGE' },
  { value: 'SHIPPING_SUPPLIES', label: '🚚 لوازم التغليف والشحن', icon: '🚚', amazonType: 'HOME_ORGANIZERS_AND_STORAGE' },
  { value: 'ARTS_AND_CRAFTS', label: '✂️ الفنون والحرف', icon: '✂️', amazonType: 'HOME_ORGANIZERS_AND_STORAGE' },
] as const

// PRODUCT_TYPES — للتوافقية مع الكود القديم
export const PRODUCT_TYPES = PRODUCT_TYPE_CATEGORIES

// ==================== Browse Nodes by Category ====================
// Browse Node IDs مأخوذة من Amazon SP-API JSON Schema (Egypt marketplace)
// 🔒 كل الأنواع تُرسل لأمازون كـ HOME_ORGANIZERS_AND_STORAGE

export const BROWSE_NODES_BY_TYPE: Record<string, {value: string; label: string}[]> = {
  // ====== 📦 تخزين وتنظيم ======
  'STORAGE': [
    { value: '2186379931', label: 'سلال وصناديق التخزين' },
    { value: '21863898031', label: 'خزائن التخزين والملابس' },
    { value: '21863900031', label: 'مساند ورفوف وأدراج التخزين' },
    { value: '21863902031', label: 'التخزين والمنظمات المكتبية المنزلية' },
    { value: '21863904031', label: 'تخزين زينة الأعياد' },
    { value: '21863901031', label: 'تخزين ديكور الأكليل' },
    { value: '21864267031', label: 'مرفقات نظام تخزين الخزانة' },
    { value: '21864265031', label: 'خزانات الأحذية' },
    { value: '27385458031', label: 'فتحات الأحذية' },
    { value: '88739314031', label: 'حقائب متحركة' },
    { value: '207834611031', label: 'منظمات النظارات' },
    { value: '85443431031', label: 'الشماعات على شكل جيوب' },
    { value: '21864751031', label: 'رفوف مقسمة' },
    { value: '21864753031', label: 'نظام الأدراج للتخزين في الخزائن' },
    { value: '85443438031', label: 'رفوف الرسائل' },
    { value: '85443434031', label: 'رفوف لتخزين الصحف' },
    { value: '85443436031', label: 'أحواض المياه المصرفية' },
    { value: '85443441031', label: 'رفرف مكاتب البيت والتخزين' },
     { value: '21864274031', label: 'رفوف وعروض المكاتب المنزلية' },
    { value: '21864277031', label: 'مخازن اضواء الاعياد' },
    { value: '207834611031', label: 'منظمات النظارات' },
    { value: '88739314031', label: 'حقائب متحركة (Moving Bags)' },
    { value: '21864265031', label: 'خزانات الأحذية' },
    { value: '85443428031', label: 'منظم مستلزمات الغرف والحمام' },
  ],

  // ====== 🍳 أدوات المطبخ ======
  'KITCHEN': [
    { value: '21863794031', label: 'المطبخ' },
    { value: '21863790031', label: 'النفايات وإعادة التدوير' },
  ],

  // ====== 🛁 مستلزمات الحمام ======
  'BATHROOM': [
    { value: '21863800031', label: 'الحمام' },
    { value: '85443310031', label: 'منظمات وتخزين الحمام' },
    { value: '85443428031', label: 'منظم مستلزمات الغرف والحمام' },
  ],

  // ====== 🎨 ديكور وزينة ======
  'DECOR': [
    { value: '21863797031', label: 'ديكور المنزل' },
  ],

  // ====== 🧹 تنظيف المنزل ======
  'CLEANING': [
    { value: '21863798031', label: 'أدوات التنظيف المنزلية والمكانس' },
    { value: '21863790031', label: 'النفايات وإعادة التدوير' },
  ],

  // ====== 🛠️ أدوات وتحسين المنزل ======
  'HOME_IMPROVEMENT': [
    { value: '21874771031', label: 'التخزين والمنظمات المنزلية' },
    { value: '51376780031', label: 'رفوف تخزين على شكل سلالم' },
    { value: '85437693031', label: 'التخزين الخارجي' },
    { value: '21874835031', label: 'منتجات تخزين وتنظيم خاصة بالكراج' },
    { value: '21875016031', label: 'ملحقات نظام تخزين الكراج' },
    { value: '21875388031', label: 'معدات لأنطمة تخزين الكراج' },
    { value: '85437913031', label: 'رفوف وحاملات للدرجات' },
    { value: '21875019031', label: 'إكسسوارات الرفوف وأنظمة الأرفف' },
  ],

  // ====== 🚚 لوازم التغليف والشحن ======
  'SHIPPING_SUPPLIES': [
    { value: '21857449031', label: 'لوازم التغليف والشحن (الرئيسية)' },
    { value: '21857535031', label: 'استرتش التغليف الصناعي' },
    { value: '21857534031', label: 'معدات اللصق والملصقات' },
    { value: '21857538031', label: 'لوازم حزم الفقاعات (بابلز)' },
    { value: '21857537031', label: 'منتجات الغطاء البلاستيك الصناعية' },
    { value: '21857536031', label: 'تسميات التعبئة والعلامات (Labels)' },
    { value: '85363007031', label: 'الظروف البريدية للشحن المجمع' },
    { value: '85363005031', label: 'التعبئة والتغليف بالربط' },
  ],

  // ====== ✂️ الفنون والحرف ======
  'ARTS_AND_CRAFTS': [
    { value: '21863903031', label: 'تخزين مواد تغليف الهدايا' },
  ],
}

// ====== Fallback: جميع الـ Browse Nodes (للتوافقية) ======
export const BROWSE_NODES = [
  ...BROWSE_NODES_BY_TYPE['STORAGE'],
  ...BROWSE_NODES_BY_TYPE['KITCHEN'],
  ...BROWSE_NODES_BY_TYPE['BATHROOM'],
  ...BROWSE_NODES_BY_TYPE['DECOR'],
  ...BROWSE_NODES_BY_TYPE['CLEANING'],
  ...BROWSE_NODES_BY_TYPE['HOME_IMPROVEMENT'],
  ...BROWSE_NODES_BY_TYPE['SHIPPING_SUPPLIES'],
  ...BROWSE_NODES_BY_TYPE['ARTS_AND_CRAFTS'],
] as const

// ==================== Conditions ====================

export const CONDITIONS = [
  { value: 'New', label: 'جديد' },
  { value: 'New - Open Box', label: 'جديد - علبة مفتوحة' },
  { value: 'New - OEM', label: 'جديد - مصنع' },
  { value: 'Refurbished', label: 'مُجدد' },
  { value: 'Used - Like New', label: 'مستعمل - كالجديد' },
  { value: 'Used - Very Good', label: 'مستعمل - جيد جداً' },
  { value: 'Used - Good', label: 'مستعمل - جيد' },
  { value: 'Used - Acceptable', label: 'مستعمل - مقبول' },
] as const

// ==================== Fulfillment Channels ====================

export const FULFILLMENT_CHANNELS = [
  { value: 'MFN', label: 'الشحن على البائع (MFN)' },
  { value: 'AFN', label: 'الشحن على Amazon - FBA' },
] as const

// ==================== ID Types ====================

export const ID_TYPES = [
  { value: 'EAN', label: 'EAN (13 رقم)' },
  { value: 'UPC', label: 'UPC (12 رقم)' },
  { value: 'ASIN', label: 'ASIN (Amazon)' },
] as const

// ==================== Countries ====================

export const COUNTRIES = [
  { value: 'CN', label: '🇨🇳 الصين' },
  { value: 'EG', label: '🇪🇬 مصر' },
  { value: 'TR', label: '🇹🇷 تركيا' },
  { value: 'IN', label: '🇮🇳 الهند' },
  { value: 'DE', label: '🇩🇪 ألمانيا' },
  { value: 'US', label: '🇺🇸 أمريكا' },
  { value: 'GB', label: '🇬🇧 بريطانيا' },
  { value: 'IT', label: '🇮🇹 إيطاليا' },
  { value: 'FR', label: '🇫🇷 فرنسا' },
  { value: 'ES', label: '🇪🇸 إسبانيا' },
  { value: 'AE', label: '🇦🇪 الإمارات' },
  { value: 'SA', label: '🇸🇦 السعودية' },
] as const

// ==================== Unit Types ====================

export const UNIT_TYPES = [
  { value: 'count', label: 'عدد' },
  { value: 'grams', label: 'جرام' },
  { value: 'kilograms', label: 'كيلوجرام' },
  { value: 'pieces', label: 'قطعة' },
  { value: 'liters', label: 'لتر' },
  { value: 'milliliters', label: 'ملليلتر' },
  { value: 'meters', label: 'متر' },
  { value: 'centimeters', label: 'سم' },
] as const

// ==================== Weight Units ====================

export const WEIGHT_UNITS = [
  { value: 'Kilograms', label: 'كجم' },
  { value: 'Grams', label: 'جرام' },
  { value: 'Pounds', label: 'رطل' },
] as const

// ==================== Dimension Units ====================

export const DIMENSION_UNITS = [
  { value: 'Centimeters', label: 'سم' },
  { value: 'Inches', label: 'بوصة' },
] as const

// ==================== Default Values ====================

export const DEFAULT_VALUES = {
  brand: 'Generic',
  condition: 'New',
  fulfillment_channel: 'MFN',
  country_of_origin: 'CN',  // 🔒 FIXED - AI cannot modify this field
  number_of_boxes: 1,
  package_quantity: 1,
  handling_time: 1,
  unit_count: 1,
  unit_count_type: 'count',
  item_weight: 0.5,
  package_weight: 0.7,
  package_length: 25,
  package_width: 10,
  package_height: 15,
  product_type: 'STORAGE',  // 📦 الفئة الافتراضية — يتم إرسالها كـ HOME_ORGANIZERS_AND_STORAGE لأمازون
  browse_node_id: '21863799031',
  id_type: 'EAN',
} as const

// ==================== Validation Rules ====================

export const VALIDATION_RULES = {
  name_ar: { min: 3, max: 500, required: true },
  name_en: { min: 3, max: 500, required: true },
  description_ar: { min: 50, max: 2000, required: true },
  description_en: { min: 50, max: 2000, required: true },
  ean: { exact: 13, required: true },
  upc: { exact: 12, required: true },
  price: { min: 0.01, required: false }, // اختياري
  quantity: { min: 0, required: false },  // اختياري
  brand: { min: 1, max: 200, required: true },
  model_number: { min: 1, max: 100, required: true },
  manufacturer: { min: 1, max: 200, required: true },
  bullet_points: { count: 5, min: 20, max: 500, required: true }, // 5 نقاط إجبارية
