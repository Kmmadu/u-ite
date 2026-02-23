#!/bin/bash
"""
U-ITE Linux/macOS Installation Script
=======================================
A streamlined installer for Linux and macOS systems. This script handles
the basic installation process without the auto-start service configuration.

This is a simpler alternative to the full installer, useful for:
- Development environments
- Users who want manual control over the service
- Systems where auto-start isn't desired
- Testing and debugging

Features:
- Python version check (3.8+ required)
- pip installation in user mode (no sudo)
- Optional PATH configuration
- Clean, minimal output
"""

# Exit on any error - prevents partial installations
set -e

# ============================================================================
# Welcome Banner
# ============================================================================
echo "📦 Installing U-ITE..."
echo ""

# ============================================================================
# Python Version Check
# ============================================================================
echo "🔍 Checking Python version..."

# Get current Python version
python_version=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
required_version="3.8"

# Compare versions using sort -V (version sort)
if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" = "$required_version" ]; then 
    echo "✅ Python $python_version found (required: $required_version+)"
else
    echo "❌ Python $required_version+ required (found: $python_version)"
    echo "   Please upgrade Python and try again"
    exit 1
fi

echo ""

# ============================================================================
# Package Installation
# ============================================================================
echo "📦 Installing U-ITE package..."

# Install in development/editable mode from current directory
# This is useful for developers testing local changes
pip3 install --user .

if [ $? -eq 0 ]; then
    echo "✅ Package installed successfully to ~/.local"
else
    echo "❌ Installation failed"
    echo "   Please check:"
    echo "   - Internet connection"
    echo "   - pip is up to date (pip3 install --upgrade pip)"
    echo "   - You have write permission to ~/.local"
    exit 1
fi

echo ""

# ============================================================================
# PATH Configuration
# ============================================================================
echo "🔧 Checking PATH configuration..."

# Check if ~/.local/bin is already in PATH
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo "   ⚠️  ~/.local/bin not found in PATH"
    echo "   Adding to ~/.bashrc..."
    
    # Add to bashrc for future sessions
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
    
    # Also update current session PATH
    export PATH="$HOME/.local/bin:$PATH"
    
    echo "✅ Added ~/.local/bin to PATH"
    echo "   Note: You may need to restart your terminal or run:"
    echo "   source ~/.bashrc"
else
    echo "✅ ~/.local/bin already in PATH"
fi

echo ""

# ============================================================================
# Installation Complete
# ============================================================================
echo "========================================"
echo "✅ U-ITE INSTALLATION COMPLETE!"
echo "========================================"
echo ""

# Check if uite command is now available
if command -v uite &> /dev/null; then
    echo "🎯 U-ITE is ready to use!"
    echo ""
    echo "📊 Quick start:"
    echo "  uite --help                 # Show all commands"
    echo "  uite daemon start            # Start monitoring (foreground)"
    echo "  uite network list            # Show detected networks"
    echo "  uite from today to now       # View today's data"
    echo ""
    echo "🔧 For background service:"
    echo "  uite service enable --auto-start  # Install as service"
    echo "  uite service status               # Check if running"
    echo "  uite service logs                  # View logs"
else
    echo "⚠️  'uite' command not found in PATH"
    echo "   You may need to:"
    echo "   1. Restart your terminal"
    echo "   2. Or run: source ~/.bashrc"
    echo "   3. Then try: uite --help"
fi

echo ""
echo "📚 Documentation: https://docs.u-ite.io"
echo "💬 Need help? https://github.com/u-ite/u-ite/issues"
echo ""
