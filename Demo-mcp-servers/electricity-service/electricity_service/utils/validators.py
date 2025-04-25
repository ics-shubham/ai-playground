"""Validation utilities for electricity service."""

import re
from typing import Pattern, Dict, Any, Tuple, Optional

# This can be extended with more validation functions as needed


def validate_input(input_dict: Dict[str, Any], required_keys: list) -> Tuple[bool, Optional[str]]:
    """Validate that all required keys exist in an input dictionary.
    
    Args:
        input_dict: Dictionary to validate.
        required_keys: List of required keys.
        
    Returns:
        Tuple of (is_valid, error_message).
    """
    missing_keys = [key for key in required_keys if key not in input_dict]
    if missing_keys:
        return False, f"Missing required keys: {', '.join(missing_keys)}"
    return True, None


def validate_pattern(value: str, pattern: Pattern) -> bool:
    """Validate that a string matches a pattern.
    
    Args:
        value: String to validate.
        pattern: Compiled regex pattern.
        
    Returns:
        True if valid, False otherwise.
    """
    return bool(pattern.match(value))