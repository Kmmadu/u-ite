"""Daemon management commands for U-ITE"""
import click
import subprocess
import signal
import os
import time
import sys
from pathlib import Path

@click.group()
def daemon():
    """Manage U-ITE foreground daemon"""
    pass

@daemon.command()
@click.option('--interval', default=30, help='Check interval in seconds')
def start(interval):
    """Start U-ITE observer in foreground"""
    click.echo(f"🚀 Starting U-ITE observer (interval: {interval}s)")
    click.echo("   Press Ctrl+C to stop")
    click.echo("")
    
    # Get the correct path to the orchestrator script
    current_file = Path(__file__).resolve()
    commands_dir = current_file.parent
    cli_dir = commands_dir.parent
    uite_dir = cli_dir.parent
    src_dir = uite_dir.parent
    project_root = src_dir.parent
    
    orchestrator_script = project_root / "src" / "uite" / "daemon" / "orchestrator.py"
    
    if not orchestrator_script.exists():
        click.echo(f"❌ Error: Orchestrator script not found")
        return
    
    # Run the orchestrator as a subprocess
    cmd = [sys.executable, str(orchestrator_script), "--interval", str(interval)]
    
    try:
        # Run the process and wait for it to complete
        process = subprocess.run(cmd)
        if process.returncode != 0:
            click.echo(f"❌ Observer exited with code {process.returncode}")
    except KeyboardInterrupt:
        click.echo("\n✅ Observer stopped")
    except Exception as e:
        click.echo(f"❌ Failed to start observer: {e}")

@daemon.command()
def status():
    """Check if daemon is running"""
    try:
        result = subprocess.run(
            ["pgrep", "-f", "orchestrator.py"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            pids = result.stdout.strip().split('\n')
            click.echo(f"✅ Observer is running (PID: {', '.join(pids)})")
        else:
            click.echo("❌ Observer is not running")
    except FileNotFoundError:
        click.echo("⚠️  Cannot check status (pgrep not available)")

@daemon.command()
def stop():
    """Stop the foreground daemon"""
    try:
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
        click.echo("⚠️  Cannot stop observer (pkill not available)")

@daemon.command()
@click.option('--lines', default=50, help='Number of lines to show')
def logs(lines):
    """Show daemon logs"""
    possible_logs = [
        Path.home() / ".local/share/uite/logs/uite-observer.log",
        Path("u-ite-observer.log"),
    ]
    
    log_file = None
    for log in possible_logs:
        if log.exists():
            log_file = log
            break
    
    if log_file:
        with open(log_file, 'r') as f:
            all_lines = f.readlines()
            last_lines = all_lines[-lines:]
            for line in last_lines:
                click.echo(line.strip())
        click.echo(f"\n📁 Full log: {log_file.absolute()}")
    else:
        click.echo("No logs found. Start the observer first.")

__all__ = ['daemon']
