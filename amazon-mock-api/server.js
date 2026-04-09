/**
 * Amazon SP-API Mock Server
 * 
 * يحاكي Amazon Selling Partner API بشكل واقعي
 * يرجع ردود مختلفة (نجاح، فشل، أخطاء) لاختبار النظام كامل
 */

const express = require('express')
const cors = require('cors')
const { v4: uuidv4 } = require('uuid')

const app = express()
const PORT = 9500

app.use(cors())
app.use(express.json())

// ============ محاكاة قاعدة بيانات Amazon ============

const amazonListings = []
const amazonFeeds = []
const amazonReports = []

// محاكاة أخطاء Amazon الواقعية
const amazonErrorScenarios = [
  {
    status: 400,
    code: 'InvalidInput',
    message: 'One or more required values is missing from the request.',
  },
  {
    status: 403,
    code: 'Unauthorized',
    message: 'Access to requested resource is denied.',
  },
  {
    status: 404,
    code: 'NotFound',
    message: 'The requested listing does not exist.',
  },
  {
    status: 429,
    code: 'TooManyRequests',
    message: 'Request is throttled.',
  },
  {
    status: 500,
    code: 'InternalFailure',
    message: 'We encountered an unexpected internal error.',
  },
  {
    status: 503,
    code: 'ServiceUnavailable',
    message: 'The service is temporarily unavailable.',
  },
]

// ============ Helper Functions ============

function delay(ms = 500) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

function randomChoice(arr) {
  return arr[Math.floor(Math.random() * arr.length)]
}

function simulateAmazonResponse(successRate = 0.85) {
  if (Math.random() > successRate) {
    const error = randomChoice(amazonErrorScenarios)
    return {
      success: false,
      error: {
        code: error.code,
        message: error.message,
        details: `Amazon API returned ${error.status} - ${error.code}`,
      },
    }
  }

  return {
    success: true,
    data: null,
  }
}

// ============ Amazon SP-API Endpoints ============

/**
 * POST /listings/2021-08-01/items/{sellerId}/{sku}
 * إنشاء أو تحديث منتج على Amazon
 */
app.post('/listings/2021-08-01/items/:sellerId/:sku', async (req, res) => {
  await delay(800 + Math.random() * 1200) // محاكاة وقت استجابة واقعي

  const { sellerId, sku } = req.params
  const { attributes } = req.body

  const result = simulateAmazonResponse(0.88) // 88% نسبة نجاح واقعية

  if (result.success) {
    const listing = {
      id: uuidv4(),
      sellerId,
      sku,
      status: 'ACCEPTED',
      issues: [],
      attributes,
      createdAt: new Date().toISOString(),
    }
    amazonListings.push(listing)

    res.status(200).json({
      sku,
      status: 'ACCEPTED',
      submissionId: listing.id,
      issues: [],
    })
  } else {
    res.status(result.error.status || 400).json({
      errors: [
        {
          code: result.error.code,
          message: result.error.message,
          details: result.error.details,
        },
      ],
    })
  }
})

/**
 * GET /listings/2021-08-01/items/{sellerId}/{sku}
 * جلب تفاصيل منتج من Amazon
 */
app.get('/listings/2021-08-01/items/:sellerId/:sku', async (req, res) => {
  await delay(400 + Math.random() * 600)

  const { sellerId, sku } = req.params
  const listing = amazonListings.find(
    (l) => l.sellerId === sellerId && l.sku === sku
  )

  if (!listing) {
    return res.status(404).json({
      errors: [
        {
          code: 'NotFound',
          message: `Listing ${sku} not found for seller ${sellerId}`,
        },
      ],
    })
  }

  res.json({
    sku: listing.sku,
    summary: {
      marketplaceId: 'ARBP9OOSHTCHU',
      status: listing.status,
      issueCount: listing.issues.length,
    },
    attributes: listing.attributes,
  })
})

/**
 * DELETE /listings/2021-08-01/items/{sellerId}/{sku}
 * حذف منتج من Amazon
 */
app.delete('/listings/2021-08-01/items/:sellerId/:sku', async (req, res) => {
  await delay(600 + Math.random() * 400)

  const { sellerId, sku } = req.params
  const idx = amazonListings.findIndex(
    (l) => l.sellerId === sellerId && l.sku === sku
  )

  if (idx === -1) {
    return res.status(404).json({
      errors: [
        {
          code: 'NotFound',
          message: `Listing ${sku} not found`,
        },
      ],
    })
  }

  amazonListings.splice(idx, 1)
  res.status(200).json({
    sku,
    status: 'DELETED',
    issues: [],
  })
})

