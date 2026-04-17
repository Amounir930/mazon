# ============================================================
# Crazy Lister v3.0 — Build Script (Windows)
# Builds: Frontend → Backend .exe → Installer
# ============================================================
# Usage: .\build_release.ps1
# ============================================================

$ErrorActionPreference = "Stop"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Crazy Lister v3.0 — Release Build" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# -------------------------------------------------------
# 1. Configuration
# -------------------------------------------------------
$PROJECT_ROOT = Split-Path $PSScriptRoot -Parent
$FRONTEND_DIR = Join-Path $PROJECT_ROOT "frontend"
$BACKEND_DIR = Join-Path $PROJECT_ROOT "backend"
$RELEASE_DIR = Join-Path $PROJECT_ROOT "releases"
$BUILD_OUTPUT = Join-Path $BACKEND_DIR "dist"
$VERSION = "3.0.0"
$BUILD_NAME = "CrazyLister-v$VERSION"

Write-Host ""
Write-Host "[1/6] Configuration" -ForegroundColor Yellow
Write-Host "  Project Root : $PROJECT_ROOT" -ForegroundColor Gray
Write-Host "  Frontend     : $FRONTEND_DIR" -ForegroundColor Gray
Write-Host "  Backend      : $BACKEND_DIR" -ForegroundColor Gray
Write-Host "  Release Dir  : $RELEASE_DIR" -ForegroundColor Gray
Write-Host "  Version      : $VERSION" -ForegroundColor Gray

# [2/6] Cleaning previous builds...
Write-Host "[2/6] Cleaning previous builds..." -ForegroundColor Yellow

# Kill any running instances to prevent file locking
Stop-Process -Name "CrazyLister" -Force -ErrorAction SilentlyContinue
Stop-Process -Name "Crazy Lister" -Force -ErrorAction SilentlyContinue

if (Test-Path "$FRONTEND_DIR\dist") {
    Remove-Item -Recurse -Force "$FRONTEND_DIR\dist"
    Write-Host "  ✓ Frontend dist cleaned" -ForegroundColor Green
}

if (Test-Path "$BACKEND_DIR\build") {
    Remove-Item -Recurse -Force "$BACKEND_DIR\build"
    Write-Host "  ✓ Backend build cleaned" -ForegroundColor Green
}

if (Test-Path "$BACKEND_DIR\dist") {
    Remove-Item -Recurse -Force "$BACKEND_DIR\dist"
    Write-Host "  ✓ Backend dist cleaned" -ForegroundColor Green
}

if (Test-Path "$RELEASE_DIR\$BUILD_NAME") {
    Remove-Item -Recurse -Force "$RELEASE_DIR\$BUILD_NAME"
    Write-Host "  ✓ Release folder cleaned" -ForegroundColor Green
}

# -------------------------------------------------------
# 3. Build Frontend
# -------------------------------------------------------
Write-Host ""
Write-Host "[3/6] Building Frontend..." -ForegroundColor Yellow

Push-Location $FRONTEND_DIR
try {
    # Use cmd /c to prevent powershell from treating stderr warnings as fatal errors
    cmd.exe /c "npm run build"
    if ($LASTEXITCODE -ne 0) {
        throw "Frontend build failed!"
    }
    Write-Host "  ✓ Frontend built successfully" -ForegroundColor Green
} finally {
    Pop-Location
}

# Verify frontend
if (-not (Test-Path "$FRONTEND_DIR\dist\index.html")) {
    throw "Frontend dist/index.html not found after build!"
}

# -------------------------------------------------------
# 4. Build Backend .exe with PyInstaller
# -------------------------------------------------------
Write-Host ""
Write-Host "[4/6] Building Backend .exe (PyInstaller)..." -ForegroundColor Yellow

Push-Location $BACKEND_DIR
try {
    cmd.exe /c "pyinstaller build.spec --clean --noconfirm"
    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller build failed!"
    }
    Write-Host "  ✓ Backend .exe built successfully" -ForegroundColor Green
} finally {
    Pop-Location
}

