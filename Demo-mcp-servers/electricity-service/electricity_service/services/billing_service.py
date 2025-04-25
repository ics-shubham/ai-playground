"""Service functions for handling billing information."""

import logging
from datetime import datetime

from electricity_service.data.billing_data import (
    validate_meter_number,
    find_billing_by_meter
)
from electricity_service.utils.formatters import get_days_until

logger = logging.getLogger(__name__)


async def check_billing(meter_number: str) -> str:
    """Check billing information for a given meter number.
    
    Args:
        meter_number: Meter number to check.
        
    Returns:
        Formatted response string with billing information.
    """
    logger.info(f"Checking billing for meter number: {meter_number}")
    
    # Normalize and validate meter number
    meter = meter_number.upper().strip()
    
    if not validate_meter_number(meter):
        return (
            "Error: Invalid meter number format. Please enter a valid meter number "
            "in the format 'UPXXXXXXXXXX' (UP followed by 10 digits)."
        )
        
    billing = find_billing_by_meter(meter)
    if not billing:
        return (
            f"Error: No billing record found for meter number '{meter}'.\n\n"
            f"Please verify your meter number and try again. If you've recently received "
            f"a new connection, your details may take up to 24 hours to appear in our system."
        )
    
    response = (
        f"Billing Info for {billing['customer_name']}\n"
        f"- Meter Number: {meter}\n"
        f"- Status: {billing['status']}\n"
        f"- Connection Type: {billing['connection_type']}\n"
        f"- Due Amount: {billing['due_amount']}\n"
        f"- Due Date: {billing['due_date']}\n"
        f"- Last Reading: {billing['last_reading']}\n"
        f"- Consumption: {billing['consumption']}\n"
    )
    
    # Add call-to-action based on status
    if billing['status'] == "Pending":
        days_left = get_days_until(billing['due_date'])
        if days_left > 0:
            response += f"\nYour payment is due in {days_left} days. Pay online at electricitypayments.in to avoid late fees."
        else:
            response += "\nYour payment is due today. Pay online at electricitypayments.in to avoid late fees."
    elif billing['status'] == "Overdue":
        response += "\nYour payment is overdue. Please settle your dues immediately to avoid disconnection."
    elif billing['status'] == "Paid":
        response += "\nThank you for your payment. Your next bill will be generated on the 1st of the next month."
    
    logger.debug(f"Generated billing response for meter: {meter}")
    return response