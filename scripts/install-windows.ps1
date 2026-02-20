# U-ITE installer for Windows

Write-Host "📦 Installing U-ITE..." -ForegroundColor Green

# Check Python version
$python_version = python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
if ([version]$python_version -ge [version]"3.8") {
    Write-Host "✅ Python $python_version found" -ForegroundColor Green
} else {
    Write-Host "❌ Python 3.8+ required" -ForegroundColor Red
    exit 1
}

# Install via pip
pip install .

Write-Host "✅ U-ITE installed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Try: uite --help"
