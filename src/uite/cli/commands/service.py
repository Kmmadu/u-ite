"""
Service Management Commands for U-ITE
======================================
Provides commands to manage U-ITE as a background system service/daemon.
Supports all major operating systems with platform-specific implementations.

Features:
- Cross-platform service management (Linux, macOS, Windows)
- Check service status
- Enable/disable auto-start on boot
- Start/stop background monitoring
- View service logs
- Platform-appropriate service commands
"""

import click
import subprocess
import time
from pathlib import Path
from uite.core.platform import OS, Platform


@click.group()
def service():
    """
    Manage U-ITE as a background system service.
    
    This command group handles running U-ITE as a proper system service/daemon
    that starts automatically on boot and runs continuously in the background.
    
    Unlike the 'daemon' command (which runs in foreground for testing),
    this is for production use.
    
    Examples:
        uite service enable --auto-start    # Install and enable auto-start
        uite service status                  # Check if running
        uite service logs                    # View logs
        uite service disable                  # Stop and remove
    """
    pass


@service.command()
def status():
    """
    Check if U-ITE is running as a background service.
    
    Uses platform-specific commands:
    - Linux: systemctl --user is-active uite
    - macOS: launchctl list com.uite.observer
    - Windows: sc query U-ITE
    
    Examples:
        uite service status
    """
    platform = OS.get_platform()
    
    if platform == Platform.LINUX:
        # Linux: Check systemd user service status
        result = subprocess.run(
            ["systemctl", "--user", "is-active", "uite"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            click.echo("✅ U-ITE is running")
        else:
            click.echo("❌ U-ITE is not running")
    
    elif platform == Platform.MACOS:
        # macOS: Check launchd service status
        result = subprocess.run(
            ["launchctl", "list", "com.uite.observer"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            click.echo("✅ U-ITE is running")
        else:
            click.echo("❌ U-ITE is not running")
    
    elif platform == Platform.WINDOWS:
        # Windows: Check Windows service status
        result = subprocess.run(
            ["sc", "query", "U-ITE"],
            capture_output=True, text=True
        )
        if "RUNNING" in result.stdout:
            click.echo("✅ U-ITE is running")
        else:
            click.echo("❌ U-ITE is not running")
    
    else:
        click.echo("❌ Unsupported platform")


@service.command()
@click.option('--auto-start', is_flag=True, help='Install and enable auto-start on boot')
def enable(auto_start):
    """
    Enable background monitoring service.
    
    Two modes:
    - Without --auto-start: Just start the service now
    - With --auto-start: Install service and enable auto-start on boot
    
    Examples:
        uite service enable                    # Start service now
        uite service enable --auto-start       # Install and enable auto-start
    """
    if auto_start:
        # Full installation with auto-start
        from uite.service.install import install_auto_start
        install_auto_start()
    else:
        # Just start existing service (no auto-start)
        platform = OS.get_platform()
        
        if platform == Platform.LINUX:
            subprocess.run(["systemctl", "--user", "start", "uite"])
            click.echo("✅ U-ITE service started")
            
        elif platform == Platform.MACOS:
            subprocess.run(["launchctl", "start", "com.uite.observer"])
            click.echo("✅ U-ITE service started")
            
        elif platform == Platform.WINDOWS:
            subprocess.run(["sc", "start", "U-ITE"])
            click.echo("✅ U-ITE service started")
            
        else:
            click.echo("❌ Unsupported platform")


@service.command()
def disable():
    """
    Stop background monitoring and disable auto-start.
    
    This command:
    - Stops the running service
    - Disables auto-start on boot
    - Removes the service configuration
    
    Examples:
        uite service disable
    """
    platform = OS.get_platform()
    
    if platform == Platform.LINUX:
        # Linux: Stop and disable systemd user service
        subprocess.run(["systemctl", "--user", "stop", "uite"])
        subprocess.run(["systemctl", "--user", "disable", "uite"])
        click.echo("✅ U-ITE service stopped and disabled")
        
    elif platform == Platform.MACOS:
        # macOS: Unload launchd service
        plist = Path.home() / "Library/LaunchAgents/com.uite.observer.plist"
        if plist.exists():
            subprocess.run(["launchctl", "unload", str(plist)])
            plist.unlink()  # Remove the plist file
            click.echo("✅ U-ITE service stopped and disabled")
        else:
            click.echo("❌ Service not found")
            
    elif platform == Platform.WINDOWS:
        # Windows: Stop and delete service
        subprocess.run(["sc", "stop", "U-ITE"])
        subprocess.run(["sc", "delete", "U-ITE"])
        click.echo("✅ U-ITE service stopped and disabled")
        
    else:
        click.echo("❌ Unsupported platform")


@service.command()
def logs():
    """
    View U-ITE service logs.
    
    Shows the last 50 lines of the service log file.
    Log locations vary by platform:
    - Linux:   ~/.local/share/uite/logs/uite.log
    - macOS:   ~/Library/Logs/uite.log
    - Windows: ~/AppData/Local/uite/logs/uite.log
    
    Examples:
        uite service logs
    """
    platform = OS.get_platform()
    
    # Determine log file location based on platform
    if platform == Platform.LINUX:
        log_file = Path.home() / ".local/share/uite/logs/uite.log"
    elif platform == Platform.MACOS:
        log_file = Path.home() / "Library/Logs/uite.log"
    elif platform == Platform.WINDOWS:
        log_file = Path.home() / "AppData/Local/uite/logs/uite.log"
    else:
        click.echo("❌ Unsupported platform")
        return
    
    # Check if log file exists and display last 50 lines
    if log_file.exists():
        click.echo(f"\n📄 Last 50 lines from: {log_file}")
        click.echo("-" * 60)
        
        with open(log_file, 'r') as f:
            lines = f.readlines()
            # Show last 50 lines (or all if less than 50)
            start_idx = max(0, len(lines) - 50)
            for line in lines[start_idx:]:
                click.echo(line.strip())
        
        click.echo("-" * 60)
        click.echo(f"📁 Full log: {log_file}")
    else:
        click.echo("No logs found. Is U-ITE running?")
        click.echo(f"Checked: {log_file}")


# Note: The actual service installation (auto-start) is handled by
# the install_auto_start() function imported from uite.service.install
# This separation keeps the CLI clean while allowing platform-specific
# installation logic to be maintained separately.


# Export the command group for registration in main CLI
__all__ = ['service']
