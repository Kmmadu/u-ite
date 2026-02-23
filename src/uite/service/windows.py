"""
Windows Service Management for U-ITE
=====================================
Provides Windows service management using both nssm (recommended) and sc.exe.
This module handles installation, uninstallation, and control of U-ITE as a
native Windows service.

Windows services are different from Unix daemons:
- Run in Session 0 (isolated from user sessions)
- Can start automatically at boot
- Managed by the Service Control Manager (SCM)
- Require administrative privileges

This implementation uses nssm (Non-Sucking Service Manager) for better
service management, with fallback options and clear error messages.
"""

import subprocess
import sys
import shutil
from pathlib import Path

# Service configuration
SERVICE_NAME = "U-ITE"
SERVICE_DISPLAY_NAME = "U-ITE Network Observer"
SERVICE_DESCRIPTION = "Continuous network monitoring and diagnostics service"


def find_nssm():
    """
    Locate nssm.exe on the system.
    
    Checks multiple possible locations:
    1. PATH environment variable
    2. Common installation directories
    3. Current working directory
    
    Returns:
        str or None: Path to nssm.exe if found, None otherwise
    """
    # Check PATH first
    nssm_path = shutil.which("nssm")
    if nssm_path:
        return nssm_path
    
    # Check common installation locations
    common_paths = [
        Path("C:/Program Files/nssm/nssm.exe"),
        Path("C:/Program Files (x86)/nssm/nssm.exe"),
        Path.home() / "nssm/nssm.exe",
        Path.cwd() / "nssm.exe",
    ]
    
    for path in common_paths:
        if path.exists():
            return str(path)
    
    return None


def install():
    """
    Install U-ITE as a Windows service.
    
    This function:
    1. Checks for nssm (recommended) or falls back to sc.exe
    2. Creates the service with auto-start configuration
    3. Sets display name and description
    4. Starts the service immediately
    
    Requires administrator privileges.
    
    Returns:
        None
        
    Example:
        >>> from uite.service.windows import install
        >>> install()
        '✅ U-ITE service installed and started'
    """
    python_path = sys.executable
    script_path = Path(__file__).parent.parent.parent / "daemon" / "orchestrator.py"
    
    # Try using nssm first (better service management)
    nssm_path = find_nssm()
    
    try:
        if nssm_path:
            print(f"🔍 Found nssm at: {nssm_path}")
            _install_with_nssm(nssm_path, python_path)
        else:
            print("⚠️  nssm not found. Falling back to sc.exe (limited functionality).")
            print("   For better service management, install nssm from: https://nssm.cc/download")
            _install_with_sc(python_path, script_path)
        
        # Set display name and description
        subprocess.run(
            f'sc config {SERVICE_NAME} displayname= "{SERVICE_DISPLAY_NAME}"',
            shell=True, check=True
        )
        subprocess.run(
            f'sc description {SERVICE_NAME} "{SERVICE_DESCRIPTION}"',
            shell=True, check=True
        )
        
        # Start the service
        subprocess.run(f'sc start {SERVICE_NAME}', shell=True, check=True)
        
        print(f"✅ U-ITE service installed and started")
        print(f"   Service name: {SERVICE_NAME}")
        print(f"   Display name: {SERVICE_DISPLAY_NAME}")
        print(f"   Use Services.msc or 'sc query {SERVICE_NAME}' to check status")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install service: {e}")
        print("   Make sure you're running as Administrator.")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


def _install_with_nssm(nssm_path, python_path):
    """
    Install service using nssm (recommended).
    
    nssm provides better service management features:
    - Automatic restart on failure
    - Rotating log files
    - Environment variable configuration
    
    Args:
        nssm_path: Path to nssm executable
        python_path: Path to Python interpreter
    """
    # Install the service
    subprocess.run([
        nssm_path, "install", SERVICE_NAME, python_path,
        "-m", "uite.daemon.orchestrator"
    ], check=True)
    
    # Set service to auto-start
    subprocess.run([nssm_path, "set", SERVICE_NAME, "Start", "SERVICE_AUTO_START"], check=True)
    
    # Configure restart on failure
    subprocess.run([nssm_path, "set", SERVICE_NAME, "AppRestartDelay", "10000"], check=True)  # 10 seconds
    
    print("✅ Service installed with nssm")


