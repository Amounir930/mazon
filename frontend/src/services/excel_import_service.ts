/**
 * Excel Import Service
 * Validates and parses Excel files for bulk product import.
 * 
 * القالب الرسمي:
 * ┌──────┬─────────────┬───────┬────────┬────────┬───────┬──────┬────────┬───────┐
 * │ SKU⚠️│اسم المنتج⚠️│السعر⚠️│الكمية⚠️│البراند│الوصف  │الفئة │الحالة  │الشحن  │
 * └──────┴─────────────┴───────┴────────┴────────┴───────┴──────┴────────┴───────┘
 * ⚠️ = إجباري    باقي الأعمدة = اختياري
 */
import * as XLSX from 'xlsx'

// ==================== القالب الرسمي ====================

/** الأعمدة العربية في ملف الإكسل */
export const TEMPLATE_AR_HEADERS = [
  'SKU',
  'اسم المنتج',
  'السعر',
  'الكمية',
  'البراند',
  'الوصف',
  'الفئة',
  'حالة المنتج',
  'طريقة الشحن',
  'الباركود (UPC/EAN)',
  'بلد المنشأ',
  'الوزن (كجم)',
  'رقم الموديل',
  'المصنع',
  'الطول (سم)',
  'العرض (سم)',
  'الارتفاع (سم)',
] as const

/** الأعمدة الإجبارية */
export const REQUIRED_COLUMNS = ['sku', 'product_name', 'price', 'quantity'] as const

/** خريطة عربي → إنجليزي */
const AR_TO_EN: Record<string, string> = {
  'SKU': 'sku',
  'اسم المنتج': 'product_name',
  'اسم المنتج بالإنجليزي': 'product_name',
  'السعر': 'price',
  'الكمية': 'quantity',
  'البراند': 'brand',
  'الوصف': 'description',
  'الفئة': 'category',
  'حالة المنتج': 'condition',
  'طريقة الشحن': 'fulfillment_channel',
  'الباركود (UPC/EAN)': 'barcode',
  'الباركود': 'barcode',
  'بلد المنشأ': 'country_of_origin',
  'الوزن (كجم)': 'weight',
  'رقم الموديل': 'model_number',
  'المصنع': 'manufacturer',
  'الطول (سم)': 'length',
  'العرض (سم)': 'width',
  'الارتفاع (سم)': 'height',
}

/** خريطة إنجليزي → key موحد */
const EN_ALIASES: Record<string, string> = {
  'sku': 'sku', 'SKU': 'sku', 'رمز المنتج': 'sku', 'كود المنتج': 'sku',
  'اسم المنتج': 'product_name', 'اسم المنتج بالإنجليزي': 'product_name',
  'product_name': 'product_name', 'product name': 'product_name',
  'Product Name': 'product_name', 'title': 'product_name', 'الاسم': 'product_name',
  'name': 'product_name', 'Name': 'product_name',
  'السعر': 'price', 'price': 'price', 'Price': 'price', 'amount': 'price', 'cost': 'price',
  'الكمية': 'quantity', 'quantity': 'quantity', 'Quantity': 'quantity',
  'stock': 'quantity', 'المخزون': 'quantity', 'العدد': 'quantity',
  'البراند': 'brand', 'brand': 'brand', 'Brand': 'brand', 'الماركة': 'brand',
  'الوصف': 'description', 'description': 'description', 'Description': 'description',
  'تفاصيل': 'description', 'details': 'description',
  'الفئة': 'category', 'category': 'category', 'Category': 'category',
  'التصنيف': 'category', 'نوع المنتج': 'category',
  'product_type': 'category', 'Product Type': 'category',
  'حالة المنتج': 'condition', 'condition': 'condition', 'Condition': 'condition', 'الحالة': 'condition',
  'طريقة الشحن': 'fulfillment_channel', 'shipping': 'fulfillment_channel',
  'fulfillment': 'fulfillment_channel', 'الشحن': 'fulfillment_channel',
  'Fulfillment Channel': 'fulfillment_channel',
  'الباركود': 'barcode', 'الباركود (UPC/EAN)': 'barcode',
  'upc': 'barcode', 'UPC': 'barcode', 'ean': 'barcode', 'EAN': 'barcode',
  'barcode': 'barcode', 'External ID': 'barcode',
  'بلد المنشأ': 'country_of_origin', 'بلد الصنع': 'country_of_origin',
  'country': 'country_of_origin', 'origin': 'country_of_origin',
  'Country of Origin': 'country_of_origin',
  'الوزن (كجم)': 'weight', 'الوزن': 'weight', 'weight': 'weight', 'Weight': 'weight', 'Weight (KG)': 'weight',
  'رقم الموديل': 'model_number', 'الموديل': 'model_number', 'model': 'model_number', 'Model Number': 'model_number',
  'المصنع': 'manufacturer', 'manufacturer': 'manufacturer', 'Manufacturer': 'manufacturer',
  'الطول (سم)': 'length', 'الطول': 'length', 'length': 'length', 'Length': 'length', 'Length (CM)': 'length',
  'العرض (سم)': 'width', 'العرض': 'width', 'width': 'width', 'Width': 'width', 'Width (CM)': 'width',
  'الارتفاع (سم)': 'height', 'الارتفاع': 'height', 'height': 'height', 'Height': 'height', 'Height (CM)': 'height',
}

