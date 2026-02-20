"""Windows service management"""
import subprocess
import sys
from pathlib import Path

SERVICE_NAME = "U-ITE"
SERVICE_DISPLAY_NAME = "U-ITE Network Observer"

def install():
    """Install Windows service"""
    python_path = sys.executable
    script_path = Path(__file__).parent.parent.parent / "daemon" / "orchestrator.py"
    
    # Create service with nssm or sc
    cmd = f'nssm install {SERVICE_NAME} "{python_path}" "-m uite.daemon.orchestrator"'
    subprocess.run(cmd, shell=True)
    
    # Set service display name
    subprocess.run(f'sc config {SERVICE_NAME} displayname= "{SERVICE_DISPLAY_NAME}"', shell=True)
    
    # Start service
    subprocess.run(f'sc start {SERVICE_NAME}', shell=True)
    
    print(f"✅ U-ITE service installed and started")

def uninstall():
    """Uninstall Windows service"""
    subprocess.run(f'sc stop {SERVICE_NAME}', shell=True)
    subprocess.run(f'sc delete {SERVICE_NAME}', shell=True)
    print(f"✅ U-ITE service uninstalled")

def start():
    subprocess.run(f'sc start {SERVICE_NAME}', shell=True)

def stop():
    subprocess.run(f'sc stop {SERVICE_NAME}', shell=True)

def status():
    result = subprocess.run(f'sc query {SERVICE_NAME}', shell=True, capture_output=True, text=True)
    return result.stdout
