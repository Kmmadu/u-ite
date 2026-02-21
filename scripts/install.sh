#!/bin/bash
# One-command installer for U-ITE

set -e

echo "========================================"
echo "🚀 U-ITE Network Observer Installer"
echo "========================================"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found"
    exit 1
fi

# Install via pip
echo "📦 Installing U-ITE..."
pip3 install --user u-ite

# Add to PATH if needed
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
    echo "✅ Added ~/.local/bin to PATH"
fi

# Enable auto-start
echo "⚙️  Enabling background service..."
uite service enable --auto-start

echo ""
echo "✅ U-ITE installed successfully!"
echo ""
echo "📊 Commands you can run:"
echo "  uite network list              # Show networks"
echo "  uite network rename <ID> <name> # Name your network"
echo "  uite from today to now          # Today's stats"
echo "  uite service status             # Check if running"
echo "  uite service logs                # View logs"
echo ""
echo "🔍 First, name your network:"
echo "  uite network list  # Copy the ID"
echo "  uite network rename <ID> \"Home WiFi\""
