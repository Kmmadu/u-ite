#!/usr/bin/env python3
"""U-ITE CLI interface"""
import click
from uite.cli.commands.history import from_command, by_network
from uite.cli.commands.network import network
from uite.cli.commands.service import service
from uite.cli.commands.graph import graph  # Add this line

@click.group()
def cli():
    """U-ITE Network Observability Platform"""
    pass

# Register commands
cli.add_command(from_command)
cli.add_command(by_network)
cli.add_command(network)
cli.add_command(service)
cli.add_command(graph)  # Add this line

if __name__ == "__main__":
    cli()