"""
Export Commands for U-ITE
=========================
Provides functionality to export network performance data in various formats.
Users can export data for specific networks or all networks at once.

Features:
- Export to CSV, JSON, or table format
- Filter by time period (--days)
- Export single network or all networks
- Smart network resolution by name, ID, or tag
- Preview data in table format before exporting
"""

import click
import csv
import json
from datetime import datetime, timedelta
from pathlib import Path
from uite.storage.db import HistoricalData
from uite.core.network_profile import NetworkProfileManager


@click.group()
def export():
    """
    Export network performance data to various formats.
    
    This command group allows you to export historical data for analysis
    in external tools like Excel, Python, or data visualization platforms.
    
    Formats supported:
    - CSV: For spreadsheets and data analysis
    - JSON: For programmatic use and APIs
    - Table: For quick preview in terminal
    
    Examples:
        uite export data --network "Home" --days 30 --format csv --output home.csv
        uite export data --network office --format json --days 7
        uite export all --days 14 --format csv --output exports/
    """
    pass


def _resolve_network(network_identifier):
    """
    Resolve a network identifier to a network ID and profile.
    
    This helper function tries multiple strategies to find a network:
    1. Exact match by full ID
    2. Partial match by short ID (first 8 chars)
    3. Case-insensitive partial name match
    4. Tag match
    
    Args:
        network_identifier (str): Network name, ID, or tag to look up
        
    Returns:
        tuple: (network_id, profile) or (None, None) if not found
    """
    manager = NetworkProfileManager()
    
    # Strategy 1: Exact match by full ID
    if network_identifier in manager.profiles:
        return network_identifier, manager.profiles[network_identifier]
    
    # Strategy 2: Partial match by short ID (first 8 characters)
    for pid, profile in manager.profiles.items():
        if pid.startswith(network_identifier):
            return pid, profile
    
    # Strategy 3: Case-insensitive partial name match
    network_lower = network_identifier.lower()
    for pid, profile in manager.profiles.items():
        if network_lower in profile.name.lower():
            return pid, profile
    
    # Strategy 4: Match by tag
    for pid, profile in manager.profiles.items():
        if profile.tags and network_lower in [t.lower() for t in profile.tags]:
            return pid, profile
    
    # No match found
    return None, None


@export.command()
@click.option('--network', required=True, help='Network name, ID, or tag')
@click.option('--days', default=7, help='Number of days to export')
@click.option('--format', 
              type=click.Choice(['csv', 'json', 'table']), 
              default='table',
              help='Output format (default: table)')
