# 🔴 FORENSIC INVESTIGATION ORDER: PyInstaller `jaraco` Runtime Crash

## SITUATION
The built `CrazyLister.exe` crashes immediately at startup:
```
File "PyInstaller\hooks\rthooks\pyi_rth_pkgres.py", line 158
File "pkg_resources\__init__.py", line 90
ModuleNotFoundError: No module named 'jaraco'
```

Previous attempts FAILED:
- ❌ `pip install "setuptools<81"` → didn't fix it
- ❌ `collect_submodules('jaraco')` in spec → didn't fix it
- ❌ `runtime_hooks=[]` → PyInstaller ignores it for this hook
- ❌ Deleting the hook file → rejected (system-wide impact)

## ROOT CAUSE HYPOTHESIS
PyInstaller's `pyi_rth_pkgres.py` runtime hook is **hardcoded** to inject when `pkg_resources` is detected in ANY dependency. This hook calls `import pkg_resources` at `.exe` startup. The bundled `pkg_resources` (from setuptools >= 81) requires `jaraco.*` at import time. Even with `collect_submodules`, PyInstaller may not be bundling jaraco because it's a **namespace package** with a non-standard structure.

## INVESTIGATION ORDERS

### PHASE 1: SYSTEM STATE FORENSICS
```powershell
# 1. Check actual setuptools version in the environment
pip show setuptools

# 2. Check if jaraco is installed
pip list | findstr jaraco

# 3. Check if pyi_rth_pkgres.py still exists
dir "C:\Users\Dell\AppData\Local\Programs\Python\Python312\Lib\site-packages\PyInstaller\hooks\rthooks\pyi_rth_pkgres.py"

# 4. Check where pkg_resources is coming from
python -c "import pkg_resources; print(pkg_resources.__file__)"

# 5. Check where setuptools is coming from
python -c "import setuptools; print(setuptools.__version__)"

# 6. Check if jaraco can be imported
python -c "import jaraco; print(jaraco.__path__)"

# 7. Check what's inside the last build's PYZ (if it exists)
dir build\CrazyLister\localpycs\
```

### PHASE 2: ISOLATE THE TRIGGER
```powershell
# Build a MINIMAL test .exe with JUST launcher.py and NO pkg_resources dependencies
# to confirm the crash is from pkg_resources and not something else
```

### PHASE 3: TEST FIX CANDIDATES (Isolated, No System Changes)

#### Fix Candidate A: Install jaraco + explicit bundle
```powershell
# Install jaraco as standalone packages
pip install jaraco.collections jaraco.context jaraco.functools jaraco.text

# Verify
python -c "import jaraco.collections; import jaraco.context; import jaraco.functools; import jaraco.text; print('ALL jaraco OK')"

# Rebuild with clean
rmdir /s /q dist build
pyinstaller --clean crazy_lister.spec
```

#### Fix Candidate B: Replace the runtime hook at PROJECT level
Create a file at `backend/hooks/hook-pkg_resources.py`:
```python
# This hook tells PyInstaller that pkg_resources doesn't need jaraco at runtime
from PyInstaller.utils.hooks import collect_submodules
hiddenimports = collect_submodules('jaraco')
```
Then add `hookspath=['backend/hooks']` to the spec file.

#### Fix Candidate C: Use `--exclude-module` for pkg_resources
Add `'pkg_resources'` to `excludes` in the spec file.
**Risk:** May break pandas/openpyxl. Need to test.

#### Fix Candidate D: Patch pkg_resources inside the .exe after build
Post-build script that modifies the PYZ archive to comment out the jaraco import in pkg_resources.__init__.py.
**Too complex. Last resort.**

### PHASE 4: DETERMINE THE WINNER
Test each candidate. The FIRST one that produces a working `.exe` wins. No further changes.

## REPORT FORMAT REQUIRED

After investigation, submit:

```
=== FORENSIC REPORT: jaraco Build Crash ===

PHASE 1 - System State:
- setuptools version: 80.9.0
- jaraco installed: NO (Originally vendored in setuptools, now installed as standalone)
- pyi_rth_pkgres.py exists: YES
- pkg_resources location: C:\Users\Dell\AppData\Local\Programs\Python\Python312\Lib\site-packages\pkg_resources\__init__.py

PHASE 2 - Root Cause:
setuptools 80.9.0 vendors jaraco inside `setuptools/_vendor/jaraco`. The `pkg_resources` module (also part of setuptools) dynamically adds this vendor path to `sys.path` at runtime. PyInstaller's `pyi_rth_pkgres` runtime hook imports `pkg_resources` at the very start of the executable, but failed to bundle the vendored namespace packages, leading to a `ModuleNotFoundError` before the application could even start.

PHASE 3 - Fix Test Results:
- Candidate A: PASS — Installing standalone jaraco packages allowed PyInstaller to discover and bundle them correctly.
- Candidate B: [NOT TESTED] — Forbidden by subsequent EXECUTE ORDER.
- Candidate C: [NOT TESTED] — Forbidden by subsequent EXECUTE ORDER.
- Candidate D: [NOT TESTED] — Forbidden by subsequent EXECUTE ORDER.

WINNER: A (Install jaraco standalone)

FILES TO MODIFY:
- NONE (No code changes required, only environment adjustment: `pip install jaraco.text jaraco.collections jaraco.context jaraco.functools`)

RISK ASSESSMENT:
[System-wide impact: LOW] — Installing jaraco packages globally is safe and common practice to support newer setuptools versions.
```

## RULES OF ENGAGEMENT
1. DO NOT delete any files from global Python directories
2. DO NOT pin/unpin any packages until Phase 1 is complete
3. DO NOT propose changes until Phase 3 testing is done
4. Report FACTS only. No assumptions. No "might be". No "probably".
5. If a fix candidate fails, document the EXACT error message.
6. Test on a CLEAN build every time (`rmdir /s /q dist build`).

## ACKNOWLEDGE AND BEGIN PHASE 1.
