"""Data and utilities for outage information."""

from typing import Dict, Any, Optional

# More realistic outage database
OUTAGE_DATABASE: Dict[str, Dict[str, str]] = {
    "sector-18": {
        "status": "ongoing",
        "reason": "Emergency transformer replacement",
        "eta": "2025-04-14T16:30:00Z",
        "area": "Sector 18",
        "affected_blocks": "A, B, C, D",
        "outage_id": "OUT-25041401"
    },
    "rajendra-nagar": {
        "status": "resolved",
        "reason": "Storm damage to transmission lines",
        "eta": "2025-04-13T22:00:00Z",
        "area": "Rajendra Nagar",
        "affected_blocks": "Main road, 1st to 5th cross",
        "outage_id": "OUT-25041256"
    },
    "vasundhara": {
        "status": "ongoing",
        "reason": "unknown",
        "eta": "2025-04-14T19:45:00Z",
        "area": "Vasundhara",
        "affected_blocks": "Sectors 1-5",
        "outage_id": "OUT-25041402"
    },
    "indirapuram": {  # Alternative spelling for better matching
        "status": "scheduled",
        "reason": "Substation maintenance and capacity upgrade",
        "eta": "2025-04-15T14:00:00Z",
        "area": "Indira Puram",
        "affected_blocks": "Vaibhav Khand, Abhay Khand",
        "outage_id": "OUT-25041398"
    }
}

# Valid area keywords for fuzzy matching
AREA_KEYWORDS = {
    "sector 18": "sector-18",
    "sector-18": "sector-18",
    "s-18": "sector-18",
    "s18": "sector-18",
    "rajendra nagar": "rajendra-nagar",
    "rajendranagar": "rajendra-nagar",
    "rajendra-nagar": "rajendra-nagar",
    "raj nagar": "rajendra-nagar",
    "indira puram": "indirapuram",
    "indirapuram": "indirapuram",
    "indira-puram": "indirapuram",
    "vasundhara": "vasundhara"
}


def find_outage_by_area(area: str) -> Optional[Dict[str, str]]:
    """Find outage information for a given area using fuzzy matching.
    
    Args:
        area: The area name to search for.
        
    Returns:
        Outage information if found, None otherwise.
    """
    # Normalize input
    area_input = area.lower().strip()
    
    # Try direct matching first
    area_key = area_input.replace(" ", "-")
    if area_key in OUTAGE_DATABASE:
        return OUTAGE_DATABASE[area_key]
    
    # Try fuzzy matching with predefined keywords
    area_key = AREA_KEYWORDS.get(area_input)
    if area_key and area_key in OUTAGE_DATABASE:
        return OUTAGE_DATABASE[area_key]
        
    return None


def get_valid_areas() -> list[str]:
    """Get a list of valid areas from the outage database.
    
    Returns:
        A list of area names.
    """
    return list(set(outage["area"] for outage in OUTAGE_DATABASE.values()))