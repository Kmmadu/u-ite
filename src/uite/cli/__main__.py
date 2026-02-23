#!/usr/bin/env python3
"""
U-ITE CLI Module Entry Point
============================
This module enables direct execution of the CLI submodule with:
    python -m uite.cli [commands]

This is useful for testing and debugging the CLI independently,
without going through the main package entry point.

Example:
    python -m uite.cli from today to now
    python -m uite.cli network list
    python -m uite.cli --help
"""

# Import the main CLI group from the parent module
# The 'cli' object is the same Click Group defined in __init__.py
from uite.cli import cli

# Standard Python idiom for entry points
# This block only runs when this file is executed directly
if __name__ == "__main__":
    # Execute the CLI with any provided command-line arguments
    # Click automatically handles argument parsing and routing
    cli()
