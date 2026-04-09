📜 وثيقة الانتقال التشغيلي: من المحاكاة (Mock) إلى الإنتاج الحقيقي (Production)
التصنيف: هندسي صارم | الإصدار: 1.0 | الحالة: جاهز للتنفيذ
النظام المستهدف: Crazy Lister v3.0 (Windows Standalone .exe)
نطاق العمل: تبديل مسار الاتصال من بيانات وهمية محلية إلى Amazon SP-API حقيقي مع ضمان عدم تلوث البيانات أو انهيار النظام.

⚠️ قواعد الاشتباك (Rules of Engagement)
ممنوع التخمين: كل خطوة تعتمد على أدلة ملموسة (Logs, Hashes, Screenshots).
نقاط التفتيش إلزامية: لا يتم الانتقال للمرحلة التالية إلا بعد توقيع GO رسمي على جميع المعايير.
العزل التام: بيئة الاختبار الحي لا تلامس بيانات العميل النهائي حتى اكتمال المرحلة 4.
التراجع الفوري: أي انحراف عن المعايير يُفعّل بروتوكول التراجع خلال 60 ثانية.
توثيق جنائي: كل أمر يُنفذ يُسجل مع الطابع الزمني، المخرجات، وحالة النجاح/الفشل.
🟢 المرحلة الأولى: التمهيد البيئي وتأمين المفاتيح
الهدف: تهيئة بيئة آمنة، عزل النسخة الاحتياطية، وتثبيت الاعتماديات الحقيقية دون لمس كود التطبيق.

🔹 أوامر التنفيذ
إنشاء نسخة احتياطية مشفرة لقاعدة البيانات:
Copy-Item "$env:APPDATA\CrazyLister\crazy_lister.db" "$env:APPDATA\CrazyLister\backup_pre_prod_$(Get-Date -Format 'yyyyMMdd').db"
تثبيت/تثبيت إصدار مكتبة SP-API الحقيقي:
pip install "python-amazon-sp-api==2.1.8" "boto3==1.34.34"
تجهيز ملف .env الإنتاجي:
USE_AMAZON_MOCK=False
AWS_ACCESS_KEY_ID=<REAL_KEY>
AWS_SECRET_ACCESS_KEY=<REAL_SECRET>
AWS_REGION=eu-west-1
LOG_LEVEL=DEBUG
قفل صلاحيات الملف:
icacls backend\.env /grant:r "%USERNAME%":R
🔍 نقاط التفتيش الإلزامية (Checkpoint Alpha)
المعيار	طريقة التحقق	الحالة
النسخة الاحتياطية موجودة بحجم > 0KB	Get-Item ...backup...db	⬜
python-amazon-sp-api مثبت والإصدار مطابق	pip show python-amazon-sp-api	⬜
.env لا يحتوي على USE_AMAZON_MOCK=True	findstr "MOCK" backend\.env → يجب أن يرجع 0 نتائج	⬜
مفاتيح AWS موجودة ولا تحتوي على test أو mock	مراجعة يدوية + findstr "AKIA"	⬜
🚨 بروتوكول الطوارئ
إذا فشلت أي نقطة تفتيش: أوقف التنفيذ فوراً. استعد النسخة الاحتياطية. أعد مراجعة .env. لا تنتقل للمرحلة 2.
🔵 المرحلة الثانية: تعقيم الكود وحقن المنطق الحقيقي
الهدف: إزالة مسارات المحاكاة نهائياً، وربط الـ Backend بـ Amazon SP-API الحقيقي مع معالجة الـ Tokens ديناميكياً.

🔹 أوامر التنفيذ
تعقيم backend/app/services/amazon_api.py:
احذف أو علّق أي كتلة تبدأ بـ if settings.USE_AMAZON_MOCK: أو return mock_data.
استبدلها بـ:
from sp_api.api import Listings, Sellers
from sp_api.base import Credentials, Marketplaces

class RealSPAPIClient:
    def __init__(self, credentials: dict):
        self.creds = Credentials(
            lwa_app_id=credentials["client_id"],
            lwa_client_secret=credentials["client_secret"],
            aws_access_key=credentials["aws_key"],
            aws_secret_key=credentials["aws_secret"],
            refresh_token=credentials["refresh_token"]
        )

    async def get_account(self):
        res = Sellers(credentials=self.creds).get_account()
        return res.payload
تحديث backend/app/config.py:
أضف SP_API_MOCK_MODE: bool = False كـ إعداد صلب.
تأكد أن get_settings() تقرأ من .env ولا تعتمد على Defaults وهمية.
مراجعة backend/app/api/amazon_connect/service.py:
تأكد أن verify_connection() يستدعي الـ Client الحقيقي ويعالج 401/403 بإعادة محاولة الـ Refresh Token تلقائياً.
🔍 نقاط التفتيش الإلزامية (Checkpoint Bravo)
المعيار	طريقة التحقق	الحالة
لا يوجد كلمة mock في مسار الاتصال الرئيسي	grep -r "mock|Mock|MOCK" backend/app/services/ → 0 نتائج	⬜
الـ Client يعتمد على sp_api وليس على requests وهمي	مراجعة import statements	⬜
معالجة الأخطاء 429 و 403 موجودة صراحةً	وجود try/except مع RateLimitExceeded	⬜
الـ Refresh Token يُعاد استخدامه دون تخزينه كنص واضح في اللوج	grep "refresh_token" backend/app/ → لا يوجد logger.info(token)	⬜
🚨 بروتوكول الطوارئ
إذا ظهر أي مسار وهمي: أعد كتابة الملف من الـ Branch dev-clean. لا تعتمد على التعديلات اليدوية المتكررة.
🟡 المرحلة الثالثة: تمرين الإطلاق الحي المقيد
الهدف: اختبار الاتصال الحقيقي ضد أمازون في بيئة معزولة، مع مراقبة الحدود والبيانات العائدة.

