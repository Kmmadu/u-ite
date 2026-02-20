"""OS service management for U-ITE"""
from uite.core.platform import OS, Platform

class ServiceManager:
    """Manage U-ITE as a system service"""
    
    @staticmethod
    def install():
        """Install U-ITE as a system service"""
        platform = OS.get_platform()
        
        if platform == Platform.LINUX:
            from .linux import install
        elif platform == Platform.MACOS:
            from .darwin import install
        elif platform == Platform.WINDOWS:
            from .windows import install
        else:
            raise Exception(f"Unsupported platform: {platform}")
        
        install()
    
    @staticmethod
    def uninstall():
        """Uninstall U-ITE service"""
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
        """Start U-ITE service"""
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
        """Stop U-ITE service"""
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
        """Check U-ITE service status"""
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
