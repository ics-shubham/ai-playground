"""Formatting utilities for electricity service responses."""

from datetime import datetime


def format_datetime(datetime_str: str, format_str: str = "%d %b %Y, %I:%M %p") -> str:
    """Format a datetime string to a more readable format.
    
    Args:
        datetime_str: ISO format datetime string.
        format_str: Output format string.
        
    Returns:
        Formatted datetime string.
    """
    try:
        dt = datetime.strptime(datetime_str, "%Y-%m-%dT%H:%M:%SZ")
        return dt.strftime(format_str)
    except ValueError:
        return datetime_str


def get_status_emoji(status: str) -> str:
    """Get an appropriate emoji for a status.
    
    Args:
        status: Status string.
        
    Returns:
        An empty string as we're removing emojis.
    """
    # Return empty string instead of emojis
    return ""


def get_days_until(date_str: str, date_format: str = "%Y-%m-%d") -> int:
    """Calculate the number of days between today and a future date.
    
    Args:
        date_str: Date string.
        date_format: Format of the date string.
        
    Returns:
        Number of days until the date (negative for past dates).
    """
    try:
        date = datetime.strptime(date_str, date_format)
        today = datetime.now()
        delta = date - today
        return delta.days
    except ValueError:
        return 0