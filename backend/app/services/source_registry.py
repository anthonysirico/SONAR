"""
SONAR — Data Source Registry
Defines all available OSINT data sources with their metadata,
authentication requirements, and capabilities.
"""

DATA_SOURCES = [
    {
        "id": "usaspending",
        "name": "USASpending.gov",
        "description": "Federal contract and award data (FPDS)",
        "auth_required": False,
        "auth_type": None,
        "auth_fields": [],
        "search_types": ["keyword", "piid"],
        "status": "active",
    },
    {
        "id": "sam_gov",
        "name": "SAM.gov",
        "description": "Entity registration, exclusions, and integrity data",
        "auth_required": True,
        "auth_type": "api_key",
        "auth_fields": ["api_key"],
        "search_types": ["keyword"],
        "status": "active",
    },
]


def get_all_sources() -> list[dict]:
    """Return all registered data sources."""
    return DATA_SOURCES


def get_source(source_id: str) -> dict | None:
    """Return a single data source by ID."""
    for s in DATA_SOURCES:
        if s["id"] == source_id:
            return s
    return None


def get_active_sources() -> list[dict]:
    """Return only active data sources."""
    return [s for s in DATA_SOURCES if s["status"] == "active"]


def sources_for_search_type(search_type: str) -> list[dict]:
    """Return sources that support the given search type."""
    return [
        s for s in DATA_SOURCES
        if s["status"] == "active" and search_type in s["search_types"]
    ]
