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
@click.option('--network', required=True, help='Network name, ID, or tag (required)')
def latency(days, network):
    """Show latency graph for a specific network"""
    _generate_graph('latency', days, network)

@graph.command()
@click.option('--days', default=7, help='Number of days to show')
@click.option('--network', required=True, help='Network name, ID, or tag (required)')
def health(days, network):
    """Show combined health graph for a specific network"""
    _generate_graph('health', days, network)

@graph.command()
@click.option('--days', default=7, help='Number of days to show')
@click.option('--network', required=True, help='Network name, ID, or tag (required)')
def loss(days, network):
    """Show packet loss graph for a specific network"""
    _generate_graph('loss', days, network)

def _generate_graph(graph_type, days, network):
    """Generate and display a graph for a specific network"""
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
    
    # Resolve network ID from name/tag
    from uite.core.network_profile import NetworkProfileManager
    manager = NetworkProfileManager()
    
    network_id = None
    network_name = None
    
    # Try to find the network - improved matching
    network_lower = network.lower()
    for pid, profile in manager.profiles.items():
        # Skip offline state
        if pid == "offline-state" or (hasattr(profile, 'is_offline_network') and profile.is_offline_network):
            continue
            
        # Check by full ID
        if network == pid:
            network_id = pid
            network_name = profile.name
            break
            
        # Check by short ID (first 8 chars)
        if len(pid) >= 8 and network == pid[:8]:
            network_id = pid
            network_name = profile.name
            break
            
        # Check by name (case-insensitive partial match)
        if network_lower in profile.name.lower():
            network_id = pid
            network_name = profile.name
            break
            
        # Check by tags
        if profile.tags and network_lower in [t.lower() for t in profile.tags]:
            network_id = pid
            network_name = profile.name
            break
    
    if not network_id:
        click.echo(f"❌ Network '{network}' not found")
        click.echo("\nAvailable networks:")
        for pid, profile in manager.profiles.items():
            # Skip offline state
            if pid == "offline-state" or (hasattr(profile, 'is_offline_network') and profile.is_offline_network):
                continue
            tags = f"[{', '.join(profile.tags)}]" if profile.tags else ""
            provider = f"({profile.provider})" if profile.provider else ""
            click.echo(f"  • {profile.name} {provider} {tags}")
            click.echo(f"    ID: {pid[:8]}")
        return
    
    click.echo(f"📡 Generating graph for network: {network_name}")
    
    # Get data for this specific network
    end = datetime.now()
    start = end - timedelta(days=days)
    
    runs = HistoricalData.get_runs_by_date_range(
        start.strftime("%d-%m-%Y"), "00:00",
        end.strftime("%d-%m-%Y"), "23:59",
        network_id=network_id
    )
    
    if not runs:
        click.echo(f"❌ No data found for {network_name} in the last {days} days")
        return
    
    click.echo(f"📊 Found {len(runs)} data points for this network")
    
    # Prepare data - filter out entries with missing values
    valid_data = []
    for r in runs:
        try:
            # Parse timestamp
            dt = datetime.fromisoformat(r['timestamp'].replace('Z', '+00:00'))
            
            # Get verdict for status coloring
            verdict = r.get('verdict', 'Unknown')
            
            # Determine status color
            if '✅' in verdict or 'Connected' in verdict or 'Healthy' in verdict:
                status = 'healthy'
            elif '⚠️' in verdict or 'Unstable' in verdict or 'Degraded' in verdict:
                status = 'degraded'
            elif '🐢' in verdict or 'Slow' in verdict:
                status = 'slow'
            elif '🌍' in verdict or 'ISP' in verdict:
                status = 'isp_issue'
            elif '🔴' in verdict or 'No Network' in verdict:
                status = 'offline'
            else:
                status = 'other'
            
            # Check if we have the required data
            if r.get('latency') is not None and r.get('loss') is not None:
                valid_data.append((dt, r['latency'], r['loss'], status))
        except (ValueError, KeyError, TypeError):
            continue
    
    if not valid_data:
        click.echo(f"❌ No valid data points with complete metrics")
        return
    
    click.echo(f"   Using {len(valid_data)} data points with complete metrics")
    
    # Extract data
    dates = [d[0] for d in valid_data]
    date_nums = mdates.date2num(dates)
    
    # Create graph based on type
    if graph_type == 'latency':
        # Professional NOC dashboard dark theme
        fig, ax = plt.subplots(figsize=(16, 8))
        fig.patch.set_facecolor('#1e1e1e')
        ax.set_facecolor('#2b2b2b')
        
        latencies = [d[1] for d in valid_data]
        
        # Smooth line plot - soft electric blue
        ax.plot(date_nums, latencies, color='#4aa3ff', linewidth=2.2, alpha=0.9, solid_capstyle='round')
        
        # Clean threshold lines
        ax.axhline(y=100, color='#2ecc71', linewidth=2, alpha=0.7)  # Green acceptable threshold
        ax.axhline(y=200, color='#e74c3c', linewidth=2, alpha=0.7)  # Red critical threshold
        
        # Minimal dashed grid
        ax.grid(True, linestyle='--', linewidth=0.5, alpha=0.2, color='#808080')
        
        # Remove all spines
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_color('#555555')
        ax.spines['left'].set_color('#555555')
        
        # Typography
        title_font = {'fontsize': 20, 'fontweight': 'bold', 'color': '#ffffff'}
        label_font = {'fontsize': 14, 'color': '#cccccc'}
        
        ax.set_title(f'LATENCY OVER TIME - {network_name.upper()}\nLast {days} Days', **title_font, pad=20)
        ax.set_ylabel('Latency (ms)', **label_font, labelpad=10)
        ax.set_xlabel('Time', **label_font, labelpad=10)
        
        # Style ticks
        ax.tick_params(axis='both', colors='#aaaaaa', labelsize=12)
        
        # Format x-axis
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M'))
        ax.xaxis.set_major_locator(mdates.HourLocator(interval=12))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, color='#aaaaaa')
        
        # Y-axis formatting
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{int(x)}ms'))
        
        # Set axis limits with padding
        ax.set_ylim(0, max(latencies) * 1.1)
        
    elif graph_type == 'loss':
        # Professional NOC dashboard dark theme for packet loss
        fig, ax = plt.subplots(figsize=(16, 8))
        fig.patch.set_facecolor('#1e1e1e')
        ax.set_facecolor('#2b2b2b')
        
        losses = [d[2] for d in valid_data]
        
        # Smooth line plot - soft orange/red for loss
        ax.plot(date_nums, losses, color='#e67e22', linewidth=2.2, alpha=0.9, solid_capstyle='round')
        
        # Clean threshold lines
        ax.axhline(y=5, color='#f1c40f', linewidth=2, alpha=0.7)   # Yellow warning threshold
        ax.axhline(y=20, color='#e74c3c', linewidth=2, alpha=0.7)  # Red critical threshold
        
        # Minimal dashed grid
        ax.grid(True, linestyle='--', linewidth=0.5, alpha=0.2, color='#808080')
        
        # Remove all spines
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_color('#555555')
        ax.spines['left'].set_color('#555555')
        
        # Typography
        title_font = {'fontsize': 20, 'fontweight': 'bold', 'color': '#ffffff'}
        label_font = {'fontsize': 14, 'color': '#cccccc'}
        
        ax.set_title(f'PACKET LOSS OVER TIME - {network_name.upper()}\nLast {days} Days', **title_font, pad=20)
        ax.set_ylabel('Packet Loss (%)', **label_font, labelpad=10)
        ax.set_xlabel('Time', **label_font, labelpad=10)
        
        # Style ticks
        ax.tick_params(axis='both', colors='#aaaaaa', labelsize=12)
        
        # Format x-axis
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M'))
        ax.xaxis.set_major_locator(mdates.HourLocator(interval=12))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, color='#aaaaaa')
        
        # Y-axis formatting
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{int(x)}%'))
        
        # Set axis limits with padding
        ax.set_ylim(0, max(losses) * 1.1 if max(losses) > 0 else 5)
        
    elif graph_type == 'health':
        # Professional NOC dashboard dark theme for health dashboard
        fig, ax1 = plt.subplots(figsize=(16, 8))
        fig.patch.set_facecolor('#1e1e1e')
        ax1.set_facecolor('#2b2b2b')
        
        ax2 = ax1.twinx()
        
        # Extract data
        latencies = [d[1] for d in valid_data]
        losses = [d[2] for d in valid_data]
        statuses = [d[3] for d in valid_data]
        
        # Plot latency - electric blue
        line1 = ax1.plot(date_nums, latencies, color='#4aa3ff', linewidth=2.2, alpha=0.9, 
                         solid_capstyle='round', label='Latency (ms)')
        ax1.set_ylabel('Latency (ms)', color='#4aa3ff', fontsize=14, labelpad=10)
        ax1.tick_params(axis='y', labelcolor='#4aa3ff', labelsize=12)
        
        # Plot packet loss - orange/red
        line2 = ax2.plot(date_nums, losses, color='#e67e22', linewidth=2.2, alpha=0.9,
                         solid_capstyle='round', label='Packet Loss (%)')
        ax2.set_ylabel('Packet Loss (%)', color='#e67e22', fontsize=14, labelpad=10)
        ax2.tick_params(axis='y', labelcolor='#e67e22', labelsize=12)
        
        # Add threshold lines
        ax1.axhline(y=100, color='#2ecc71', linewidth=1.5, alpha=0.5, linestyle=':')
        ax1.axhline(y=200, color='#e74c3c', linewidth=1.5, alpha=0.5, linestyle=':')
        ax2.axhline(y=5, color='#f1c40f', linewidth=1.5, alpha=0.5, linestyle=':')
        ax2.axhline(y=20, color='#e74c3c', linewidth=1.5, alpha=0.5, linestyle=':')
        
        # Minimal dashed grid
        ax1.grid(True, linestyle='--', linewidth=0.5, alpha=0.2, color='#808080')
        
        # Remove all spines
        ax1.spines['top'].set_visible(False)
        ax1.spines['right'].set_visible(False)
        ax1.spines['bottom'].set_color('#555555')
        ax1.spines['left'].set_color('#4aa3ff')
        ax2.spines['right'].set_color('#e67e22')
        
        # Color-code background based on status
        status_colors = {
            'healthy': '#27ae60',   # Darker green for background
            'degraded': '#f39c12',   # Darker orange
            'slow': '#e67e22',       # Darker orange/red
            'isp_issue': '#c0392b',  # Darker red
            'offline': '#7f8c8d',    # Darker gray
            'other': '#34495e'       # Dark blue-gray
        }
        
        # Group consecutive same-status periods
        current_status = statuses[0]
        start_idx = 0
        
        for i, status in enumerate(statuses):
            if status != current_status or i == len(statuses) - 1:
                end_idx = i + 1 if i == len(statuses) - 1 else i
                color = status_colors.get(current_status, '#34495e')
                ax1.axvspan(date_nums[start_idx], date_nums[end_idx-1], 
                           alpha=0.15, color=color)
                current_status = status
                start_idx = i
        
        # Typography
        title_font = {'fontsize': 20, 'fontweight': 'bold', 'color': '#ffffff'}
        label_font = {'fontsize': 14, 'color': '#cccccc'}
        
        plt.title(f'NETWORK HEALTH DASHBOARD - {network_name.upper()}\nLast {days} Days', 
                 **title_font, pad=20)
        ax1.set_xlabel('Time', **label_font, labelpad=10)
        
        # Format x-axis
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M'))
        ax1.xaxis.set_major_locator(mdates.HourLocator(interval=12))
        plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, color='#aaaaaa')
        
        # Calculate statistics
        total_points = len(valid_data)
        status_counts = {s: statuses.count(s) for s in set(statuses)}
        
        # Add status summary in bottom right
        status_text = (
            f"● Healthy: {status_counts.get('healthy', 0)} ({status_counts.get('healthy', 0)/total_points*100:.1f}%)\n"
            f"● Degraded: {status_counts.get('degraded', 0)} ({status_counts.get('degraded', 0)/total_points*100:.1f}%)\n"
            f"● Slow: {status_counts.get('slow', 0)} ({status_counts.get('slow', 0)/total_points*100:.1f}%)\n"
            f"● ISP Issue: {status_counts.get('isp_issue', 0)} ({status_counts.get('isp_issue', 0)/total_points*100:.1f}%)\n"
            f"● Offline: {status_counts.get('offline', 0)} ({status_counts.get('offline', 0)/total_points*100:.1f}%)"
        )
        
        ax1.text(0.98, 0.02, status_text, transform=ax1.transAxes, 
                verticalalignment='bottom', horizontalalignment='right',
                fontsize=11, color='#cccccc',
                bbox=dict(boxstyle='round', facecolor='#2b2b2b', alpha=0.9, edgecolor='#555555'))
    
    plt.tight_layout()
    
    # Save and open
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
        plt.savefig(tmp.name, dpi=100, bbox_inches='tight', facecolor='#1e1e1e')
        click.echo(f"✅ Graph saved to: {tmp.name}")
        
        # Open with default viewer
        try:
            import platform
            system = platform.system().lower()
            
            if system == 'linux':
                subprocess.run(['xdg-open', tmp.name])
            elif system == 'darwin':
                subprocess.run(['open', tmp.name])
            elif system == 'windows':
                subprocess.run(['start', tmp.name], shell=True)
        except:
            click.echo(f"📁 Graph file: {tmp.name}")

__all__ = ['graph']