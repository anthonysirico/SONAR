"""
SONAR — USASpending.gov API Client
Handles search, award detail retrieval, and mapping to SONAR graph schema.
Base URL: https://api.usaspending.gov
No authentication required.
"""

import httpx
from typing import Optional

BASE_URL = "https://api.usaspending.gov"
TIMEOUT = 30.0

# Contract award type codes (excludes grants, loans, direct payments)
CONTRACT_CODES = ["A", "B", "C", "D"]
IDV_CODES = ["IDV_A", "IDV_B", "IDV_B_A", "IDV_B_B", "IDV_B_C", "IDV_C", "IDV_D", "IDV_E"]
ALL_CONTRACT_CODES = CONTRACT_CODES + IDV_CODES


# ─── API Calls ───────────────────────────────────────────────

async def _search_awards(keyword: str, award_codes: list, fields: list,
                         limit: int = 25, page: int = 1) -> dict:
    """Internal: single search call against one award type group."""
    payload = {
        "filters": {
            "keywords": [keyword],
            "award_type_codes": award_codes,
        },
        "fields": fields,
        "page": page,
        "limit": limit,
        "sort": "Award Amount",
        "order": "desc",
    }
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.post(f"{BASE_URL}/api/v2/search/spending_by_award/", json=payload)
        resp.raise_for_status()
        return resp.json()


# Fields valid for contracts (A/B/C/D)
CONTRACT_FIELDS = [
    "Award ID",
    "Recipient Name",
    "Recipient UEI",
    "Start Date",
    "End Date",
    "Award Amount",
    "Awarding Agency",
    "Awarding Sub Agency",
    "Contract Award Type",
    "recipient_id",
    "generated_internal_id",
]

# Fields valid for IDVs — no "End Date" (IDVs use "Last Date to Order" instead)
IDV_FIELDS = [
    "Award ID",
    "Recipient Name",
    "Recipient UEI",
    "Start Date",
    "Award Amount",
    "Awarding Agency",
    "Awarding Sub Agency",
    "Contract Award Type",
    "recipient_id",
    "generated_internal_id",
]


async def search_awards_by_keyword(keyword: str, limit: int = 25, page: int = 1) -> dict:
    """Search contract awards by keyword. Queries contracts and IDVs separately, merges results."""
    # Primary: definitive contracts
    contract_resp = await _search_awards(keyword, CONTRACT_CODES, CONTRACT_FIELDS, limit, page)

    # Secondary: IDVs (best-effort, don't fail the whole search)
    try:
        idv_resp = await _search_awards(keyword, IDV_CODES, IDV_FIELDS, limit, page)
        idv_results = idv_resp.get("results", [])
    except Exception:
        idv_results = []

    # Merge: contracts first, then IDVs, cap at limit
    combined = contract_resp.get("results", []) + idv_results
    combined.sort(key=lambda r: r.get("Award Amount") or 0, reverse=True)
    combined = combined[:limit]

    contract_meta = contract_resp.get("page_metadata", {})
    contract_total = contract_meta.get("total", 0)
    idv_total = idv_resp.get("page_metadata", {}).get("total", 0) if idv_results else 0

    return {
        "results": combined,
        "page_metadata": {
            "page": page,
            "hasNext": contract_meta.get("hasNext", False),
            "total": contract_total + idv_total,
        },
    }


async def search_awards_by_piid(piid: str, limit: int = 10) -> dict:
    """Search awards by PIID. Tries contracts first, falls back to IDVs."""
    contract_resp = await _search_awards(piid, CONTRACT_CODES, CONTRACT_FIELDS, limit)
    results = contract_resp.get("results", [])

    if not results:
        try:
            idv_resp = await _search_awards(piid, IDV_CODES, IDV_FIELDS, limit)
            results = idv_resp.get("results", [])
            return idv_resp
        except Exception:
            pass

    return contract_resp


async def get_award_detail(internal_id: str) -> dict:
    """Fetch full award detail by USASpending internal ID."""
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.get(f"{BASE_URL}/api/v2/awards/{internal_id}/")
        resp.raise_for_status()
        return resp.json()


async def get_recipient_profile(recipient_id: str) -> dict:
    """Fetch recipient (vendor) profile."""
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.get(f"{BASE_URL}/api/v2/recipient/{recipient_id}/")
        resp.raise_for_status()
        return resp.json()


# ─── Response Mappers ────────────────────────────────────────
# Convert USASpending JSON into dicts compatible with graph_service functions.

