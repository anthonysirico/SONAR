"""
SONAR — SAM.gov Exclusions API Client
Queries the SAM.gov Exclusions endpoint for debarred/suspended entities.
Uses the same API key as the Entity Management API.

Base URL: https://api.sam.gov/entity-information/v3/exclusions
Authentication: API key required.
"""

import httpx
from typing import Optional

BASE_URL = "https://api.sam.gov/entity-information/v3/exclusions"
TIMEOUT = 30.0


async def search_exclusions(keyword: str, api_key: str, limit: int = 10) -> dict:
    """
    Search SAM.gov exclusions by entity name.
    Returns active exclusion records (debarments, suspensions, etc.).
    """
    params = {
        "api_key": api_key,
        "q": keyword,
        "page": 0,
        "size": min(limit, 10),
    }

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.get(BASE_URL, params=params)
        resp.raise_for_status()
        return resp.json()


async def check_exclusion_by_uei(uei: str, api_key: str) -> dict:
    """Check if a specific entity (by UEI) has any exclusion records."""
    params = {
        "api_key": api_key,
        "ueiSAM": uei,
    }

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.get(BASE_URL, params=params)
        resp.raise_for_status()
        return resp.json()


def map_exclusion_to_summary(record: dict) -> dict:
    """Map a SAM.gov exclusion record to a SONAR-compatible summary."""
    return {
        "entity_name": record.get("name", ""),
        "uei": record.get("ueiSAM", ""),
        "cage_code": record.get("cageCode", ""),
        "exclusion_type": record.get("exclusionType", ""),
        "exclusion_program": record.get("exclusionProgram", ""),
        "excluding_agency": record.get("excludingAgencyName", ""),
        "action_date": record.get("actionDate", ""),
        "termination_date": record.get("terminationDate", ""),
        "classification": record.get("classificationType", ""),
        "active_date": record.get("activeDate", ""),
        "description": record.get("description", ""),
        "source": "sam_exclusions",
    }
