تم تحديث ملف الذاكرة (HANDOFF_MEMORY.md) بشكل جنائي وشامل. هذا الملف الآن يحتوي على كل قرار هندسي، كل خطأ تم إصلاحه، وكل “فخ” برمجي تم اكتشافه، لضمان أن أي مهندس جديد يستلم المشروع لا يضيع وقتاً في تكرار أخطاء الماضي.

يمكنك نسخ محتوى الملف أدناه واستخدامه كمرجع دائم.

📋 Crazy Lister v3.0 — Forensic Handoff Document
Version: 3.0 (Hybrid: Desktop Target + Web Dev Mode)
Last Updated: April 10, 2026
Current Mode: Development (Simulation Active)
Status: 🟡 Stable Core / UI in Final Polish

🚨 Executive Summary (The “State of the Union”)
The system is a Single-Client Amazon Automation Tool. It was migrated from a complex SaaS (PostgreSQL + Celery) to a lightweight Desktop App architecture (SQLite + Asyncio + PyWebView).

Current Working State:

✅ Backend: FastAPI serves data, handles CRUD, and mocks Amazon responses.
✅ Database: SQLite in %APPDATA%. No Docker needed.
✅ Frontend: React + Vite. Connected to Backend via Proxy.
✅ Build: PyInstaller .exe generation works (after critical fix to pyi_rth_pkgres.py).
✅ Connection: Dynamic! User can change Amazon credentials in Settings, and the system updates instantly.
🛠️ Critical Forensic Fixes (Do NOT Revert)
1. The “PyInstaller jaraco” Loop of Death 🔴
Symptom: ModuleNotFoundError: No module named 'jaraco' on .exe startup.
Root Cause: PyInstaller’s pyi_rth_pkgres.py hook forces a dependency on pkg_resources, which in setuptools 80+ requires hidden vendored packages (jaraco).
The Fix: We Neutralized the hook file instead of deleting it.
Location: .../site-packages/PyInstaller/hooks/rthooks/pyi_rth_pkgres.py
Action: Content was replaced with an empty file.
WARNING: DO NOT delete this file (causes registry error). DO NOT restore it.
2. The “307 Redirect” Loop 🟡
Symptom: Frontend stuck in “Loading” state; Console shows 307 Temporary Redirect.
Root Cause: Backend routes had trailing slashes (@router.get("/")), but Frontend requested without (/products).
The Fix: Removed trailing slashes from all endpoints in backend/app/api/.
products.py, listings.py, amazon_connect/endpoints.py.
3. Dynamic Amazon API Client 🟢
Symptom: System rejected credentials entered in Settings because RealSPAPIClient ignored them and looked at .env.
The Fix: Refactored RealSPAPIClient to accept client_id, client_secret, etc., as optional arguments.
Impact: Now, when you change settings, the system actually uses the NEW credentials immediately.
4. Settings Page & “Dead” Inputs 🟢
Symptom: Settings page showed “string” and inputs were read-only.
The Fix: Rebuilt SettingsPage.tsx as a full Form.
Added “Edit/View” mode.
Added “Save & Connect” button.
Connected it to useConnectAmazon hook.
5. Database Seeding Logic (The Overwrite Bug) 🟢
Symptom: Every time the server restarted, it reset the Seller data to “Demo”, ignoring what the user changed in Settings.
The Fix: Modified main.py startup logic.
Logic: IF (Seller Exists) THEN DO NOTHING. ELSE Seed Mock Data.
Result: User changes are now persistent.
📂 Project Architecture
Tech Stack
Backend: Python 3.11, FastAPI, Uvicorn, SQLAlchemy (SQLite).
Frontend: React 19, TypeScript, Vite, TailwindCSS, TanStack Query.
Desktop: PyWebView 4.4.1 (Browser window wrapper).
Build: PyInstaller 6.5.0.
Key File Map
File	Responsibility	Status
backend/app/main.py	Entry point, DB Seeding Logic, Task Mgr startup.	🟢 Modified
backend/app/services/amazon_api.py	Amazon SP-API Client. Handles Real vs Mock logic.	🟢 Modified
backend/app/api/settings.py	(N/A - logic moved to amazon_connect).	🟡 Deprecated
backend/app/api/amazon_connect/...	Handles /connect, /verify, /status.	🟢 Active
frontend/src/pages/settings/SettingsPage.tsx	User Config Form. Inputs for Credentials.	🟢 Rebuilt
frontend/src/pages/products/ProductCreatePage.tsx	Add/Edit Product, Multi-Listing Logic.	🟢 Fixed
frontend/src/pages/listings/ListingQueuePage.tsx	Displays Queue from Backend.	🟢 Active
frontend/src/components/common/MediaUploader.tsx	Drag & Drop Image Uploader.	🟢 Active
start-dev.bat	Master Start Script. Kills ports, starts both servers.	🟢 Created
crazy_lister.spec	PyInstaller build config.	🟢 Active
🚀 Workflow: How to Run & Build
1. Development Mode (Daily Work)
ALWAYS use the batch file to ensure clean ports.

Run start-dev.bat (Located in root).
Wait for: Uvicorn running on http://127.0.0.1:8765.
Browser opens at: http://localhost:3000.
First Run Check: Go to Settings -> Edit -> Enter test123 for IDs -> Save.
2. Building the .exe
# 1. Clean old builds
rmdir /s /q dist build

# 2. Build Frontend (Production)
cd frontend && npm run build && cd ..

# 3. Build Backend (PyInstaller)
pyinstaller --clean crazy_lister.spec
🐛 Known Bugs & Open Tasks
1. Image Uploader (Drag & Drop) 🟡
Status: Component exists (MediaUploader.tsx), but logic needs review to ensure Base64 or local file paths are saving correctly to SQLite.
Task: Verify that images persist after refresh.
2. “Edit Product” Routing 🟡
Status: “Edit” button in Product List works, but sometimes data pre-filling is slow.
Task: Optimize useLocation state transfer.
3. Multi-Listing Logic 🟢
Status: Implemented. Creates SKU-01, SKU-02 based on “Copies” input.
Task: Monitor performance when creating 50+ copies at once (might need background task delay).
🔑 Credentials & Access
Admin: Not applicable (Single user app).
Amazon Mock Credentials:
Client ID: test123
Client Secret: test123
Refresh Token: Atzr|test123
Seller ID: MOCK-SELLER-01
Database: %APPDATA%/CrazyLister/crazy_lister.db
📝 Engineer’s Checklist (Day 1)
[ ] Verify pyi_rth_pkgres.py is empty (size 0kb).
[ ] Run start-dev.bat and confirm no port conflicts.
[ ] Check backend/.env -> USE_AMAZON_MOCK=True.
[ ] Go to Settings, enter mock creds, verify “Connected” status.
[ ] Create a product, verify it appears in the List.
[ ] Submit Listing, verify it appears in the Queue.
END OF FORENSIC REPORT