def map_award_to_contract(award: dict) -> dict:
    """Map USASpending award detail → SONAR Contract node dict."""
    latest = award.get("latest_transaction_contract_data") or {}
    pop = award.get("period_of_performance") or {}
    return {
        "piid": award.get("piid") or award.get("fain") or "",
        "award_amount": award.get("base_and_all_options_value") or 0.0,
        "obligated_amount": award.get("total_obligation") or 0.0,
        "award_date": pop.get("start_date") or "",
        "contract_type": latest.get("type_of_contract_pricing") or "",
        "competition_type": _map_competition(latest.get("extent_competed")),
        "set_aside_type": latest.get("type_set_aside") or "",
        "naics_code": latest.get("naics") or "",
        "place_of_performance": _build_pop_string(award.get("place_of_performance")),
        "mod_count": latest.get("number_of_actions") or 0,
    }


def map_award_to_company(award: dict) -> dict:
    """Map USASpending award detail → SONAR Company node dict."""
    recipient = award.get("recipient") or {}
    location = recipient.get("location") or {}
    return {
        "uei": recipient.get("recipient_uei") or recipient.get("recipient_unique_id") or "",
        "name": recipient.get("recipient_name") or "",
        "cage_code": "",  # Not in USASpending — enriched via SAM.gov later
        "address": _build_address_string(location),
        "naics_codes": [award.get("latest_transaction_contract_data", {}).get("naics", "")],
        "entity_type": "",
        "set_aside_status": [],
        "exclusion_flag": False,
        "active": True,
        "first_seen": award.get("period_of_performance", {}).get("start_date") or "",
        "source": "USASpending",
    }


def map_award_to_organization(award: dict) -> dict:
    """Map USASpending award detail → SONAR Organization node dict."""
    awarding = award.get("awarding_agency") or {}
    sub = awarding.get("subtier_agency") or {}
    top = awarding.get("toptier_agency") or {}
    # Prefer subtier (e.g., "Department of the Navy") over toptier ("Department of Defense")
    name = sub.get("name") or top.get("name") or ""
    return {
        "name": name,
        "org_type": "awarding_agency",
        "uic": sub.get("abbreviation") or "",
    }


def map_award_to_awarded_edge(award: dict) -> dict:
    """Map USASpending award detail → SONAR AWARDED_TO edge props."""
    latest = award.get("latest_transaction_contract_data") or {}
    pop = award.get("period_of_performance") or {}
    return {
        "piid": award.get("piid") or "",
        "weight": _normalize_amount(award.get("total_obligation") or 0),
        "confidence": 0.90,  # Federal source, high but not manual-verified
        "source": ["USASpending"],
        "amount": award.get("total_obligation") or 0.0,
        "date": pop.get("start_date") or "",
        "competition_type": _map_competition(latest.get("extent_competed")),
    }


def map_search_result_summary(result: dict) -> dict:
    """Map a spending_by_award search result to a lightweight summary."""
    return {
        "award_id": result.get("Award ID") or "",
        "recipient_name": result.get("Recipient Name") or "",
        "recipient_uei": result.get("Recipient UEI") or "",
        "award_amount": result.get("Award Amount") or 0,
        "awarding_agency": result.get("Awarding Agency") or "",
        "awarding_sub_agency": result.get("Awarding Sub Agency") or "",
        "start_date": result.get("Start Date") or "",
        "end_date": result.get("End Date") or "",
        "award_type": result.get("Contract Award Type") or "",
        "internal_id": result.get("generated_internal_id") or result.get("internal_id") or "",
        "recipient_id": result.get("recipient_id") or "",
    }


# ─── Helpers ─────────────────────────────────────────────────

def _build_address_string(location: dict) -> str:
    parts = [
        location.get("address_line1", ""),
        location.get("city_name", ""),
        location.get("state_code", ""),
        location.get("zip5", ""),
    ]
    return ", ".join(p for p in parts if p)


def _build_pop_string(pop: Optional[dict]) -> str:
    if not pop:
        return ""
    parts = [
        pop.get("city_name", ""),
        pop.get("state_code", ""),
        pop.get("country_name", ""),
    ]
    return ", ".join(p for p in parts if p)


def _map_competition(extent_competed: Optional[str]) -> str:
    """Normalize USASpending competition codes to SONAR terms."""
    mapping = {
        "A": "Full and Open",
        "B": "Not Available for Competition",
        "C": "Not Competed",
        "D": "Full and Open after Exclusion",
        "E": "Follow On",
        "F": "Competed under SAP",
        "G": "Not Competed under SAP",
        "CDO": "Competitive Delivery Order",
        "NDO": "Non-Competitive Delivery Order",
    }
    return mapping.get(extent_competed or "", extent_competed or "")


def _normalize_amount(amount: float) -> float:
    """Normalize dollar amounts to a 0-1 weight.
    Scale: $10M+ = 1.0, log-scaled below that.
    """
    import math
    if amount <= 0:
        return 0.0
    if amount >= 10_000_000:
        return 1.0
    return round(min(math.log10(max(amount, 1)) / 7.0, 1.0), 4)