"""
SONAR — ProPublica Nonprofit Explorer API Client (v2)
Searches IRS 990 data via ProPublica's free API. No authentication required.

Provides:
  - Organization search by name
  - Full organization detail with filings (revenue, expenses, officers, comp)
  - Mapping to SONAR graph schema (Filing990 nodes, Individual/OFFICER_OF edges)

Base URL: https://projects.propublica.org/nonprofits/api/v2
Rate limit: Be courteous — no published limit, but throttle to ~2 req/s.
"""

import httpx
from typing import Optional

BASE_URL = "https://projects.propublica.org/nonprofits/api/v2"
TIMEOUT = 30.0


# ─── API Calls ───────────────────────────────────────────────

async def search_nonprofits(keyword: str, page: int = 0) -> dict:
    """
    Search nonprofits by name/keyword.
    Returns Organization objects (no financial data — use org detail for that).
    Max 25 results per page.
    """
    params = {"q": keyword, "page": page}

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.get(f"{BASE_URL}/search.json", params=params)
        resp.raise_for_status()
        return resp.json()


async def get_organization(ein: str) -> dict:
    """
    Fetch full organization detail by EIN (integer, no dashes).
    Returns org metadata + filings_with_data (990 financial data).
    """
    # Strip dashes if present
    ein_clean = ein.replace("-", "").strip()

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.get(f"{BASE_URL}/organizations/{ein_clean}.json")
        resp.raise_for_status()
        return resp.json()


# ─── Response Mappers ────────────────────────────────────────

def map_search_result_summary(org: dict) -> dict:
    """Map a ProPublica search result Organization object to a lightweight summary."""
    return {
        "ein": str(org.get("ein", "")),
        "strein": org.get("strein", ""),
        "name": org.get("name", ""),
        "sub_name": org.get("sub_name", ""),
        "city": org.get("city", ""),
        "state": org.get("state", ""),
        "ntee_code": org.get("ntee_code", ""),
        "subsection_code": org.get("subseccd", ""),
        "classification_codes": org.get("classification_codes", ""),
        "ruling_date": org.get("ruling_date", ""),
        "tax_period": org.get("tax_period", ""),
        "income_amount": org.get("income_amount", 0),
        "revenue_amount": org.get("revenue_amount", 0),
        "asset_amount": org.get("asset_amount", 0),
        "source": "propublica_990",
    }


def map_filing_to_990(filing: dict, org: dict) -> dict:
    """
    Map a ProPublica Filing object to a SONAR Filing990 node dict.
    Extracts revenue, expenses, assets, officer compensation data.
    """
    return {
        "ein": str(filing.get("ein") or org.get("ein", "")),
        "tax_period": filing.get("tax_prd", ""),
        "tax_year": filing.get("tax_prd_yr", 0),
        "form_type": _form_type_label(filing.get("formtype")),
        "total_revenue": filing.get("totrevenue", 0) or 0,
        "total_expenses": filing.get("totfuncexpns", 0) or 0,
        "total_assets": filing.get("totassetsend", 0) or 0,
        "total_liabilities": filing.get("totliabend", 0) or 0,
        "net_assets": (filing.get("totassetsend", 0) or 0) - (filing.get("totliabend", 0) or 0),
        "officer_compensation_pct": filing.get("pct_compnsatncurrofcr", 0) or 0,
        # Form 990 specific fields (may be None for 990-EZ/PF)
        "program_service_revenue": filing.get("prgmservrev", 0) or 0,
        "contributions_grants": filing.get("totcntrbgfts", 0) or 0,
        "investment_income": filing.get("invstmntinc", 0) or 0,
        "government_grants": filing.get("grntstogovt", 0) or 0,
        # Compensation fields
        "comp_curnt_ofcrs_key": filing.get("compnsatncurrofcr", 0) or 0,
        "comp_former_ofcrs": filing.get("compnsatnandothr", 0) or 0,
        "other_salaries": filing.get("othrsalwages", 0) or 0,
        "total_compensation": (
            (filing.get("compnsatncurrofcr", 0) or 0) +
            (filing.get("compnsatnandothr", 0) or 0) +
            (filing.get("othrsalwages", 0) or 0)
        ),
        "pdf_url": filing.get("pdf_url", ""),
        "source": "propublica_990",
    }


def map_org_to_nonprofit_summary(data: dict) -> dict:
    """
    Map full org detail response to a SONAR-compatible nonprofit summary.
    Includes latest filing financial data for quick risk assessment.
    """
    org = data.get("organization", {})
    filings = data.get("filings_with_data", [])

    # Get the most recent filing
    latest = filings[0] if filings else {}

    return {
        "ein": str(org.get("ein", "")),
        "name": org.get("name", ""),
        "city": org.get("city", ""),
        "state": org.get("state", ""),
        "ntee_code": org.get("ntee_code", ""),
        "subsection_code": org.get("subseccd", ""),
        "filing_count": len(filings),
        "latest_tax_year": latest.get("tax_prd_yr", 0),
        "latest_revenue": latest.get("totrevenue", 0) or 0,
        "latest_expenses": latest.get("totfuncexpns", 0) or 0,
        "latest_assets": latest.get("totassetsend", 0) or 0,
        "officer_comp_pct": latest.get("pct_compnsatncurrofcr", 0) or 0,
        "source": "propublica_990",
    }


def extract_officers_from_filing(filing: dict) -> list[dict]:
    """
    Extract officer/key employee data from a 990 filing.
    Note: ProPublica summary data includes aggregate compensation
    but not individual officer names. Individual names require
    parsing the XML e-file data directly.

    For now, we return aggregate compensation data that can be
    associated with the Company node.
    """
    officers = []

    comp_current = filing.get("compnsatncurrofcr", 0) or 0
    comp_other = filing.get("compnsatnandothr", 0) or 0

    if comp_current > 0:
        officers.append({
            "category": "Current Officers/Directors/Key Employees",
            "total_compensation": comp_current,
            "source": "990_aggregate",
        })

    if comp_other > 0:
        officers.append({
            "category": "Former/Disqualified Persons",
            "total_compensation": comp_other,
            "source": "990_aggregate",
        })

    return officers


# ─── Helpers ─────────────────────────────────────────────────

def _form_type_label(code) -> str:
    """Convert ProPublica formtype code to human label."""
    mapping = {
        0: "990",
        1: "990-EZ",
        2: "990-PF",
    }
    return mapping.get(code, f"Unknown ({code})")