export const VALID_CONDITIONS = ['New', 'UsedLikeNew', 'UsedVeryGood', 'UsedGood', 'UsedAcceptable', 'Refurbished']
export const VALID_FULFILLMENT = ['MFN', 'AFN']
export const VALID_CATEGORIES = ['HOME_ORGANIZERS_AND_STORAGE', 'BABY_PRODUCT', 'APPAREL']

// ==================== Types ====================

export interface ParsedProduct {
  row: number
  sku: string
  name: string
  price: number
  quantity: number
  category?: string
  brand?: string
  description?: string
  condition: string
  fulfillment_channel: string
  upc?: string
  ean?: string
  asin?: string
  weight?: number
  dimensions?: { length?: number; width?: number; height?: number }
  country_of_origin?: string
  model_number?: string
  manufacturer?: string
  sale_price?: number
  sale_start_date?: string
  sale_end_date?: string
  handling_time?: number
  currency?: string
  bullet_points?: string[]
  parent_sku?: string
  variation_theme?: string
  is_parent?: boolean
}

export interface ValidationError {
  row: number
  field: string
  message: string
  severity: 'error' | 'warning'
}

export interface ImportResult {
  products: ParsedProduct[]
  templateType: string
  columnErrors: ValidationError[]
  rowErrors: { row: number; errors: ValidationError[] }[]
}

// ==================== Helpers ====================

/** يحول اسم العمود العربي/الإنجليزي إلى key موحد */
function normalizeHeader(header: string): string {
  const h = header.trim()
  if (AR_TO_EN[h]) return AR_TO_EN[h]
  if (EN_ALIASES[h]) return EN_ALIASES[h]
  return h.toLowerCase()
}

// ==================== Core Functions ====================

/**
 * ينشئ قالب Excel رسمي بالعربي مع بيانات نموذجية + دليل
 */
export function generateTemplateExcel(): ArrayBuffer {
  const headerRow = [...TEMPLATE_AR_HEADERS] as string[]

  const sample1 = [
    'SKU-001',
    'منظم ملابس داخلي 6 قطع - Underwear Organizer',
    199.99, 50, 'Generic',
    'منظم ملابس داخلي مصنوع من قماش عالي الجودة مع 6 جيوب منفصلة',
    'HOME_ORGANIZERS_AND_STORAGE', 'New', 'MFN',
    '', 'CN', 0.5, '', '', 30, 20, 15,
  ]

  const sample2 = [
    'SKU-002',
    'حافظات طعام أطفال 4 قطع - Baby Food Containers',
    89.99, 100, 'BabyCare',
    'حافظات طعام أطفال آمنة وخالية من BPA مع أغطية محكمة الغلق',
    'BABY_PRODUCT', 'New', 'MFN',
    '', 'CN', 0.3, 'BFC-001', '', 15, 15, 8,
  ]

  const emptyRow = TEMPLATE_AR_HEADERS.map(() => '')

  const ws = XLSX.utils.aoa_to_sheet([
    headerRow,
    sample1,
    sample2,
    ...Array(5).fill(emptyRow),
  ])

  ws['!cols'] = TEMPLATE_AR_HEADERS.map((h, i) => {
    if (i === 1) return { wch: 45 }
    if (i === 5) return { wch: 55 }
    return { wch: Math.max(h.length + 2, 12) }
  })

  // Guide sheet
  const guideData = [
    ['دليل الأعمدة', '', ''],
    ['اسم العمود', 'إجباري؟', 'ملاحظات'],
    ['SKU', '✅ نعم', 'كود فريد - 3 أحرف على الأقل'],
    ['اسم المنتج', '✅ نعم', '5 أحرف على الأقل'],
    ['السعر', '✅ نعم', 'رقم موجب'],
    ['الكمية', '✅ نعم', 'رقم غير سالب'],
    ['البراند', '❌ اختياري', 'يفضل حقيقي - Generic = incomplete'],
    ['الوصف', '❌ اختياري', '10 أحرف على الأقل'],
    ['الفئة', '❌ اختياري', 'HOME_ORGANIZERS_AND_STORAGE / BABY_PRODUCT / APPAREL'],
    ['حالة المنتج', '❌ اختياري', 'New / Refurbished'],
    ['طريقة الشحن', '❌ اختياري', 'MFN (بائع) / AFN (Amazon)'],
    ['الباركود', '❌ اختياري', 'UPC (12 رقم) / EAN (13 رقم)'],
    ['بلد المنشأ', '❌ اختياري', 'CN / EG / TR'],
    ['الوزن', '❌ اختياري', 'بالكيلو'],
    ['رقم الموديل', '❌ اختياري', ''],
    ['المصنع', '❌ اختياري', ''],
    ['الطول/العرض/الارتفاع', '❌ اختياري', 'بالسنتيمتر'],
    ['', '', ''],
    ['⚠️ ملاحظات:', '', ''],
    ['مفيش صور → incomplete', '', ''],
    ['مفيش باركود → incomplete', '', ''],
    ['البراند Generic → incomplete', '', ''],
    ['incomplete → مش هيرفع لـ Amazon', '', ''],
  ]

  const wsGuide = XLSX.utils.aoa_to_sheet(guideData)
  wsGuide['!cols'] = [{ wch: 30 }, { wch: 12 }, { wch: 40 }]

  const wb = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(wb, ws, 'المنتجات')
  XLSX.utils.book_append_sheet(wb, wsGuide, 'دليل الأعمدة')

  return XLSX.write(wb, { bookType: 'xlsx', type: 'array' }) as ArrayBuffer
}

