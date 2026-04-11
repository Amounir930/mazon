# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Crazy Lister v3.0
Builds a single .exe file with bundled frontend
"""
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

# Collect all jaraco submodules (needed by pkg_resources/setuptools at runtime)
_jaraco_imports = collect_submodules('jaraco')

a = Analysis(
    ['backend/app/launcher.py'],
    pathex=['backend'],
    binaries=[],
    datas=[
        ('frontend/dist', 'frontend/dist'),
        ('assets/icon.ico', 'assets'),
    ],
    hiddenimports=[
        # Uvicorn
        'uvicorn',
        'uvicorn.lifespan.on',
        'uvicorn.lifespan.off',
        'uvicorn.loops.auto',
        'uvicorn.loops.asyncio',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.http.h11_impl',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.protocols.websockets.wsproto_impl',
        'uvicorn.logging',
        # FastAPI / Starlette
        'fastapi',
        'fastapi.routing',
        'starlette',
        'starlette.routing',
        # Database
        'sqlalchemy',
        'sqlalchemy.dialects.sqlite',
        'sqlalchemy.orm',
        'sqlalchemy.orm.session',
        'sqlalchemy.orm.decl_api',
        # Pydantic
        'pydantic',
        'pydantic_settings',
        'pydantic.fields',
        # PyWebView
        'webview',
        'webview.platforms.winforms',
        # Amazon SP-API
        'sp_api',
        'sp_api.api',
        'sp_api.base',
        'sp_api.api.listings_items',
        'sp_api.api.sellers',
        'sp_api.api.feeds',
        'boto3',
        'botocore',
        # App modules
        'app.models.seller',
        'app.models.product',
        'app.models.listing',
        'app.api.router',
        'app.api.amazon_connect',
        'app.api.sellers',
        'app.api.products',
        'app.api.listings',
        'app.api.feeds',
        'app.api.tasks',
        'app.api.products_sync',
        'app.api.bulk_upload',
        'app.services.amazon_api',
        'app.services.listing_service',
        'app.services.product_service',
        'app.services.feed_service',
        'app.tasks.task_manager',
        'app.tasks.listing_tasks',
        'app.tasks.feed_tasks',
        'app.schemas.product',
        # Utilities
        'loguru',
        'pandas',
        'openpyxl',
        'dateutil',
        'email_validator',
        'httpx',
        # setuptools / pkg_resources runtime dependencies
        'setuptools',
        'pkg_resources',
        'packaging',
        'packaging.version',
        'packaging.specifiers',
        'packaging.requirements',
        'platformdirs',
    ] + _jaraco_imports,
    hookspath=[],
    hooksconfig={},
    # Disable the pkg_resources runtime hook — our app doesn't use it,
    # and it causes ModuleNotFoundError for jaraco at startup.
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'scipy',
        'IPython',
        'pip',
        'pytest',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='CrazyLister',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico',          # Application icon
)
