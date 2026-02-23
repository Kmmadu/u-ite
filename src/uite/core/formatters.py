"""
Formatting Utilities for U-ITE
===============================
Provides human-readable formatting functions for various data types.
Currently supports duration formatting, with room for expansion.

This module ensures consistent, user-friendly output across all CLI commands.
The main use case is formatting downtime durations and runtime periods in a
way that's easy for humans to understand.

Features:
- Convert seconds to natural language (e.g., "2 hours 30 minutes")
- Handles ranges from seconds to years
- Proper pluralization (minute vs minutes)
- Clean, readable output format
"""

def format_duration(seconds):
    """
    Convert a duration in seconds to a human-readable string.
    
    Takes a raw number of seconds and formats it into natural language
    with appropriate units and pluralization. Handles durations from
    seconds to years.
    
    Args:
        seconds (int/float): Duration in seconds
        
    Returns:
        str: Human-readable duration string
        
    Examples:
        >>> format_duration(45)
        '45 seconds'
        >>> format_duration(125)
        '2 minutes 5 seconds'
        >>> format_duration(3720)
        '1 hour 2 minutes'
        >>> format_duration(90000)
        '1 day 1 hour'
        >>> format_duration(700000)
        '1 week 1 day'
        >>> format_duration(30000000)
        '1 year 1 month'
    """
    # Handle sub-minute durations (1-59 seconds)
    if seconds < 60:
        return f"{seconds} seconds"
    
    # Handle durations up to 1 hour (60-3599 seconds)
    elif seconds < 3600:
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        
        if remaining_seconds == 0:
            # Exact minutes, no seconds
            return f"{minutes} minute{'s' if minutes > 1 else ''}"
        else:
            # Minutes and seconds
            return (f"{minutes} minute{'s' if minutes > 1 else ''} "
                   f"{remaining_seconds} second{'s' if remaining_seconds > 1 else ''}")
    
    # Handle durations up to 1 day (3600-86399 seconds)
    elif seconds < 86400:
        hours = seconds // 3600
        remaining_minutes = (seconds % 3600) // 60
        
        if remaining_minutes == 0:
            # Exact hours, no minutes
            return f"{hours} hour{'s' if hours > 1 else ''}"
        else:
            # Hours and minutes
            return (f"{hours} hour{'s' if hours > 1 else ''} "
                   f"{remaining_minutes} minute{'s' if remaining_minutes > 1 else ''}")
    
    # Handle durations up to 1 week (86400-604799 seconds)
    elif seconds < 604800:
        days = seconds // 86400
        remaining_hours = (seconds % 86400) // 3600
        
        if remaining_hours == 0:
            # Exact days, no hours
            return f"{days} day{'s' if days > 1 else ''}"
        else:
            # Days and hours
            return (f"{days} day{'s' if days > 1 else ''} "
                   f"{remaining_hours} hour{'s' if remaining_hours > 1 else ''}")
    
    # Handle durations up to 1 month (~28 days) (604800-2419199 seconds)
    elif seconds < 2419200:  # 28 days * 86400
        weeks = seconds // 604800
        remaining_days = (seconds % 604800) // 86400
        
        if remaining_days == 0:
            # Exact weeks, no days
            return f"{weeks} week{'s' if weeks > 1 else ''}"
        else:
            # Weeks and days
            return (f"{weeks} week{'s' if weeks > 1 else ''} "
                   f"{remaining_days} day{'s' if remaining_days > 1 else ''}")
    
    # Handle durations up to 1 year (2419200-31535999 seconds)
    elif seconds < 31536000:  # 365 days * 86400
        months = seconds // 2419200  # Approximate month as 28 days
        remaining_weeks = (seconds % 2419200) // 604800
        
        if remaining_weeks == 0:
            # Exact months, no weeks
            return f"{months} month{'s' if months > 1 else ''}"
        else:
            # Months and weeks
            return (f"{months} month{'s' if months > 1 else ''} "
                   f"{remaining_weeks} week{'s' if remaining_weeks > 1 else ''}")
    
    # Handle durations longer than 1 year
    else:
        years = seconds // 31536000
        remaining_months = (seconds % 31536000) // 2419200
        
        if remaining_months == 0:
            # Exact years, no months
            return f"{years} year{'s' if years > 1 else ''}"
        else:
            # Years and months
            return (f"{years} year{'s' if years > 1 else ''} "
                   f"{remaining_months} month{'s' if remaining_months > 1 else ''}")


# Additional formatting utilities can be added here in the future
# For example:
# - format_bytes() for data sizes
# - format_percentage() for consistent percentage display
# - format_timestamp() for consistent date/time formatting


# Example usage and test cases (commented out)
"""
if __name__ == "__main__":
    # Test cases
    test_cases = [
        30,           # 30 seconds
        90,           # 1 minute 30 seconds
        120,          # 2 minutes
        3665,         # 1 hour 1 minute 5 seconds
        7200,         # 2 hours
        90000,        # 1 day 1 hour
        172800,       # 2 days
        700000,       # 1 week 1 day
        2419200,      # 1 month (28 days)
        31536000,     # 1 year
        63072000,     # 2 years
    ]
    
    for seconds in test_cases:
        print(f"{seconds:8d} → {format_duration(seconds)}")
"""
