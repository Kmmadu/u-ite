"""Service management commands for U-ITE"""
import click
from uite.service import ServiceManager

@click.group()
def service():
    """Manage U-ITE background service"""
    pass

@service.command()
def install():
    """Install U-ITE as a background service"""
    try:
        ServiceManager.install()
    except Exception as e:
        click.echo(f"❌ Failed to install service: {e}")

@service.command()
def uninstall():
    """Uninstall U-ITE background service"""
    try:
        ServiceManager.uninstall()
    except Exception as e:
        click.echo(f"❌ Failed to uninstall service: {e}")

@service.command()
def start():
    """Start U-ITE service"""
    try:
        ServiceManager.start()
        click.echo("✅ Service started")
    except Exception as e:
        click.echo(f"❌ Failed to start service: {e}")

@service.command()
def stop():
    """Stop U-ITE service"""
    try:
        ServiceManager.stop()
        click.echo("✅ Service stopped")
    except Exception as e:
        click.echo(f"❌ Failed to stop service: {e}")

@service.command()
def status():
    """Check service status"""
    try:
        status = ServiceManager.status()
        click.echo(status)
    except Exception as e:
        click.echo(f"❌ Failed to get status: {e}")

@service.command()
def logs():
    """View service logs"""
    from uite.core.platform import OS, Platform
    from pathlib import Path
    
    platform = OS.get_platform()
    
    if platform == Platform.LINUX:
        log_file = Path.home() / ".local" / "share" / "uite" / "logs" / "uite.log"
    elif platform == Platform.MACOS:
        log_file = Path.home() / "Library" / "Logs" / "uite.log"
    elif platform == Platform.WINDOWS:
        log_file = Path.home() / "AppData" / "Local" / "uite" / "logs" / "uite.log"
    else:
        click.echo("❌ Unsupported platform")
        return
    
    if log_file.exists():
        click.echo(log_file.read_text())
    else:
        click.echo("No logs found")
