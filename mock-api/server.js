const express = require('express')
const cors = require('cors')
const { v4: uuidv4 } = require('uuid')

const app = express()
const PORT = 8000

app.use(cors())
app.use(express.json())

// ============ Mock Database ============
const mockSellers = [
  {
    id: 'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
    email: 'demo@example.com',
    seller_id: 'MOCK-SELLER-001',
    marketplace_id: 'ARBP9OOSHTCHU',
    region: 'EU',
    is_active: true,
    created_at: '2026-04-01T10:00:00Z',
    updated_at: '2026-04-09T10:00:00Z',
  },
]

const mockProducts = [
  {
    id: uuidv4(),
    seller_id: 'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
    sku: 'TSHIRT-RED-XL',
    parent_sku: null,
    is_parent: false,
    name: 'تيشرت قطن أحمر - مقاس كبير',
    category: 'ملابس',
    brand: 'CrazyBrand',
    upc: '123456789012',
    ean: null,
    description: 'تيشرت قطن 100% مريح وعملي للاستخدام اليومي',
    bullet_points: ['قطن 100%', 'مريح وعملي', 'قابل للغسيل في الغسالة', 'متوفر بجميع الألوان'],
    keywords: ['تيشرت', 'قطن', 'رجالي', 'صيفي'],
    price: 299.00,
    compare_price: 399.00,
    cost: 150.00,
    quantity: 250,
    weight: 0.3,
    dimensions: { length: 30, width: 25, height: 2, unit: 'cm' },
    images: [],
    attributes: { color: 'أحمر', size: 'XL', material: 'قطن' },
    status: 'published',
    optimized_data: null,
    created_at: '2026-04-08T10:00:00Z',
    updated_at: '2026-04-09T08:00:00Z',
  },
  {
    id: uuidv4(),
    seller_id: 'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
    sku: 'PANTS-BLUE-32',
    parent_sku: null,
    is_parent: false,
    name: 'بنطال جينز أزرق كلاسيك',
    category: 'ملابس',
    brand: 'CrazyBrand',
    upc: '987654321098',
    description: 'بنطال جينز عالي الجودة بقصة مستقيمة',
    bullet_points: ['جينز عالي الجودة', 'قصة مستقيمة', 'مريح طوال اليوم'],
    keywords: ['بنطال', 'جينز', 'رجالي'],
    price: 450.00,
    compare_price: 599.00,
    cost: 200.00,
    quantity: 180,
    weight: 0.8,
    images: [],
    attributes: { color: 'أزرق', size: '32' },
    status: 'published',
    optimized_data: null,
    created_at: '2026-04-07T10:00:00Z',
    updated_at: '2026-04-09T07:00:00Z',
  },
  {
    id: uuidv4(),
    seller_id: 'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
    sku: 'SHOES-SPORT-42',
    parent_sku: null,
    is_parent: false,
    name: 'حذاء رياضي خفيف للجري',
    category: 'رياضة',
    brand: 'SportMax',
    upc: '456789012345',
    description: 'حذاء رياضي خفيف الوزن مناسب للجري والتمارين',
    bullet_points: ['خفيف الوزن', 'مريح للقدم', 'نعل مضاد للانزلاق'],
    keywords: ['حذاء', 'رياضي', 'جري'],
    price: 750.00,
    compare_price: 999.00,
    cost: 350.00,
    quantity: 95,
    weight: 0.5,
    images: [],
    attributes: { color: 'أسود', size: '42' },
    status: 'queued',
    optimized_data: null,
    created_at: '2026-04-09T09:00:00Z',
    updated_at: '2026-04-09T09:00:00Z',
  },
]

