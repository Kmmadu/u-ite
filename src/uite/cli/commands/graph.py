"""Graph generation commands for U-ITE"""
import click
from datetime import datetime, timedelta
import tempfile
import subprocess
import webbrowser
from uite.storage.db import HistoricalData

@click.group()
def graph():
    """Generate graphs from historical data"""
    pass

@graph.command()
@click.option('--days', default=7, help='Number of days to show')
@click.option('--network', help='Filter by network ID or name')
def latency(days, network):
    """Show latency graph"""
    _generate_graph('latency', days, network)

@graph.command()
@click.option('--days', default=7, help='Number of days to show')
@click.option('--network', help='Filter by network ID or name')
def health(days, network):
    """Show health/uptime graph"""
    _generate_graph('health', days, network)

@graph.command()
@click.option('--days', default=7, help='Number of days to show')
@click.option('--network', help='Filter by network ID or name')
def loss(days, network):
    """Show packet loss graph"""
    _generate_graph('loss', days, network)

def _generate_graph(graph_type, days, network):
    """Generate and display a graph"""
    try:
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
        import matplotlib
        matplotlib.use('Agg')  # Non-interactive backend
        import numpy as np
    except ImportError as e:
        click.echo(f"❌ Missing dependency: {e}")
        click.echo("   Please install: pip install matplotlib numpy")
        return
    
    # Resolve network ID if name was provided
    network_id = None
    if network:
        from uite.core.network_profile import NetworkProfileManager
        manager = NetworkProfileManager()
        for pid, profile in manager.profiles.items():
            if network in profile.name or network == pid or (profile.tags and network in profile.tags):
                network_id = pid
                click.echo(f"📡 Using network: {profile.name}")
                break
    
    # Get data
    end = datetime.now()
    start = end - timedelta(days=days)
    
    runs = HistoricalData.get_runs_by_date_range(
        start.strftime("%d-%m-%Y"), "00:00",
        end.strftime("%d-%m-%Y"), "23:59",
        network_id=network_id
    )
    
    if not runs:
        click.echo("❌ No data found for this period")
        return
    
    click.echo(f"📊 Generating {graph_type} graph from {len(runs)} data points...")
    
    # Prepare data - filter out entries with missing values
    valid_data = []
    for r in runs:
        try:
            # Parse timestamp
            dt = datetime.fromisoformat(r['timestamp'].replace('Z', '+00:00'))
            
            # Check if we have the required data based on graph type
            if graph_type == 'latency' and r.get('latency') is not None:
                valid_data.append((dt, r['latency'], None))
            elif graph_type == 'loss' and r.get('loss') is not None:
                valid_data.append((dt, None, r['loss']))
            elif graph_type == 'health' and r.get('latency') is not None and r.get('loss') is not None:
                valid_data.append((dt, r['latency'], r['loss']))
        except (ValueError, KeyError, TypeError):
            continue
    
    if not valid_data:
        click.echo(f"❌ No valid {graph_type} data found")
        return
    
    # Extract data
    dates = [d[0] for d in valid_data]
    
    click.echo(f"   Using {len(valid_data)} valid data points")
    
    # Convert to matplotlib date numbers
    date_nums = mdates.date2num(dates)
    
    # Create graph based on type
    if graph_type == 'latency':
        fig, ax = plt.subplots(figsize=(12, 6))
        latencies = [d[1] for d in valid_data]
        
        ax.plot(date_nums, latencies, 'b-', linewidth=1, alpha=0.7, label='Latency')
        ax.fill_between(date_nums, 0, latencies, alpha=0.2, color='blue')
        
        # Add threshold lines
        ax.axhline(y=100, color='orange', linestyle='--', alpha=0.5, label='Slow (100ms)')
        ax.axhline(y=200, color='red', linestyle='--', alpha=0.5, label='Very slow (200ms)')
        
        ax.set_ylabel('Latency (ms)')
        ax.set_title(f'Latency Over Last {days} Days ({len(valid_data)} samples)')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # Add stats
        avg_latency = sum(latencies) / len(latencies)
        max_latency = max(latencies)
        ax.text(0.02, 0.98, f'Avg: {avg_latency:.1f}ms\nMax: {max_latency:.1f}ms', 
                transform=ax.transAxes, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        # Format x-axis
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M'))
        ax.xaxis.set_major_locator(mdates.HourLocator(interval=12))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        
    elif graph_type == 'loss':
        fig, ax = plt.subplots(figsize=(12, 6))
        losses = [d[2] for d in valid_data]
        
        ax.plot(date_nums, losses, 'r-', linewidth=1, alpha=0.7, label='Packet Loss')
        ax.fill_between(date_nums, 0, losses, alpha=0.2, color='red')
        
        # Add threshold lines
        ax.axhline(y=5, color='orange', linestyle='--', alpha=0.5, label='Warning (5%)')
        ax.axhline(y=20, color='red', linestyle='--', alpha=0.5, label='Critical (20%)')
        
        ax.set_ylabel('Packet Loss (%)')
        ax.set_title(f'Packet Loss Over Last {days} Days ({len(valid_data)} samples)')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # Add stats
        avg_loss = sum(losses) / len(losses)
        max_loss = max(losses)
        ax.text(0.02, 0.98, f'Avg: {avg_loss:.1f}%\nMax: {max_loss:.1f}%', 
                transform=ax.transAxes, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        # Format x-axis
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M'))
        ax.xaxis.set_major_locator(mdates.HourLocator(interval=12))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        
    elif graph_type == 'health':
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
        
        # Latency subplot
        latencies = [d[1] for d in valid_data]
        ax1.plot(date_nums, latencies, 'b-', linewidth=1, alpha=0.7)
        ax1.fill_between(date_nums, 0, latencies, alpha=0.2, color='blue')
        ax1.axhline(y=100, color='orange', linestyle='--', alpha=0.5)
        ax1.axhline(y=200, color='red', linestyle='--', alpha=0.5)
        ax1.set_ylabel('Latency (ms)')
        ax1.set_title(f'Network Health Overview ({len(valid_data)} samples)')
        ax1.grid(True, alpha=0.3)
        
        # Format x-axis for first subplot
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M'))
        ax1.xaxis.set_major_locator(mdates.HourLocator(interval=12))
        plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)
        
        # Loss subplot
        losses = [d[2] for d in valid_data]
        ax2.plot(date_nums, losses, 'r-', linewidth=1, alpha=0.7)
        ax2.fill_between(date_nums, 0, losses, alpha=0.2, color='red')
        ax2.axhline(y=5, color='orange', linestyle='--', alpha=0.5)
        ax2.axhline(y=20, color='red', linestyle='--', alpha=0.5)
        ax2.set_ylabel('Packet Loss (%)')
        ax2.set_xlabel('Time')
        ax2.grid(True, alpha=0.3)
        
        # Format x-axis for second subplot
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M'))
        ax2.xaxis.set_major_locator(mdates.HourLocator(interval=12))
        plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)
    
    plt.tight_layout()
    
    # Save to temp file and open
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
        plt.savefig(tmp.name, dpi=100, bbox_inches='tight')
        click.echo(f"✅ Graph saved to: {tmp.name}")
        
        # Try to open with default image viewer
        try:
            import platform
            system = platform.system().lower()
            
            if system == 'linux':
                subprocess.run(['xdg-open', tmp.name])
            elif system == 'darwin':  # macOS
                subprocess.run(['open', tmp.name])
            elif system == 'windows':
                subprocess.run(['start', tmp.name], shell=True)
            else:
                click.echo(f"📁 Graph file: {tmp.name}")
        except Exception as e:
            click.echo(f"📁 Graph file: {tmp.name}")
            click.echo(f"   (Could not auto-open: {e})")

__all__ = ['graph']