/**
 * POST /feeds/2021-06-30/documents
 * إنشاء مستند Feed لرفع جماعي
 */
app.post('/feeds/2021-06-30/documents', async (req, res) => {
  await delay(500 + Math.random() * 1000)

  const { contentType } = req.body

  const result = simulateAmazonResponse(0.92)

  if (result.success) {
    const document = {
      documentId: 'DOC_' + uuidv4().replace(/-/g, '').substring(0, 16),
      url: `https://mock-upload.amazon.com/feeds/${uuidv4()}`,
      contentType,
      createdAt: new Date().toISOString(),
    }
    amazonFeeds.push({ ...document, status: 'UPLOADING' })

    res.status(201).json({
      feedDocumentId: document.documentId,
      url: document.url,
    })
  } else {
    res.status(result.error.status || 400).json({
      errors: [
        {
          code: result.error.code,
          message: result.error.message,
        },
      ],
    })
  }
})

/**
 * POST /feeds/2021-06-30/feeds
 * إرسال Feed إلى Amazon
 */
app.post('/feeds/2021-06-30/feeds', async (req, res) => {
  await delay(1000 + Math.random() * 2000)

  const { feedType, marketplaceIds, inputFeedDocumentId } = req.body

  const feed = {
    feedId: 'FEED_' + Date.now(),
    feedType,
    marketplaceIds,
    inputFeedDocumentId,
    status: 'IN_QUEUE',
    createdAt: new Date().toISOString(),
    processingStatus: 'IN_QUEUE',
  }

  amazonFeeds.push(feed)

  // محاكاة معالجة الـ Feed
  setTimeout(() => {
    const f = amazonFeeds.find((f) => f.feedId === feed.feedId)
    if (f) {
      f.processingStatus = 'IN_PROGRESS'
      f.status = 'PROCESSING'

      setTimeout(() => {
        if (f) {
          const success = Math.random() > 0.15 // 85% نسبة نجاح
          f.processingStatus = success ? 'DONE' : 'FATAL'
          f.status = success ? 'DONE' : 'FATAL'
          f.completedAt = new Date().toISOString()

          if (success) {
            f.resultFeedDocumentId = 'RESULT_' + uuidv4().replace(/-/g, '').substring(0, 16)
          } else {
            f.errors = [
              {
                code: 'InvalidData',
                message: 'Feed contains invalid data',
                severity: 'ERROR',
              },
            ]
          }
        }
      }, 5000 + Math.random() * 10000) // 5-15 ثانية معالجة
    }
  }, 2000 + Math.random() * 3000) // 2-5 ثانية انتظار

  res.status(202).json({
    feedId: feed.feedId,
  })
})

/**
 * GET /feeds/2021-06-30/feeds/{feedId}
 * حالة Feed
 */
app.get('/feeds/2021-06-30/feeds/:feedId', async (req, res) => {
  await delay(200 + Math.random() * 300)

  const { feedId } = req.params
  const feed = amazonFeeds.find((f) => f.feedId === feedId)

  if (!feed) {
    return res.status(404).json({
      errors: [
        {
          code: 'NotFound',
          message: `Feed ${feedId} not found`,
        },
      ],
    })
  }

  res.json({
    feedId: feed.feedId,
    feedType: feed.feedType,
    marketplaceIds: feed.marketplaceIds,
    status: feed.status,
    processingStatus: feed.processingStatus,
    createdAt: feed.createdAt,
    completedAt: feed.completedAt,
    resultFeedDocumentId: feed.resultFeedDocumentId,
    errors: feed.errors,
  })
})

/**
 * GET /feeds/2021-06-30/documents/{documentId}
 * جلب نتائج Feed
 */
app.get('/feeds/2021-06-30/documents/:documentId', async (req, res) => {
  await delay(400 + Math.random() * 600)

  const { documentId } = req.params

  // محاكاة تقرير نتائج
  res.json({
    documentId,
    url: `https://mock-download.amazon.com/reports/${documentId}`,
    contentType: 'text/tab-separated-values',
    data: `sku\tstatus\tmessage
PRODUCT-001\tSUCCESS\tSuccessfully processed
PRODUCT-002\tERROR\tInvalid UPC format
PRODUCT-003\tWARNING\tMissing brand information`,
  })
})

/**
 * POST /reports/2021-06-30/reports
 * إنشاء تقرير
 */
