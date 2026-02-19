"""Formatting utilities for U-ITE"""

def format_duration(seconds):
    """Convert seconds to human-readable format"""
    if seconds < 60:
        return f"{seconds} seconds"
    elif seconds < 3600:
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        if remaining_seconds == 0:
            return f"{minutes} minute{'s' if minutes > 1 else ''}"
        return f"{minutes} minute{'s' if minutes > 1 else ''} {remaining_seconds} second{'s' if remaining_seconds > 1 else ''}"
    elif seconds < 86400:
        hours = seconds // 3600
        remaining_minutes = (seconds % 3600) // 60
        if remaining_minutes == 0:
            return f"{hours} hour{'s' if hours > 1 else ''}"
        return f"{hours} hour{'s' if hours > 1 else ''} {remaining_minutes} minute{'s' if remaining_minutes > 1 else ''}"
    elif seconds < 604800:
        days = seconds // 86400
        remaining_hours = (seconds % 86400) // 3600
        if remaining_hours == 0:
            return f"{days} day{'s' if days > 1 else ''}"
        return f"{days} day{'s' if days > 1 else ''} {remaining_hours} hour{'s' if remaining_hours > 1 else ''}"
    elif seconds < 2419200:
        weeks = seconds // 604800
        remaining_days = (seconds % 604800) // 86400
        if remaining_days == 0:
            return f"{weeks} week{'s' if weeks > 1 else ''}"
        return f"{weeks} week{'s' if weeks > 1 else ''} {remaining_days} day{'s' if remaining_days > 1 else ''}"
    elif seconds < 31536000:
        months = seconds // 2419200
        remaining_weeks = (seconds % 2419200) // 604800
        if remaining_weeks == 0:
            return f"{months} month{'s' if months > 1 else ''}"
        return f"{months} month{'s' if months > 1 else ''} {remaining_weeks} week{'s' if remaining_weeks > 1 else ''}"
    else:
        years = seconds // 31536000
        remaining_months = (seconds % 31536000) // 2419200
        if remaining_months == 0:
            return f"{years} year{'s' if years > 1 else ''}"
        return f"{years} year{'s' if years > 1 else ''} {remaining_months} month{'s' if remaining_months > 1 else ''}"
