#!/bin/bash
# Test installation script for U-ITE on Linux

echo "======================================"
echo "🔍 Testing U-ITE Linux Installation"
echo "======================================"

# Check Python version
echo -n "Checking Python version... "
python_version=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" = "$required_version" ]; then 
    echo "✅ Python $python_version"
else
    echo "❌ Python 3.8+ required (found $python_version)"
    exit 1
fi

# Create a virtual environment for testing
echo -n "Creating test virtual environment... "
python3 -m venv test_venv
source test_venv/bin/activate
echo "✅"

# Install the package
echo "Installing U-ITE package..."
pip install --upgrade pip
pip install -e .

# Test imports
echo -n "Testing imports... "
python -c "
from uite.cli import cli
from uite.daemon import orchestrator
from uite.storage.db import HistoricalData
from uite.core.platform import OS
print('✅')
"

# Test CLI command
echo -n "Testing CLI help... "
uite --help > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅"
else
    echo "❌"
fi

# Show installation info
echo ""
echo "======================================"
echo "📦 Installation Test Results"
echo "======================================"
echo "Package: uite"
echo "Location: $(which uite)"
echo "Version: $(pip show u-ite | grep Version)"
echo ""
echo "Available commands:"
uite --help | grep -A 20 "Commands:"

# Clean up
echo ""
echo "======================================"
echo "🧹 Clean up test environment?"
echo "======================================"
echo "Test virtual environment is at: test_venv"
echo "To clean up, run: deactivate && rm -rf test_venv"
echo ""
echo "✅ Test complete!"
