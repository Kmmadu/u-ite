#!/usr/bin/env python3
"""
U-ITE Command Line Interface
============================
Main CLI entry point that defines the command structure and orchestrates all
subcommands. Uses Click library for elegant command-line parsing.

This module creates a hierarchical command structure:
    uite <command> [subcommand] [options]

All functionality is organized into logical command groups:
    - from / by-network : Historical data queries
    - network           : Network profile management
    - service           : Background service management
    - graph             : Graph generation
    - daemon            : Foreground monitoring
    - export            : Data export
    - compare           : Network comparison
"""

import sys

# ======================================================================
# Windows Unicode/Emoji Fix for CLI
# This ensures emojis display correctly on Windows consoles
# ======================================================================
if sys.platform == "win32":
    import codecs
    # Force UTF-8 encoding for console output
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer)

import click
from uite import __version__

# Import all command groups from their respective modules
from uite.cli.commands.history import from_command, by_network  # Date-based queries
from uite.cli.commands.network import network                    # Network profile management
from uite.cli.commands.service import service                    # Background service control
from uite.cli.commands.graph import graph                        # Graph generation
from uite.cli.commands.daemon import daemon                      # Foreground daemon control
from uite.cli.commands.export import export                      # Data export utilities
from uite.cli.commands.compare import compare                    # Network comparison


@click.group(invoke_without_command=True)
@click.option('--version', is_flag=True, help='Show version information')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.pass_context
def cli(ctx, version, verbose):
    """
    U-ITE Network Observability Platform
    
    A continuous network monitoring tool that runs in the background,
    collects performance data, and provides rich insights through this CLI.
    
    Features:
    - Automatic network detection and profiling
    - Continuous monitoring every 30 seconds
    - Historical data storage in SQLite
    - Rich querying with natural language dates
    - Graph generation for visual analysis
    - Multi-network comparison
    - Data export to CSV/JSON
    
    Examples:
        uite from today to now                    # Today's data
        uite network list                          # Show networks
        uite graph latency --network "Home" --days 7  # Latency graph
        uite compare "Office" "Home" --days 30     # Compare networks
    """
    # Handle --version flag: show version and exit immediately
    if version:
        click.echo(f"U-ITE version {__version__}")
        ctx.exit()
    
    # If no subcommand provided, show help with additional resources
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())
        click.echo("\n📚 Documentation: https://docs.u-ite.io")
        click.echo("💬 Feedback: https://github.com/u-ite/feedback")
        ctx.exit()
    
    # Note: 'verbose' flag is available for future use
    # Can be used to enable debug logging across all commands
    if verbose:
        # TODO: Implement verbose mode (e.g., set logging level to DEBUG)
        pass


# ============================================================================
# Register all command groups with the main CLI
# Each group becomes a top-level command: uite <group> ...
# ============================================================================

# Historical data queries (from the 'history' module)
cli.add_command(from_command)      # uite from <start> to <end>
cli.add_command(by_network)        # uite by-network <network> [options]

# Network profile management
cli.add_command(network)           # uite network <list|rename|tag|stats|...>

# Service management (background daemon)
cli.add_command(service)           # uite service <install|start|stop|status|...>

# Graph generation
cli.add_command(graph)             # uite graph <latency|loss|health> [options]

# Foreground daemon (for testing/debugging)
cli.add_command(daemon)            # uite daemon <start|status|stop|logs>

# Data export utilities
cli.add_command(export)            # uite export <data|all> [options]

# Network comparison
cli.add_command(compare)           # uite compare <between|multi> [options]


# ============================================================================
# Direct execution (when run as script)
# ============================================================================
if __name__ == "__main__":
    # This allows testing the CLI directly without installation:
    # python src/uite/cli/__init__.py from today to now
    cli()