const mockListings = [
  {
    id: uuidv4(),
    product_id: mockProducts[0].id,
    seller_id: 'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
    feed_submission_id: 'FEED_12345678',
    status: 'success',
    amazon_asin: 'B00ABC1234',
    amazon_url: 'https://www.amazon.eg/dp/B00ABC1234',
    error_message: null,
    queue_position: 1,
    submitted_at: '2026-04-08T10:30:00Z',
    completed_at: '2026-04-08T10:35:00Z',
    created_at: '2026-04-08T10:25:00Z',
  },
  {
    id: uuidv4(),
    product_id: mockProducts[1].id,
    seller_id: 'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
    feed_submission_id: 'FEED_87654321',
    status: 'success',
    amazon_asin: 'B00XYZ5678',
    amazon_url: 'https://www.amazon.eg/dp/B00XYZ5678',
    error_message: null,
    queue_position: 2,
    submitted_at: '2026-04-09T08:00:00Z',
    completed_at: '2026-04-09T08:05:00Z',
    created_at: '2026-04-09T07:55:00Z',
  },
  {
    id: uuidv4(),
    product_id: mockProducts[2].id,
    seller_id: 'a1b2c3d4-e5f6-7890-abcd-ef1234567890',
    feed_submission_id: null,
    status: 'queued',
    amazon_asin: null,
    amazon_url: null,
    error_message: null,
    queue_position: 3,
    submitted_at: null,
    completed_at: null,
    created_at: '2026-04-09T09:00:00Z',
  },
]

// ============ Helper Functions ============
function paginate(items, page = 1, pageSize = 50) {
  const start = (page - 1) * pageSize
  const end = start + pageSize
  return {
    items: items.slice(start, end),
    total: items.length,
    page,
    pages: Math.ceil(items.length / pageSize),
    has_next: end < items.length,
    has_prev: page > 1,
  }
}

function delay(ms = 300) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

// ============ Health Check ============
app.get('/health', async (req, res) => {
  await delay(100)
  res.json({ status: 'ok', version: '2.0.0-MOCK', app_name: 'Crazy Lister API (Mock)' })
})

// ============ Sellers ============
app.post('/api/v1/sellers/register', async (req, res) => {
  await delay(500)
  const { email, seller_id, marketplace_id, region } = req.body
  const seller = {
    id: uuidv4(),
    email: email || 'new@example.com',
    seller_id: seller_id || 'MOCK-SELLER-' + Date.now(),
    marketplace_id: marketplace_id || 'ARBP9OOSHTCHU',
    region: region || 'EU',
    is_active: true,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  }
  mockSellers.push(seller)
  res.status(201).json(seller)
})

app.get('/api/v1/sellers/:id', async (req, res) => {
  await delay(200)
  const seller = mockSellers.find((s) => s.id === req.params.id)
  if (!seller) return res.status(404).json({ error: 'Seller not found' })
  res.json(seller)
})

// ============ Products ============
app.get('/api/v1/products', async (req, res) => {
  await delay(400)
  const { seller_id, status, category, page = 1, page_size = 50 } = req.query
  
  let filtered = [...mockProducts]
  if (seller_id) filtered = filtered.filter((p) => p.seller_id === seller_id)
  if (status) filtered = filtered.filter((p) => p.status === status)
  if (category) filtered = filtered.filter((p) => p.category === category)
  
  const result = paginate(filtered, parseInt(page), parseInt(page_size))
  res.json(result)
})

app.get('/api/v1/products/:id', async (req, res) => {
  await delay(200)
  const product = mockProducts.find((p) => p.id === req.params.id)
  if (!product) return res.status(404).json({ error: 'Product not found' })
  res.json(product)
})

app.post('/api/v1/products', async (req, res) => {
  await delay(600)
  const { seller_id } = req.query
  const newProduct = {
    id: uuidv4(),
    seller_id: seller_id || mockSellers[0].id,
    ...req.body,
    status: 'draft',
    optimized_data: null,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  }
  mockProducts.push(newProduct)
  res.status(201).json(newProduct)
})

app.put('/api/v1/products/:id', async (req, res) => {
  await delay(400)
  const idx = mockProducts.findIndex((p) => p.id === req.params.id)
  if (idx === -1) return res.status(404).json({ error: 'Product not found' })
  
  mockProducts[idx] = {
    ...mockProducts[idx],
    ...req.body,
    updated_at: new Date().toISOString(),
  }
  res.json(mockProducts[idx])
})

app.delete('/api/v1/products/:id', async (req, res) => {
  await delay(300)
  const idx = mockProducts.findIndex((p) => p.id === req.params.id)
  if (idx === -1) return res.status(404).json({ error: 'Product not found' })
  
  mockProducts.splice(idx, 1)
  res.json({ message: 'Product deleted successfully' })
})

