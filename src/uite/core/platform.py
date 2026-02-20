"""OS platform detection and abstraction"""
import platform
import sys
from pathlib import Path
from enum import Enum

class Platform(Enum):
    LINUX = "linux"
    MACOS = "darwin"
    WINDOWS = "windows"
    UNKNOWN = "unknown"

class OS:
    """OS platform detection and utilities"""
    
    @staticmethod
    def get_platform() -> Platform:
        """Detect current operating system"""
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
        return OS.get_platform() == Platform.LINUX
    
    @staticmethod
    def is_macos() -> bool:
        return OS.get_platform() == Platform.MACOS
    
    @staticmethod
    def is_windows() -> bool:
        return OS.get_platform() == Platform.WINDOWS
    
    @staticmethod
    def get_config_dir() -> Path:
        """Get OS-appropriate config directory"""
        platform = OS.get_platform()
        home = Path.home()
        
        if platform == Platform.LINUX:
            return home / ".config" / "uite"
        elif platform == Platform.MACOS:
            return home / "Library" / "Application Support" / "uite"
        elif platform == Platform.WINDOWS:
            return home / "AppData" / "Local" / "uite"
        else:
            return home / ".uite"
    
    @staticmethod
    def get_data_dir() -> Path:
        """Get OS-appropriate data directory"""
        platform = OS.get_platform()
        home = Path.home()
        
        if platform == Platform.LINUX:
            return home / ".local" / "share" / "uite"
        elif platform == Platform.MACOS:
            return home / "Library" / "Application Support" / "uite" / "data"
        elif platform == Platform.WINDOWS:
            return home / "AppData" / "Local" / "uite" / "data"
        else:
            return home / ".uite" / "data"
    
    @staticmethod
    def get_log_dir() -> Path:
        """Get OS-appropriate log directory"""
        platform = OS.get_platform()
        home = Path.home()
        
        if platform == Platform.LINUX:
            return home / ".local" / "share" / "uite" / "logs"
        elif platform == Platform.MACOS:
            return home / "Library" / "Logs" / "uite"
        elif platform == Platform.WINDOWS:
            return home / "AppData" / "Local" / "uite" / "logs"
        else:
            return home / ".uite" / "logs"
    
    @staticmethod
    def get_service_name() -> str:
        """Get OS-appropriate service name"""
        platform = OS.get_platform()
        
        if platform == Platform.LINUX:
            return "uite.service"
        elif platform == Platform.MACOS:
            return "com.uite.daemon.plist"
        elif platform == Platform.WINDOWS:
            return "U-ITE Service"
        else:
            return "uite"
