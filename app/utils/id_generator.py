# ABOUTME: Utility for generating prefixed IDs for different entity types
# ABOUTME: Ensures consistent ID format across the application

import uuid
from typing import Literal


def generate_id(entity_type: Literal["agent", "conversation", "node", "message"]) -> str:
    """Generate a prefixed UUID for different entity types."""
    prefixes = {
        "agent": "a",
        "conversation": "c", 
        "node": "n",
        "message": "m"
    }
    
    prefix = prefixes.get(entity_type, "")
    return f"{prefix}-{str(uuid.uuid4())}"


def extract_uuid(prefixed_id: str) -> str:
    """Extract the UUID portion from a prefixed ID."""
    if "-" in prefixed_id:
        parts = prefixed_id.split("-", 1)
        if len(parts) == 2:
            return parts[1]
    return prefixed_id


def validate_id_format(prefixed_id: str, expected_prefix: str) -> bool:
    """Validate that an ID has the expected prefix."""
    return prefixed_id.startswith(f"{expected_prefix}-")