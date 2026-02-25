#!/usr/bin/env python3
"""
U-ITE Command Line Interface
============================
Main CLI entry point that defines the command structure.
"""

import sys
import click
from uite import __version__

# Import all command groups
from uite.cli.commands.history import from_command, by_network
from uite.cli.commands.network import network
from uite.cli.commands.service import service
from uite.cli.commands.daemon import daemon
from uite.cli.commands.export import export
from uite.cli.commands.graph_new import graph
from uite.cli.commands.compare import compare


@click.group(invoke_without_command=True)
@click.option('--version', is_flag=True, help='Show version information')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.pass_context
def cli(ctx, version, verbose):
    """U-ITE Network Observability Platform
    
    A continuous network monitoring tool that runs in the background,
    collects performance data, and provides rich insights through this CLI.
    
    Features:
    - Automatic network detection and profiling
    - Continuous monitoring every 30 seconds
    - Historical data storage in SQLite
    - Rich querying with natural language dates
    - Advanced graph generation with trend analysis
    - Multi-network comparison
    - Data export to CSV/JSON
    
    Examples:
        uite from today to now                    # Today's data
        uite network list                          # Show networks
        uite graph latency --network "Home" --days 7  # Latency graph
        uite graph trend --network "Home" --pattern    # Daily patterns
        uite compare "Office" "Home" --days 30     # Compare networks
    """
    if version:
        click.echo(f"U-ITE version {__version__}")
        ctx.exit()
    
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())
        click.echo("\n📚 Documentation: https://docs.u-ite.io")
        click.echo("💬 Feedback: https://github.com/u-ite/feedback")
        ctx.exit()


# Register all command groups
cli.add_command(from_command)
cli.add_command(by_network)
cli.add_command(network)
cli.add_command(service)
cli.add_command(daemon)
cli.add_command(export)
cli.add_command(graph)
cli.add_command(compare)


if __name__ == "__main__":
    cli()
