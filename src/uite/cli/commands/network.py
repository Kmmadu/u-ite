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
    """List all detected networks"""
    manager = NetworkProfileManager()
    profiles = manager.list_profiles()
    
    if not profiles:
        click.echo("No networks detected yet. Run the observer first.")
        return
    
    table = []
    for p in profiles:
        # Format tags
        tags_display = ", ".join(p.tags) if p.tags else ""
        
        # Calculate total runs (you might want to add this to the profile)
        total_runs = getattr(p, 'total_runs', 'N/A')
        
        table.append([
            p.network_id[:8],  # Short ID
            p.name,
            p.provider or "Unknown",
            tags_display,
            p.first_seen.strftime("%Y-%m-%d %H:%M"),
            p.last_seen.strftime("%Y-%m-%d %H:%M"),
            total_runs
        ])
    
    click.echo("\n📡 Detected Networks:")
    click.echo(tabulate(
        table,
        headers=["ID", "Name", "Provider", "Tags", "First Seen", "Last Seen", "Runs"],
        tablefmt="grid"
    ))
    
    # Show usage tips
    click.echo("\n💡 Tips:")
    click.echo("  • Rename: uite network rename <ID> \"New Name\"")
    click.echo("  • Set provider: uite network provider <ID> \"ISP Name\"")
    click.echo("  • Add tag: uite network tag <ID> <tag>")
    click.echo("  • View stats: uite by-network <name/ID/tag> --days 30")

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

# Export the group
__all__ = ['network']
