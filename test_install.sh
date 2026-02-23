#!/bin/bash
"""
U-ITE Linux Test Installation Script
======================================
Automated test script to verify U-ITE installation in a clean environment.
This script creates a virtual environment, installs the package, and runs
basic validation tests to ensure everything works correctly.

Features:
- Creates isolated test environment (virtual env)
- Checks Python version compatibility
- Tests all critical imports
- Verifies CLI command availability
- Shows installation details
- Non-destructive (can clean up after)

Use cases:
- CI/CD pipeline testing
- Pre-release validation
- Developer testing
- Quality assurance
"""

# ============================================================================
# Configuration
# ============================================================================
set -e  # Exit on any error

# Color codes for output (if supported)
if [ -t 1 ]; then
    GREEN='\033[0;32m'
    RED='\033[0;31m'
    YELLOW='\033[1;33m'
    NC='\033[0m' # No Color
else
    GREEN=''
    RED=''
    YELLOW=''
    NC=''
fi

# ============================================================================
# Helper Functions
# ============================================================================
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

# ============================================================================
# Test Banner
# ============================================================================
echo "============================================================"
echo "🔍 U-ITE Linux Installation Test Suite"
echo "============================================================"
echo ""

# ============================================================================
# Test 1: Python Version Check
# ============================================================================
echo "📋 Test 1: Python Version Compatibility"
echo "----------------------------------------"

echo -n "Checking Python version... "
python_version=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" = "$required_version" ]; then 
    print_success "Python $python_version (required: $required_version+)"
else
    print_error "Python $required_version+ required (found $python_version)"
    exit 1
fi

echo ""

# ============================================================================
# Test 2: Virtual Environment Creation
# ============================================================================
echo "📋 Test 2: Virtual Environment Setup"
echo "----------------------------------------"

# Create a unique test environment name with timestamp
TEST_ENV="test_venv_$(date +%s)"
echo -n "Creating virtual environment ($TEST_ENV)... "

python3 -m venv "$TEST_ENV"
if [ $? -eq 0 ]; then
    print_success "Virtual environment created"
else
    print_error "Failed to create virtual environment"
    exit 1
fi

# Activate the environment
source "$TEST_ENV/bin/activate"
print_success "Virtual environment activated"

echo ""

# ============================================================================
# Test 3: Package Installation
# ============================================================================
echo "📋 Test 3: Package Installation"
echo "----------------------------------------"

echo "Updating pip..."
pip install --quiet --upgrade pip
print_success "pip updated"

echo "Installing U-ITE in development mode..."
pip install --quiet -e .
if [ $? -eq 0 ]; then
    print_success "Package installed successfully"
else
    print_error "Package installation failed"
    exit 1
fi

# Show installed version
INSTALLED_VERSION=$(pip show u-ite | grep Version | cut -d' ' -f2)
print_info "Installed version: $INSTALLED_VERSION"

echo ""

# ============================================================================
# Test 4: Import Tests
# ============================================================================
echo "📋 Test 4: Module Imports"
echo "----------------------------------------"

# List of critical modules to test
MODULES=(
    "uite.cli"
    "uite.daemon.orchestrator"
    "uite.storage.db"
    "uite.storage.db.HistoricalData"
    "uite.core.platform"
    "uite.core.platform.OS"
    "uite.core.device"
    "uite.core.fingerprint"
    "uite.core.network_profile"
    "uite.tracking.event_detector"
    "uite.tracking.event_factory"
)

FAILED_IMPORTS=0
for module in "${MODULES[@]}"; do
    echo -n "   Testing $module... "
    if python -c "import $module" 2>/dev/null; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗${NC}"
        FAILED_IMPORTS=$((FAILED_IMPORTS + 1))
    fi
done

if [ $FAILED_IMPORTS -eq 0 ]; then
    print_success "All imports successful"
else
    print_error "$FAILED_IMPORTS import(s) failed"
    exit 1
fi

echo ""

# ============================================================================
# Test 5: CLI Command Availability
# ============================================================================
echo "📋 Test 5: CLI Commands"
echo "----------------------------------------"

# Check if uite command is available
echo -n "Checking 'uite' command... "
if command -v uite &> /dev/null; then
    print_success "uite command found at $(which uite)"
else
    print_error "uite command not found in PATH"
    exit 1
fi

# Test help command
echo -n "Testing 'uite --help'... "
if uite --help &> /dev/null; then
    print_success "Help command works"
else
    print_error "Help command failed"
    exit 1
fi

# List available commands
echo ""
echo "Available commands:"
uite --help | grep -E "^\s{2}[a-z-]+" | sed 's/^/  /'

echo ""

# ============================================================================
# Test 6: Basic Functionality (Optional)
# ============================================================================
echo "📋 Test 6: Basic Functionality (Optional)"
echo "----------------------------------------"
echo "Note: These tests require network connectivity"
echo ""

# Test network list (should work even with no networks)
echo -n "Testing 'uite network list'... "
if uite network list &> /dev/null; then
    print_success "Network list command works"
else
    print_info "Network list command failed (may be normal with no networks)"
fi

# Test from command with dates
echo -n "Testing 'uite from yesterday to today'... "
if uite from yesterday to today &> /dev/null; then
    print_success "Date query works"
else
    print_info "Date query failed (may be normal with no data)"
fi

echo ""

# ============================================================================
# Test Summary
# ============================================================================
echo "============================================================"
echo "📊 Test Summary"
echo "============================================================"
echo "✅ Python version:      $python_version"
echo "✅ Virtual env:         $TEST_ENV"
echo "✅ Package version:     $INSTALLED_VERSION"
echo "✅ Imports tested:      ${#MODULES[@]}"
echo "✅ CLI command:         $(which uite)"
echo ""

if [ $FAILED_IMPORTS -eq 0 ]; then
    print_success "All tests passed!"
else
    print_error "$FAILED_IMPORTS test(s) failed"
    exit 1
fi

echo ""

# ============================================================================
# Cleanup Prompt
# ============================================================================
echo "============================================================"
echo "🧹 Cleanup"
echo "============================================================"
echo "Test virtual environment: $TEST_ENV"
echo ""
echo "Options:"
echo "  1) Keep environment for debugging"
echo "  2) Delete environment and exit"
echo ""
read -p "Choose (1/2): " -n 1 -r CLEANUP_CHOICE
echo ""

case $CLEANUP_CHOICE in
    2)
        echo "Cleaning up..."
        deactivate 2>/dev/null || true
        rm -rf "$TEST_ENV"
        print_success "Test environment removed"
        ;;
    *)
        print_info "Keeping test environment: $TEST_ENV"
        print_info "To activate later: source $TEST_ENV/bin/activate"
        print_info "To clean up: deactivate && rm -rf $TEST_ENV"
        ;;
esac

echo ""
echo "============================================================"
echo "✅ Test execution complete!"
echo "============================================================"
