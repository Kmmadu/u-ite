"""Linux systemd service management"""
import subprocess
import sys
from pathlib import Path

SERVICE_NAME = "uite"
SERVICE_FILE = f"/etc/systemd/system/{SERVICE_NAME}.service"

def get_service_content():
    """Generate systemd service file content"""
    python_path = sys.executable
    uite_path = Path(__file__).parent.parent.parent
    
    return f"""[Unit]
Description=U-ITE Network Observer
After=network.target

[Service]
Type=simple
User=%i
ExecStart={python_path} -m uite.daemon.orchestrator
Restart=always
RestartSec=10
StandardOutput=append:{Path.home()}/.local/share/uite/logs/uite.log
StandardError=append:{Path.home()}/.local/share/uite/logs/uite.error.log

[Install]
WantedBy=multi-user.target
"""

def install():
    """Install systemd service"""
    content = get_service_content()
    
    # Write service file
    with open(SERVICE_FILE, 'w') as f:
        f.write(content)
    
    # Reload systemd
    subprocess.run(["sudo", "systemctl", "daemon-reload"])
    
    # Enable and start
    subprocess.run(["sudo", "systemctl", "enable", SERVICE_NAME])
    subprocess.run(["sudo", "systemctl", "start", SERVICE_NAME])
    
    print(f"✅ U-ITE service installed and started")

def uninstall():
    """Uninstall systemd service"""
    subprocess.run(["sudo", "systemctl", "stop", SERVICE_NAME])
    subprocess.run(["sudo", "systemctl", "disable", SERVICE_NAME])
    subprocess.run(["sudo", "rm", "-f", SERVICE_FILE])
    subprocess.run(["sudo", "systemctl", "daemon-reload"])
    print(f"✅ U-ITE service uninstalled")

def start():
    subprocess.run(["sudo", "systemctl", "start", SERVICE_NAME])

def stop():
    subprocess.run(["sudo", "systemctl", "stop", SERVICE_NAME])

def status():
    result = subprocess.run(["systemctl", "status", SERVICE_NAME], capture_output=True, text=True)
    return result.stdout
