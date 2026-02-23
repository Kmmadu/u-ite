"""Network comparison commands for U-ITE"""
import click
from datetime import datetime, timedelta
from tabulate import tabulate
from uite.storage.db import HistoricalData
from uite.core.network_profile import NetworkProfileManager

@click.group()
def compare():
    """Compare network performance"""
    pass

def _resolve_network(network_identifier):
    """Helper to resolve network ID from name/tag/ID"""
    manager = NetworkProfileManager()
    
    # Try exact match
    if network_identifier in manager.profiles:
        return network_identifier, manager.profiles[network_identifier]
    
    # Try short ID
    for pid, profile in manager.profiles.items():
        if pid.startswith(network_identifier):
            return pid, profile
    
    # Try name
    network_lower = network_identifier.lower()
    for pid, profile in manager.profiles.items():
        if network_lower in profile.name.lower():
            return pid, profile
    
    # Try tag
    for pid, profile in manager.profiles.items():
        if profile.tags and network_lower in [t.lower() for t in profile.tags]:
            return pid, profile
    
    return None, None

# Main comparison command - this is what users will use directly
@compare.command()
@click.argument('network1')
@click.argument('network2')
@click.option('--days', default=7, help='Number of days to compare')
@click.option('--metric', type=click.Choice(['all', 'latency', 'loss', 'uptime']), 
              default='all', help='Metric to compare')
def between(network1, network2, days, metric):
    """Compare two networks side by side"""
    
    # Resolve networks
    id1, profile1 = _resolve_network(network1)
    id2, profile2 = _resolve_network(network2)
    
    if not id1:
        click.echo(f"❌ Network '{network1}' not found")
        _show_available_networks()
        return
    if not id2:
        click.echo(f"❌ Network '{network2}' not found")
        _show_available_networks()
        return
    
    # Get stats for both networks
    stats1 = HistoricalData.get_network_stats(id1, days)
    stats2 = HistoricalData.get_network_stats(id2, days)
    
    # Calculate uptime percentages
    uptime1 = (stats1['healthy_runs'] / stats1['total_runs'] * 100) if stats1['total_runs'] > 0 else 0
    uptime2 = (stats2['healthy_runs'] / stats2['total_runs'] * 100) if stats2['total_runs'] > 0 else 0
    
    click.echo("\n" + "=" * 80)
    click.echo(f"📊 NETWORK COMPARISON (Last {days} days)")
    click.echo("=" * 80)
    
    if metric == 'all' or metric == 'overview':
        # Overview table
        table_data = [
            ["Network", profile1.name, profile2.name],
            ["Provider", profile1.provider or "Unknown", profile2.provider or "Unknown"],
            ["Total Checks", stats1['total_runs'], stats2['total_runs']],
            ["Healthy Checks", stats1['healthy_runs'], stats2['healthy_runs']],
            ["Uptime", f"{uptime1:.1f}%", f"{uptime2:.1f}%"],
        ]
        
        click.echo(tabulate(table_data, headers=["Metric", "Network 1", "Network 2"], 
                           tablefmt="grid"))
    
    if metric == 'all' or metric == 'latency':
        # Latency comparison
        click.echo("\n⏱️  LATENCY COMPARISON")
        table_data = [
            ["Avg Latency", f"{stats1['avg_latency']:.1f}ms" if stats1['avg_latency'] else 'N/A',
                          f"{stats2['avg_latency']:.1f}ms" if stats2['avg_latency'] else 'N/A'],
            ["Max Latency", f"{stats1['max_latency']:.1f}ms" if stats1['max_latency'] else 'N/A',
                          f"{stats2['max_latency']:.1f}ms" if stats2['max_latency'] else 'N/A'],
        ]
        click.echo(tabulate(table_data, headers=["Metric", profile1.name, profile2.name], 
                           tablefmt="grid"))
    
    if metric == 'all' or metric == 'loss':
        # Packet loss comparison
        click.echo("\n📉 PACKET LOSS COMPARISON")
        table_data = [
            ["Avg Loss", f"{stats1['avg_loss']:.1f}%" if stats1['avg_loss'] else 'N/A',
                       f"{stats2['avg_loss']:.1f}%" if stats2['avg_loss'] else 'N/A'],
            ["Max Loss", f"{stats1['max_loss']:.1f}%" if stats1['max_loss'] else 'N/A',
                       f"{stats2['max_loss']:.1f}%" if stats2['max_loss'] else 'N/A'],
        ]
        click.echo(tabulate(table_data, headers=["Metric", profile1.name, profile2.name], 
                           tablefmt="grid"))
    
    # Winner determination
    if metric == 'all' or metric == 'uptime':
        click.echo("\n🏆 VERDICT")
        if uptime1 > uptime2:
            click.echo(f"   {profile1.name} is more reliable (+{(uptime1-uptime2):.1f}% uptime)")
        elif uptime2 > uptime1:
            click.echo(f"   {profile2.name} is more reliable (+{(uptime2-uptime1):.1f}% uptime)")
        else:
            click.echo("   Both networks have equal reliability")

