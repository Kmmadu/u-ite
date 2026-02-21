"""Service management commands for U-ITE"""
import click
import subprocess
import time
from uite.core.platform import OS, Platform

@click.group()
def service():
    """Manage U-ITE background service"""
    pass

@service.command()
def status():
    """Check if U-ITE is running in background"""
    platform = OS.get_platform()
    
    if platform == Platform.LINUX:
        result = subprocess.run(
            ["systemctl", "--user", "is-active", "uite"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            click.echo("✅ U-ITE is running")
        else:
            click.echo("❌ U-ITE is not running")
    
    elif platform == Platform.MACOS:
        result = subprocess.run(
            ["launchctl", "list", "com.uite.observer"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            click.echo("✅ U-ITE is running")
        else:
            click.echo("❌ U-ITE is not running")
    
    elif platform == Platform.WINDOWS:
        result = subprocess.run(
            ["sc", "query", "U-ITE"],
            capture_output=True, text=True
        )
        if "RUNNING" in result.stdout:
            click.echo("✅ U-ITE is running")
        else:
            click.echo("❌ U-ITE is not running")

@service.command()
@click.option('--auto-start', is_flag=True, help='Start automatically on boot')
def enable(auto_start):
    """Enable background monitoring"""
    if auto_start:
        from uite.service.install import install_auto_start
        install_auto_start()
    else:
        # Just start now, not on boot
        platform = OS.get_platform()
        if platform == Platform.LINUX:
            subprocess.run(["systemctl", "--user", "start", "uite"])
        elif platform == Platform.MACOS:
            subprocess.run(["launchctl", "start", "com.uite.observer"])
        elif platform == Platform.WINDOWS:
            subprocess.run(["sc", "start", "U-ITE"])
        click.echo("✅ U-ITE started")

@service.command()
def disable():
    """Stop background monitoring"""
    platform = OS.get_platform()
    
    if platform == Platform.LINUX:
        subprocess.run(["systemctl", "--user", "stop", "uite"])
        subprocess.run(["systemctl", "--user", "disable", "uite"])
    elif platform == Platform.MACOS:
        plist = Path.home() / "Library/LaunchAgents/com.uite.observer.plist"
        subprocess.run(["launchctl", "unload", str(plist)])
    elif platform == Platform.WINDOWS:
        subprocess.run(["sc", "stop", "U-ITE"])
        subprocess.run(["sc", "delete", "U-ITE"])
    
    click.echo("✅ U-ITE stopped and disabled")

@service.command()
def logs():
    """View U-ITE logs"""
    from pathlib import Path
    from uite.core.platform import OS, Platform
    
    platform = OS.get_platform()
    
    if platform == Platform.LINUX:
        log_file = Path.home() / ".local/share/uite/logs/uite.log"
    elif platform == Platform.MACOS:
        log_file = Path.home() / "Library/Logs/uite.log"
    elif platform == Platform.WINDOWS:
        log_file = Path.home() / "AppData/Local/uite/logs/uite.log"
    else:
        click.echo("❌ Unsupported platform")
        return
    
    if log_file.exists():
        # Show last 50 lines
        with open(log_file, 'r') as f:
            lines = f.readlines()[-50:]
            for line in lines:
                click.echo(line.strip())
    else:
        click.echo("No logs found. Is U-ITE running?")