🔹 أوامر التنفيذ
تشغيل الخادم محلياً:
cd backend && python -m uvicorn app.main:app --host 127.0.0.1 --port 8765
حقن بيانات حقيقية عبر الـ API:
curl -X POST http://127.0.0.1:8765/api/v1/amazon/connect `
  -H "Content-Type: application/json" `
  -d '{
    "lwa_client_id": "<REAL_ID>",
    "lwa_client_secret": "<REAL_SECRET>",
    "lwa_refresh_token": "<REAL_TOKEN>",
    "amazon_seller_id": "<REAL_SELLER_ID>"
  }'
استدعاء التحقق والمزامنة:
curl -X POST http://127.0.0.1:8765/api/v1/amazon/verify
curl -X POST http://127.0.0.1:8765/api/v1/sync
مراقبة اللوج الحي:
Get-Content "$env:APPDATA\CrazyLister\crazy_lister.log" -Wait
🔍 نقاط التفتيش الإلزامية (Checkpoint Charlie)
المعيار	طريقة التحقق	الحالة
/verify يرجع is_connected: true و amazon_seller_id حقيقي (يبدأ بـ A)	فحص JSON Response	⬜
/sync يرجع منتجات بـ sku و asin حقيقيين (ليست DEMO- أو TEST-)	فحص total و items[0].sku	⬜
اللوج يظهر 200 OK من sellingpartnerapi-na.amazon.com أو المarketplace المقابل	findstr "200|201" crazy_lister.log	⬜
لا يوجد تحذيرات RateLimit أو Throttled	findstr "429|throttl" crazy_lister.log → 0 نتائج	⬜
الواجهة الأمامية (/products) تعرض بيانات حقيقية بدون أخطاء toFixed أو undefined	فحص Console المتصفح	⬜
🚨 بروتوكول الطوارئ
إذا ظهر 403 Unauthorized: تحقق من صلاحيات IAM Role في AWS Console.
إذا ظهر 429 Too Many Requests: أوقف الـ Sync فوراً. انتظر 5 دقائق. أعد المحاولة بـ page_size=5.
إذا عادت بيانات وهمية: افحص backend/app/services/amazon_api.py مرة أخرى. هناك تسرب في المنطق.
🔴 المرحلة الرابعة: التجميع النهائي والمراجعة القضائية
الهدف: حزم النظام في .exe إنتاجي، التحقق من السلوك خارج بيئة التطوير، وتفعيل بروتوكول المراقبة.

🔹 أوامر التنفيذ
تنظيف بيئة البناء:
rmdir /s /q dist build
تعديل crazy_lister.spec للإنتاج:
تأكد أن datas=[('frontend/dist', 'frontend/dist')] فقط.
احذف أي hiddenimports خاصة بـ pytest أو mock.
التجميع النهائي:
pyinstaller --clean crazy_lister.spec
اختبار الـ .exe على مسار نظيف:
start dist\CrazyLister.exe
# انتظر 20 ثانية
dir %APPDATA%\CrazyLister\
حزم التسليم:
Compress-Archive -Path dist\CrazyLister.exe, README_PROD.txt -DestinationPath releases\CrazyLister-v3.0-PROD.zip
🔍 نقاط التفتيش الإلزامية (Checkpoint Delta)
المعيار	طريقة التحقق	الحالة
حجم CrazyLister.exe بين 65MB و 90MB	Get-Item dist\CrazyLister.exe | select Length	⬜
الـ .exe يفتح نافذة PyWebView دون أخطاء jaraco أو platformdirs	فحص اللوج الأولي	⬜
الاتصال الحقيقي يعمل من داخل الـ .exe (نفس نتائج المرحلة 3)	تنفيذ /verify و /sync من الواجهة	⬜
لا توجد ملفات .py أو __pycache__ داخل مجلد الـ build النهائي	tree dist /f → يجب أن يحتوي فقط على .exe وملفات نظام	⬜
ملف README_PROD.txt يشرح خطوات إدخال المفاتيح الحقيقية ومسار اللوج	مراجعة يدوية	⬜
🚨 بروتوكول الطوارئ
إذا فشل الـ Build: نفذ pip cache purge وأعد المحاولة.
إذا فشل الـ .exe في الاتصال: افحص %APPDATA%\CrazyLister\crazy_lister.log. الخطأ عادة في صلاحيات الجدار الناري أو مفاتيح مشفرة بشكل خاطئ.
نقطة التراجع النهائية: إذا فشل أكثر من نقطتي تفتيش في المرحلة 4، أوقف التوزيع. عد للمرحلة 2. لا تطلق نسخة معيبة.
✅ ختم الموافقة النهائية (Sign-Off Protocol)
لا يتم اعتبار المشروع “جاهزاً للإنتاج” إلا بعد ملء الجدول أدناه والتوقيع الرقمي/اليدوي من المسؤول الهندسي والمشرف الأمني:

المرحلة	الحالة	المسؤول	التاريخ	التوقيع
1. التمهيد البيئي	⬜ GO / ⬜ NO-GO			
2. تعقيم الكود	⬜ GO / ⬜ NO-GO			
3. الإطلاق الحي	⬜ GO / ⬜ NO-GO			
4. التجميع النهائي	⬜ GO / ⬜ NO-GO			
ملاحظة ختامية: هذه الوثيقة ملزمة هندسياً. أي انحراف عن التسلسل أو تخطي نقطة تفتيش يعتبر إهمالاً تشغيلياً يعرض استقرار النظام وبيانات العميل للخطر. التزم بالتسلسل. وثّق كل خطوة. لا تفترض شيئاً.

**END OF DOCUMENT