// ============ Listings ============
app.post('/api/v1/listings/submit', async (req, res) => {
  await delay(800)
  const { product_id, seller_id } = req.body
  
  const newListing = {
    id: uuidv4(),
    product_id,
    seller_id: seller_id || mockSellers[0].id,
    feed_submission_id: null,
    status: 'queued',
    amazon_asin: null,
    amazon_url: null,
    error_message: null,
    queue_position: mockListings.length + 1,
    submitted_at: null,
    completed_at: null,
    created_at: new Date().toISOString(),
  }
  mockListings.push(newListing)
  
  // Simulate async processing
  setTimeout(() => {
    const listing = mockListings.find((l) => l.id === newListing.id)
    if (listing) {
      listing.status = 'processing'
      
      setTimeout(() => {
        listing.status = 'submitted'
        listing.feed_submission_id = 'FEED_' + Date.now()
        listing.submitted_at = new Date().toISOString()
        
        setTimeout(() => {
          listing.status = Math.random() > 0.15 ? 'success' : 'failed'
          listing.completed_at = new Date().toISOString()
          if (listing.status === 'success') {
            listing.amazon_asin = 'B00MOCK' + Math.random().toString(36).substr(2, 4).toUpperCase()
            listing.amazon_url = `https://www.amazon.eg/dp/${listing.amazon_asin}`
          } else {
            listing.error_message = 'Feed processing error: Invalid UPC format'
          }
        }, 5000)
      }, 3000)
    }
  }, 2000)
  
  res.status(201).json(newListing)
})

app.get('/api/v1/listings', async (req, res) => {
  await delay(300)
  const { seller_id, status } = req.query
  
  let filtered = [...mockListings]
  if (seller_id) filtered = filtered.filter((l) => l.seller_id === seller_id)
  if (status) filtered = filtered.filter((l) => l.status === status)
  
  res.json(filtered)
})

app.post('/api/v1/listings/:id/retry', async (req, res) => {
  await delay(400)
  const listing = mockListings.find((l) => l.id === req.params.id)
  if (!listing) return res.status(404).json({ error: 'Listing not found' })
  
  listing.status = 'queued'
  listing.error_message = null
  listing.submitted_at = null
  listing.completed_at = null
  listing.feed_submission_id = null
  
  res.json({ message: 'Listing retry queued successfully' })
})

app.delete('/api/v1/listings/:id', async (req, res) => {
  await delay(300)
  const listing = mockListings.find((l) => l.id === req.params.id)
  if (!listing) return res.status(404).json({ error: 'Listing not found' })
  
  if (!['queued', 'processing'].includes(listing.status)) {
    return res.status(400).json({ error: 'Can only cancel queued or processing listings' })
  }
  
  listing.status = 'cancelled'
  res.json({ message: 'Listing cancelled successfully' })
})

// ============ Feeds ============
app.get('/api/v1/feeds/:feedId/status', async (req, res) => {
  await delay(300)
  res.json({
    feedId: req.params.feedId,
    processingStatus: 'DONE',
    resultFeedDocumentId: 'DOC_' + req.params.feedId,
  })
})

// ============ Auth Mock ============
app.post('/api/v1/auth/login', async (req, res) => {
  await delay(600)
  res.json({
    access_token: 'mock-jwt-token-' + Date.now(),
    refresh_token: 'mock-refresh-token',
    user: mockSellers[0],
  })
})

// ============ Error Handler ============
app.use((err, req, res, next) => {
  console.error(err)
  res.status(500).json({ error: 'Internal server error' })
})

// ============ Start Server ============
app.listen(PORT, () => {
  console.log(`\n🚀 Mock API Server running on http://localhost:${PORT}`)
  console.log(`\n📋 Available endpoints:`)
  console.log(`   GET    /health`)
  console.log(`   GET    /api/v1/products`)
  console.log(`   POST   /api/v1/products?seller_id=xxx`)
  console.log(`   PUT    /api/v1/products/:id`)
  console.log(`   DELETE /api/v1/products/:id`)
  console.log(`   POST   /api/v1/listings/submit`)
  console.log(`   GET    /api/v1/listings`)
  console.log(`   GET    /api/v1/feeds/:feedId/status`)
  console.log(`   POST   /api/v1/auth/login`)
  console.log(`\n📊 Mock data: ${mockProducts.length} products, ${mockListings.length} listings`)
  console.log(`\n⏸️  Press Ctrl+C to stop\n`)
})
