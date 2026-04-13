# Clean ALL temp/build/log files
# Run: powershell -ExecutionPolicy Bypass -File clean.ps1

$ErrorActionPreference = "SilentlyContinue"
$deletedCount = 0

function Remove-Tree($path, $desc) {
    if (Test-Path $path) {
        Remove-Item -Path $path -Recurse -Force
        Write-Host "DELETED: $desc ($path)" -ForegroundColor Green
        $script:deletedCount++
    }
}

function Remove-ByPattern($root, $pattern, $desc) {
    $items = Get-ChildItem -Path $root -Recurse -Force -Filter $pattern -ErrorAction SilentlyContinue
    foreach ($item in $items) {
        Remove-Item -Path $item.FullName -Recurse -Force
        Write-Host "  DELETED $desc : $($item.Name)" -ForegroundColor Green
        $script:deletedCount++
    }
}

Write-Host "`nStarting Cleanup..." -ForegroundColor Cyan
Write-Host "==========================================`n" -ForegroundColor Cyan

# 1. Python cache
Write-Host "Removing __pycache__ folders..."
Remove-ByPattern "backend" "__pycache__" "__pycache__"
Remove-ByPattern "." "*.pyc" ".pyc files"

# 2. Build artifacts
Remove-Tree "build" "Build folder"
Remove-Tree "dist" "Dist folder"

# 3. Log files
Write-Host "`nRemoving log files..."
Remove-ByPattern "." "*.log" "Log file"

# 4. Temp files
Write-Host "`nRemoving temp files..."
Remove-ByPattern "." "*.tmp" "Temp file"

# 5. Execute output files
Write-Host "`nRemoving execute-output files..."
$execOutputs = Get-ChildItem -Path "$env:USERPROFILE\.qwen" -Recurse -Force -Filter "execute-output-*" -ErrorAction SilentlyContinue
foreach ($file in $execOutputs) {
    Remove-Item -Path $file.FullName -Force
    Write-Host "  DELETED execute-output: $($file.Name)" -ForegroundColor Green
    $script:deletedCount++
}

# 6. Product images (keep if needed)
Write-Host "`nRemoving product images..."
$imageFiles = @("51raTibkapL._AC_SL1000_.jpg", "61f4oiT466L._AC_SL1000_.jpg", "61VQ6XxrCGL._AC_SL1000_.jpg")
foreach ($img in $imageFiles) {
    if (Test-Path $img) {
        Remove-Item -Path $img -Force
        Write-Host "  DELETED image: $img" -ForegroundColor Green
        $script:deletedCount++
    }
}

# 7. .pytest_cache
Remove-Tree ".pytest_cache" "Pytest cache"

# 8. .mypy_cache
Remove-Tree ".mypy_cache" "Mypy cache"

Write-Host "`n==========================================" -ForegroundColor Cyan
Write-Host "Cleanup Complete!" -ForegroundColor Green
Write-Host "Deleted: $deletedCount items" -ForegroundColor Green
Write-Host ""
