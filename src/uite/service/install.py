"""
Auto-Start Service Installation Module for U-ITE
==================================================
Provides direct service installation functions for all supported platforms.
This module handles the low-level details of creating and enabling system
services on Linux (systemd), macOS (launchd), and Windows (nssm).

This module is used by the service management system to implement the
'--auto-start' option when enabling the U-ITE service.

Relationship to other service modules:
- service/__init__.py: Provides unified ServiceManager interface
- service/linux.py: Contains Linux-specific service functions
- service/darwin.py: Contains macOS-specific service functions
- service/windows.py: Contains Windows-specific service functions
- service/install.py: (THIS FILE) Auto-start installation helpers

Note: This module focuses specifically on the auto-start installation aspect,
complementing the platform-specific modules which provide full service
management (install, uninstall, start, stop, status).
"""

from uite.core.platform import OS, Platform
import subprocess
import sys
from pathlib import Path
import shutil  # Fixed: Added missing import


def install_auto_start():
    """
    Install U-ITE to start automatically on boot.
    
    This is the main entry point for auto-start installation. It detects
    the current platform and calls the appropriate platform-specific
    installer function.
    
    The service will be:
    - Installed as a user-level service (no sudo required on Linux/macOS)
    - Configured to start automatically on boot/login
    - Started immediately after installation
    
    Returns:
        None
        
    Raises:
        Prints error message if platform is unsupported
        
    Example:
        >>> from uite.service.install import install_auto_start
        >>> install_auto_start()
        '✅ U-ITE auto-start enabled (systemd user service)'
    """
    platform = OS.get_platform()
    
    if platform == Platform.LINUX:
        _install_linux_systemd()
    elif platform == Platform.MACOS:
        _install_macos_launchd()
    elif platform == Platform.WINDOWS:
        _install_windows_service()
    else:
        print("❌ Unsupported platform")
        print(f"   Detected: {platform.value}")


def _install_linux_systemd():
    """
    Install systemd user service on Linux (no sudo needed).
    
    Creates a systemd user service file at:
    ~/.config/systemd/user/uite.service
    
    Service configuration:
    - Starts after network is available
    - Restarts automatically if it crashes
    - Logs to ~/.local/share/uite/logs/uite.log
    - Auto-starts on user login
    
    Returns:
        None
    """
    service_content = f"""[Unit]
Description=U-ITE Network Observer
After=network.target
Documentation=https://github.com/u-ite/docs

[Service]
Type=simple
ExecStart={sys.executable} -m uite.daemon.orchestrator
Restart=always
RestartSec=10
StandardOutput=append:{Path.home()}/.local/share/uite/logs/uite.log
StandardError=append:{Path.home()}/.local/share/uite/logs/uite.error.log

[Install]
WantedBy=default.target
"""
    # Create systemd user directory if it doesn't exist
    service_dir = Path.home() / ".config" / "systemd" / "user"
    service_dir.mkdir(parents=True, exist_ok=True)
    
    service_file = service_dir / "uite.service"
    service_file.write_text(service_content)
    
    # Reload systemd and enable/start the service
    subprocess.run(["systemctl", "--user", "daemon-reload"], check=True)
    subprocess.run(["systemctl", "--user", "enable", "uite"], check=True)
    subprocess.run(["systemctl", "--user", "start", "uite"], check=True)
    
    print("✅ U-ITE auto-start enabled (systemd user service)")
    print(f"   Service file: {service_file}")
    print(f"   Logs: {Path.home()}/.local/share/uite/logs/uite.log")


def _install_macos_launchd():
    """
    Install macOS launchd agent.
    
    Creates a launchd plist file at:
    ~/Library/LaunchAgents/com.uite.observer.plist
    
    Agent configuration:
    - Starts automatically on user login
    - Restarts if it crashes (KeepAlive)
    - Logs to ~/Library/Logs/uite.log
    - Uses standard macOS logging locations
    
    Returns:
        None
    """
    plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.uite.observer</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>{sys.executable}</string>
        <string>-m</string>
        <string>uite.daemon.orchestrator</string>
    </array>
    
    <key>RunAtLoad</key>
    <true/>
    
    <key>KeepAlive</key>
    <true/>
    
    <key>StandardOutPath</key>
    <string>{Path.home()}/Library/Logs/uite.log</string>
    
    <key>StandardErrorPath</key>
    <string>{Path.home()}/Library/Logs/uite.error.log</string>
    
    <key>WorkingDirectory</key>
    <string>{Path(__file__).parent.parent.parent}</string>
