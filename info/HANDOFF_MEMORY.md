# 📋 Crazy Lister v3.0 — Chat Memory & Handoff Document
## Project Status: Active Development / Frontend Bug Fixing

> **Last Updated:** April 10, 2026  
> **Version:** 3.0.0 (Desktop Standalone App)  
> **Current Phase:** Phase 8 (Amazon Integration) & Phase 9 (Frontend Polish)  
> **Mode:** Simulation Mode (`USE_AMAZON_MOCK=True`)

---

## 🎯 Executive Summary (30 Seconds)
**Goal:** Windows Desktop App (`.exe`) for single-seller Amazon listing automation.  
**Tech Stack:** FastAPI (Python 3.11) + React 19 (TypeScript/Vite) + PyWebView + SQLite.  
**Current Status:**
*   ✅ **Backend:** 100% Working. SQLite, Asyncio Tasks, Amazon Mock Client.
*   ✅ **Desktop Wrapper:** PyInstaller builds work (Fixed `pyi_rth_pkgres.py` issue).
*   ✅ **Frontend Connectivity:** Connected to Backend (Port `8765`).
*   🟡 **Frontend Actions:** Delete works. **Create & Edit are BROKEN** (Needs immediate fix).

---

## 🛠️ Critical Technical Fixes Implemented (Do Not Revert)

### 1. The "Jaraco" / PyInstaller Build Fix 🔴
*   **Issue:** `pyi_rth_pkgres.py` caused infinite dependency loops (`ModuleNotFoundError: jaraco/platformdirs`).
*   **Solution:** **Neutralized** the file (made it empty) at:
    `.../site-packages/PyInstaller/hooks/rthooks/pyi_rth_pkgres.py`.
*   **Result:** `.exe` builds successfully (~70-80MB) without errors.

### 2. The "Redirect Loop" / 404 Fix 🟡
*   **Issue:** Frontend requests resulted in `307 Redirects` because Backend routes ended with `/` but Frontend requested without (e.g., `/products`).
*   **Solution:** Removed trailing slashes from `@router.get("/")` in:
    *   `backend/app/api/products.py`
    *   `backend/app/api/listings.py`
    *   `backend/app/api/amazon_connect/endpoints.py`
*   **Result:** API calls return `200 OK` immediately.

### 3. The Proxy Fix (Vite) 🟡
*   **Issue:** Frontend `dev` server wasn't reaching Backend.
*   **Solution:** Updated `frontend/vite.config.ts` proxy target to `http://127.0.0.1:8765`.

---

## 📂 Current File Structure (Key Files)

```text
c:\Users\Dell\Desktop\learn\amazon\
├── backend/
│   ├── app/
│   │   ├── launcher.py              ← Entry point (Desktop Mode)
│   │   ├── services/
│   │   │   └── amazon_api.py        ← Contains BOTH Real API + High-Fidelity Simulation
│   │   ├── api/
│   │   │   ├── products.py          ← CRUD (Delete works, Create/Edit logic exists)
│   │   │   ├── listings.py          ← Listing submission (Asyncio tasks)
│   │   │   └── amazon_connect/      ← Auth endpoints
│   └── .env                         ← USE_AMAZON_MOCK=True (Currently Active)
├── frontend/
│   ├── src/pages/products/
│   │   ├── ProductListPage.tsx      ← Delete works. Edit button is DUMMY currently.
│   │   └── ProductCreatePage.tsx    ← Currently sends HARD CODED data. Needs State Binding.
│   └── vite.config.ts               ← Proxy configured to 8765
└── releases/
    └── CrazyLister-v3.0.0/          ← Last working .exe build
```

---

## 🚨 OPEN ISSUES (Immediate Action Required)

### Issue #1: Product Create Form is Hardcoded
*   **Problem:** `ProductCreatePage.tsx` ignores user input. It sends `sku: 'TEST-' + Date.now()` and fixed names.
*   **Fix Needed:** Implement `useState` for all form fields and pass actual data to API.

### Issue #2: Product Edit Button is Dummy
*   **Problem:** `ProductListPage.tsx` edit button shows a toast "Coming Soon".
*   **Fix Needed:** Implement routing to Create page with pre-filled data for editing existing products.

---

## 🚀 Deployment Workflow (How to Run/Build)

### 1. Local Development (For Testing Fixes)
**Terminal 1 (Backend):**
```powershell
cd c:\Users\Dell\Desktop\learn\amazon\backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8765 --log-level info
```
**Terminal 2 (Frontend):**
```powershell
cd c:\Users\Dell\Desktop\learn\amazon\frontend
npm run dev
# Access via http://localhost:3001 (or port shown)
```

### 2. Building the .exe
```powershell
cd c:\Users\Dell\Desktop\learn\amazon
rmdir /s /q dist build
pyinstaller --clean crazy_lister.spec
```

---

## 💾 Database & Credentials
*   **Database Location:** `%APPDATA%\CrazyLister\crazy_lister.db`
*   **Amazon Credentials:** currently stored in `backend/.env` (`USE_AMAZON_MOCK=True`).
    *   *Note:* Real AWS keys are placeholders (`<REAL_KEY>`) in `.env`.
*   **Simulation Data:** The Mock Client returns 3 realistic products (T-shirt, Speaker, Yoga Mat).

---

## 📝 Engineer's Next Task
**Directive:** **"FRONTEND CRUD ACTIVATION"**
*   **Scope:** Fix `ProductCreatePage.tsx` and `ProductListPage.tsx`.
*   **Constraint:** No dummy data allowed. All inputs must be controlled components.
*   **Goal:** User can Type Name/Price -> Click Save -> See it in table -> Click Edit -> Change Price -> Save.
