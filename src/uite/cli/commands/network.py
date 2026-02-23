"""
Network Profile Management Commands for U-ITE
==============================================
Provides commands to manage and interact with network profiles detected by U-ITE.

Features:
- List all connected networks with their metadata
- View offline sessions separately
- Rename networks with friendly names
- Set ISP/provider information
- Add/remove tags for organization
- View detailed network statistics
- Clean up old offline sessions
"""

import click
from tabulate import tabulate
from uite.core.network_profile import NetworkProfileManager
from datetime import datetime


@click.group()
def network():
    """
    Manage network profiles detected by U-ITE.
    
    This command group allows you to view, organize, and analyze the networks
    your device has connected to. You can rename networks, add tags, set
    provider information, and view detailed statistics.
    
    Examples:
        uite network list
        uite network rename abc123 "Home Fiber"
        uite network tag abc123 primary
        uite network stats abc123
        uite network cleanup --days 30
    """
    pass


@network.command(name="list")
def list_networks():
    """
    List all networks the device has connected to.
    
    Shows only real networks (filters out offline sessions and temporary states).
    Displays network ID, name, provider, tags, first seen, and last seen with
    human-readable time indicators (today, yesterday, X days ago).
    
    Examples:
        uite network list
    """
    manager = NetworkProfileManager()
    profiles = manager.list_profiles()
    
    if not profiles:
        click.echo("No networks detected yet. Run the observer first.")
        return
    
    # ======================================================================
    # Filter to show ONLY networks that were actually connected to
    # ======================================================================
    connected_networks = []
    for p in profiles:
        # Skip anything that's clearly not a real network
        if p.network_id == "offline-state":
            continue
        if hasattr(p, 'is_offline_network') and p.is_offline_network:
            continue
        if p.name == "Offline State" or "offline" in p.name.lower():
            continue
        
        # Include networks that have been manually managed (provider or tags set)
        if p.provider and p.provider != "Unknown":
            connected_networks.append(p)
            continue
            
        if p.tags:
            connected_networks.append(p)
            continue
        
        # Include networks with proper hash IDs (likely real networks)
        if p.network_id and len(p.network_id) >= 8 and not p.network_id.startswith("offline"):
            connected_networks.append(p)
    
    if not connected_networks:
        click.echo("No connected networks found. Run the observer while connected to WiFi.")
        return
    
    # Sort by last seen (most recent first)
    connected_networks.sort(key=lambda x: x.last_seen, reverse=True)
    
    # Build table for display
    table = []
    for p in connected_networks:
        # Format tags as comma-separated string
        tags_display = ", ".join(p.tags) if p.tags else ""
        
        # Format last seen with human-readable relative time
        last_seen = p.last_seen.strftime("%Y-%m-%d %H:%M")
        days_ago = (datetime.now() - p.last_seen).days
        if days_ago == 0:
            last_seen_display = f"{last_seen} (today)"
        elif days_ago == 1:
            last_seen_display = f"{last_seen} (yesterday)"
        else:
            last_seen_display = f"{last_seen} ({days_ago} days ago)"
        
        table.append([
            p.network_id[:8],  # Show only first 8 chars of ID for readability
            p.name,
            p.provider or "Unknown",
            tags_display,
            p.first_seen.strftime("%Y-%m-%d"),
            last_seen_display
        ])
    
    # Display the table
    click.echo(f"\n📡 Connected Networks ({len(connected_networks)}):")
    click.echo(tabulate(
        table,
        headers=["ID", "Name", "Provider", "Tags", "First Seen", "Last Seen"],
        tablefmt="grid"
    ))
    
    # Show count of filtered offline sessions if any
    filtered_count = len(profiles) - len(connected_networks)
    if filtered_count > 0:
        click.echo(f"\nℹ️  {filtered_count} offline session(s) not shown (use 'list-all' to see them)")
    
    # Show helpful tips
    click.echo("\n💡 Tips:")
    click.echo("  • Rename: uite network rename <ID> \"New Name\"")
    click.echo("  • Set provider: uite network provider <ID> \"ISP Name\"")
    click.echo("  • Add tag: uite network tag <ID> <tag>")
    click.echo("  • View stats: uite by-network <name/ID/tag> --days 30")


