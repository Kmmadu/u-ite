"""
Event Category Enumeration for U-ITE
======================================
Defines the standard categories for network events. Categories help organize
and filter events by their functional area, making it easier to analyze
different aspects of network health.

Categories follow a logical hierarchy:
- CONNECTIVITY: Basic network connectivity issues
- PERFORMANCE: Speed and quality problems
- INFRASTRUCTURE: Hardware/equipment issues
- APPLICATION: Service/application failures
- SECURITY: Security-related events

Each event in the system must have a category, ensuring consistent
classification across all event types.
"""

from enum import Enum


class Category(str, Enum):
    """
    Network event categories.
    
    These categories are used to classify events by their functional area,
    enabling filtering and analysis of specific network aspects.
    
    Values:
        CONNECTIVITY: Basic network connectivity issues
            Examples: Internet down, router unreachable, DNS failure
        
        PERFORMANCE: Speed and quality problems
            Examples: High latency, packet loss, degraded throughput
        
        INFRASTRUCTURE: Hardware and equipment issues
            Examples: Router failure, switch problems, cable faults
        
        APPLICATION: Service and application failures
            Examples: Website unreachable, API timeout, service down
        
        SECURITY: Security-related events
            Examples: Unusual traffic, authentication failures, attacks
    
    Usage:
        >>> from uite.tracking.category import Category
        >>> event_category = Category.CONNECTIVITY
        >>> if event_category == Category.CONNECTIVITY:
        ...     print("This is a connectivity issue")
        
        >>> # Get string value
        >>> str(Category.PERFORMANCE)
        'PERFORMANCE'
    """
    CONNECTIVITY = "CONNECTIVITY"
    PERFORMANCE = "PERFORMANCE"
    INFRASTRUCTURE = "INFRASTRUCTURE"
    APPLICATION = "APPLICATION"
    SECURITY = "SECURITY"


def is_valid_category(value) -> bool:
    """
    Validate if a given value is a valid Category.
    
    This function checks whether the input can be converted to a Category
    enum member. It handles both enum instances and strings.
    
    Args:
        value: Value to check (can be Category enum or string)
    
    Returns:
        bool: True if value is a valid Category, False otherwise
    
    Examples:
        >>> is_valid_category("CONNECTIVITY")
        True
        >>> is_valid_category("INVALID")
        False
        >>> is_valid_category(Category.PERFORMANCE)
        True
        >>> is_valid_category("connectivity")  # Case-sensitive
        False
    """
    try:
        Category(value)
        return True
    except ValueError:
        return False


# ============================================================================
# Additional utility functions
# ============================================================================

def get_all_categories() -> list[str]:
    """
    Get a list of all category values.
    
    Returns:
        list[str]: All category strings
        
    Example:
        >>> categories = get_all_categories()
        >>> print(categories)
        ['CONNECTIVITY', 'PERFORMANCE', 'INFRASTRUCTURE', 'APPLICATION', 'SECURITY']
    """
    return [c.value for c in Category]


def get_category_descriptions() -> dict[str, str]:
    """
    Get human-readable descriptions for each category.
    
    Returns:
        dict: Mapping of category to description
        
    Example:
        >>> desc = get_category_descriptions()
        >>> print(desc['CONNECTIVITY'])
        'Basic network connectivity issues'
    """
    return {
        "CONNECTIVITY": "Basic network connectivity issues (Internet down, router unreachable, DNS failure)",
        "PERFORMANCE": "Speed and quality problems (High latency, packet loss, degraded throughput)",
        "INFRASTRUCTURE": "Hardware and equipment issues (Router failure, switch problems, cable faults)",
        "APPLICATION": "Service and application failures (Website unreachable, API timeout, service down)",
        "SECURITY": "Security-related events (Unusual traffic, authentication failures, attacks)",
    }


def categorize_by_keyword(text: str) -> Category | None:
    """
    Attempt to categorize a text description based on keywords.
    
    This is a helper function for automatically categorizing events
    based on their description text.
    
    Args:
        text (str): Description text to analyze
        
    Returns:
        Category or None: Best matching category, or None if no match
        
    Example:
        >>> cat = categorize_by_keyword("Internet connection lost")
        >>> print(cat)
        Category.CONNECTIVITY
    """
    text_lower = text.lower()
    
    # Keyword mappings
    keywords = {
        Category.CONNECTIVITY: ['internet', 'connection', 'network', 'dns', 'ping', 'router'],
        Category.PERFORMANCE: ['latency', 'slow', 'packet loss', 'degraded', 'speed', 'performance'],
        Category.INFRASTRUCTURE: ['router', 'switch', 'cable', 'hardware', 'equipment', 'power'],
        Category.APPLICATION: ['website', 'app', 'service', 'api', 'http', 'https', 'web'],
        Category.SECURITY: ['security', 'auth', 'login', 'attack', 'threat', 'firewall'],
    }
    
    for category, words in keywords.items():
        if any(word in text_lower for word in words):
            return category
    
    return None


# Export public interface
__all__ = [
    'Category',
    'is_valid_category',
    'get_all_categories',
    'get_category_descriptions',
    'categorize_by_keyword'
]
