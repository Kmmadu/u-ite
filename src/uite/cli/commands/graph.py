"""
Graph Generation Commands for U-ITE
====================================
Provides data visualization capabilities for network performance metrics.
Generates professional NOC-style graphs with dark theme for better visibility.

Features:
- Latency graphs with threshold lines (100ms warning, 200ms critical)
- Packet loss graphs with threshold lines (5% warning, 20% critical)
- Combined health dashboard showing both metrics with simplified status (Healthy vs Degraded)
- Professional dark theme optimized for NOC environments
- Automatic graph opening in default image viewer
- Cross-platform support (Linux, macOS, Windows)
"""

import click
from datetime import datetime, timedelta
import tempfile
import subprocess
import webbrowser
from uite.storage.db import HistoricalData


@click.group()
def graph():
    """
    Generate visual graphs from historical network data.
    
    Creates professional NOC-style graphs to visualize network performance
    trends over time. Three graph types are available:
    
    - latency:    Line graph of latency with threshold lines
    - loss:       Line graph of packet loss with threshold lines  
    - health:     Combined dashboard with both metrics and simplified status
    
    All graphs use a dark theme optimized for monitoring environments.
    
    Examples:
        uite graph latency --network "Home" --days 7
        uite graph loss --network "Office" --days 30
        uite graph health --network primary --days 14
    """
    pass


@graph.command()
@click.option('--days', default=7, help='Number of days to show')
@click.option('--network', required=True, help='Network name, ID, or tag')
def latency(days, network):
    """
    Generate a latency graph for a specific network.
    
    Creates a line graph showing latency over time with threshold lines:
    - Green line at 100ms (acceptable threshold)
    - Red line at 200ms (critical threshold)
    
    The graph uses a professional dark theme and includes:
    - Average and maximum latency statistics
    - Time series data with proper date formatting
    - Clean grid lines for easy reading
    """
    _generate_graph('latency', days, network)


@graph.command()
@click.option('--days', default=7, help='Number of days to show')
@click.option('--network', required=True, help='Network name, ID, or tag')
def health(days, network):
    """
    Generate a simplified health dashboard.
    
    Creates a dual-axis graph showing both latency and packet loss:
    - Left axis (blue): Latency over time
    - Right axis (orange): Packet loss over time
    
    Background colors indicate network status (SIMPLIFIED):
    - Green:  Healthy operation
    - Orange: Degraded (any issue: slow, unstable, ISP problems)
    
    Includes status summary with percentage breakdowns.
    Note: Offline periods are excluded as they represent connectivity, not performance.
    """
    _generate_graph('health', days, network)


@graph.command()
@click.option('--days', default=7, help='Number of days to show')
@click.option('--network', required=True, help='Network name, ID, or tag')
def loss(days, network):
    """
    Generate a packet loss graph for a specific network.
    
    Creates a line graph showing packet loss over time with threshold lines:
    - Yellow line at 5% (warning threshold)
    - Red line at 20% (critical threshold)
    
    The graph uses a professional dark theme and includes:
    - Average and maximum loss statistics
    - Time series data with proper date formatting
    - Clean grid lines for easy reading
    """
    _generate_graph('loss', days, network)