/**
 * يحلل ملف Excel ويرجّع المنتجات
 */
export function importExcelFile(data: ArrayBuffer): ImportResult {
  const workbook = XLSX.read(data, { type: 'array' })
  const sheet = workbook.Sheets[workbook.SheetNames[0]]
  const rows: any[] = XLSX.utils.sheet_to_json(sheet, { defval: '' })

  if (rows.length === 0) {
    throw new Error('الملف فاضي')
  }

  // Detect columns from first row
  const rawColumns = Object.keys(rows[0])
  const normalizedMap: Record<string, string> = {}
  for (const col of rawColumns) {
    normalizedMap[col] = normalizeHeader(col)
  }

  // Check required columns
  const normalizedCols = new Set(Object.values(normalizedMap))
  const missingRequired = REQUIRED_COLUMNS.filter(r => !normalizedCols.has(r))
  const columnErrors: ValidationError[] = missingRequired.map(col => ({
    row: 0,
    field: col,
    message: `العمود الإجباري "${col}" مش موجود في الملف`,
    severity: 'error' as const,
  }))

  if (columnErrors.length > 0) {
    return { products: [], templateType: 'invalid', columnErrors, rowErrors: [] }
  }

  // Parse each row
  const products: ParsedProduct[] = []
  const rowErrors: { row: number; errors: ValidationError[] }[] = []

  for (let i = 0; i < rows.length; i++) {
    const row = rows[i]
    const excelRow = i + 1

    // Helper
    const getVal = (key: string): any => {
      for (const [orig, norm] of Object.entries(normalizedMap)) {
        if (norm === key) return row[orig]
      }
      return undefined
    }

    const sku = String(getVal('sku') || '').trim()
    const name = String(getVal('product_name') || '').trim()
    const price = parseFloat(String(getVal('price') || '0'))
    const quantity = parseInt(String(getVal('quantity') || '0'))
    const barcode = String(getVal('barcode') || '').trim()

    let upc: string | undefined
    let ean: string | undefined
    if (barcode.length === 12) upc = barcode
    else if (barcode.length === 13) ean = barcode

    const errors: ValidationError[] = []

    if (!sku || sku.length < 3) errors.push({ row: excelRow, field: 'sku', message: 'SKU مطلوب (3 أحرف)', severity: 'error' })
    if (!name || name.length < 2) errors.push({ row: excelRow, field: 'product_name', message: 'اسم المنتج مطلوب (2 حرف)', severity: 'error' })
    if (!price || price <= 0) errors.push({ row: excelRow, field: 'price', message: 'السعر لازم يكون موجب', severity: 'error' })

    if (errors.length > 0) {
      rowErrors.push({ row: excelRow, errors })
      continue
    }

    products.push({
      row: excelRow,
      sku, name, price, quantity,
      brand: String(getVal('brand') || 'Generic').trim(),
      description: String(getVal('description') || '').trim(),
      category: String(getVal('category') || '').trim(),
      condition: String(getVal('condition') || 'New').trim(),
      fulfillment_channel: String(getVal('fulfillment_channel') || 'MFN').trim(),
      upc, ean,
      country_of_origin: String(getVal('country_of_origin') || '').trim() || undefined,
      weight: getVal('weight') ? parseFloat(String(getVal('weight'))) : undefined,
      model_number: String(getVal('model_number') || '').trim() || undefined,
      manufacturer: String(getVal('manufacturer') || '').trim() || undefined,
      dimensions: (getVal('length') || getVal('width') || getVal('height'))
        ? {
            length: getVal('length') ? parseFloat(String(getVal('length'))) : undefined,
            width: getVal('width') ? parseFloat(String(getVal('width'))) : undefined,
            height: getVal('height') ? parseFloat(String(getVal('height'))) : undefined,
          }
        : undefined,
      currency: 'EGP',
    })
  }

  return {
    products,
    templateType: 'arabic',
    columnErrors,
    rowErrors,
  }
}