# Verify .exe
$EXE_PATH = "$BACKEND_DIR\dist\CrazyLister\CrazyLister.exe"
if (-not (Test-Path $EXE_PATH)) {
    throw "CrazyLister.exe not found at $EXE_PATH"
}

# -------------------------------------------------------
# 5. Prepare Release Package
# -------------------------------------------------------
Write-Host ""
Write-Host "[5/6] Preparing release package..." -ForegroundColor Yellow

# Create release folder
New-Item -ItemType Directory -Force -Path "$RELEASE_DIR\$BUILD_NAME" | Out-Null

# Copy .exe folder contents (Flattened)
Copy-Item -Recurse -Force "$BACKEND_DIR\dist\CrazyLister\*" "$RELEASE_DIR\$BUILD_NAME\"
Write-Host "  ✓ Executable files flattened and copied" -ForegroundColor Green

# Copy .env
if (Test-Path "$BACKEND_DIR\.env") {
    Copy-Item -Force "$BACKEND_DIR\.env" "$RELEASE_DIR\$BUILD_NAME\"
    Write-Host "  ✓ .env copied" -ForegroundColor Green
} else {
    Copy-Item -Force "$BACKEND_DIR\.env.example" "$RELEASE_DIR\$BUILD_NAME\.env"
    Write-Host "  ✓ .env.example copied as .env" -ForegroundColor Green
}

# Copy README
Copy-Item -Force "$PROJECT_ROOT\README.md" "$RELEASE_DIR\$BUILD_NAME\" 2>$null
Write-Host "  ✓ README copied" -ForegroundColor Green

# Create launcher batch file
$BATCH_CONTENT = @"
@echo off
echo Starting Crazy Lister v$VERSION...
start "" "CrazyLister.exe"
echo If the window doesn't appear, check the logs in %%APPDATA%%\CrazyLister\
"@

$BATCH_PATH = "$RELEASE_DIR\$BUILD_NAME\StartCrazyLister.bat"
Set-Content -Path $BATCH_PATH -Value $BATCH_CONTENT -Encoding ASCII
Write-Host "  ✓ Launcher batch file created" -ForegroundColor Green

# Create shortcuts.lnk (optional, for advanced installer)
Write-Host "  ✓ Release package prepared" -ForegroundColor Green

# -------------------------------------------------------
# 6. Skip ZIP archive for speed
# -------------------------------------------------------
Write-Host ""
Write-Host "[6/6] Creating ZIP archive (SKIPPED)..." -ForegroundColor Yellow

# $ZIP_PATH = "$RELEASE_DIR\$BUILD_NAME.zip"
# if (Test-Path $ZIP_PATH) {
#    Remove-Item -Force $ZIP_PATH
# }
# Compress-Archive -Path "$RELEASE_DIR\$BUILD_NAME\*" -DestinationPath $ZIP_PATH
# $ZIP_SIZE = (Get-Item $ZIP_PATH).Length / 1MB
# $ZIP_SIZE_STR = "{0:N2} MB" -f $ZIP_SIZE
# Write-Host "  ✓ ZIP created: $ZIP_PATH ($ZIP_SIZE_STR)" -ForegroundColor Green

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  ✓ Build Complete!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Release Folder: $RELEASE_DIR\$BUILD_NAME\" -ForegroundColor White
# Write-Host "  ZIP Archive   : $ZIP_PATH"
# Write-Host "  Size          : $ZIP_SIZE_STR"
Write-Host ""
Write-Host "  To install on client machine:" -ForegroundColor Yellow
Write-Host "  1. Copy the Release Folder contents to C:\Program Files\CrazyLister\" -ForegroundColor Gray
Write-Host "  2. Run StartCrazyLister.bat or CrazyLister.exe" -ForegroundColor Gray
Write-Host "  3. Configure Amazon SP-API credentials in .env" -ForegroundColor Gray
Write-Host ""