@compare.command()
@click.argument('networks', nargs=-1)
@click.option('--days', default=7, help='Number of days to compare')
def multi(networks, days):
    """Compare multiple networks (up to 5)"""
    if len(networks) < 2:
        click.echo("❌ Please specify at least 2 networks")
        return
    if len(networks) > 5:
        click.echo("❌ Maximum 5 networks can be compared at once")
        return
    
    # Resolve all networks
    resolved = []
    for n in networks:
        nid, profile = _resolve_network(n)
        if nid:
            resolved.append((nid, profile))
        else:
            click.echo(f"⚠️  Skipping unknown network: {n}")
    
    if len(resolved) < 2:
        click.echo("❌ Not enough valid networks to compare")
        _show_available_networks()
        return
    
    # Get stats for all networks
    stats_list = []
    for nid, profile in resolved:
        stats = HistoricalData.get_network_stats(nid, days)
        stats_list.append((profile, stats))
    
    # Build comparison table
    click.echo("\n" + "=" * 80)
    click.echo(f"📊 MULTI-NETWORK COMPARISON (Last {days} days)")
    click.echo("=" * 80)
    
    # Headers
    headers = ["Metric"] + [p.name for p, _ in stats_list]
    table_data = []
    
    # Uptime row
    uptime_row = ["Uptime (%)"]
    for _, stats in stats_list:
        uptime = (stats['healthy_runs'] / stats['total_runs'] * 100) if stats['total_runs'] > 0 else 0
        uptime_row.append(f"{uptime:.1f}%")
    table_data.append(uptime_row)
    
    # Latency rows
    latency_row = ["Avg Latency (ms)"]
    for _, stats in stats_list:
        latency_row.append(f"{stats['avg_latency']:.1f}" if stats['avg_latency'] else 'N/A')
    table_data.append(latency_row)
    
    # Loss rows
    loss_row = ["Avg Loss (%)"]
    for _, stats in stats_list:
        loss_row.append(f"{stats['avg_loss']:.1f}" if stats['avg_loss'] else 'N/A')
    table_data.append(loss_row)
    
    # Total checks
    checks_row = ["Total Checks"]
    for _, stats in stats_list:
        checks_row.append(str(stats['total_runs']))
    table_data.append(checks_row)
    
    click.echo(tabulate(table_data, headers=headers, tablefmt="grid"))
    
    # Find winner (highest uptime)
    winner_idx = max(range(len(stats_list)), 
                    key=lambda i: stats_list[i][1]['healthy_runs'] / stats_list[i][1]['total_runs'] 
                    if stats_list[i][1]['total_runs'] > 0 else 0)
    winner = stats_list[winner_idx][0]
    click.echo(f"\n🏆 Most reliable: {winner.name}")

def _show_available_networks():
    """Show available networks for comparison"""
    manager = NetworkProfileManager()
    click.echo("\nAvailable networks:")
    for pid, profile in manager.profiles.items():
        if pid != "offline-state":
            tags = f"[{', '.join(profile.tags)}]" if profile.tags else ""
            provider = f"({profile.provider})" if profile.provider else ""
            click.echo(f"  • {profile.name} {provider} {tags}")
            click.echo(f"    ID: {pid[:8]}")

__all__ = ['compare']
