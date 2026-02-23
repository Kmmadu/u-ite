"""
OS Service Management for U-ITE
=================================
Provides a unified interface for managing U-ITE as a system service across
all supported platforms (Linux, macOS, Windows).

This module acts as a facade/decorator that:
1. Detects the current operating system
2. Dynamically imports the appropriate platform-specific module
3. Delegates service operations to that module
4. Presents a consistent API to the rest of the application

This allows the CLI and other components to use simple service commands
without worrying about platform differences.
"""

from uite.core.platform import OS, Platform


class ServiceManager:
    """
    Unified service manager for all platforms.
    
    This class provides static methods for all service operations.
    It automatically selects the correct platform-specific implementation
    based on the current OS.
    
    Usage:
        >>> from uite.service import ServiceManager
        >>> ServiceManager.install()   # Install service on current platform
        >>> ServiceManager.start()      # Start the service
        >>> ServiceManager.status()     # Check service status
    
    Platform-specific implementations are in:
    - linux.py   (systemd)
    - darwin.py  (launchd)
    - windows.py (Windows Service)
    """
    
    @staticmethod
    def install():
        """
        Install U-ITE as a system service with auto-start.
        
        This performs a full installation:
        - Creates the necessary service configuration files
        - Enables auto-start on boot
        - Starts the service immediately
        
        Platform-specific actions:
        - Linux: Creates systemd user service
        - macOS: Creates launchd agent
        - Windows: Creates Windows Service
        
        Returns:
            None
            
        Raises:
            Exception: If platform is unsupported
            
        Example:
            >>> ServiceManager.install()
        """
        platform = OS.get_platform()
        
        # Dynamically import the appropriate platform module
        if platform == Platform.LINUX:
            from .linux import install
        elif platform == Platform.MACOS:
            from .darwin import install
        elif platform == Platform.WINDOWS:
            from .windows import install
        else:
            raise Exception(f"Unsupported platform: {platform}")
        
        # Delegate to platform-specific implementation
        install()
    
    @staticmethod
    def uninstall():
        """
        Uninstall U-ITE service completely.
        
        This removes all traces of the service:
        - Stops the service if running
        - Disables auto-start
        - Removes service configuration files
        
        Returns:
            None
            
        Raises:
            Exception: If platform is unsupported
            
        Example:
            >>> ServiceManager.uninstall()
        """
        platform = OS.get_platform()
        
        if platform == Platform.LINUX:
            from .linux import uninstall
        elif platform == Platform.MACOS:
            from .darwin import uninstall
        elif platform == Platform.WINDOWS:
            from .windows import uninstall
        else:
            raise Exception(f"Unsupported platform: {platform}")
        
        uninstall()
    
    @staticmethod
    def start():
        """
        Start the U-ITE service.
        
        This starts the service if it's installed but not running.
        Does not change auto-start settings.
        
        Returns:
            None
            
        Raises:
            Exception: If platform is unsupported
            
        Example:
            >>> ServiceManager.start()
        """
        platform = OS.get_platform()
        
        if platform == Platform.LINUX:
            from .linux import start
        elif platform == Platform.MACOS:
            from .darwin import start
        elif platform == Platform.WINDOWS:
            from .windows import start
        else:
            raise Exception(f"Unsupported platform: {platform}")
        
        start()
    
    @staticmethod
    def stop():
        """
        Stop the U-ITE service.
        
        This stops the service if it's running.
        Does not change auto-start settings.
        
        Returns:
            None
            
        Raises:
            Exception: If platform is unsupported
            
        Example:
            >>> ServiceManager.stop()
        """
        platform = OS.get_platform()
        
        if platform == Platform.LINUX:
            from .linux import stop
        elif platform == Platform.MACOS:
            from .darwin import stop
        elif platform == Platform.WINDOWS:
            from .windows import stop
        else:
            raise Exception(f"Unsupported platform: {platform}")
        
        stop()
    
    @staticmethod
    def status():
        """
        Check the status of the U-ITE service.
        
        Returns platform-specific status information:
        - Linux: systemctl status output
        - macOS: launchctl list output
        - Windows: sc query output
        
        Returns:
            str: Platform-specific status information
            
        Raises:
            Exception: If platform is unsupported
            
        Example:
            >>> status = ServiceManager.status()
            >>> if "running" in status.lower():
            ...     print("Service is running")
        """
        platform = OS.get_platform()
        
        if platform == Platform.LINUX:
            from .linux import status
        elif platform == Platform.MACOS:
            from .darwin import status
        elif platform == Platform.WINDOWS:
            from .windows import status
        else:
            raise Exception(f"Unsupported platform: {platform}")
        
        return status()


# ============================================================================
# Convenience Functions
# ============================================================================

def is_supported_platform() -> bool:
    """
    Check if the current platform is supported.
    
    Returns:
        bool: True if platform is Linux, macOS, or Windows
        
    Example:
        >>> if is_supported_platform():
        ...     ServiceManager.install()
        ... else:
        ...     print("Your OS is not supported for service installation")
    """
    platform = OS.get_platform()
    return platform in [Platform.LINUX, Platform.MACOS, Platform.WINDOWS]


def get_service_type() -> str:
    """
    Get the type of service management on this platform.
    
    Returns:
        str: "systemd", "launchd", "windows_service", or "unknown"
        
    Example:
        >>> service_type = get_service_type()
        >>> print(f"Using {service_type}")
    """
    platform = OS.get_platform()
    
    if platform == Platform.LINUX:
        return "systemd"
    elif platform == Platform.MACOS:
        return "launchd"
    elif platform == Platform.WINDOWS:
        return "windows_service"
    else:
        return "unknown"


# Export public interface
__all__ = [
    'ServiceManager',
    'is_supported_platform',
    'get_service_type'
]
