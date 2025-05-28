"""Service functions for handling outage information."""

import logging

from electricity_service.data.outage_data import find_outage_by_area, get_valid_areas
from electricity_service.utils.formatters import format_datetime

logger = logging.getLogger(__name__)


async def check_outage(area: str) -> str:
    """Check outage information for a given area.
    
    Args:
        area: Area name to check.
        
    Returns:
        Formatted response string with outage information.
    """
    logger.info(f"Checking outage for area: {area}")
    
    # Normalize and find outage
    area = area.strip()
    outage = find_outage_by_area(area)
    
    if not outage:
        # List valid areas in the error message
        valid_areas = get_valid_areas()
        suggestions = ", ".join(valid_areas)
        return (
            f"Error: No outage information found for '{area}'.\n\n"
            f"Valid areas in our system include: {suggestions}.\n\n"
            f"Please check your spelling or try one of the areas listed above."
        )
    
    # Format dates/times for better readability
    formatted_eta = format_datetime(outage['eta'])
    
    response = (
        f"Outage Info for {outage['area']} (ID: {outage['outage_id']})\n"
        f"- Status: {outage['status'].upper()}\n"
        f"- Reason: {outage['reason']}\n"
        f"- Affected Areas: {outage['affected_blocks']}\n"
        f"- Estimated Resolution: {formatted_eta}\n"
    )
    
    if outage['status'] == "resolved":
        response += "\nPower has been restored in this area. If you're still experiencing issues, please contact our helpline at 1800-XXX-XXXX."
    elif outage['status'] == "ongoing":
        response += "\nOur technical team is working to resolve this issue. We apologize for the inconvenience."
    elif outage['status'] == "scheduled":
        response += "\nThis is a planned outage for essential maintenance. Please plan accordingly."
    
    logger.debug(f"Generated outage response for area: {area}")
    return response