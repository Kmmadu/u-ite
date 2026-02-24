"""
U-ITE (U - Internet Truth Engine) Network Observability Platform
================================================================
A continuous network monitoring and diagnostics tool that runs in the background,
collects network performance data, and provides insights through a CLI interface.

This package provides:
- Continuous network monitoring every 30 seconds
- Automatic network detection and profiling
- Historical data storage in SQLite
- Rich CLI for querying and visualizing data
- Cross-platform support (Linux, macOS, Windows)

Package metadata and version information.
"""

# Package version following Semantic Versioning (SemVer)
# Format: MAJOR.MINOR.PATCH
# - MAJOR: Incompatible API changes
# - MINOR: New functionality in backwards compatible manner
# - PATCH: Backwards compatible bug fixes
__version__ = "0.2.1"

# Package authorship information
__author__ = "Your Name"  # Replace with your name/organization
__license__ = "MIT"        # Open source license for the project

# Optional: Add more metadata as needed
__email__ = "your.email@example.com"  # Contact email
__status__ = "Development"  # "Development", "Production", or "Beta"

# The following would be used if you want to expose specific modules
# when users do `from uite import *`
__all__ = [
    # List public modules/classes here if needed
]
