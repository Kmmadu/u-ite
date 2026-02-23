#!/usr/bin/env python3
"""
U-ITE Main Entry Point
======================
This module serves as the entry point when the package is run directly with:
    python -m uite

It delegates all functionality to the CLI module, which handles command parsing
and execution. This separation allows the CLI to be imported and used elsewhere
while maintaining a clean entry point.
"""

# Import the main CLI group from the cli module
# The 'cli' object is a Click Group that contains all registered commands
from uite.cli import cli

# This block only executes when the script is run directly, not when imported
# This is the standard Python idiom for entry points
if __name__ == "__main__":
    # Execute the CLI with any command-line arguments
    # Click automatically parses sys.argv and routes to the appropriate command
    cli()
