/**
 * Amazon SP-API Constants
 * 
 * جميع الثوابت والقوائم المنسدلة المطلوبة لـ Amazon SP-API
 * مصدر واحد مركزي - ممنوع الـ Hardcoding في الـ Components
 */

// ==================== Product Types ====================

export const PRODUCT_TYPES = [
  { value: 'HOME_ORGANIZERS_AND_STORAGE', label: 'أدوات تنظيم وتخزين المنزل' },
  { value: 'BABY_PRODUCT', label: 'منتجات أطفال' },
  { value: 'APPAREL', label: 'ملابس وأزياء' },
  { value: 'HOME_KITCHEN', label: 'المنزل والمطبخ' },
  { value: 'ELECTRONICS', label: 'إلكترونيات' },
  { value: 'TOYS_AND_GAMES', label: 'ألعاب وألعاب' },
  { value: 'BEAUTY', label: 'العناية الشخصية والجمال' },
  { value: 'SPORTING_GOODS', label: 'الرياضة والسلع الرياضية' },
  { value: 'OFFICE_PRODUCTS', label: 'مستلزمات المكتبة والأدوات المكتبية' },
  { value: 'PET_PRODUCTS', label: 'مستلزمات الحيوانات الأليفة' },
] as const

// ==================== Browse Nodes ====================

export const BROWSE_NODES = [
  { value: '21863799031', label: 'المنزل والمطبخ > التخزين والتنظيم المنزلي' },
  { value: '21863899031', label: 'المنزل والمطخب > سلال وصناديق التخزين' },
  { value: '21863898031', label: 'المنزل والمطبخ > خزائن التخزين والملابس' },
  { value: '21863798031', label: 'المنزل والمطبخ > أدوات المطبخ' },
  { value: '21863797031', label: 'المنزل والمطبخ > الديكور المنزلي' },
  { value: '21863796031', label: 'المنزل والمطبخ > الأثاث' },
  { value: '21863795031', label: 'المنزل والمطبخ > الإضاءة' },
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
  { value: 'EXEMPT', label: 'معفي من الباركود (GTIN Exempt)' },
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
  country_of_origin: 'CN',
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
  product_type: 'HOME_ORGANIZERS_AND_STORAGE',
  browse_node_id: '21863799031',
  id_type: 'EAN',
} as const

// ==================== Validation Rules ====================

export const VALIDATION_RULES = {
  name_ar: { min: 3, max: 500, required: true },
  name_en: { min: 3, max: 500, required: true },
  description_ar: { min: 5, max: 2000, required: true },
  description_en: { min: 5, max: 2000, required: true },
  ean: { exact: 13, required: true },
  upc: { exact: 12, required: true },
  price: { min: 0.01, required: true },
  quantity: { min: 0, required: true },
  brand: { min: 1, max: 200, required: true },
  model_number: { min: 1, max: 100, required: true },
  manufacturer: { min: 1, max: 200, required: true },
  bullet_points: { count: 5, min: 10, max: 500 },
  images: { main: { required: true, min_size: 1000 }, extra: { max: 8 } },
} as const