</dict>
</plist>
"""
    # Create LaunchAgents directory if it doesn't exist
    plist_dir = Path.home() / "Library" / "LaunchAgents"
    plist_dir.mkdir(parents=True, exist_ok=True)
    
    plist_file = plist_dir / "com.uite.observer.plist"
    plist_file.write_text(plist_content)
    
    # Load the service with launchctl
    subprocess.run(["launchctl", "load", str(plist_file)], check=True)
    
    print("✅ U-ITE auto-start enabled (launchd agent)")
    print(f"   Plist file: {plist_file}")
    print(f"   Logs: {Path.home()}/Library/Logs/uite.log")


def _install_windows_service():
    """
    Install Windows service (requires admin privileges).
    
    Uses nssm (Non-Sucking Service Manager) to create a Windows service.
    Users must install nssm separately from https://nssm.cc/download
    
    Service configuration:
    - Starts automatically on system boot
    - Runs as a Windows service
    - Logs to Windows Event Log
    
    Note:
        This function requires administrative privileges to run.
        nssm must be installed and available in PATH.
    
    Returns:
        None
    """
    # Check if nssm is available
    nssm_path = shutil.which("nssm")
    if not nssm_path:
        print("⚠️  nssm not found. Please install it first:")
        print("   Download from: https://nssm.cc/download")
        print("   Add nssm.exe to your PATH after installation.")
        return
    
    try:
        # Install the service using nssm
        subprocess.run([
            nssm_path, "install", "U-ITE", sys.executable,
            "-m", "uite.daemon.orchestrator"
        ], check=True)
        
        # Set service to auto-start
        subprocess.run(["sc", "config", "U-ITE", "start=", "auto"], check=True)
        
        # Start the service
        subprocess.run(["sc", "start", "U-ITE"], check=True)
        
        print("✅ U-ITE auto-start enabled (Windows service)")
        print("   Service name: U-ITE")
        print("   Use Services.msc to manage or 'sc query U-ITE' to check status")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install Windows service: {e}")
        print("   Make sure you're running as Administrator.")


# ============================================================================
# Utility Functions
# ============================================================================

def check_auto_start_status() -> bool:
    """
    Check if auto-start is currently enabled.
    
    Returns:
        bool: True if auto-start is enabled, False otherwise
        
    Example:
        >>> if check_auto_start_status():
        ...     print("Auto-start is enabled")
    """
    platform = OS.get_platform()
    
    if platform == Platform.LINUX:
        result = subprocess.run(
            ["systemctl", "--user", "is-enabled", "uite"],
            capture_output=True, text=True
        )
        return result.returncode == 0
        
    elif platform == Platform.MACOS:
        plist_file = Path.home() / "Library/LaunchAgents/com.uite.observer.plist"
        return plist_file.exists()
        
    elif platform == Platform.WINDOWS:
        result = subprocess.run(
            ["sc", "qc", "U-ITE"],
            capture_output=True, text=True
        )
        return "AUTO_START" in result.stdout
        
    else:
        return False


def remove_auto_start():
    """
    Remove auto-start configuration (opposite of install_auto_start).
    
    This function disables auto-start without completely uninstalling
    the service. For complete removal, use the platform-specific
    uninstall functions.
    
    Returns:
        None
    """
    platform = OS.get_platform()
    
    if platform == Platform.LINUX:
        subprocess.run(["systemctl", "--user", "disable", "uite"], check=False)
        subprocess.run(["systemctl", "--user", "stop", "uite"], check=False)
        print("✅ Auto-start disabled for Linux systemd service")
        
    elif platform == Platform.MACOS:
        plist_file = Path.home() / "Library/LaunchAgents/com.uite.observer.plist"
        if plist_file.exists():
            subprocess.run(["launchctl", "unload", str(plist_file)], check=False)
            plist_file.unlink()
            print("✅ Auto-start disabled for macOS launchd agent")
        
    elif platform == Platform.WINDOWS:
        subprocess.run(["sc", "config", "U-ITE", "start=", "demand"], check=False)
        print("✅ Auto-start disabled for Windows service")
        
    else:
        print("❌ Unsupported platform")


# Export public interface
__all__ = [
    'install_auto_start',
    'check_auto_start_status',
    'remove_auto_start'
]