@network.command(name="list-all")
def list_all_networks():
    """
    List all networks including offline sessions.
    
    Shows both real networks and temporary offline sessions separately.
    Useful for debugging and cleaning up old sessions.
    
    Examples:
        uite network list-all
    """
    manager = NetworkProfileManager()
    profiles = manager.list_profiles()
    
    if not profiles:
        click.echo("No networks detected yet.")
        return
    
    # Separate connected networks from offline sessions
    connected = []
    offline = []
    
    for p in profiles:
        is_offline = (p.network_id == "offline-state" or 
                     (hasattr(p, 'is_offline_network') and p.is_offline_network) or
                     p.name == "Offline State" or 
                     "offline" in p.name.lower())
        
        if is_offline:
            offline.append(p)
        else:
            connected.append(p)
    
    # Show connected networks
    if connected:
        table = []
        for p in connected:
            tags_display = ", ".join(p.tags) if p.tags else ""
            table.append([
                p.network_id[:8],
                p.name,
                p.provider or "Unknown",
                tags_display,
                p.first_seen.strftime("%Y-%m-%d %H:%M"),
                p.last_seen.strftime("%Y-%m-%d %H:%M")
            ])
        
        click.echo("\n📡 Connected Networks:")
        click.echo(tabulate(
            table,
            headers=["ID", "Name", "Provider", "Tags", "First Seen", "Last Seen"],
            tablefmt="grid"
        ))
    
    # Show offline sessions separately
    if offline:
        table = []
        for p in offline:
            tags_display = ", ".join(p.tags) if p.tags else ""
            # Truncate offline ID for display
            display_id = p.network_id[:8] if len(p.network_id) > 8 else p.network_id
            table.append([
                display_id,
                f"{p.name} (offline)",
                p.provider or "Unknown",
                tags_display,
                p.first_seen.strftime("%Y-%m-%d %H:%M"),
                p.last_seen.strftime("%Y-%m-%d %H:%M")
            ])
        
        click.echo("\n📡 Offline Sessions:")
        click.echo(tabulate(
            table,
            headers=["ID", "Name", "Provider", "Tags", "First Seen", "Last Seen"],
            tablefmt="grid"
        ))


@network.command()
@click.argument('network_id')
@click.argument('name')
def rename(network_id, name):
    """
    Rename a network with a friendly, memorable name.
    
    Examples:
        uite network rename abc123 "Home Fiber"
        uite network rename b23c4fec "Office Network"
    """
    manager = NetworkProfileManager()
    
    # Try to find by full ID or prefix (first 8 chars)
    found = None
    for pid, profile in manager.profiles.items():
        if pid == network_id or pid.startswith(network_id):
            found = pid
            break
    
    if found:
        manager.rename(found, name)
        click.echo(f"✅ Network renamed to: {name}")
    else:
        click.echo(f"❌ Network {network_id} not found")
        # Show available networks to help the user
        click.echo("\nAvailable networks:")
        for pid, profile in manager.profiles.items():
            # Skip offline sessions in suggestions
            if pid == "offline-state" or (hasattr(profile, 'is_offline_network') and profile.is_offline_network):
                continue
            click.echo(f"  • {pid[:8]} - {profile.name}")


@network.command()
@click.argument('network_id')
@click.argument('provider')
def provider(network_id, provider):
    """
    Set the Internet Service Provider (ISP) name for a network.
    
    Examples:
        uite network provider abc123 "Comcast"
        uite network provider b23c4fec "AT&T Fiber"
    """
    manager = NetworkProfileManager()
    
    # Try to find by full ID or prefix
    found = None
    for pid, profile in manager.profiles.items():
        if pid == network_id or pid.startswith(network_id):
            found = pid
            break
    
    if found:
        manager.profiles[found].provider = provider
        manager.save()
        click.echo(f"✅ Provider set to: {provider}")
    else:
        click.echo(f"❌ Network {network_id} not found")


