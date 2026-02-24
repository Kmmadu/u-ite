"""
Daemon Management Commands for U-ITE
=====================================
Provides commands to run the U-ITE observer in the foreground for testing,
debugging, and development purposes.

This module handles:
- Starting the observer as a foreground process
- Checking process status
- Stopping running observers
- Viewing real-time logs

Note: For production use, use 'uite service' commands instead.
"""

import click
import subprocess
import signal
import os
import time
import sys
from pathlib import Path


@click.group()
def daemon():
    """
    Manage U-ITE foreground observer (for testing/debugging).
    
    This command group runs the observer in the foreground, showing logs
    directly in the terminal. It's perfect for:
    - Testing new features
    - Debugging issues
    - Development work
    
    For production use, use 'uite service' to run in the background.
    
    Examples:
        uite daemon start --interval 30
        uite daemon status
        uite daemon logs --lines 100
        uite daemon stop
    """
    pass


@daemon.command()
@click.option('--interval', default=30, help='Check interval in seconds')
def start(interval):
    """
    Start U-ITE observer in the foreground.
    
    This launches the observer process and displays logs in real-time.
    Press Ctrl+C to stop gracefully.
    
    Args:
        interval: Seconds between diagnostic checks (default: 30)
    
    Examples:
        uite daemon start
        uite daemon start --interval 60
    """
    click.echo(f"🚀 Starting U-ITE observer (interval: {interval}s)")
    click.echo("   Press Ctrl+C to stop")
    click.echo("")
    
    # ======================================================================
    # Path Resolution - Works in both development and installed environments
    # ======================================================================
    import sys
    from pathlib import Path
    import importlib.util
    
    orchestrator_script = None
    
    # Method 1: Try installed package location first (when installed via pip)
    try:
        import uite
        uite_package_path = Path(uite.__file__).parent
        test_path = uite_package_path / "daemon" / "orchestrator.py"
        if test_path.exists():
            orchestrator_script = test_path
            click.echo(f"📦 Using installed package: {orchestrator_script}")
    except (ImportError, AttributeError):
        pass
    
    # Method 2: Try development path (when running from source)
    if not orchestrator_script or not orchestrator_script.exists():
        current_file = Path(__file__).resolve()
        # Navigate up from .../cli/commands/daemon.py to project root
        for parent in current_file.parents:
            test_path = parent / "src" / "uite" / "daemon" / "orchestrator.py"
            if test_path.exists():
                orchestrator_script = test_path
                click.echo(f"🔧 Using development path: {orchestrator_script}")
                break
    
    # Method 3: Try current working directory (last resort)
    if not orchestrator_script or not orchestrator_script.exists():
        test_path = Path.cwd() / "src" / "uite" / "daemon" / "orchestrator.py"
        if test_path.exists():
            orchestrator_script = test_path
            click.echo(f"📁 Using current directory: {orchestrator_script}")
    
    # Verify the script exists
    if not orchestrator_script or not orchestrator_script.exists():
        click.echo(f"❌ Error: Orchestrator script not found")
        click.echo(f"   Tried multiple locations:")
        click.echo(f"   - In installed package: site-packages/uite/daemon/orchestrator.py")
        click.echo(f"   - In development: src/uite/daemon/orchestrator.py")
        click.echo(f"   - In current dir: {Path.cwd()}/src/uite/daemon/orchestrator.py")
        return
    
    # Build the command to execute
    cmd = [
        sys.executable,              # Use the same Python interpreter
        str(orchestrator_script),    # Path to orchestrator
        "--interval",                 # Pass interval as named argument
        str(interval)
    ]
    
    try:
        # Run the orchestrator as a subprocess and wait for it to complete
        # This blocks until the process exits (either normally or via Ctrl+C)
        process = subprocess.run(cmd)
        
        # Check if the process exited with an error
        if process.returncode != 0:
            click.echo(f"❌ Observer exited with code {process.returncode}")
            
    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully - the subprocess will also receive SIGINT
        click.echo("\n✅ Observer stopped")
        
    except Exception as e:
        # Handle any other unexpected errors
        click.echo(f"❌ Failed to start observer: {e}")


@daemon.command()
def status():
    """
    Check if the observer is currently running.
    
    Uses 'pgrep' to find any processes running orchestrator.py.
    Returns the PID(s) if found.
    
    Examples:
        uite daemon status
    """
    try:
        # Use pgrep to find processes matching 'orchestrator.py'
        result = subprocess.run(
            ["pgrep", "-f", "orchestrator.py"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            # Process found - show PIDs
            pids = result.stdout.strip().split('\n')
            click.echo(f"✅ Observer is running (PID: {', '.join(pids)})")
        else:
            # No process found
            click.echo("❌ Observer is not running")
            
    except FileNotFoundError:
        # pgrep not installed on this system
        click.echo("⚠️  Cannot check status (pgrep not available)")
        click.echo("   Try: ps aux | grep orchestrator.py")


@daemon.command()
def stop():
    """
    Stop a running observer process.
    
    Uses 'pkill' to terminate any processes running orchestrator.py.
    
    Examples:
        uite daemon stop
    """
    try:
        # Use pkill to terminate processes matching 'orchestrator.py'
        result = subprocess.run(
            ["pkill", "-f", "orchestrator.py"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            click.echo("✅ Observer stopped")
        else:
            click.echo("❌ No running observer found")
            
    except FileNotFoundError:
        # pkill not installed on this system
        click.echo("⚠️  Cannot stop observer (pkill not available)")
        click.echo("   Try: pkill -f orchestrator.py")


@daemon.command()
@click.option('--lines', default=50, help='Number of lines to show')
def logs(lines):
    """
    Show recent observer logs.
    
    Displays the last N lines from the log file. Checks multiple
    possible log locations for compatibility.
    
    Args:
        lines: Number of log lines to show (default: 50)
    
    Examples:
        uite daemon logs
        uite daemon logs --lines 200
    """
    # List of possible log file locations (in order of preference)
    possible_logs = [
        Path.home() / ".local/share/uite/logs/uite-observer.log",  # Linux/macOS
        Path.home() / "Library/Logs/uite.log",                     # macOS alternative
        Path.home() / "AppData/Local/uite/logs/uite.log",          # Windows
        Path("u-ite-observer.log"),                                 # Legacy/current directory
    ]
    
    # Find the first existing log file
    log_file = None
    for log in possible_logs:
        if log.exists():
            log_file = log
            break
    
    if log_file:
        # Read and display the last N lines
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
                last_lines = all_lines[-lines:]
                
                # Print each line (stripping trailing newlines)
                for line in last_lines:
                    click.echo(line.rstrip())
            
            # Show the full path for reference
            click.echo(f"\n📁 Full log: {log_file.absolute()}")
        except Exception as e:
            click.echo(f"❌ Error reading log file: {e}")
    else:
        click.echo("No logs found. Start the observer first.")
        if sys.platform == "win32":
            click.echo("   On Windows, logs are typically in:")
            click.echo(f"   {Path.home() / 'AppData/Local/uite/logs/uite.log'}")


# Export the command group for registration in main CLI
__all__ = ['daemon']
