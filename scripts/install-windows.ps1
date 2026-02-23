<#
U-ITE Windows Installation Script
==================================
PowerShell installer for U-ITE on Windows systems. This script handles
the basic installation process with Windows-specific considerations.

Features:
- Python version check (3.8+ required)
- pip installation
- User-friendly colored output
- Error handling

Usage:
    .\install-windows.ps1
    # or from PowerShell:
    powershell -ExecutionPolicy Bypass -File install-windows.ps1
#>

# ============================================================================
# Welcome Banner
# ============================================================================
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "📦 U-ITE Network Observer Installer" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# ============================================================================
# Python Version Check
# ============================================================================
Write-Host "🔍 Checking Python version..." -ForegroundColor Yellow

try {
    # Get Python version
    $python_version = python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
    
    if ($python_version) {
        Write-Host "   Detected Python $python_version" -ForegroundColor Gray
        
        # Compare versions (3.8+ required)
        if ([version]$python_version -ge [version]"3.8") {
            Write-Host "✅ Python $python_version found (required: 3.8+)" -ForegroundColor Green
        } else {
            Write-Host "❌ Python 3.8+ required (found: $python_version)" -ForegroundColor Red
            Write-Host "   Please download Python 3.8 or later from:" -ForegroundColor Yellow
            Write-Host "   https://www.python.org/downloads/" -ForegroundColor Cyan
            exit 1
        }
    } else {
        throw "Python not found"
    }
}
catch {
    Write-Host "❌ Python not found" -ForegroundColor Red
    Write-Host "   Please install Python 3.8 or later from:" -ForegroundColor Yellow
    Write-Host "   https://www.python.org/downloads/" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "   After installation, make sure Python is added to PATH" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# ============================================================================
# Check pip availability
# ============================================================================
Write-Host "🔍 Checking pip..." -ForegroundColor Yellow

try {
    $pip_version = pip --version 2>$null
    if ($pip_version) {
        Write-Host "✅ pip found" -ForegroundColor Green
    } else {
        throw "pip not found"
    }
}
catch {
    Write-Host "⚠️  pip not found, attempting to install..." -ForegroundColor Yellow
    
    # Try to ensure pip
    python -m ensurepip --upgrade 2>$null
    
    # Check again
    $pip_version = pip --version 2>$null
    if (-not $pip_version) {
        Write-Host "❌ Could not install pip automatically" -ForegroundColor Red
        Write-Host "   Please install pip manually:" -ForegroundColor Yellow
        Write-Host "   python -m ensurepip --upgrade" -ForegroundColor Cyan
        exit 1
    }
}

Write-Host ""

# ============================================================================
# Package Installation
# ============================================================================
Write-Host "📦 Installing U-ITE package..." -ForegroundColor Yellow

# Try to install from current directory
try {
    $process = Start-Process -FilePath "pip" -ArgumentList "install", "." -Wait -PassThru -NoNewWindow
    
    if ($process.ExitCode -eq 0) {
        Write-Host "✅ Package installed successfully" -ForegroundColor Green
    } else {
        throw "pip install failed with exit code $($process.ExitCode)"
    }
}
catch {
    Write-Host "❌ Installation failed" -ForegroundColor Red
    Write-Host "   Error: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "   Troubleshooting tips:" -ForegroundColor Yellow
    Write-Host "   1. Check internet connection" -ForegroundColor Gray
    Write-Host "   2. Update pip: python -m pip install --upgrade pip" -ForegroundColor Gray
    Write-Host "   3. Try installing with: pip install --user ." -ForegroundColor Gray
    exit 1
}

Write-Host ""

# ============================================================================
# Check if uite command is available
# ============================================================================
Write-Host "🔍 Verifying installation..." -ForegroundColor Yellow

try {
    $uite_help = uite --help 2>$null
    if ($uite_help) {
        Write-Host "✅ U-ITE command is available" -ForegroundColor Green
    } else {
        throw "uite command not found"
    }
}
catch {
    Write-Host "⚠️  'uite' command not found in PATH" -ForegroundColor Yellow
    Write-Host "   This is normal if Python Scripts directory isn't in PATH" -ForegroundColor Gray
    Write-Host ""
    Write-Host "   To fix this, add to PATH manually:" -ForegroundColor Cyan
    Write-Host "   1. Find your Python Scripts folder (usually):" -ForegroundColor Gray
    Write-Host "      C:\Users\$env:USERNAME\AppData\Local\Programs\Python\Python3*\Scripts\" -ForegroundColor Gray
    Write-Host "   2. Add it to your System PATH environment variable" -ForegroundColor Gray
    Write-Host "   3. Restart your terminal" -ForegroundColor Gray
}

Write-Host ""

# ============================================================================
# Installation Complete
# ============================================================================
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "✅ U-ITE INSTALLATION COMPLETE!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "🎯 U-ITE is now installed!" -ForegroundColor Green
Write-Host ""

Write-Host "📊 QUICK START COMMANDS:" -ForegroundColor Yellow
Write-Host "  uite --help                 # Show all commands" -ForegroundColor White
Write-Host "  uite daemon start            # Start monitoring (foreground)" -ForegroundColor White
Write-Host "  uite network list            # Show detected networks" -ForegroundColor White
Write-Host "  uite from today to now       # View today's data" -ForegroundColor White
Write-Host ""

Write-Host "🔧 SERVICE MANAGEMENT (Run as Administrator):" -ForegroundColor Yellow
Write-Host "  uite service enable --auto-start  # Install as Windows service" -ForegroundColor White
Write-Host "  uite service status               # Check if running" -ForegroundColor White
Write-Host "  uite service logs                  # View logs" -ForegroundColor White
Write-Host ""

Write-Host "📚 Documentation: https://docs.u-ite.io" -ForegroundColor Cyan
Write-Host "💬 Need help? https://github.com/u-ite/u-ite/issues" -ForegroundColor Cyan
Write-Host ""

# Optional: Offer to add to PATH automatically
if (-not (Get-Command uite -ErrorAction SilentlyContinue)) {
    Write-Host "🔧 Would you like to add U-ITE to your PATH automatically?" -ForegroundColor Yellow
    $choice = Read-Host "   (y/n)"
    
    if ($choice -eq 'y') {
        try {
            # Find Python Scripts directory
            $python_path = (Get-Command python).Source
            $scripts_dir = Join-Path (Split-Path $python_path) "Scripts"
            
            if (Test-Path $scripts_dir) {
                # Add to current session PATH
                $env:Path += ";$scripts_dir"
                
                # Add to user PATH permanently
                [Environment]::SetEnvironmentVariable("Path", $env:Path + ";$scripts_dir", [EnvironmentVariableTarget]::User)
                
                Write-Host "✅ Added $scripts_dir to PATH" -ForegroundColor Green
                Write-Host "   Please restart your terminal for changes to take effect" -ForegroundColor Yellow
            } else {
                Write-Host "❌ Could not find Python Scripts directory" -ForegroundColor Red
            }
        }
        catch {
            Write-Host "❌ Failed to add to PATH: $_" -ForegroundColor Red
        }
    }
}

Write-Host ""
Write-Host "🎉 Enjoy using U-ITE!" -ForegroundColor Green
