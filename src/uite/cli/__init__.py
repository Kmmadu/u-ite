#!/usr/bin/env python3
"""U-ITE CLI interface"""
import click
from uite.cli.commands.history import from_command

@click.group()
def cli():
    """U-ITE Network Observability Platform"""
    pass

# Register commands
cli.add_command(from_command)

if __name__ == "__main__":
    cli()
