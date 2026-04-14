# -*- mode: python ; coding: utf-8 -*-
"""
Crazy Lister v3.0 — PyInstaller Build Specification
Builds a standalone Windows .exe with bundled frontend.

Usage:
    pyinstaller build.spec
"""
import os
from pathlib import Path

# Project paths - SPECPATH is the directory containing this .spec file
BACKEND_DIR = Path(SPECPATH)
PROJECT_ROOT = BACKEND_DIR.parent
FRONTEND_DIST = PROJECT_ROOT / "frontend" / "dist"
ASSETS_DIR = PROJECT_ROOT / "assets"

# Verify frontend was built
if not FRONTEND_DIST.exists():
    raise RuntimeError(
        f"❌ Frontend not built! Run 'cd frontend && npm run build' first.\n"
        f"Expected: {FRONTEND_DIST}"
    )

a = Analysis(
    ['app/launcher.py'],
    pathex=[str(BACKEND_DIR)],
    binaries=[],
    datas=[
        # Bundle built frontend
        (str(FRONTEND_DIST), 'frontend/dist'),
        # Bundle icon
        (str(ASSETS_DIR / 'icon.ico'), 'assets'),
    ],
    hiddenimports=[
        # FastAPI + Uvicorn
        'fastapi',
        'uvicorn',
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        # SQLAlchemy
        'sqlalchemy',
        'sqlalchemy.ext.asyncio',
        'sqlalchemy.dialects.sqlite',
        'alembic',
        # Amazon SP-API
        'boto3',
        'botocore',
        # Playwright
        'playwright',
        'playwright.sync_api',
        # HTTP
        'requests',
        'httpx',
        'niquests',
        'curl_cffi',
        'aiofiles',
        # Data processing
        'openpyxl',
        'pandas',
        # Utilities
        'loguru',
        'pydantic',
        'pydantic_settings',
        'multipart',
        'dotenv',
        'tenacity',
        'bs4',
        'cryptography',
        # PyWebView
        'webview',
        'webview.http',
        'webview.js',
        # SSL/TLS
        'certifi',
        'ssl',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Remove unnecessary GUI toolkits
        'tkinter',
        'PyQt5',
        'PyQt6',
        'PySide2',
        'PySide6',
        'wx',
        # Remove test/dev packages
        'unittest',
        'pytest',
        'ipython',
        'jupyter',
        # Remove unnecessary backends
        'matplotlib',
        'scipy',
        'numpy',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='CrazyLister',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Hide console window (desktop app mode)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(ASSETS_DIR / 'icon.ico'),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='CrazyLister',
)
