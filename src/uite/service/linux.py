"""
Linux Systemd Service Management for U-ITE
===========================================
Provides systemd service management for Linux platforms. This module handles
installation, uninstallation, and control of U-ITE as a systemd system service.

This implementation installs U-ITE as a system-wide service (requires sudo)
rather than a user service. The service runs as root and starts automatically
at system boot.

Features:
- System-wide service installation (requires sudo)
- Automatic start on boot
- Automatic restart on failure
- Proper logging to systemd journal and log files
- Clean uninstall that removes all traces

Note: For user-level installation without sudo, use the user service approach
      in service/install.py instead.
"""

import subprocess
import sys
from pathlib import Path

# Service configuration
SERVICE_NAME = "uite"
SERVICE_FILE = f"/etc/systemd/system/{SERVICE_NAME}.service"


def get_service_content():
    """
    Generate systemd service file content.
    
    Creates a systemd service unit file with the following characteristics:
    - Runs as root (system service)
    - Starts after network is available
    - Automatically restarts on failure (10s delay)
    - Logs to both systemd journal and log files
    
    Returns:
        str: Systemd service unit file content
        
    Note:
        The service runs with Type=simple, which means systemd considers
        the service started as soon as the process is forked.
    """
    python_path = sys.executable  # Path to current Python interpreter
    uite_path = Path(__file__).parent.parent.parent  # Project root
    
    return f"""[Unit]
Description=U-ITE Network Observer
Documentation=https://github.com/u-ite/docs
After=network.target
Wants=network.target

[Service]
Type=simple
User=root
Group=root
ExecStart={python_path} -m uite.daemon.orchestrator
Restart=always
RestartSec=10
StandardOutput=append:{Path.home()}/.local/share/uite/logs/uite.log
StandardError=append:{Path.home()}/.local/share/uite/logs/uite.error.log
# Also log to journal for easier debugging
StandardOutput=journal+console
StandardError=journal+console

# Security hardening (optional but recommended)
NoNewPrivileges=yes
ProtectHome=yes
ProtectSystem=full
PrivateTmp=yes

[Install]
WantedBy=multi-user.target
"""


def install():
    """
    Install U-ITE as a systemd system service.
    
    This function:
    1. Creates the service unit file in /etc/systemd/system/
    2. Reloads systemd to recognize the new service
    3. Enables the service to start on boot
    4. Starts the service immediately
    
    Requires sudo privileges.
    
    Returns:
        None
        
    Example:
        >>> from uite.service.linux import install
        >>> install()
        '✅ U-ITE service installed and started'
    """
    content = get_service_content()
    
    try:
        # Write service file (requires sudo)
        with open(SERVICE_FILE, 'w') as f:
            f.write(content)
        
        # Reload systemd to recognize new service
        subprocess.run(["sudo", "systemctl", "daemon-reload"], check=True)
        
        # Enable auto-start on boot
        subprocess.run(["sudo", "systemctl", "enable", SERVICE_NAME], check=True)
        
        # Start the service now
        subprocess.run(["sudo", "systemctl", "start", SERVICE_NAME], check=True)
        
        print(f"✅ U-ITE service installed and started")
        print(f"   Service file: {SERVICE_FILE}")
        print(f"   Use 'systemctl status {SERVICE_NAME}' to check status")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install service: {e}")
        print("   Make sure you have sudo privileges.")
    except PermissionError:
        print("❌ Permission denied. Please run with sudo.")
        print("   Try: sudo python -c 'from uite.service.linux import install; install()'")


def uninstall():
    """
    Uninstall U-ITE systemd service completely.
    
    This function:
    1. Stops the service if running
    2. Disables auto-start on boot
    3. Removes the service unit file
    4. Reloads systemd to clean up
    
    Requires sudo privileges.
    
    Returns:
        None
        
    Example:
        >>> from uite.service.linux import uninstall
        >>> uninstall()
        '✅ U-ITE service uninstalled'
    """
    try:
        # Stop the service
        subprocess.run(["sudo", "systemctl", "stop", SERVICE_NAME], check=False)
        
        # Disable auto-start
        subprocess.run(["sudo", "systemctl", "disable", SERVICE_NAME], check=False)
        
        # Remove service file
        subprocess.run(["sudo", "rm", "-f", SERVICE_FILE], check=True)
        
        # Reload systemd
        subprocess.run(["sudo", "systemctl", "daemon-reload"], check=True)
        
        print(f"✅ U-ITE service uninstalled")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to uninstall service: {e}")
    except PermissionError:
        print("❌ Permission denied. Please run with sudo.")


def start():
    """
    Start the U-ITE service.
    
    Starts the service if it's installed but not running.
    Does not change auto-start settings.
    
    Returns:
        None
    """
    try:
        subprocess.run(["sudo", "systemctl", "start", SERVICE_NAME], check=True)
        print(f"✅ Service started")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start service: {e}")


def stop():
    """
    Stop the U-ITE service.
    
    Stops the service if it's running.
    Does not change auto-start settings.
    
    Returns:
        None
    """
    try:
        subprocess.run(["sudo", "systemctl", "stop", SERVICE_NAME], check=True)
        print(f"✅ Service stopped")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to stop service: {e}")


def status():
    """
    Get the current status of the U-ITE service.
    
    Returns the raw output of `systemctl status` for detailed information.
    
    Returns:
        str: Systemd status output
        
    Example:
        >>> status_output = status()
        >>> if "active (running)" in status_output:
        ...     print("Service is running")
    """
    try:
        result = subprocess.run(
            ["systemctl", "status", SERVICE_NAME],
            capture_output=True,
            text=True,
            check=False  # Don't raise on non-zero exit (service may be inactive)
        )
        return result.stdout
    except Exception as e:
        return f"Error getting status: {e}"


# ============================================================================
# Utility Functions
# ============================================================================

def is_installed() -> bool:
    """
    Check if the service is installed.
    
    Returns:
        bool: True if service file exists, False otherwise
        
    Example:
        >>> if is_installed():
        ...     print("Service is installed")
    """
    return Path(SERVICE_FILE).exists()


def is_running() -> bool:
    """
    Check if the service is currently running.
    
    Returns:
        bool: True if service is active, False otherwise
        
    Example:
        >>> if is_running():
        ...     print("Service is running")
    """
    try:
        result = subprocess.run(
            ["systemctl", "is-active", SERVICE_NAME],
            capture_output=True,
            text=True,
            check=False
        )
        return result.returncode == 0
    except:
        return False


def get_logs(lines: int = 50) -> str:
    """
    Get recent service logs from journal.
    
    Args:
        lines: Number of log lines to retrieve
        
    Returns:
        str: Recent log entries
        
    Example:
        >>> print(get_logs(100))
    """
    try:
        result = subprocess.run(
            ["journalctl", "-u", SERVICE_NAME, "-n", str(lines), "--no-pager"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error getting logs: {e}"


# Export public interface
__all__ = [
    'install',
    'uninstall',
    'start',
    'stop',
    'status',
    'is_installed',
    'is_running',
    'get_logs'
]
