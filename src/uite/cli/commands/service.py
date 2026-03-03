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
from uite.service import ServiceManager


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
            click.echo("[OK] U-ITE is running")
        else:
            click.echo("[ERROR] U-ITE is not running")
    
    elif platform == Platform.MACOS:
        # macOS: Check launchd service status
        result = subprocess.run(
            ["launchctl", "list", "com.uite.observer"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            click.echo("[OK] U-ITE is running")
        else:
            click.echo("[ERROR] U-ITE is not running")
    
    elif platform == Platform.WINDOWS:
        # Use ServiceManager for consistent status
        if ServiceManager.status() == "running":
            click.echo("[OK] U-ITE is running")
        else:
            click.echo("[ERROR] U-ITE is not running")
    
    else:
        click.echo("[ERROR] Unsupported platform")


@service.command()
@click.option('--auto-start', is_flag=True, help='Install and enable auto-start on boot')
def enable(auto_start):
    """
    Enable background monitoring service.
    
    Two modes:
    - Without --auto-start: Just start the service now
    - With --auto-start: Install service and enable auto-start on boot
    
    On Windows, auto-start uses bundled nssm.exe for better reliability.
    
    Examples:
        uite service enable                    # Start service now
        uite service enable --auto-start       # Install and enable auto-start
    """
    platform = OS.get_platform()
    
    if platform == Platform.WINDOWS:
        if auto_start:
            # Windows with auto-start using bundled nssm
            click.echo("[INFO] Installing U-ITE as Windows service with auto-start...")
            click.echo("   Note: Administrator privileges required")
            
            try:
                from uite.service.windows_nssm import install
                install()
            except ImportError as e:
                click.echo(f"[ERROR] Failed to load nssm module: {e}")
                click.echo("   Falling back to basic service...")
                ServiceManager.install(auto_start=False)
        else:
            # Windows without auto-start (simple background)
            click.echo("[INFO] Starting U-ITE as background process...")
            from uite.service.windows import start_simple_background
            start_simple_background()
            click.echo("[OK] U-ITE background service started")
            click.echo("   Note: Service will stop when you reboot")
            click.echo("   For auto-start on boot, use: uite service enable --auto-start")
    
    elif platform == Platform.LINUX:
        if auto_start:
            # Linux with auto-start
            from uite.service.linux import install
            install()
            click.echo("[OK] U-ITE service installed with auto-start")
        else:
            # Linux without auto-start
            subprocess.run(["systemctl", "--user", "start", "uite"])
            click.echo("[OK] U-ITE service started")
    
    elif platform == Platform.MACOS:
        if auto_start:
            # macOS with auto-start
            from uite.service.darwin import install
            install()
            click.echo("[OK] U-ITE service installed with auto-start")
        else:
            # macOS without auto-start
            subprocess.run(["launchctl", "start", "com.uite.observer"])
            click.echo("[OK] U-ITE service started")
    
    else:
        click.echo("[ERROR] Unsupported platform")


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
        click.echo("[OK] U-ITE service stopped and disabled")
        
    elif platform == Platform.MACOS:
        # macOS: Unload launchd service
        plist = Path.home() / "Library/LaunchAgents/com.uite.observer.plist"
        if plist.exists():
            subprocess.run(["launchctl", "unload", str(plist)])
            plist.unlink()  # Remove the plist file
            click.echo("[OK] U-ITE service stopped and disabled")
        else:
            click.echo("[ERROR] Service not found")
            
    elif platform == Platform.WINDOWS:
        # Windows: Use nssm uninstall if available
        try:
            from uite.service.windows_nssm import uninstall
            uninstall()
        except ImportError:
            # Fall back to sc.exe
            subprocess.run(["sc", "stop", "U-ITE"], capture_output=True)
            subprocess.run(["sc", "delete", "U-ITE"], capture_output=True)
            click.echo("[OK] U-ITE service stopped and disabled")
        
    else:
        click.echo("[ERROR] Unsupported platform")


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
        click.echo("[ERROR] Unsupported platform")
        return
    
    # Check if log file exists and display last 50 lines
    if log_file.exists():
        click.echo(f"\n[LOGS] Last 50 lines from: {log_file}")
        click.echo("-" * 60)
        
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            # Show last 50 lines (or all if less than 50)
            start_idx = max(0, len(lines) - 50)
            for line in lines[start_idx:]:
                click.echo(line.strip())
        
        click.echo("-" * 60)
        click.echo(f"[PATH] Full log: {log_file}")
    else:
        click.echo("No logs found. Is U-ITE running?")
        click.echo(f"Checked: {log_file}")


# Export the command group for registration in main CLI
__all__ = ['service']