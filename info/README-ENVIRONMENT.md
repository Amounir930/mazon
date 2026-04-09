# 🚀 Crazy Lister - بيئة الإنتاج الكاملة

## تشغيل كل شيء مرة واحدة

```bash
# من المجلد الرئيسي
docker compose up -d
```

### الخدمات المشغلة

| الخدمة | البورت | الوصف |
|--------|--------|-------|
| **Amazon Mock API** | 9500 | محاكاة Amazon SP-API |
| **Backend API** | 8000 | FastAPI Backend |
| **Celery Worker** | - | معالجة المهام غير المتزامنة |
| **Redis** | 6379 | Cache + Message Broker |
| **Flower** | 5555 | مراقبة Celery |
| **Frontend** | 3000 | React Frontend (تشغّل محلياً) |

### تشغيل الفرونت-إند

```bash
cd frontend
npm install
npm run dev
```

### الروابط

| الخدمة | الرابط |
|--------|--------|
| الفرونت-إند | http://localhost:3000 |
| API Docs | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |
| Flower | http://localhost:5555 |
| Amazon Mock | http://localhost:9000/health |

### تبديل بين Mock والـ الحقيقي

في ملف `backend/.env`:
```bash
# للاختبار (افتراضي)
USE_AMAZON_MOCK=true

# للإنتاج
USE_AMAZON_MOCK=false
```
