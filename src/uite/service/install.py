"""Auto-start service installation"""
from uite.core.platform import OS, Platform
import subprocess
import sys
from pathlib import Path

def install_auto_start():
    """Install U-ITE to start automatically on boot"""
    platform = OS.get_platform()
    
    if platform == Platform.LINUX:
        _install_linux_systemd()
    elif platform == Platform.MACOS:
        _install_macos_launchd()
    elif platform == Platform.WINDOWS:
        _install_windows_service()
    else:
        print("❌ Unsupported platform")

def _install_linux_systemd():
    """Install systemd user service (no sudo needed)"""
    service_content = f"""[Unit]
Description=U-ITE Network Observer
After=network.target

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
    service_dir = Path.home() / ".config" / "systemd" / "user"
    service_dir.mkdir(parents=True, exist_ok=True)
    
    service_file = service_dir / "uite.service"
    service_file.write_text(service_content)
    
    subprocess.run(["systemctl", "--user", "daemon-reload"])
    subprocess.run(["systemctl", "--user", "enable", "uite"])
    subprocess.run(["systemctl", "--user", "start", "uite"])
    
    print("✅ U-ITE auto-start enabled (systemd user service)")

def _install_macos_launchd():
    """Install macOS launchd agent"""
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
</dict>
</plist>
"""
    plist_dir = Path.home() / "Library" / "LaunchAgents"
    plist_dir.mkdir(parents=True, exist_ok=True)
    
    plist_file = plist_dir / "com.uite.observer.plist"
    plist_file.write_text(plist_content)
    
    subprocess.run(["launchctl", "load", str(plist_file)])
    print("✅ U-ITE auto-start enabled (launchd agent)")

def _install_windows_service():
    """Install Windows service (requires admin)"""
    # Using nssm (Non-Sucking Service Manager) - users need to install it
    nssm_path = shutil.which("nssm")
    if not nssm_path:
        print("⚠️  nssm not found. Please install it first:")
        print("   https://nssm.cc/download")
        return
    
    subprocess.run([
        nssm_path, "install", "U-ITE", sys.executable,
        "-m", "uite.daemon.orchestrator"
    ])
    subprocess.run(["sc", "config", "U-ITE", "start=", "auto"])
    subprocess.run(["sc", "start", "U-ITE"])
    print("✅ U-ITE auto-start enabled (Windows service)")
