"""
SONAR — SAM.gov Entity Management API Client (v3)
Handles entity search, detail retrieval, and mapping to SONAR graph schema.
Base URL: https://api.sam.gov/entity-information/v3
Authentication: API key required (Personal or System Account).

Public data only — no FOUO/Sensitive access.
"""

import httpx
from typing import Optional

BASE_URL = "https://api.sam.gov/entity-information/v3"
TIMEOUT = 30.0


# ─── API Calls ───────────────────────────────────────────────

async def search_entities(keyword: str, api_key: str, limit: int = 10) -> dict:
    """
    Search SAM.gov entities by keyword (company/legal business name).
    Uses the free-text 'q' parameter against the Entity Management API v3.
    Returns entityRegistration and coreData sections.
    """
    params = {
        "api_key": api_key,
        "q": keyword,
        "registrationStatus": "A",
        "includeSections": "entityRegistration,coreData",
        "page": 0,
        "size": min(limit, 10),  # SAM.gov max page size is 10
    }

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.get(f"{BASE_URL}/entities", params=params)
        resp.raise_for_status()
        return resp.json()


async def get_entity_by_uei(uei: str, api_key: str) -> dict:
    """Fetch a specific entity by UEI for enrichment."""
    params = {
        "api_key": api_key,
        "ueiSAM": uei,
        "includeSections": "entityRegistration,coreData",
    }

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.get(f"{BASE_URL}/entities", params=params)
        resp.raise_for_status()
        data = resp.json()
        entities = data.get("entityData", [])
        if entities:
            return entities[0]
        return {}


# ─── Response Mappers ────────────────────────────────────────

def map_entity_to_company(entity: dict) -> dict:
    """Map SAM.gov entity data → SONAR Company node dict for enrichment."""
    reg = entity.get("entityRegistration", {})
    core = entity.get("coreData", {})
    phys_addr = core.get("physicalAddress", {})
    general = core.get("generalInformation", {})
    biz_types = core.get("businessTypes", {})

    # Extract set-aside / SBA certifications
    set_aside_status = []
    for sba in biz_types.get("sbaBusinessTypeList", []):
        desc = sba.get("sbaBusinessTypeDesc")
        if desc:
            set_aside_status.append(desc)
    for bt in biz_types.get("businessTypeList", []):
        code = bt.get("businessTypeCode", "")
        # Common small-business set-aside codes
        if code in ("27", "A5", "QF", "A2", "JT", "2X"):
            desc = bt.get("businessTypeDesc", "")
            if desc and desc not in set_aside_status:
                set_aside_status.append(desc)

    exclusion_flag = reg.get("exclusionStatusFlag", "N") == "Y"

    return {
        "uei": reg.get("ueiSAM", ""),
        "name": reg.get("legalBusinessName", ""),
        "cage_code": reg.get("cageCode", ""),
        "address": _build_address_string(phys_addr),
        "entity_type": general.get("entityStructureDesc", ""),
        "set_aside_status": set_aside_status,
        "exclusion_flag": exclusion_flag,
        "active": reg.get("registrationStatus", "") == "Active",
        "registration_date": reg.get("registrationDate", ""),
        "registration_expiration": reg.get("registrationExpirationDate", ""),
        "dba_name": reg.get("dbaName", ""),
        "state_of_incorporation": general.get("stateOfIncorporationDesc", ""),
        "country_of_incorporation": general.get("countryOfIncorporationDesc", ""),
        "profit_structure": general.get("profitStructureDesc", ""),
        "source": "SAM.gov",
    }


def map_entity_to_summary(entity: dict) -> dict:
    """Map SAM.gov entity → lightweight summary for search result display."""
    reg = entity.get("entityRegistration", {})
    core = entity.get("coreData", {})
    phys_addr = core.get("physicalAddress", {})
    general = core.get("generalInformation", {})

    exclusion_flag = reg.get("exclusionStatusFlag", "N") == "Y"

    return {
        "legal_business_name": reg.get("legalBusinessName", ""),
        "dba_name": reg.get("dbaName", ""),
        "uei": reg.get("ueiSAM", ""),
        "cage_code": reg.get("cageCode", ""),
        "registration_status": reg.get("registrationStatus", ""),
        "exclusion_flag": exclusion_flag,
        "entity_type": general.get("entityStructureDesc", ""),
        "address": _build_address_string(phys_addr),
        "state_of_incorporation": general.get("stateOfIncorporationDesc", ""),
        "registration_date": reg.get("registrationDate", ""),
        "expiration_date": reg.get("registrationExpirationDate", ""),
        "activation_date": reg.get("activationDate", ""),
        "source": "sam_gov",
    }


# ─── Helpers ─────────────────────────────────────────────────

def _build_address_string(address: Optional[dict]) -> str:
    if not address:
        return ""
    parts = [
        address.get("addressLine1", ""),
        address.get("city", ""),
        address.get("stateOrProvinceCode", ""),
        address.get("zipCode", ""),
    ]
    return ", ".join(p for p in parts if p)