def _generate_graph(graph_type, days, network):
    """
    Core graph generation function.
    
    This internal function handles all graph types, data processing,
    and visualization logic. It:
    1. Validates and resolves the network identifier
    2. Fetches historical data for the specified period
    3. Filters and prepares data for plotting
    4. Creates the appropriate graph based on type
    5. Saves and opens the generated image
    
    Args:
        graph_type (str): Type of graph ('latency', 'loss', or 'health')
        days (int): Number of days of data to include
        network (str): Network name, ID, or tag to graph
    """
    try:
        # Import matplotlib conditionally to avoid making it a hard dependency
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
        import matplotlib
        matplotlib.use('Agg')  # Use non-interactive backend for headless operation
        import numpy as np
    except ImportError as e:
        click.echo(f"❌ Missing dependency: {e}")
        click.echo("   Please install: pip install matplotlib numpy")
        return
    
    # ======================================================================
    # Network Resolution
    # Find the network by ID, name, or tag
    # ======================================================================
    from uite.core.network_profile import NetworkProfileManager
    manager = NetworkProfileManager()
    
    network_id = None
    network_name = None
    
    # Try to find the network using multiple strategies
    network_lower = network.lower()
    for pid, profile in manager.profiles.items():
        # Skip offline state in graph queries
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
            if pid == "offline-state" or (hasattr(profile, 'is_offline_network') and profile.is_offline_network):
                continue
            tags = f"[{', '.join(profile.tags)}]" if profile.tags else ""
            provider = f"({profile.provider})" if profile.provider else ""
            click.echo(f"  • {profile.name} {provider} {tags}")
            click.echo(f"    ID: {pid[:8]}")
        return
    
    click.echo(f"📡 Generating graph for network: {network_name}")
    
    # ======================================================================
    # Data Fetching
    # Get historical data for the specified period
    # ======================================================================
    runs = HistoricalData.get_runs_for_last_days(network_id, days)
    
    if not runs:
        click.echo(f"❌ No data found for {network_name} in the last {days} days")
        return
    
    click.echo(f"📊 Found {len(runs)} data points for this network")
    
    # ======================================================================
    # Data Preparation
    # Filter and validate data points, extract metrics
    # ======================================================================
    valid_data = []
    for r in runs:
        try:
            # Parse timestamp (handle potential 'Z' timezone indicator)
            dt = datetime.fromisoformat(r['timestamp'].replace('Z', '+00:00'))
            
            # Get verdict for status coloring (used in health graph)
            verdict = r.get('verdict', 'Unknown')
            
            # Determine status category based on verdict emoji
            if '✅' in verdict or 'Connected' in verdict or 'Healthy' in verdict:
                status = 'healthy'
            elif '⚠️' in verdict or 'Unstable' in verdict or 'Degraded' in verdict:
                status = 'degraded'
            elif '🐢' in verdict or 'Slow' in verdict:
                status = 'degraded'  # Consolidated into degraded
            elif '🌍' in verdict or 'ISP' in verdict:
                status = 'degraded'  # Consolidated into degraded
            elif '🔴' in verdict or 'No Network' in verdict:
                status = 'offline'   # Will be filtered out for health graph
            else:
                status = 'other'
            
            # Only include data points with both latency and loss metrics
            if r.get('latency') is not None and r.get('loss') is not None:
                valid_data.append((dt, r['latency'], r['loss'], status))
        except (ValueError, KeyError, TypeError):
            # Skip invalid data points
            continue
    
    if not valid_data:
        click.echo(f"❌ No valid data points with complete metrics")
        return
    
    click.echo(f"   Using {len(valid_data)} data points with complete metrics")
    
    # Extract data components
    dates = [d[0] for d in valid_data]
    date_nums = mdates.date2num(dates)  # Convert to matplotlib date format
    
    # ======================================================================
    # Graph Creation
    # Generate the appropriate graph type with professional styling
    # ======================================================================
    
    if graph_type == 'latency':
        # Latency Graph - Professional NOC dashboard dark theme
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
        
        # Remove all spines for clean look
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_color('#555555')
        ax.spines['left'].set_color('#555555')
        
        # Typography - Professional NOC styling
        title_font = {'fontsize': 20, 'fontweight': 'bold', 'color': '#ffffff'}
        label_font = {'fontsize': 14, 'color': '#cccccc'}
        
        ax.set_title(f'LATENCY OVER TIME - {network_name.upper()}\nLast {days} Days', **title_font, pad=20)
        ax.set_ylabel('Latency (ms)', **label_font, labelpad=10)
        ax.set_xlabel('Time', **label_font, labelpad=10)
        
        # Style ticks
        ax.tick_params(axis='both', colors='#aaaaaa', labelsize=12)
        
        # Format x-axis with date/time
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M'))
        ax.xaxis.set_major_locator(mdates.HourLocator(interval=12))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, color='#aaaaaa')
        
        # Y-axis formatting
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{int(x)}ms'))
        
        # Set axis limits with padding
        ax.set_ylim(0, max(latencies) * 1.1)
        
    elif graph_type == 'loss':
        # Packet Loss Graph - Professional NOC dashboard dark theme
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
        # SIMPLIFIED HEALTH DASHBOARD - Healthy vs Degraded only
        # Filter out offline periods (they represent connectivity, not performance)
        online_data = [(d[0], d[1], d[2], d[3]) for d in valid_data if d[3] != 'offline']
        
        if not online_data:
            click.echo("⚠️ No online data points in this period (all offline)")
            return
        
        click.echo(f"   Using {len(online_data)} online data points for health graph")
        
        dates = [d[0] for d in online_data]
        date_nums = mdates.date2num(dates)
        latencies = [d[1] for d in online_data]
        losses = [d[2] for d in online_data]
        statuses = [d[3] for d in online_data]
        
        # Simplify status to Healthy vs Degraded
        simplified_status = []
        for s in statuses:
            if s == 'healthy':
                simplified_status.append('healthy')
            else:
                # Unstable, slow, ISP issues, other all become "degraded"
                simplified_status.append('degraded')
        
        # Create dual-axis graph
        fig, ax1 = plt.subplots(figsize=(16, 8))
        fig.patch.set_facecolor('#1e1e1e')
        ax1.set_facecolor('#2b2b2b')
        
        ax2 = ax1.twinx()
        
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
        
        # Add threshold lines (dotted for subtlety)
        ax1.axhline(y=100, color='#2ecc71', linewidth=1.5, alpha=0.5, linestyle=':')
        ax1.axhline(y=200, color='#e74c3c', linewidth=1.5, alpha=0.5, linestyle=':')
        ax2.axhline(y=5, color='#f1c40f', linewidth=1.5, alpha=0.5, linestyle=':')
        ax2.axhline(y=20, color='#e74c3c', linewidth=1.5, alpha=0.5, linestyle=':')
        
        # Minimal dashed grid
        ax1.grid(True, linestyle='--', linewidth=0.5, alpha=0.2, color='#808080')
        
        # Remove all spines except bottom and colored axes
        ax1.spines['top'].set_visible(False)
        ax1.spines['right'].set_visible(False)
        ax1.spines['bottom'].set_color('#555555')
        ax1.spines['left'].set_color('#4aa3ff')
        ax2.spines['right'].set_color('#e67e22')
        
        # Color-code background based on SIMPLIFIED status (Healthy vs Degraded)
        status_colors = {
            'healthy': '#27ae60',   # Green for healthy
            'degraded': '#e67e22',   # Orange for degraded
        }
        
        # Group consecutive same-status periods
        current_status = simplified_status[0]
        start_idx = 0
        
        for i, status in enumerate(simplified_status):
            if status != current_status or i == len(simplified_status) - 1:
                end_idx = i + 1 if i == len(simplified_status) - 1 else i
                color = status_colors.get(current_status, '#34495e')
                ax1.axvspan(date_nums[start_idx], date_nums[end_idx-1], 
                           alpha=0.15, color=color)
                current_status = status
                start_idx = i
        
        # Typography
        title_font = {'fontsize': 20, 'fontweight': 'bold', 'color': '#ffffff'}
        label_font = {'fontsize': 14, 'color': '#cccccc'}
        
        plt.title(f'NETWORK PERFORMANCE DASHBOARD - {network_name.upper()}\nLast {days} Days', 
                 **title_font, pad=20)
        ax1.set_xlabel('Time', **label_font, labelpad=10)
        
        # Format x-axis
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M'))
        ax1.xaxis.set_major_locator(mdates.HourLocator(interval=12))
        plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, color='#aaaaaa')
        
        # Calculate statistics (SIMPLIFIED)
        total_points = len(simplified_status)
        healthy_count = simplified_status.count('healthy')
        degraded_count = simplified_status.count('degraded')
        
        # Add status summary in bottom right (SIMPLIFIED)
        status_text = (
            f"● Healthy: {healthy_count} ({healthy_count/total_points*100:.1f}%)\n"
            f"● Degraded: {degraded_count} ({degraded_count/total_points*100:.1f}%)"
        )
        
        ax1.text(0.98, 0.02, status_text, transform=ax1.transAxes, 
                verticalalignment='bottom', horizontalalignment='right',
                fontsize=11, color='#cccccc',
                bbox=dict(boxstyle='round', facecolor='#2b2b2b', alpha=0.9, edgecolor='#555555'))
    
    # Adjust layout to prevent clipping
    plt.tight_layout()
    
    # ======================================================================
    # Save and Open
    # Save graph to temporary file and open with default viewer
    # ======================================================================
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
        plt.savefig(tmp.name, dpi=100, bbox_inches='tight', facecolor='#1e1e1e')
        click.echo(f"✅ Graph saved to: {tmp.name}")
        
        # Open with default system image viewer (cross-platform)
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
            # If auto-open fails, at least show the file path
            click.echo(f"📁 Graph file: {tmp.name}")
            click.echo(f"   (Could not auto-open: {e})")


# Export the command group for registration in main CLI
__all__ = ['graph']
