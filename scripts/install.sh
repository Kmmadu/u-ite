#!/bin/bash
"""
U-ITE One-Command Installer
=============================
A simple, user-friendly installer script that handles the entire installation
process for U-ITE. This script is designed to be run by end users with a
single command.

Features:
- Automatic Python version check
- pip installation with --user flag (no sudo required)
- PATH configuration for user binaries
- Automatic service enablement with auto-start
- User-friendly output with clear instructions

Usage:
    curl -sSL https://raw.githubusercontent.com/u-ite/installer/main/install.sh | bash
    # or
    wget -qO- https://raw.githubusercontent.com/u-ite/installer/main/install.sh | bash
"""

# Exit on any error - prevents partial installations
set -e

# ============================================================================
# Welcome Banner
# ============================================================================
echo "========================================"
echo "🚀 U-ITE Network Observer Installer"
echo "========================================"
echo ""

# ============================================================================
# Python Version Check
# ============================================================================
echo "🔍 Checking system requirements..."

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found"
    echo "   Please install Python 3.8 or later from:"
    echo "   https://www.python.org/downloads/"
    exit 1
fi

# Check Python version (optional but recommended)
python_version=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" = "$required_version" ]; then 
    echo "✅ Python $python_version found"
else
    echo "⚠️  Python $python_version detected, but version $required_version+ is recommended"
    echo "   Continuing anyway, but you may encounter issues..."
fi

echo ""

# ============================================================================
# Package Installation
# ============================================================================
echo "📦 Installing U-ITE package..."

# Install with --user flag to avoid sudo requirements
# This installs to ~/.local/lib/python*/site-packages/
pip3 install --user u-ite

if [ $? -eq 0 ]; then
    echo "✅ Package installed successfully"
else
    echo "❌ Installation failed"
    echo "   Please check your internet connection and try again"
    exit 1
fi

echo ""

# ============================================================================
# PATH Configuration
# ============================================================================
echo "🔧 Configuring system PATH..."

# Check if ~/.local/bin is already in PATH
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo "   Adding ~/.local/bin to PATH..."
    
    # Detect which shell config file to use
    if [ -n "$BASH_VERSION" ]; then
        # Bash shell
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
        echo "✅ Added to ~/.bashrc"
    elif [ -n "$ZSH_VERSION" ]; then
        # Zsh shell
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
        echo "✅ Added to ~/.zshrc"
    else
        # Unknown shell - provide instructions
        echo "⚠️  Could not detect shell configuration file"
        echo "   Please add the following line to your shell config:"
        echo '   export PATH="$HOME/.local/bin:$PATH"'
    fi
    
    # Also update current session PATH for immediate use
    export PATH="$HOME/.local/bin:$PATH"
else
    echo "✅ ~/.local/bin already in PATH"
fi

echo ""

# ============================================================================
# Service Configuration
# ============================================================================
echo "⚙️  Configuring background service..."

# Check if uite command is now available
if ! command -v uite &> /dev/null; then
    echo "⚠️  'uite' command not found in PATH"
    echo "   You may need to restart your terminal or run:"
    echo "   source ~/.bashrc (or ~/.zshrc)"
    echo ""
    echo "   After that, run: uite service enable --auto-start"
else
    # Enable auto-start service
    echo "   Enabling auto-start on boot..."
    uite service enable --auto-start
    
    if [ $? -eq 0 ]; then
        echo "✅ Service enabled and started"
    else
        echo "⚠️  Service configuration failed"
        echo "   You can manually configure it later with:"
        echo "   uite service enable --auto-start"
    fi
fi

echo ""

# ============================================================================
# Installation Complete - Show Next Steps
# ============================================================================
echo "========================================"
echo "✅ U-ITE INSTALLATION COMPLETE!"
echo "========================================"
echo ""
echo "📊 COMMANDS YOU CAN RUN:"
echo "  uite network list              # Show all detected networks"
echo "  uite network rename <ID> <name> # Give your network a friendly name"
echo "  uite from today to now          # View today's statistics"
echo "  uite service status             # Check if background service is running"
echo "  uite service logs               # View service logs"
echo "  uite graph health --network <name> --days 7  # Generate health graph"
echo ""
echo "🔍 FIRST STEPS:"
echo "  1. Name your network:"
echo "     uite network list"
echo "     uite network rename <ID> \"Home WiFi\""
echo ""
echo "  2. Add tags (optional):"
echo "     uite network tag <ID> primary"
echo "     uite network tag <ID> home"
echo ""
echo "  3. Set your ISP (optional):"
echo "     uite network provider <ID> \"Comcast\""
echo ""
echo "📚 DOCUMENTATION:"
echo "  https://docs.u-ite.io"
echo ""
echo "💬 NEED HELP?"
echo "  GitHub: https://github.com/u-ite/u-ite"
echo "  Issues: https://github.com/u-ite/u-ite/issues"
echo ""
echo "========================================"
echo ""

# ============================================================================
# Optional: Run a quick test
# ============================================================================
if command -v uite &> /dev/null; then
    echo "🔍 Running quick test..."
    echo "   uite network list"
    uite network list 2>/dev/null || echo "   (No networks detected yet - run the service first)"
fi

echo ""
echo "🎉 Enjoy using U-ITE!"
