#!/usr/bin/env python3
"""U-ITE CLI interface"""
import click
from uite.cli.commands.history import from_command, by_network
from uite.cli.commands.network import network
from uite.cli.commands.service import service
from uite.cli.commands.graph import graph
from uite.cli.commands.daemon import daemon      # Add this
from uite.cli.commands.export import export      # Add this
from uite.cli.commands.compare import compare    # Add this
from uite import __version__

@click.group(invoke_without_command=True)
@click.option('--version', is_flag=True, help='Show version information')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.pass_context
def cli(ctx, version, verbose):
    """U-ITE Network Observability Platform
    
    Continuous network monitoring and diagnostics tool.
    Runs in background, stores historical data, provides insights.
    """
    if version:
        click.echo(f"U-ITE version {__version__}")
        ctx.exit()
    
    if ctx.invoked_subcommand is None:
        # Show custom help
        click.echo(ctx.get_help())
        click.echo("\n📚 Documentation: https://docs.u-ite.io")
        click.echo("💬 Feedback: https://github.com/u-ite/feedback")
        ctx.exit()

# Register all command groups
cli.add_command(from_command)
cli.add_command(by_network)
cli.add_command(network)
cli.add_command(service)
cli.add_command(graph)
cli.add_command(daemon)      # Add this
cli.add_command(export)      # Add this
cli.add_command(compare)     # Add this

if __name__ == "__main__":
    cli()
