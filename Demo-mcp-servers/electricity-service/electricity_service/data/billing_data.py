"""Data and utilities for billing information."""

import re
from typing import Dict, Optional, Pattern

# Valid meter number pattern
METER_PATTERN: Pattern = re.compile(r"^UP\d{10}$", re.IGNORECASE)

# More realistic billing database with Indian-style meter numbers
BILLING_DATABASE: Dict[str, Dict[str, str]] = {
    "UP7284651023": {
        "customer_name": "Rajesh Sharma",
        "due_amount": "₹2,345.50",
        "due_date": "2025-04-20",
        "status": "Pending",
        "last_reading": "8723",
        "consumption": "342 units",
        "connection_type": "Domestic"
    },
    "UP7291382456": {
        "customer_name": "Priya Patel",
        "due_amount": "₹0.00",
        "due_date": "2025-04-05",
        "status": "Paid",
        "last_reading": "6218",
        "consumption": "187 units",
        "connection_type": "Domestic"
    },
    "UP7265893147": {
        "customer_name": "Sunil Verma",
        "due_amount": "₹1,870.25",
        "due_date": "2025-04-17",
        "status": "Pending",
        "last_reading": "12983",
        "consumption": "256 units",
        "connection_type": "Domestic"
    },
    "UP7234129876": {
        "customer_name": "Kavita Gupta",
        "due_amount": "₹4,320.75",
        "due_date": "2025-04-15",
        "status": "Overdue",
        "last_reading": "45621",
        "consumption": "528 units",
        "connection_type": "Domestic"  
    },
    "UP7287654238": {
        "customer_name": "Axis Bank (Branch 142)",
        "due_amount": "₹13,245.80",
        "due_date": "2025-04-18",
        "status": "Pending",
        "last_reading": "82641",
        "consumption": "1245 units",
        "connection_type": "Commercial"
    }
}


def validate_meter_number(meter_number: str) -> bool:
    """Validate the format of a meter number.
    
    Args:
        meter_number: The meter number to validate.
        
    Returns:
        True if valid, False otherwise.
    """
    return bool(METER_PATTERN.match(meter_number))


def find_billing_by_meter(meter_number: str) -> Optional[Dict[str, str]]:
    """Find billing information for a given meter number.
    
    Args:
        meter_number: The meter number to search for.
        
    Returns:
        Billing information if found, None otherwise.
    """
    return BILLING_DATABASE.get(meter_number.upper())