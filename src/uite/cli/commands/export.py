
"""Export commands for U-ITE"""
import click
import csv
import json
from datetime import datetime, timedelta
from pathlib import Path
from uite.storage.db import HistoricalData
from uite.core.network_profile import NetworkProfileManager

@click.group()
def export():
    """Export historical data"""
    pass

def _resolve_network(network_identifier):
    """Helper to resolve network ID from name/tag/ID"""
    manager = NetworkProfileManager()
    
    # Try exact match first
    if network_identifier in manager.profiles:
        return network_identifier, manager.profiles[network_identifier]
    
    # Try by short ID
    for pid, profile in manager.profiles.items():
        if pid.startswith(network_identifier):
            return pid, profile
    
    # Try by name (case-insensitive)
    network_lower = network_identifier.lower()
    for pid, profile in manager.profiles.items():
        if network_lower in profile.name.lower():
            return pid, profile
    
    # Try by tag
    for pid, profile in manager.profiles.items():
        if profile.tags and network_lower in [t.lower() for t in profile.tags]:
            return pid, profile
    
    return None, None

@export.command()
@click.option('--network', required=True, help='Network name, ID, or tag')
@click.option('--days', default=7, help='Number of days to export')
@click.option('--format', type=click.Choice(['csv', 'json', 'table']), default='table')
@click.option('--output', help='Output file path (optional)')
def data(network, days, format, output):
    """Export network data to CSV, JSON, or table format"""
    
    # Resolve network
    network_id, profile = _resolve_network(network)
    
    if not network_id:
        click.echo(f"❌ Network '{network}' not found")
        click.echo("\nAvailable networks:")
        manager = NetworkProfileManager()
        for pid, p in manager.profiles.items():
            if pid != "offline-state":
                click.echo(f"  • {p.name} (ID: {pid[:8]})")
        return
    
    # Get data
    click.echo(f"📊 Exporting data for: {profile.name}")
    runs = HistoricalData.get_runs_for_last_days(network_id, days)
    
    if not runs:
        click.echo(f"❌ No data found for the last {days} days")
        return
    
    click.echo(f"   Found {len(runs)} data points")
    
    # Prepare data for export
    export_data = []
    for r in runs:
        export_data.append({
            'timestamp': r['timestamp'],
            'verdict': r['verdict'],
            'latency_ms': r.get('latency', 'N/A'),
            'packet_loss_pct': r.get('loss', 'N/A'),
            'network_id': r['network_id']
        })
    
    # Export based on format
    if format == 'json':
        output_data = json.dumps(export_data, indent=2)
        if output:
            with open(output, 'w') as f:
                f.write(output_data)
            click.echo(f"✅ Exported to {output}")
        else:
            click.echo(output_data)
    
    elif format == 'csv':
        if output:
            with open(output, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=export_data[0].keys())
                writer.writeheader()
                writer.writerows(export_data)
            click.echo(f"✅ Exported to {output}")
        else:
            import io
            output_data = io.StringIO()
            writer = csv.DictWriter(output_data, fieldnames=export_data[0].keys())
            writer.writeheader()
            writer.writerows(export_data)
            click.echo(output_data.getvalue())
    
    elif format == 'table':
        from tabulate import tabulate
        table_data = []
        for r in export_data[-20:]:  # Show last 20 for table
            table_data.append([
                r['timestamp'][11:19],  # Time only
                r['verdict'][:30],
                f"{r['latency_ms']}ms" if r['latency_ms'] != 'N/A' else 'N/A',
                f"{r['packet_loss_pct']}%" if r['packet_loss_pct'] != 'N/A' else 'N/A'
            ])
        
        click.echo(tabulate(
            table_data,
            headers=['Time', 'Verdict', 'Latency', 'Loss'],
            tablefmt='grid'
        ))
        if len(export_data) > 20:
            click.echo(f"\n   (Showing last 20 of {len(export_data)} records)")

@export.command()
@click.option('--days', default=7, help='Number of days to export')
@click.option('--format', type=click.Choice(['csv', 'json']), default='json')
@click.option('--output', help='Output directory (creates files per network)')
def all(days, format, output):
    """Export data for all networks"""
    manager = NetworkProfileManager()
    
    if not output:
        output = f"uite_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    output_path = Path(output)
    if not output_path.suffix:  # If no extension, treat as directory
        output_path.mkdir(exist_ok=True)
        
        for pid, profile in manager.profiles.items():
            if pid == "offline-state":
                continue
            
            runs = HistoricalData.get_runs_for_last_days(pid, days)
            if runs:
                filename = output_path / f"{profile.name.replace(' ', '_')}.{format}"
                click.echo(f"📊 Exporting {profile.name}...")
                
                # Reuse the data command logic
                ctx = click.get_current_context()
                ctx.invoke(data, network=pid, days=days, format=format, output=str(filename))
    else:
        click.echo("❌ For --all, please provide a directory path (not a file)")

__all__ = ['export']
