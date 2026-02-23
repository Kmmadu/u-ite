"""
Network Comparison Commands for U-ITE
=====================================
Provides commands to compare performance metrics between different networks.
Users can compare two networks side-by-side or multiple networks at once.

Features:
- Compare two networks with detailed metrics
- Multi-network comparison (up to 5 networks)
- Filter by time period (--days)
- Choose specific metrics (latency, loss, uptime)
- Automatic network resolution by name, ID, or tag
- Winner determination based on uptime
"""

import click
from datetime import datetime, timedelta
from tabulate import tabulate
from uite.storage.db import HistoricalData
from uite.core.network_profile import NetworkProfileManager


@click.group()
def compare():
    """
    Compare network performance metrics side-by-side.
    
    This command group allows you to compare the performance of different
    networks over specified time periods. You can compare two networks
    in detail or multiple networks at a glance.
    
    Examples:
        uite compare between "Home" "Office" --days 30
        uite compare multi Home Office Backup --days 7
        uite compare between primary backup --metric latency
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


@compare.command()
@click.argument('network1')
@click.argument('network2')
@click.option('--days', default=7, help='Number of days to compare')
@click.option('--metric', 
              type=click.Choice(['all', 'latency', 'loss', 'uptime']), 
              default='all', 
              help='Metric to focus on (default: all)')
def between(network1, network2, days, metric):
    """
    Compare two networks side by side with detailed metrics.
    
    This command provides a comprehensive comparison between two networks,
    showing provider information, total checks, uptime percentage, latency,
    and packet loss statistics.
    
    Examples:
        uite compare between "Home Fiber" "Office Network" --days 30
        uite compare between primary backup --metric latency --days 7
        uite compare between "Comcast" "AT&T" --metric uptime
    """
    
    # Resolve both network identifiers to actual network IDs
    id1, profile1 = _resolve_network(network1)
    id2, profile2 = _resolve_network(network2)
    
    # Handle not found cases
    if not id1:
        click.echo(f"❌ Network '{network1}' not found")
        _show_available_networks()
        return
    if not id2:
        click.echo(f"❌ Network '{network2}' not found")
        _show_available_networks()
        return
    
    # Fetch statistics for both networks
    stats1 = HistoricalData.get_network_stats(id1, days)
    stats2 = HistoricalData.get_network_stats(id2, days)
    
    # Calculate uptime percentages (healthy checks / total checks)
    uptime1 = (stats1['healthy_runs'] / stats1['total_runs'] * 100) if stats1['total_runs'] > 0 else 0
    uptime2 = (stats2['healthy_runs'] / stats2['total_runs'] * 100) if stats2['total_runs'] > 0 else 0
    
    # Header
    click.echo("\n" + "=" * 80)
    click.echo(f"📊 NETWORK COMPARISON (Last {days} days)")
    click.echo("=" * 80)
    
    # Overview section (always shown, even with metric filter)
    if metric == 'all' or metric == 'overview':
        table_data = [
            ["Network", profile1.name, profile2.name],
            ["Provider", profile1.provider or "Unknown", profile2.provider or "Unknown"],
            ["Total Checks", stats1['total_runs'], stats2['total_runs']],
            ["Healthy Checks", stats1['healthy_runs'], stats2['healthy_runs']],
            ["Uptime", f"{uptime1:.1f}%", f"{uptime2:.1f}%"],
        ]
        
        click.echo(tabulate(table_data, 
                           headers=["Metric", "Network 1", "Network 2"], 
                           tablefmt="grid"))
    
    # Latency comparison (if requested)
    if metric == 'all' or metric == 'latency':
        click.echo("\n⏱️  LATENCY COMPARISON")
        table_data = [
            ["Avg Latency", 
             f"{stats1['avg_latency']:.1f}ms" if stats1['avg_latency'] else 'N/A',
             f"{stats2['avg_latency']:.1f}ms" if stats2['avg_latency'] else 'N/A'],
            ["Max Latency", 
             f"{stats1['max_latency']:.1f}ms" if stats1['max_latency'] else 'N/A',
             f"{stats2['max_latency']:.1f}ms" if stats2['max_latency'] else 'N/A'],
        ]
        click.echo(tabulate(table_data, 
                           headers=["Metric", profile1.name, profile2.name], 
                           tablefmt="grid"))
    
    # Packet loss comparison (if requested)
    if metric == 'all' or metric == 'loss':
        click.echo("\n📉 PACKET LOSS COMPARISON")
        table_data = [
            ["Avg Loss", 
             f"{stats1['avg_loss']:.1f}%" if stats1['avg_loss'] else 'N/A',
             f"{stats2['avg_loss']:.1f}%" if stats2['avg_loss'] else 'N/A'],
            ["Max Loss", 
             f"{stats1['max_loss']:.1f}%" if stats1['max_loss'] else 'N/A',
             f"{stats2['max_loss']:.1f}%" if stats2['max_loss'] else 'N/A'],
        ]
        click.echo(tabulate(table_data, 
                           headers=["Metric", profile1.name, profile2.name], 
                           tablefmt="grid"))
    
    # Winner determination based on uptime
    if metric == 'all' or metric == 'uptime':
        click.echo("\n🏆 VERDICT")
        if uptime1 > uptime2:
            click.echo(f"   {profile1.name} is more reliable "
                      f"(+{(uptime1-uptime2):.1f}% uptime)")
        elif uptime2 > uptime1:
            click.echo(f"   {profile2.name} is more reliable "
                      f"(+{(uptime2-uptime1):.1f}% uptime)")
        else:
            click.echo("   Both networks have equal reliability")


@compare.command()
@click.argument('networks', nargs=-1)
@click.option('--days', default=7, help='Number of days to compare')
def multi(networks, days):
    """
    Compare multiple networks at a glance (up to 5).
    
    This command provides a high-level comparison of multiple networks,
    showing key metrics in a compact table format. Perfect for getting
    a quick overview of all your networks.
    
    Examples:
        uite compare multi Home Office Backup --days 30
        uite compare multi primary secondary tertiary --days 7
    """
    # Validate input
    if len(networks) < 2:
        click.echo("❌ Please specify at least 2 networks")
        return
    if len(networks) > 5:
        click.echo("❌ Maximum 5 networks can be compared at once")
        return
    
    # Resolve all network identifiers to actual networks
    resolved = []
    for n in networks:
        nid, profile = _resolve_network(n)
        if nid:
            resolved.append((nid, profile))
        else:
            click.echo(f"⚠️  Skipping unknown network: {n}")
    
    # Ensure we have at least 2 valid networks
    if len(resolved) < 2:
        click.echo("❌ Not enough valid networks to compare")
        _show_available_networks()
        return
    
    # Fetch statistics for all networks
    stats_list = []
    for nid, profile in resolved:
        stats = HistoricalData.get_network_stats(nid, days)
        stats_list.append((profile, stats))
    
    # Header
    click.echo("\n" + "=" * 80)
    click.echo(f"📊 MULTI-NETWORK COMPARISON (Last {days} days)")
    click.echo("=" * 80)
    
    # Build comparison table
    headers = ["Metric"] + [p.name for p, _ in stats_list]
    table_data = []
    
    # Uptime row
    uptime_row = ["Uptime (%)"]
    for _, stats in stats_list:
        uptime = (stats['healthy_runs'] / stats['total_runs'] * 100) if stats['total_runs'] > 0 else 0
        uptime_row.append(f"{uptime:.1f}%")
    table_data.append(uptime_row)
    
    # Average latency row
    latency_row = ["Avg Latency (ms)"]
    for _, stats in stats_list:
        latency_row.append(f"{stats['avg_latency']:.1f}" if stats['avg_latency'] else 'N/A')
    table_data.append(latency_row)
    
    # Average loss row
    loss_row = ["Avg Loss (%)"]
    for _, stats in stats_list:
        loss_row.append(f"{stats['avg_loss']:.1f}" if stats['avg_loss'] else 'N/A')
    table_data.append(loss_row)
    
    # Total checks row (for context)
    checks_row = ["Total Checks"]
    for _, stats in stats_list:
        checks_row.append(str(stats['total_runs']))
    table_data.append(checks_row)
    
    # Display the table
    click.echo(tabulate(table_data, headers=headers, tablefmt="grid"))
    
    # Find the winner (network with highest uptime)
    winner_idx = max(range(len(stats_list)), 
                    key=lambda i: stats_list[i][1]['healthy_runs'] / stats_list[i][1]['total_runs'] 
                    if stats_list[i][1]['total_runs'] > 0 else 0)
    winner = stats_list[winner_idx][0]
    click.echo(f"\n🏆 Most reliable: {winner.name}")


def _show_available_networks():
    """
    Display all available networks to help users with correct identifiers.
    
    Shows network names, providers, tags, and short IDs for easy reference.
    This is called when a network lookup fails.
    """
    manager = NetworkProfileManager()
    click.echo("\nAvailable networks:")
    for pid, profile in manager.profiles.items():
        # Skip offline state in suggestions
        if pid != "offline-state":
            tags = f"[{', '.join(profile.tags)}]" if profile.tags else ""
            provider = f"({profile.provider})" if profile.provider else ""
            click.echo(f"  • {profile.name} {provider} {tags}")
            click.echo(f"    ID: {pid[:8]}")


# Export the command group for registration in main CLI
__all__ = ['compare']