@click.option('--output', help='Output file path (optional)')
def data(network, days, format, output):
    """
    Export data for a specific network.
    
    Exports diagnostic runs for a single network in the requested format.
    If no output file is specified, prints to stdout (useful for piping).
    
    Args:
        network: Network name, ID, or tag
        days: Number of days of data to export
        format: Output format (csv, json, or table)
        output: Optional file path to save the export
    
    Examples:
        uite export data --network "Home" --days 30 --format csv --output home.csv
        uite export data --network office --format json --days 7
        uite export data --network primary --format table --days 1
    """
    
    # Resolve the network identifier to an actual network ID
    network_id, profile = _resolve_network(network)
    
    if not network_id:
        click.echo(f"❌ Network '{network}' not found")
        # Show available networks to help the user
        click.echo("\nAvailable networks:")
        manager = NetworkProfileManager()
        for pid, p in manager.profiles.items():
            if pid != "offline-state":
                click.echo(f"  • {p.name} (ID: {pid[:8]})")
        return
    
    # Fetch the data
    click.echo(f"📊 Exporting data for: {profile.name}")
    runs = HistoricalData.get_runs_for_last_days(network_id, days)
    
    if not runs:
        click.echo(f"❌ No data found for the last {days} days")
        return
    
    click.echo(f"   Found {len(runs)} data points")
    
    # Prepare data for export by normalizing the structure
    export_data = []
    for r in runs:
        export_data.append({
            'timestamp': r['timestamp'],
            'verdict': r['verdict'],
            'latency_ms': r.get('latency', 'N/A'),
            'packet_loss_pct': r.get('loss', 'N/A'),
            'network_id': r['network_id']
        })
    
    # ======================================================================
    # Format-specific export handlers
    # ======================================================================
    
    if format == 'json':
        # JSON export - pretty printed with indentation
        output_data = json.dumps(export_data, indent=2)
        if output:
            with open(output, 'w') as f:
                f.write(output_data)
            click.echo(f"✅ Exported to {output}")
        else:
            click.echo(output_data)
    
    elif format == 'csv':
        # CSV export - comma-separated values with headers
        if output:
            with open(output, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=export_data[0].keys())
                writer.writeheader()
                writer.writerows(export_data)
            click.echo(f"✅ Exported to {output}")
        else:
            # Print to stdout if no output file specified
            import io
            output_data = io.StringIO()
            writer = csv.DictWriter(output_data, fieldnames=export_data[0].keys())
            writer.writeheader()
            writer.writerows(export_data)
            click.echo(output_data.getvalue())
    
    elif format == 'table':
        # Table format - nice terminal display using tabulate
        from tabulate import tabulate
        
        # Show only last 20 records for table view to avoid overwhelming the terminal
        table_data = []
        for r in export_data[-20:]:
            table_data.append([
                r['timestamp'][11:19],  # Extract time portion only (HH:MM:SS)
                r['verdict'][:30],       # Truncate long verdicts
                f"{r['latency_ms']}ms" if r['latency_ms'] != 'N/A' else 'N/A',
                f"{r['packet_loss_pct']}%" if r['packet_loss_pct'] != 'N/A' else 'N/A'
            ])
        
        click.echo(tabulate(
            table_data,
            headers=['Time', 'Verdict', 'Latency', 'Loss'],
            tablefmt='grid'
        ))
        
        # Indicate if there are more records not shown
        if len(export_data) > 20:
            click.echo(f"\n   (Showing last 20 of {len(export_data)} records)")


@export.command()
@click.option('--days', default=7, help='Number of days to export')
@click.option('--format', 
              type=click.Choice(['csv', 'json']), 
              default='json',
              help='Output format (csv or json)')
@click.option('--output', help='Output directory (creates files per network)')
def all(days, format, output):
    """
    Export data for all networks.
    
    Creates separate export files for each network in the specified directory.
    Each file is named after the network (spaces replaced with underscores).
    
    Args:
        days: Number of days of data to export
        format: Output format (csv or json - table not supported for multi-export)
        output: Directory path to save the files
    
    Examples:
        uite export all --days 30 --format csv --output exports/
        uite export all --days 7 --format json --output network_data/
    """
    manager = NetworkProfileManager()
    
    # Generate default output directory name if not specified
    if not output:
        output = f"uite_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    output_path = Path(output)
    
    # Check if output path has an extension - if so, it's a file, not a directory
    if not output_path.suffix:  # No extension means it's a directory
        # Create the output directory
        output_path.mkdir(exist_ok=True)
        
        # Export each network
        exported_count = 0
        for pid, profile in manager.profiles.items():
            # Skip offline state in exports
            if pid == "offline-state":
                continue
            
            # Check if this network has any data
            runs = HistoricalData.get_runs_for_last_days(pid, days)
            if runs:
                # Generate filename: network_name.format (spaces replaced with underscores)
                filename = output_path / f"{profile.name.replace(' ', '_')}.{format}"
                click.echo(f"📊 Exporting {profile.name}...")
                
                # Reuse the data command logic by invoking it programmatically
                ctx = click.get_current_context()
                ctx.invoke(data, network=pid, days=days, format=format, output=str(filename))
                exported_count += 1
        
        click.echo(f"\n✅ Exported {exported_count} networks to {output_path.absolute()}")
        
    else:
        # User provided a file path, but --all requires a directory
        click.echo("❌ For --all, please provide a directory path (not a file)")
        click.echo("   Example: uite export all --days 7 --format csv --output exports/")


# Export the command group for registration in main CLI
__all__ = ['export']
