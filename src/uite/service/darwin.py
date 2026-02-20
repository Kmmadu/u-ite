"""macOS launchd service management"""
import subprocess
import sys
import plistlib
from pathlib import Path

SERVICE_NAME = "com.uite.daemon"
SERVICE_FILE = Path.home() / "Library" / "LaunchAgents" / f"{SERVICE_NAME}.plist"

def get_service_content():
    """Generate launchd plist content"""
    python_path = sys.executable
    uite_path = Path(__file__).parent.parent.parent
    
    return {
        'Label': SERVICE_NAME,
        'ProgramArguments': [python_path, '-m', 'uite.daemon.orchestrator'],
        'RunAtLoad': True,
        'KeepAlive': True,
        'StandardOutPath': str(Path.home() / "Library" / "Logs" / "uite.log"),
        'StandardErrorPath': str(Path.home() / "Library" / "Logs" / "uite.error.log"),
        'WorkingDirectory': str(uite_path),
    }

def install():
    """Install launchd service"""
    content = get_service_content()
    
    # Write plist file
    with open(SERVICE_FILE, 'wb') as f:
        plistlib.dump(content, f)
    
    # Load the service
    subprocess.run(["launchctl", "load", str(SERVICE_FILE)])
    
    print(f"✅ U-ITE service installed and started")

def uninstall():
    """Uninstall launchd service"""
    subprocess.run(["launchctl", "unload", str(SERVICE_FILE)])
    SERVICE_FILE.unlink(missing_ok=True)
    print(f"✅ U-ITE service uninstalled")

def start():
    subprocess.run(["launchctl", "start", SERVICE_NAME])

def stop():
    subprocess.run(["launchctl", "stop", SERVICE_NAME])

def status():
    result = subprocess.run(["launchctl", "list", SERVICE_NAME], capture_output=True, text=True)
    return result.stdout
