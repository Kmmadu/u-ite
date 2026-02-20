#!/bin/bash
# U-ITE installer for Linux/macOS

set -e

echo "📦 Installing U-ITE..."

# Check Python version
python_version=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" = "$required_version" ]; then 
    echo "✅ Python $python_version found"
else
    echo "❌ Python 3.8+ required"
    exit 1
fi

# Install via pip
pip3 install --user .

# Add to PATH if needed
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
    echo "✅ Added ~/.local/bin to PATH (restart terminal or run 'source ~/.bashrc')"
fi

echo "✅ U-ITE installed successfully!"
echo ""
echo "Try: uite --help"