@network.command()
@click.argument('network_id')
@click.argument('tag')
def tag(network_id, tag):
    """
    Add a tag to a network for easy filtering and organization.
    
    Tags can be used with 'by-network' command to filter networks.
    Common tags: primary, backup, work, home, office, guest
    
    Examples:
        uite network tag abc123 primary
        uite network tag abc123 backup
        uite network tag b23c4fec work
    """
    manager = NetworkProfileManager()
    
    # Try to find by full ID or prefix
    found = None
    for pid, profile in manager.profiles.items():
        if pid == network_id or pid.startswith(network_id):
            found = pid
            break
    
    if found:
        if tag not in manager.profiles[found].tags:
            manager.profiles[found].tags.append(tag)
            manager.save()
            click.echo(f"✅ Added tag: {tag}")
        else:
            click.echo(f"⚠️ Tag '{tag}' already exists")
    else:
        click.echo(f"❌ Network {network_id} not found")


@network.command()
@click.argument('network_id')
def stats(network_id):
    """
    Show detailed statistics for a specific network.
    
    Displays network metadata and performance statistics from the last 30 days:
    - Network ID, name, provider, tags
    - First seen and last seen timestamps
    - Total diagnostic runs
    - Uptime percentage
    
    Examples:
        uite network stats abc123
        uite network stats b23c4fec
    """
    from uite.storage.db import HistoricalData
    from datetime import datetime, timedelta
    
    manager = NetworkProfileManager()
    
    # Try to find by full ID or prefix
    found = None
    profile = None
    for pid, p in manager.profiles.items():
        if pid == network_id or pid.startswith(network_id):
            found = pid
            profile = p
            break
    
    if not found:
        click.echo(f"❌ Network {network_id} not found")
        return
    
    # Get last 30 days of data
    end = datetime.now()
    start = end - timedelta(days=30)
    
    runs = HistoricalData.get_runs_by_date_range(
        start.strftime("%d-%m-%Y"), start.strftime("%H:%M"),
        end.strftime("%d-%m-%Y"), end.strftime("%H:%M"),
        network_id=found
    )
    
    # Display network information
    click.echo(f"\n📊 Network Statistics: {profile.name}")
    click.echo("=" * 50)
    click.echo(f"ID: {found}")
    click.echo(f"Provider: {profile.provider or 'Not set'}")
    click.echo(f"Tags: {', '.join(profile.tags) if profile.tags else 'None'}")
    click.echo(f"First seen: {profile.first_seen.strftime('%Y-%m-%d %H:%M')}")
    click.echo(f"Last seen: {profile.last_seen.strftime('%Y-%m-%d %H:%M')}")
    click.echo(f"Total runs (30d): {len(runs)}")
    
    if runs:
        # Calculate uptime percentage
        healthy = sum(1 for r in runs if '✅' in r.get('verdict', '') or 'Connected' in r.get('verdict', ''))
        uptime = (healthy / len(runs)) * 100 if runs else 0
        click.echo(f"Uptime (30d): {uptime:.1f}%")


@network.command(name="cleanup")
@click.option('--days', default=7, help='Remove offline sessions older than N days')
def cleanup_networks(days):
    """
    Remove old offline network sessions to keep the profile list clean.
    
    Offline sessions are temporary profiles created when the device has
    no network connection. This command removes those that are older than
    the specified number of days.
    
    Examples:
        uite network cleanup               # Remove sessions older than 7 days
        uite network cleanup --days 30     # Remove sessions older than 30 days
        uite network cleanup --days 0      # Remove all offline sessions
    """
    manager = NetworkProfileManager()
    profiles = manager.list_profiles()
    
    removed = 0
    now = datetime.now()
    
    # Iterate through profiles and remove old offline sessions
    for pid, profile in list(manager.profiles.items()):
        # Check if this is an offline network
        is_offline = (pid == "offline-state" or 
                     (hasattr(profile, 'is_offline_network') and profile.is_offline_network) or
                     profile.name == "Offline State" or 
                     "offline" in profile.name.lower())
        
        if is_offline:
            age = (now - profile.last_seen).days
            if age >= days:
                del manager.profiles[pid]
                removed += 1
    
    if removed > 0:
        manager.save()
        click.echo(f"✅ Removed {removed} old offline session(s)")
    else:
        click.echo("No old offline sessions to remove")


# Export the command group for registration in main CLI
__all__ = ['network']
