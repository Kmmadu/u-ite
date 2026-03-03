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
    - windows.py (Windows Service using sc.exe)
    - windows_nssm.py (Windows Service using nssm - auto-start)
    """
    
    @staticmethod
    def install(auto_start=True):
        """
        Install U-ITE as a system service with auto-start.
        
        Args:
            auto_start (bool): Whether to enable auto-start on boot
            
        Returns:
            None
            
        Raises:
            Exception: If platform is unsupported
            
        Example:
            >>> ServiceManager.install(auto_start=True)
        """
        platform = OS.get_platform()
        
        # Dynamically import the appropriate platform module
        if platform == Platform.LINUX:
            from .linux import install
            install()
        elif platform == Platform.MACOS:
            from .darwin import install
            install()
        elif platform == Platform.WINDOWS:
            if auto_start:
                # Use nssm for auto-start
                try:
                    from .windows_nssm import install
                    install()
                except ImportError:
                    # Fall back to regular windows service
                    from .windows import install
                    install()
            else:
                # Use simple sc.exe service
                from .windows import install_simple
                install_simple()
        else:
            raise Exception(f"Unsupported platform: {platform}")
    
    @staticmethod
    def uninstall():
        """Uninstall U-ITE service completely."""
        platform = OS.get_platform()
        
        if platform == Platform.LINUX:
            from .linux import uninstall
            uninstall()
        elif platform == Platform.MACOS:
            from .darwin import uninstall
            uninstall()
        elif platform == Platform.WINDOWS:
            # Try nssm first, fall back to sc.exe
            try:
                from .windows_nssm import uninstall
                if not uninstall(silent=True):
                    from .windows import uninstall
                    uninstall()
            except ImportError:
                from .windows import uninstall
                uninstall()
        else:
            raise Exception(f"Unsupported platform: {platform}")
    
    @staticmethod
    def start():
        """Start the U-ITE service."""
        platform = OS.get_platform()
        
        if platform == Platform.LINUX:
            from .linux import start
            start()
        elif platform == Platform.MACOS:
            from .darwin import start
            start()
        elif platform == Platform.WINDOWS:
            # Try nssm first, fall back to sc.exe
            try:
                from .windows_nssm import start
                start()
            except ImportError:
                from .windows import start
                start()
        else:
            raise Exception(f"Unsupported platform: {platform}")
    
    @staticmethod
    def stop():
        """Stop the U-ITE service."""
        platform = OS.get_platform()
        
        if platform == Platform.LINUX:
            from .linux import stop
            stop()
        elif platform == Platform.MACOS:
            from .darwin import stop
            stop()
        elif platform == Platform.WINDOWS:
            # Try nssm first, fall back to sc.exe
            try:
                from .windows_nssm import stop
                stop()
            except ImportError:
                from .windows import stop
                stop()
        else:
            raise Exception(f"Unsupported platform: {platform}")
    
    @staticmethod
    def status():
        """Check the status of the U-ITE service."""
        platform = OS.get_platform()
        
        if platform == Platform.LINUX:
            from .linux import status
            return status()
        elif platform == Platform.MACOS:
            from .darwin import status
            return status()
        elif platform == Platform.WINDOWS:
            # Try nssm first, fall back to sc.exe
            try:
                from .windows_nssm import status
                return status()
            except ImportError:
                from .windows import status
                return status()
        else:
            raise Exception(f"Unsupported platform: {platform}")


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