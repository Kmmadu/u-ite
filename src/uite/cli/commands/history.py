import click
from datetime import datetime, timedelta
import re
from uite.storage.history import HistoricalData

@click.command(name="from")
@click.argument('args', nargs=-1, required=True)
def from_command(args):
    """
    Show data between two dates/times.
    
    Examples:
        uite from 17/02 to 18/02
        uite from 17/02/2026 08:00 to 18/02/2026 18:00
        uite from yesterday to today
        uite from "Jan 17" to "Jan 18"
    """
    # Join all arguments into a string
    text = ' '.join(args).lower()
    
    # Try multiple parsing strategies
    start_str = None
    end_str = None
    
    # Strategy 1: Look for "from" and "to" positions
    words = text.split()
    if 'from' in words and 'to' in words:
        from_idx = words.index('from')
        to_idx = words.index('to')
        
        if to_idx > from_idx:
            # Get everything between "from" and "to"
            start_parts = words[from_idx+1:to_idx]
            end_parts = words[to_idx+1:]
            
            if start_parts and end_parts:
                start_str = ' '.join(start_parts)
                end_str = ' '.join(end_parts)
    
    # Strategy 2: Try regex pattern
    if not start_str or not end_str:
        patterns = [
            r'from\s+(.+?)\s+to\s+(.+)',  # Standard format
            r'from\s+(\d{1,2}[/-]\d{1,2}(?:[/-]\d{4})?(?:\s+\d{1,2}:\d{2})?)\s+to\s+(\d{1,2}[/-]\d{1,2}(?:[/-]\d{4})?(?:\s+\d{1,2}:\d{2})?)',  # Date patterns
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                start_str = match.group(1).strip()
                end_str = match.group(2).strip()
                break
    
    if not start_str or not end_str:
        click.echo("❌ Please use format: uite from <start> to <end>")
        click.echo("   Examples:")
        click.echo("     uite from 17/02 to 18/02")
        click.echo("     uite from 17/02/2026 08:00 to 18/02/2026 18:00")
        click.echo("     uite from yesterday to today")
        return
    
    # Parse start and end dates
    start = parse_natural_date(start_str)
    end = parse_natural_date(end_str)
    
    if not start or not end:
        return
    
    # Ensure start is before end
    if start > end:
        start, end = end, start
        click.echo("ℹ️  Swapped dates to ensure start is before end")
    
    # Format for database query
    start_date = start.strftime("%d-%m-%Y")
    start_time = start.strftime("%H:%M")
    end_date = end.strftime("%d-%m-%Y")
    end_time = end.strftime("%H:%M")
    
    # Get the data
    click.echo(f"\n🔍 Fetching data from {start_date} {start_time} to {end_date} {end_time}...")
    
    runs = HistoricalData.get_runs_by_date_range(
        start_date, start_time, end_date, end_time
    )
    
    if not runs:
        click.echo("📭 No data found for this period")
        return
    
    # Display results
    display_results(runs, start, end)

def parse_natural_date(text):
    """Parse natural language dates like '17/02', 'yesterday', 'today'"""
    now = datetime.now()
    text = text.lower().strip()
    
    # Handle special words
    if text == 'today':
        return now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif text == 'yesterday':
        return (now - timedelta(days=1)).replace(hour=0, minute=0, second=0)
    elif text == 'tomorrow':
        return (now + timedelta(days=1)).replace(hour=0, minute=0, second=0)
    elif text == 'now':
        return now
    
    # Try to parse with time
    time_match = re.search(r'(\d{1,2}):(\d{2})', text)
    hour = minute = 0
    if time_match:
        hour = int(time_match.group(1))
        minute = int(time_match.group(2))
        text = text.replace(time_match.group(0), '').strip()
    
    # Try different date formats
    date_formats = [
        ('%d/%m', f"{datetime.now().year}"),  # 17/02
        ('%d/%m/%Y', ''),                      # 17/02/2026
        ('%d-%m', f"{datetime.now().year}"),   # 17-02
        ('%d-%m-%Y', ''),                      # 17-02-2026
        ('%m/%d', f"{datetime.now().year}"),   # 02/17 (US format)
        ('%m/%d/%Y', ''),                      # 02/17/2026
        ('%b %d', f"{datetime.now().year}"),   # Feb 17
        ('%B %d', f"{datetime.now().year}"),   # February 17
        ('%d %b', f"{datetime.now().year}"),   # 17 Feb
        ('%d %B', f"{datetime.now().year}"),   # 17 February
    ]
    
    # Try each format
    for fmt, year_suffix in date_formats:
        try:
            if year_suffix:
                # If year suffix is provided, append it
                date_str = f"{text} {year_suffix}"
                dt = datetime.strptime(date_str, f"{fmt} %Y")
            else:
                dt = datetime.strptime(text, fmt)
                # If no year in format, assume current year
                dt = dt.replace(year=now.year)
            
            # Set the time
            return dt.replace(hour=hour, minute=minute)
        except ValueError:
            continue
    
    click.echo(f"❌ Could not understand date: '{text}'")
    click.echo("   Try formats like: 17/02, 17/02/2026, 17-02, yesterday, today")
    return None

def display_results(runs, start, end):
    """Display the historical data in a nice format"""
    
    total = len(runs)
    duration = end - start
    days = duration.days
    if days == 0:
        days = 1  # Prevent division by zero
    
    # Calculate statistics
    verdict_counts = {}
    latencies = []
    losses = []
    
    for run in runs:
        v = run.get('verdict', 'Unknown')
        verdict_counts[v] = verdict_counts.get(v, 0) + 1
        
        if run.get('latency') is not None:
            latencies.append(run['latency'])
        if run.get('loss') is not None:
            losses.append(run['loss'])
    
    # Header
    click.echo("\n" + "=" * 70)
    click.echo(f"📊 Historical Summary ({start.strftime('%d %b %Y %H:%M')} to {end.strftime('%d %b %Y %H:%M')})")
    click.echo("=" * 70)
    
    # Overview
    click.echo(f"\n📈 Overview:")
    click.echo(f"   Total checks: {total}")
    click.echo(f"   Time period: {duration.days} day{'s' if duration.days != 1 else ''}")
    if duration.days > 0:
        click.echo(f"   Average checks per day: {total // duration.days}")
    
    # Health stats
    healthy_count = 0
    for v, count in verdict_counts.items():
        if '✅' in v or 'Connected' in v or 'Healthy' in v:
            healthy_count += count
    
    if healthy_count:
        percentage = (healthy_count / total) * 100
        click.echo(f"\n✅ Health: {healthy_count}/{total} ({percentage:.1f}%)")
    
    # Performance
    if latencies:
        avg_latency = sum(latencies) / len(latencies)
        max_latency = max(latencies)
        click.echo(f"\n⏱️  Latency:")
        click.echo(f"   Average: {avg_latency:.1f}ms")
        click.echo(f"   Maximum: {max_latency:.1f}ms")
    
    if losses:
        avg_loss = sum(losses) / len(losses)
        max_loss = max(losses)
        click.echo(f"\n📉 Packet Loss:")
        click.echo(f"   Average: {avg_loss:.1f}%")
        click.echo(f"   Maximum: {max_loss:.1f}%")
    
    # Issues breakdown
    issues = {}
    for v, count in verdict_counts.items():
        if '✅' not in v and 'Connected' not in v and 'Healthy' not in v:
            issues[v] = count
    
    if issues:
        click.echo(f"\n⚠️  Issues Detected:")
        for verdict, count in sorted(issues.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total) * 100
            click.echo(f"   {verdict}: {count} times ({percentage:.1f}%)")
    
    # Show sample of recent events
    if runs:
        click.echo(f"\n📋 Recent Events (last 5):")
        for run in runs[-5:]:
            time_str = run['timestamp'][11:19]  # HH:MM:SS
            verdict = run['verdict']
            latency = f"{run['latency']:.1f}ms" if run.get('latency') is not None else 'N/A'
            loss = f"{run['loss']}%" if run.get('loss') is not None else 'N/A'
            click.echo(f"   {time_str} - {verdict:35} | Lat: {latency:8} | Loss: {loss:6}")
    
    # Footer with tip
    click.echo("\n💡 Tip: Use 'uite export' to save this data to CSV")