app.post('/reports/2021-06-30/reports', async (req, res) => {
  await delay(800 + Math.random() * 1200)

  const { reportType, marketplaceIds, dataStartTime, dataEndTime } = req.body

  const report = {
    reportId: 'RPT_' + Date.now(),
    reportType,
    marketplaceIds,
    reportStatus: 'IN_QUEUE',
    createdAt: new Date().toISOString(),
  }

  amazonReports.push(report)

  res.status(201).json({
    reportId: report.reportId,
  })
})

/**
 * GET /reports/2021-06-30/reports/{reportId}
 * حالة تقرير
 */
app.get('/reports/2021-06-30/reports/:reportId', async (req, res) => {
  await delay(300 + Math.random() * 400)

  const { reportId } = req.params
  const report = amazonReports.find((r) => r.reportId === reportId)

  if (!report) {
    return res.status(404).json({
      errors: [{ code: 'NotFound', message: 'Report not found' }],
    })
  }

  res.json({
    reportId: report.reportId,
    reportType: report.reportType,
    reportStatus: report.reportStatus,
    createdAt: report.createdAt,
  })
})

/**
 * POST /tokens/2021-03-01/restrictedDataToken
 * الحصول على Token مقيد
 */
app.post('/tokens/2021-03-01/restrictedDataToken', async (req, res) => {
  await delay(600 + Math.random() * 800)

  const { restrictedResources } = req.body

  res.json({
    restrictedDataToken: 'RDT_' + uuidv4().replace(/-/g, '').substring(0, 32),
    expiresIn: 3600,
  })
})

/**
 * GET /catalog/2022-04-01/items/{asin}
 * البحث في كتالوج Amazon
 */
app.get('/catalog/2022-04-01/items/:asin', async (req, res) => {
  await delay(400 + Math.random() * 600)

  const { asin } = req.params
  const marketplaceId = req.query.marketplaceId || 'ARBP9OOSHTCHU'

  // محاكاة بيانات كتالوج
  res.json({
    asin,
    marketplaceId,
    productType: 'PRODUCT',
    title: 'Mock Product - ' + asin,
    brand: 'MockBrand',
    manufacturer: 'MockManufacturer',
    dimensions: {
      length: { value: 30, unit: 'centimeters' },
      width: { value: 25, unit: 'centimeters' },
      height: { value: 2, unit: 'centimeters' },
    },
    itemWeight: {
      value: 0.3,
      unit: 'kilograms',
    },
    images: [
      {
        link: `https://mock-images.amazon.com/${asin}_main.jpg`,
        variant: 'MAIN',
      },
    ],
  })
})

/**
 * POST /fba/inbound/v0/shipments
 * إنشاء شحنة FBA (محاكاة)
 */
app.post('/fba/inbound/v0/shipments', async (req, res) => {
  await delay(1000 + Math.random() * 2000)

  res.status(201).json({
    payload: {
      shipmentId: 'SHPT_' + Date.now(),
      status: 'WORKING',
      shipmentName: 'Mock Shipment',
      destinationAddress: {
        name: 'Amazon Fulfillment Center',
        addressLine1: '123 Warehouse Blvd',
        city: 'Cairo',
        countryCode: 'EG',
      },
    },
  })
})

/**
 * GET /seller/orders/v1/orders
 * جلب الطلبات (محاكاة)
 */
app.get('/seller/orders/v1/orders', async (req, res) => {
  await delay(500 + Math.random() * 1000)

  // محاكاة طلبات عشوائية
  const mockOrders = [
    {
      amazonOrderId: 'ORD_' + Date.now(),
      sellerOrderId: 'SELLER_' + Date.now(),
      purchaseDate: new Date(Date.now() - 86400000).toISOString(),
      lastUpdateDate: new Date().toISOString(),
      orderStatus: 'Unshipped',
      fulfillmentChannel: 'MFN',
      numberOfItemsShipped: 0,
      orderTotal: {
        Amount: '299.00',
        CurrencyCode: 'EGP',
      },
      shippingAddress: {
        name: 'Mock Customer',
        addressLine1: '123 Main St',
        city: 'Cairo',
        countryCode: 'EG',
      },
    },
  ]

  res.json({
    payload: mockOrders,
    NextToken: null,
  })
})

/**
 * POST /listings/2021-08-01/items/{sellerId}/{sku} (PUT)
 * تحديث منتج كامل
 */
app.put('/listings/2021-08-01/items/:sellerId/:sku', async (req, res) => {
  await delay(800 + Math.random() * 1200)

  const result = simulateAmazonResponse(0.90)

  if (result.success) {
    res.status(200).json({
      sku: req.params.sku,
      status: 'ACCEPTED',
      issues: [],
    })
  } else {
    res.status(result.error.status || 400).json({
      errors: [{ code: result.error.code, message: result.error.message }],
    })
  }
})

