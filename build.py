"""
Build Script for Crazy Lister v3.0
====================================
Builds the standalone Windows .exe file.

Usage:
    python build.py

Requirements:
    - Node.js 18+ (for frontend build)
    - Python 3.11+ (for backend)
    - All dependencies installed (pip install -r backend/requirements.txt)
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path
from datetime import datetime

# Colors for console output
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"


def print_header(text):
    print(f"\n{BOLD}{'='*60}{RESET}")
    print(f"  {text}")
    print(f"{BOLD}{'='*60}{RESET}\n")


def print_success(text):
    print(f"{GREEN}✅ {text}{RESET}")


def print_warning(text):
    print(f"{YELLOW}⚠️  {text}{RESET}")


def print_error(text):
    print(f"{RED}❌ {text}{RESET}")


def run(cmd, cwd=None, check=True):
    """Run a shell command"""
    print(f"  $ {cmd}")
    result = subprocess.run(
        cmd, shell=True, cwd=cwd,
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print_error(f"Command failed: {cmd}")
        if result.stderr:
            print(f"  Error: {result.stderr[:500]}")
        if check:
            sys.exit(1)
    return result


def check_requirements():
    """Check that all requirements are met"""
    print_header("Step 0: Checking Requirements")

    # Check Python version
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 11):
        print_error(f"Python 3.11+ required (found {version.major}.{version.minor})")
        sys.exit(1)
    print_success(f"Python {version.major}.{version.minor}.{version.micro}")

    # Check Node.js
    try:
        result = run("node --version", check=False)
        print_success(f"Node.js {result.stdout.strip()}")
    except:
        print_error("Node.js not found. Install from https://nodejs.org/")
        sys.exit(1)

    # Check npm
    try:
        result = run("npm --version", check=False)
        print_success(f"npm {result.stdout.strip()}")
    except:
        print_error("npm not found")
        sys.exit(1)

    # Check PyInstaller
    try:
        import PyInstaller
        print_success(f"PyInstaller {PyInstaller.__version__}")
    except ImportError:
        print_error("PyInstaller not installed. Run: pip install pyinstaller")
        sys.exit(1)

    # Check pywebview
    try:
        import webview
        version = getattr(webview, '__version__', 'unknown')
        print_success(f"pywebview {version}")
    except ImportError:
        print_error("pywebview not installed. Run: pip install pywebview")
        sys.exit(1)


def build_frontend():
    """Build the React frontend"""
    print_header("Step 1: Building Frontend (React/Vite)")

    project_root = Path(__file__).parent
    frontend_dir = project_root / "frontend"

    if not frontend_dir.exists():
        print_error(f"Frontend directory not found: {frontend_dir}")
        sys.exit(1)

    # Install dependencies
    print("  Installing frontend dependencies...")
    run("npm install", cwd=frontend_dir)

    # Build
    print("  Building frontend...")
    run("npm run build", cwd=frontend_dir)

    # Verify
    dist_dir = frontend_dir / "dist"
    index_html = dist_dir / "index.html"

    if not index_html.exists():
        print_error("Frontend build failed — index.html not found")
        sys.exit(1)

    # Count files
    file_count = sum(1 for _ in dist_dir.rglob("*") if _.is_file())
    total_size = sum(f.stat().st_size for f in dist_dir.rglob("*") if f.is_file())
    size_mb = total_size / (1024 * 1024)

    print_success(f"Frontend built: {file_count} files, {size_mb:.1f} MB")


def build_exe():
    """Build the .exe with PyInstaller"""
    print_header("Step 2: Building .exe (PyInstaller)")

    project_root = Path(__file__).parent
    spec_file = project_root / "crazy_lister.spec"

    if not spec_file.exists():
        print_error(f"Spec file not found: {spec_file}")
        sys.exit(1)

    # Clean previous build
    dist_dir = project_root / "dist"
    build_dir = project_root / "build"

    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    if build_dir.exists():
        shutil.rmtree(build_dir)

    # Run PyInstaller
    print("  Running PyInstaller...")
    run(f"pyinstaller --clean {spec_file}")

    # Verify output
    exe_path = dist_dir / "CrazyLister.exe"
    if not exe_path.exists():
        print_error("Build failed — .exe not found")
        sys.exit(1)

    size_mb = exe_path.stat().st_size / (1024 * 1024)
    print_success(f"Build successful: {exe_path.name} ({size_mb:.1f} MB)")

    # Check for warnings
    warn_file = project_root / "build" / "warn-CrazyLister.txt"
    if warn_file.exists():
        print_warning("PyInstaller generated warnings (check build/warn-CrazyLister.txt)")


def create_release():
    """Create a release package"""
    print_header("Step 3: Creating Release Package")

    project_root = Path(__file__).parent
    dist_dir = project_root / "dist"
    exe_path = dist_dir / "CrazyLister.exe"

    # Create release folder
    version = "3.0.0"
    release_name = f"CrazyLister-v{version}"
    release_dir = project_root / "releases" / release_name
    release_dir.mkdir(parents=True, exist_ok=True)

    # Copy .exe
    shutil.copy(exe_path, release_dir / f"{release_name}.exe")

    # Create README
    readme = release_dir / "README.txt"
    readme.write_text(f"""
===============================================
  Crazy Lister v{version} — تعليمات الاستخدام
===============================================

1. المتطلبات:
   - Windows 10 أو أحدث
   - اتصال بالإنترنت (للربط مع Amazon)
   - حساب Amazon Seller Central

2. التشغيل:
   - دبل كليك على {release_name}.exe
   - انتظر 2-3 ثواني حتى يفتح البرنامج

3. الإعداد الأولي:
   - أدخل بيانات Amazon (Client ID, Secret, Refresh Token, Seller ID)
   - اضغط "تحقق من الاتصال"

4. أين يتم حفظ البيانات؟
   - %APPDATA%\\CrazyLister\\

5. الدعم:
   - اللوجات: %APPDATA%\\CrazyLister\\crazy_lister.log
   - تاريخ البناء: {datetime.now().strftime('%Y-%m-%d')}
""")

    print_success(f"Release created: {release_dir}")

    # Show final info
    release_size = sum(f.stat().st_size for f in release_dir.rglob("*") if f.is_file())
    print(f"\n  📦 Release size: {release_size / (1024*1024):.1f} MB")
    print(f"  📁 Location: {release_dir}")
    print(f"  📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")


def main():
    print(f"\n{BOLD}🚀 Crazy Lister v3.0 — Build Script{RESET}\n")

    check_requirements()
    build_frontend()
    build_exe()
    create_release()

    print_header("Build Complete!")
    print(f"{GREEN}  🎉 Your app is ready!{RESET}\n")


if __name__ == "__main__":
    main()