def _install_with_sc(python_path, script_path):
    """
    Install service using sc.exe (built-in, limited functionality).
    
    This is a fallback method when nssm is not available.
    sc.exe has limitations:
    - No automatic restart on failure
    - Limited configuration options
    
    Args:
        python_path: Path to Python interpreter
        script_path: Path to orchestrator script
    """
    # Create the service with sc.exe
    cmd = (
        f'sc create {SERVICE_NAME} '
        f'binPath= "{python_path} -m uite.daemon.orchestrator" '
        f'start= auto '
        f'DisplayName= "{SERVICE_DISPLAY_NAME}"'
    )
    subprocess.run(cmd, shell=True, check=True)
    
    print("✅ Service installed with sc.exe (basic)")


def uninstall():
    """
    Uninstall U-ITE Windows service.
    
    This function:
    1. Stops the service if running
    2. Deletes the service completely
    
    Requires administrator privileges.
    
    Returns:
        None
        
    Example:
        >>> from uite.service.windows import uninstall
        >>> uninstall()
        '✅ U-ITE service uninstalled'
    """
    try:
        # Try to stop the service first (ignore errors if not running)
        subprocess.run(f'sc stop {SERVICE_NAME}', shell=True, check=False)
        
        # Delete the service
        subprocess.run(f'sc delete {SERVICE_NAME}', shell=True, check=True)
        
        print(f"✅ U-ITE service uninstalled")
        
        # Try to clean up nssm if it was used
        nssm_path = find_nssm()
        if nssm_path:
            try:
                subprocess.run([nssm_path, "remove", SERVICE_NAME, "confirm"], check=False)
            except:
                pass  # Ignore nssm cleanup errors
                
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to uninstall service: {e}")
        print("   Make sure you're running as Administrator.")


def start():
    """
    Start the U-ITE service.
    
    Starts the service if it's installed but not running.
    
    Returns:
        None
    """
    try:
        subprocess.run(f'sc start {SERVICE_NAME}', shell=True, check=True)
        print(f"✅ Service started")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start service: {e}")


def stop():
    """
    Stop the U-ITE service.
    
    Stops the service if it's running.
    
    Returns:
        None
    """
    try:
        subprocess.run(f'sc stop {SERVICE_NAME}', shell=True, check=True)
        print(f"✅ Service stopped")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to stop service: {e}")


def status():
    """
    Get the current status of the U-ITE service.
    
    Returns the raw output of `sc query` for detailed information.
    
    Returns:
        str: Service status information
        
    Example:
        >>> status_output = status()
        >>> if "RUNNING" in status_output:
        ...     print("Service is running")
    """
    try:
        result = subprocess.run(
            f'sc query {SERVICE_NAME}',
            shell=True,
            capture_output=True,
            text=True,
            check=False
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
        bool: True if service exists, False otherwise
        
    Example:
        >>> if is_installed():
        ...     print("Service is installed")
    """
    result = subprocess.run(
        f'sc query {SERVICE_NAME}',
        shell=True,
        capture_output=True,
        text=True,
        check=False
    )
    return result.returncode == 0


def is_running() -> bool:
    """
    Check if the service is currently running.
    
    Returns:
        bool: True if service is running, False otherwise
        
    Example:
        >>> if is_running():
        ...     print("Service is running")
    """
    status_output = status()
    return "RUNNING" in status_output


def get_config() -> dict:
    """
    Get service configuration.
    
    Returns:
        dict: Service configuration parameters
        
    Example:
        >>> config = get_config()
        >>> print(config['START_TYPE'])
    """
    result = subprocess.run(
        f'sc qc {SERVICE_NAME}',
        shell=True,
        capture_output=True,
        text=True,
        check=False
    )
    
    config = {}
    for line in result.stdout.split('\n'):
        if ':' in line:
            key, value = line.split(':', 1)
            config[key.strip()] = value.strip()
    
    return config


# Export public interface
__all__ = [
    'install',
    'uninstall',
    'start',
    'stop',
    'status',
    'is_installed',
    'is_running',
    'get_config'
]
