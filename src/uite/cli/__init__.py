#!/usr/bin/env python3
"""U-ITE CLI interface"""
import click
from uite.cli.commands.history import from_command, by_network
from uite.cli.commands.network import network

@click.group()
def cli():
    """U-ITE Network Observability Platform"""
    pass

# Register commands
cli.add_command(from_command)
cli.add_command(by_network)
cli.add_command(network)  # Add the network command group

if __name__ == "__main__":
    cli()
