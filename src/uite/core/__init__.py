"""
Core Package Initialization for U-ITE
=======================================
Makes core modules easily importable from the uite.core package.

This __init__.py file serves as a convenience layer, exposing commonly used
functions from core submodules at the package level. This allows other parts
of the application to import them directly from uite.core rather than from
specific submodules.

Current exports:
- format_duration: Human-readable duration formatting from .formatters

Benefits:
- Shorter import paths
- Centralized control over the public API
- Internal modules can be reorganized without breaking external imports
- Clear documentation of what's available from the core package
"""

# Import commonly used functions to make them available at package level
from .formatters import format_duration

# Define what should be imported with "from uite.core import *"
__all__ = [
    'format_duration',
    # Add other core exports here as they are created
    # 'get_device_id',
    # 'collect_fingerprint',
    # 'generate_network_id',
]

# Optional: Add package-level docstring
__doc__ = """
U-ITE Core Package - Fundamental utilities and helpers.

This package contains core functionality used throughout U-ITE:
- formatters: Human-readable formatting utilities
- device: Device ID management
- fingerprint: Network fingerprinting
- platform: OS detection and abstraction
- network_profile: Network profile management
"""
