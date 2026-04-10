"""
SONAR — Data Sources Router
Exposes available data sources and their authentication requirements
so the frontend knows what to display and prompt for.
"""

from fastapi import APIRouter
from app.services.source_registry import get_all_sources

router = APIRouter()


@router.get("/")
async def list_sources():
    """Return all registered data sources with auth metadata."""
    return {"sources": get_all_sources()}
