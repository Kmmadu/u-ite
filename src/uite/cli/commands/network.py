import click
from tabulate import tabulate
from uite.core.network_profile import NetworkProfileManager
from datetime import datetime

@click.group()
def network():
    """Manage network profiles"""
    pass

@network.command(name="list")
def list_networks():
    """List all networks the device has connected to"""
    manager = NetworkProfileManager()
    profiles = manager.list_profiles()
    
    if not profiles:
        click.echo("No networks detected yet. Run the observer first.")
        return
    
    # Filter to show ONLY networks that were actually connected to
    connected_networks = []
    for p in profiles:
        # Skip anything that's clearly not a real network
        if p.network_id == "offline-state":
            continue
        if hasattr(p, 'is_offline_network') and p.is_offline_network:
            continue
        if p.name == "Offline State" or "offline" in p.name.lower():
            continue
        
        # Check if this network has ever had a successful connection
        # If it has a provider set or tags, it's been manually managed (so it's real)
        if p.provider and p.provider != "Unknown":
            connected_networks.append(p)
            continue
            
        if p.tags:
            connected_networks.append(p)
            continue
        
        # If it has a proper hash ID (16+ chars) and doesn't start with "offline"
        if p.network_id and len(p.network_id) >= 8 and not p.network_id.startswith("offline"):
            # This is likely a real network
            connected_networks.append(p)
    
    if not connected_networks:
        click.echo("No connected networks found. Run the observer while connected to WiFi.")
        return
    
    # Sort by last seen (most recent first)
    connected_networks.sort(key=lambda x: x.last_seen, reverse=True)
    
    table = []
    for p in connected_networks:
        # Format tags
        tags_display = ", ".join(p.tags) if p.tags else ""
        
        # Format last seen nicely
        last_seen = p.last_seen.strftime("%Y-%m-%d %H:%M")
        days_ago = (datetime.now() - p.last_seen).days
        if days_ago == 0:
            last_seen_display = f"{last_seen} (today)"
        elif days_ago == 1:
            last_seen_display = f"{last_seen} (yesterday)"
        else:
            last_seen_display = f"{last_seen} ({days_ago} days ago)"
        
        table.append([
            p.network_id[:8],  # Short ID
            p.name,
            p.provider or "Unknown",
            tags_display,
            p.first_seen.strftime("%Y-%m-%d"),
            last_seen_display
        ])
    
    click.echo(f"\n📡 Connected Networks ({len(connected_networks)}):")
    click.echo(tabulate(
        table,
        headers=["ID", "Name", "Provider", "Tags", "First Seen", "Last Seen"],
        tablefmt="grid"
    ))
    
    # Show count of filtered offline sessions if any
    filtered_count = len(profiles) - len(connected_networks)
    if filtered_count > 0:
        click.echo(f"\nℹ️  {filtered_count} offline session(s) not shown")
    
    # Show usage tips
    click.echo("\n💡 Tips:")
    click.echo("  • Rename: uite network rename <ID> \"New Name\"")
    click.echo("  • Set provider: uite network provider <ID> \"ISP Name\"")
    click.echo("  • Add tag: uite network tag <ID> <tag>")
    click.echo("  • View stats: uite by-network <name/ID/tag> --days 30")

@network.command(name="list-all")
def list_all_networks():
    """List all networks including offline sessions"""
    manager = NetworkProfileManager()
    profiles = manager.list_profiles()
    
    if not profiles:
        click.echo("No networks detected yet.")
        return
    
    # Separate connected and offline
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
    
    # Show offline sessions
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
    """Rename a network"""
    manager = NetworkProfileManager()
    
    # Try to find by full ID or prefix
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
    """Set provider for a network"""
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
    """Add a tag to a network (e.g., primary, backup, work)"""
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
    """Show detailed stats for a network"""
    from uite.storage.history import HistoricalData
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
    
    click.echo(f"\n📊 Network Statistics: {profile.name}")
    click.echo("=" * 50)
    click.echo(f"ID: {found}")
    click.echo(f"Provider: {profile.provider or 'Not set'}")
    click.echo(f"Tags: {', '.join(profile.tags) if profile.tags else 'None'}")
    click.echo(f"First seen: {profile.first_seen.strftime('%Y-%m-%d %H:%M')}")
    click.echo(f"Last seen: {profile.last_seen.strftime('%Y-%m-%d %H:%M')}")
    click.echo(f"Total runs (30d): {len(runs)}")
    
    if runs:
        # Calculate uptime
        healthy = sum(1 for r in runs if '✅' in r.get('verdict', '') or 'Connected' in r.get('verdict', ''))
        uptime = (healthy / len(runs)) * 100 if runs else 0
        click.echo(f"Uptime (30d): {uptime:.1f}%")

@network.command(name="cleanup")
@click.option('--days', default=7, help='Remove offline sessions older than N days')
def cleanup_networks(days):
    """Remove old offline network sessions"""
    manager = NetworkProfileManager()
    profiles = manager.list_profiles()
    
    removed = 0
    now = datetime.now()
    
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

# Export the group
__all__ = ['network']
