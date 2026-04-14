import httpx
from typing import Optional

BASE__URL = "https://api.opencorporates.com/v0.4"
TIMEOUT = 30.0

# ─── API Calls ───────────────────────────────────────────────
async def search_companies(name: str, api_key: Optional[str] = None, limit: int = 10) -> dict:
    """Search OpenCorporates for companies by name."""
    params = {
        "q": name,
        "per_page": min(limit, 100),  # OpenCorporates max per_page is 100
    }
    if api_key:
        params["api_token"] = api_key

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.get(f"{BASE__URL}/companies/search", params=params)
        resp.raise_for_status()
        return resp.json()
    
async def get_company_by_jurisdiction_and_number(jurisdiction_code: str, company_number: str, api_key: Optional[str] = None) -> dict:
    """Fetch a specific company by jurisdiction code and company number for enrichment."""
    params = {}
    if api_key:
        params["api_token"] = api_key

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.get(f"{BASE__URL}/companies/{jurisdiction_code}/{company_number}", params=params)
        resp.raise_for_status()
        return resp.json()

