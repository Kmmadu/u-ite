"""
macOS Service Management for U-ITE
====================================
Provides macOS-specific service management using launchd, the native service
manager on macOS. This module handles installation, uninstallation, and
control of U-ITE as a launchd agent.

Launchd is the equivalent of systemd on Linux - it manages daemons and
agents that run in the background. This module creates a LaunchAgent
that runs U-ITE automatically when the user logs in.

Features:
- Creates LaunchAgent plist file
- Auto-starts on user login
- Keeps the service alive if it crashes
- Proper log redirection to macOS standard locations
- Clean uninstall that removes all traces
"""

import subprocess
import sys
import plistlib
from pathlib import Path

# Service identifiers
SERVICE_NAME = "com.uite.daemon"  # Reverse-DNS style identifier (standard on macOS)
SERVICE_FILE = Path.home() / "Library" / "LaunchAgents" / f"{SERVICE_NAME}.plist"
# macOS LaunchAgents directory: ~/Library/LaunchAgents/


def get_service_content():
    """
    Generate the launchd plist configuration.
    
    The plist file defines how launchd should manage the service:
    - Program to run (Python + orchestrator)
    - Auto-start at login
    - Keep alive if it crashes
    - Log file locations
    - Working directory
    
    Returns:
        dict: Plist-compatible dictionary with service configuration
        
    Note:
        The plist format is XML, but plistlib handles the conversion.
    """
    python_path = sys.executable  # Path to current Python interpreter
    uite_path = Path(__file__).parent.parent.parent  # Project root
    
    return {
        # Service identifier (must match filename)
        'Label': SERVICE_NAME,
        
        # Command to run: python -m uite.daemon.orchestrator
        'ProgramArguments': [python_path, '-m', 'uite.daemon.orchestrator'],
        
        # Start immediately after loading
        'RunAtLoad': True,
        
        # Keep the service running (restart if it exits)
        'KeepAlive': True,
        
        # Standard output log (U-ITE's console output)
        'StandardOutPath': str(Path.home() / "Library" / "Logs" / "uite.log"),
        
        # Standard error log (for crashes and errors)
        'StandardErrorPath': str(Path.home() / "Library" / "Logs" / "uite.error.log"),
        
        # Working directory (where to run from)
        'WorkingDirectory': str(uite_path),
    }


def install():
    """
    Install U-ITE as a launchd agent.
    
    This function:
    1. Generates the plist configuration
    2. Writes it to ~/Library/LaunchAgents/com.uite.daemon.plist
    3. Loads the service with launchctl
    
    After installation, U-ITE will:
    - Start automatically when you log in
    - Run continuously in the background
    - Restart if it crashes
    - Log to ~/Library/Logs/uite.log
    
    Returns:
        None
        
    Example:
        >>> from uite.service.darwin import install
        >>> install()
        '✅ U-ITE service installed and started'
    """
    content = get_service_content()
    
    # Write plist file (binary plist format)
    with open(SERVICE_FILE, 'wb') as f:
        plistlib.dump(content, f)
    
    # Load the service with launchctl
    # This starts it immediately and enables auto-start
    subprocess.run(["launchctl", "load", str(SERVICE_FILE)])
    
    print(f"✅ U-ITE service installed and started")


def uninstall():
    """
    Uninstall U-ITE launchd agent.
    
    This function:
    1. Unloads the service (stops it and disables auto-start)
    2. Removes the plist file
    
    After uninstallation, U-ITE will no longer run in the background.
    
    Returns:
        None
        
    Example:
        >>> from uite.service.darwin import uninstall
        >>> uninstall()
        '✅ U-ITE service uninstalled'
    """
    # Unload the service (stops it and removes from launchd)
    subprocess.run(["launchctl", "unload", str(SERVICE_FILE)])
    
    # Remove the plist file (cleanup)
    SERVICE_FILE.unlink(missing_ok=True)
    
    print(f"✅ U-ITE service uninstalled")


def start():
    """
    Start the U-ITE service without changing auto-start settings.
    
    This is useful if the service is installed but currently stopped.
    
    Returns:
        None
        
    Example:
        >>> from uite.service.darwin import start
        >>> start()
    """
    subprocess.run(["launchctl", "start", SERVICE_NAME])


def stop():
    """
    Stop the U-ITE service without uninstalling.
    
    The service will remain installed but won't run until started again
    or until next login (if auto-start is enabled).
    
    Returns:
        None
        
    Example:
        >>> from uite.service.darwin import stop
        >>> stop()
    """
    subprocess.run(["launchctl", "stop", SERVICE_NAME])


def status():
    """
    Check if the U-ITE service is running.
    
    Returns the raw output of `launchctl list` for this service.
    
    Returns:
        str: Launchctl output containing service status
        
    Example:
        >>> from uite.service.darwin import status
        >>> print(status())
        {
            "Label" = "com.uite.daemon";
            "PID" = 12345;
            "Status" = 0;
        }
    """
    result = subprocess.run(
        ["launchctl", "list", SERVICE_NAME], 
        capture_output=True, 
        text=True
    )
    return result.stdout


# ============================================================================
# Utility Functions
# ============================================================================

def is_installed() -> bool:
    """
    Check if the service is installed.
    
    Returns:
        bool: True if plist file exists, False otherwise
        
    Example:
        >>> if is_installed():
        ...     print("Service is installed")
    """
    return SERVICE_FILE.exists()


def get_log_paths() -> dict:
    """
    Get the paths to service log files.
    
    Returns:
        dict: Contains 'stdout' and 'stderr' log paths
        
    Example:
        >>> logs = get_log_paths()
        >>> print(logs['stdout'])
        '/Users/username/Library/Logs/uite.log'
    """
    return {
        'stdout': Path.home() / "Library" / "Logs" / "uite.log",
        'stderr': Path.home() / "Library" / "Logs" / "uite.error.log"
    }


# Export public interface
__all__ = [
    'install', 
    'uninstall', 
    'start', 
    'stop', 
    'status',
    'is_installed',
    'get_log_paths'
]
