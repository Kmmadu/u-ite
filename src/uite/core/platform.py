"""
OS Platform Detection and Abstraction Module for U-ITE
=======================================================
Provides a unified interface for platform-specific operations across
Linux, macOS, and Windows. This module is critical for making U-ITE
truly cross-platform.

Features:
- Platform detection (Linux, macOS, Windows)
- OS-appropriate directory paths (config, data, logs)
- Service naming conventions per platform
- Boolean flags for conditional logic
- Centralized platform-specific logic

This abstraction ensures that the rest of the codebase can remain
platform-agnostic, with all OS-specific details handled here.
"""

import platform
import sys
from pathlib import Path
from enum import Enum


class Platform(Enum):
    """
    Supported operating system platforms.
    
    Values:
        LINUX: Linux-based systems (Ubuntu, Debian, Fedora, etc.)
        MACOS: Apple macOS (Darwin kernel)
        WINDOWS: Microsoft Windows
        UNKNOWN: Unrecognized/unsupported platform
    
    Example:
        >>> if OS.get_platform() == Platform.LINUX:
        ...     use_systemd()
    """
    LINUX = "linux"
    MACOS = "darwin"
    WINDOWS = "windows"
    UNKNOWN = "unknown"


class OS:
    """
    Operating system detection and path utilities.
    
    This class provides static methods for all OS-specific operations.
    It follows the XDG Base Directory Specification on Linux and uses
    platform conventions on macOS and Windows.
    
    All methods are static, so no instantiation is needed:
        >>> from uite.core.platform import OS
        >>> data_dir = OS.get_data_dir()
        >>> if OS.is_linux():
        ...     # Linux-specific code
    """
    
    @staticmethod
    def get_platform() -> Platform:
        """
        Detect the current operating system.
        
        Uses Python's platform module to determine the OS.
        
        Returns:
            Platform: Enum value representing the current OS
            
        Example:
            >>> platform = OS.get_platform()
            >>> if platform == Platform.MACOS:
            ...     print("Running on macOS")
        """
        system = platform.system().lower()
        if system == "linux":
            return Platform.LINUX
        elif system == "darwin":
            return Platform.MACOS
        elif system == "windows":
            return Platform.WINDOWS
        return Platform.UNKNOWN
    
    @staticmethod
    def is_linux() -> bool:
        """
        Check if running on Linux.
        
        Returns:
            bool: True if on Linux, False otherwise
        """
        return OS.get_platform() == Platform.LINUX
    
    @staticmethod
    def is_macos() -> bool:
        """
        Check if running on macOS.
        
        Returns:
            bool: True if on macOS, False otherwise
        """
        return OS.get_platform() == Platform.MACOS
    
    @staticmethod
    def is_windows() -> bool:
        """
        Check if running on Windows.
        
        Returns:
            bool: True if on Windows, False otherwise
        """
        return OS.get_platform() == Platform.WINDOWS
    
    @staticmethod
    def get_config_dir() -> Path:
        """
        Get the OS-appropriate directory for configuration files.
        
        Follows platform conventions:
        - Linux:   ~/.config/uite/        (XDG_CONFIG_HOME)
        - macOS:   ~/Library/Application Support/uite/
        - Windows: ~/AppData/Local/uite/
        - Unknown: ~/.uite/
        
        Returns:
            Path: Platform-specific config directory
            
        Example:
            >>> config_file = OS.get_config_dir() / "settings.toml"
        """
        platform = OS.get_platform()
        home = Path.home()
        
        if platform == Platform.LINUX:
            # XDG Base Directory Specification
            return home / ".config" / "uite"
        elif platform == Platform.MACOS:
            # macOS Application Support
            return home / "Library" / "Application Support" / "uite"
        elif platform == Platform.WINDOWS:
            # Windows Local AppData
            return home / "AppData" / "Local" / "uite"
        else:
            # Fallback for unknown platforms
            return home / ".uite"
    
    @staticmethod
    def get_data_dir() -> Path:
        """
        Get the OS-appropriate directory for persistent data.
        
        Follows platform conventions:
        - Linux:   ~/.local/share/uite/        (XDG_DATA_HOME)
        - macOS:   ~/Library/Application Support/uite/data/
        - Windows: ~/AppData/Local/uite/data/
        - Unknown: ~/.uite/data/
        
        Returns:
            Path: Platform-specific data directory
            
        Example:
            >>> db_path = OS.get_data_dir() / "u_ite.db"
        """
        platform = OS.get_platform()
        home = Path.home()
        
        if platform == Platform.LINUX:
            # XDG Base Directory Specification
            return home / ".local" / "share" / "uite"
        elif platform == Platform.MACOS:
            # macOS Application Support with data subdirectory
            return home / "Library" / "Application Support" / "uite" / "data"
        elif platform == Platform.WINDOWS:
            # Windows Local AppData with data subdirectory
            return home / "AppData" / "Local" / "uite" / "data"
        else:
            # Fallback for unknown platforms
            return home / ".uite" / "data"
    
    @staticmethod
    def get_log_dir() -> Path:
        """
        Get the OS-appropriate directory for log files.
        
        Follows platform conventions:
        - Linux:   ~/.local/share/uite/logs/   (under XDG_DATA_HOME)
        - macOS:   ~/Library/Logs/uite/
        - Windows: ~/AppData/Local/uite/logs/
        - Unknown: ~/.uite/logs/
        
        Returns:
            Path: Platform-specific log directory
            
        Example:
            >>> log_file = OS.get_log_dir() / "uite-observer.log"
        """
        platform = OS.get_platform()
        home = Path.home()
        
        if platform == Platform.LINUX:
            # Under XDG data directory
            return home / ".local" / "share" / "uite" / "logs"
        elif platform == Platform.MACOS:
            # macOS standard logs location
            return home / "Library" / "Logs" / "uite"
        elif platform == Platform.WINDOWS:
            # Under Local AppData
            return home / "AppData" / "Local" / "uite" / "logs"
        else:
            # Fallback for unknown platforms
            return home / ".uite" / "logs"
    
    @staticmethod
    def get_service_name() -> str:
        """
        Get the OS-appropriate service/daemon name.
        
        Returns platform-specific service naming conventions:
        - Linux:   "uite.service"           (systemd unit name)
        - macOS:   "com.uite.daemon.plist"  (launchd plist name)
        - Windows: "U-ITE Service"          (Windows service name)
        - Unknown: "uite"                    (generic)
        
        Returns:
            str: Platform-specific service name
            
        Example:
            >>> service_name = OS.get_service_name()
            >>> subprocess.run(["systemctl", "start", service_name])
        """
        platform = OS.get_platform()
        
        if platform == Platform.LINUX:
            return "uite.service"
        elif platform == Platform.MACOS:
            return "com.uite.daemon.plist"
        elif platform == Platform.WINDOWS:
            return "U-ITE Service"
        else:
            return "uite"


# ============================================================================
# Convenience functions for common operations
# ============================================================================
def ensure_dirs_exist():
    """
    Ensure all required directories exist.
    
    Creates config, data, and log directories if they don't exist.
    This should be called during initialization.
    
    Example:
        >>> from uite.core.platform import ensure_dirs_exist
        >>> ensure_dirs_exist()
    """
    OS.get_config_dir().mkdir(parents=True, exist_ok=True)
    OS.get_data_dir().mkdir(parents=True, exist_ok=True)
    OS.get_log_dir().mkdir(parents=True, exist_ok=True)


def get_platform_name() -> str:
    """
    Get a human-readable platform name.
    
    Returns:
        str: "Linux", "macOS", "Windows", or "Unknown"
    """
    platform = OS.get_platform()
    if platform == Platform.LINUX:
        return "Linux"
    elif platform == Platform.MACOS:
        return "macOS"
    elif platform == Platform.WINDOWS:
        return "Windows"
    else:
        return "Unknown"


# Export public interface
__all__ = [
    'Platform',
    'OS',
    'ensure_dirs_exist',
    'get_platform_name',
]