/**
 * POST /listings/2021-08-01/items/{sellerId}/{sku} (PATCH)
 * تحديث جزئي للمنتج
 */
app.patch('/listings/2021-08-01/items/:sellerId/:sku', async (req, res) => {
  await delay(600 + Math.random() * 800)

  const result = simulateAmazonResponse(0.92)

  if (result.success) {
    res.status(200).json({
      sku: req.params.sku,
      status: 'ACCEPTED',
      issues: [],
    })
  } else {
    res.status(result.error.status || 400).json({
      errors: [{ code: result.error.code, message: result.error.message }],
    })
  }
})

/**
 * DELETE /listings/2021-08-01/items/{sellerId}/{sku}
 * حذف منتج
 */
app.delete('/listings/2021-08-01/items/:sellerId/:sku', async (req, res) => {
  await delay(500 + Math.random() * 700)

  const { sellerId, sku } = req.params
  const idx = amazonListings.findIndex(
    (l) => l.sellerId === sellerId && l.sku === sku
  )

  if (idx === -1) {
    return res.status(404).json({
      errors: [{ code: 'NotFound', message: `Listing ${sku} not found` }],
    })
  }

  amazonListings.splice(idx, 1)
  res.json({
    sku,
    status: 'DELETED',
    issues: [],
  })
})

/**
 * GET /health
 * فحص حالة Amazon Mock API
 */
app.get('/health', async (req, res) => {
  res.json({
    status: 'ok',
    service: 'Amazon SP-API Mock',
    version: '1.0.0',
    listings: amazonListings.length,
    feeds: amazonFeeds.length,
    reports: amazonReports.length,
    errorSimulation: '85% success rate, realistic error codes',
  })
})

/**
 * GET /stats
 * إحصائيات Amazon Mock API
 */
app.get('/stats', async (req, res) => {
  const successFeeds = amazonFeeds.filter((f) => f.status === 'DONE').length
  const failedFeeds = amazonFeeds.filter((f) => f.status === 'FATAL').length

  res.json({
    totalListings: amazonListings.length,
    totalFeeds: amazonFeeds.length,
    successfulFeeds: successFeeds,
    failedFeeds: failedFeeds,
    feedSuccessRate:
      amazonFeeds.length > 0
        ? ((successFeeds / amazonFeeds.length) * 100).toFixed(1) + '%'
        : '0%',
  })
})

/**
 * POST /reset
 * إعادة تعيين البيانات (للاختبار)
 */
app.post('/reset', async (req, res) => {
  amazonListings.length = 0
  amazonFeeds.length = 0
  amazonReports.length = 0
  res.json({ message: 'Amazon Mock API data reset' })
})

// ============ Error Handler ============
app.use((err, req, res, next) => {
  console.error('Amazon Mock API Error:', err)
  res.status(500).json({
    errors: [
      {
        code: 'InternalFailure',
        message: 'Internal server error in Amazon Mock API',
      },
    ],
  })
})

// ============ Start Server ============
app.listen(PORT, () => {
  console.log(`\n🟠 Amazon SP-API Mock Server running on http://localhost:${PORT}`)
  console.log(`\n📋 Available endpoints:`)
  console.log(`   POST   /listings/2021-08-01/items/{sellerId}/{sku}`)
  console.log(`   GET    /listings/2021-08-01/items/{sellerId}/{sku}`)
  console.log(`   DELETE /listings/2021-08-01/items/{sellerId}/{sku}`)
  console.log(`   POST   /feeds/2021-06-30/documents`)
  console.log(`   POST   /feeds/2021-06-30/feeds`)
  console.log(`   GET    /feeds/2021-06-30/feeds/{feedId}`)
  console.log(`   GET    /feeds/2021-06-30/documents/{documentId}`)
  console.log(`   POST   /reports/2021-06-30/reports`)
  console.log(`   GET    /catalog/2022-04-01/items/{asin}`)
  console.log(`   POST   /tokens/2021-03-01/restrictedDataToken`)
  console.log(`   POST   /fba/inbound/v0/shipments`)
  console.log(`   GET    /seller/orders/v1/orders`)
  console.log(`   GET    /health`)
  console.log(`   GET    /stats`)
  console.log(`   POST   /reset`)
  console.log(`\n⚠️  Error simulation: 15% failure rate with realistic Amazon errors`)
  console.log(`\n⏸️  Press Ctrl+C to stop\n`)
})
