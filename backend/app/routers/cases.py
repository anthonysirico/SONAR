"""
SONAR — Cases Router
Case management and data source search/ingest endpoints.

Workflow:
  1. POST /api/cases/              → create a case
  2. POST /api/cases/{id}/search   → search USASpending, preview results
  3. POST /api/cases/{id}/ingest   → pull award details, write to Neo4j
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
import logging

from app.services import case_service
from app.services import usaspending
from app.services import graph_service
from app.services import entity_resolution

logger = logging.getLogger("sonar.cases")

router = APIRouter()


# ─── Request / Response Models ───────────────────────────────

class CaseCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str = ""

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    search_type: str = Field(
        default="keyword",
        description="keyword | piid"
    )
    limit: int = Field(default=25, ge=1, le=100)

class IngestRequest(BaseModel):
    """Cherry-pick which search results to pull into the graph."""
    internal_ids: list[str] = Field(
        ...,
        min_length=1,
        description="USASpending internal_id values from search results"
    )


# ─── Case CRUD ───────────────────────────────────────────────

@router.post("/")
async def create_case(body: CaseCreate):
    case = case_service.create_case(body.name, body.description)
    if not case:
        raise HTTPException(500, "Failed to create case")
    return {"status": "created", "case": case}


@router.get("/")
async def list_cases(status: Optional[str] = None):
    cases = case_service.list_cases(status)
    return {"cases": cases}


@router.get("/{case_id}")
async def get_case(case_id: str):
    case = case_service.get_case(case_id)
    if not case:
        raise HTTPException(404, "Case not found")
    return {"case": case}


@router.patch("/{case_id}/close")
async def close_case(case_id: str):
    case = case_service.close_case(case_id)
    if not case:
        raise HTTPException(404, "Case not found")
    return {"status": "closed", "case": case}


@router.get("/{case_id}/graph")
async def get_case_graph(case_id: str):
    """Return all nodes/edges belonging to this case."""
    case = case_service.get_case(case_id)
    if not case:
        raise HTTPException(404, "Case not found")
    graph = case_service.get_case_graph(case_id)
    return {"case_id": case_id, "graph": graph}


# ─── Search (preview, no write) ─────────────────────────────

@router.post("/{case_id}/search")
async def search_usaspending(case_id: str, body: SearchRequest):
    """
    Search USASpending.gov and return preview results.
    Nothing is written to Neo4j yet — the investigator reviews
    and selects which awards to ingest.
    """
    # Verify case exists
    case = case_service.get_case(case_id)
    if not case:
        raise HTTPException(404, "Case not found")

    try:
        if body.search_type == "piid":
            raw = await usaspending.search_awards_by_piid(body.query, limit=body.limit)
        else:
            raw = await usaspending.search_awards_by_keyword(body.query, limit=body.limit, page=1)
    except Exception as e:
        logger.error(f"USASpending search failed: {e}")
        raise HTTPException(502, f"USASpending API error: {str(e)}")

    results = raw.get("results", [])
    page_meta = raw.get("page_metadata", {})

    summaries = [usaspending.map_search_result_summary(r) for r in results]

    return {
        "case_id": case_id,
        "query": body.query,
        "search_type": body.search_type,
        "result_count": len(summaries),
        "total_available": page_meta.get("total", 0),
        "has_next": page_meta.get("hasNext", False),
        "results": summaries,
    }


# ─── Ingest (write to graph) ────────────────────────────────

@router.post("/{case_id}/ingest")
async def ingest_awards(case_id: str, body: IngestRequest):
    """
    Fetch full award details from USASpending and write
    Company, Contract, Organization nodes + AWARDED_TO edges
    into Neo4j, linked to the case.
    """
    case = case_service.get_case(case_id)
    if not case:
        raise HTTPException(404, "Case not found")

    created_nodes = []
    errors = []

    for internal_id in body.internal_ids:
        try:
            award = await usaspending.get_award_detail(internal_id)
            nodes = _ingest_single_award(award, case_id)
            created_nodes.append(nodes)
        except Exception as e:
            logger.error(f"Failed to ingest award {internal_id}: {e}")
            errors.append({"internal_id": internal_id, "error": str(e)})

    case_service.update_case_timestamp(case_id)

    # Run entity resolution after ingest
    resolution = {}
    try:
        resolution = entity_resolution.resolve_companies()
    except Exception as e:
        logger.warning(f"Entity resolution failed: {e}")

    return {
        "case_id": case_id,
        "ingested": len(created_nodes),
        "errors": errors,
        "nodes": created_nodes,
        "entity_resolution": resolution,
    }


# ─── Ingest Logic ────────────────────────────────────────────

def _ingest_single_award(award: dict, case_id: str) -> dict:
    """
    Take a single USASpending award detail response and write
    all corresponding nodes and edges to Neo4j.
    Returns a summary of what was created.
    """
    summary = {"company": None, "contract": None, "organization": None, "edges": []}

    # 1. Company (recipient)
    company_data = usaspending.map_award_to_company(award)
    if company_data.get("name"):
        company_record = graph_service.create_company(company_data)
        if company_record:
            node = company_record["c"]
            summary["company"] = {"name": node.get("name"), "node_id": node.get("node_id")}
            case_service.link_node_to_case(node.get("node_id"), case_id)

    # 2. Contract
    contract_data = usaspending.map_award_to_contract(award)
    if contract_data.get("piid"):
        contract_record = graph_service.create_contract(contract_data)
        if contract_record:
            node = contract_record["ct"]
            summary["contract"] = {"piid": node.get("piid"), "node_id": node.get("node_id")}
            case_service.link_node_to_case(node.get("node_id"), case_id)

    # 3. Organization (awarding agency)
    org_data = usaspending.map_award_to_organization(award)
    if org_data.get("name"):
        org_record = graph_service.create_organization(org_data)
        if org_record:
            node = org_record["o"]
            summary["organization"] = {"name": node.get("name"), "node_id": node.get("node_id")}
            case_service.link_node_to_case(node.get("node_id"), case_id)

    # 4. AWARDED_TO edge (Organization → Company)
    if org_data.get("name") and company_data.get("uei"):
        edge_props = usaspending.map_award_to_awarded_edge(award)
        edge_record = graph_service.create_awarded_to(
            org_data["name"], company_data["uei"], edge_props
        )
        if edge_record:
            summary["edges"].append("AWARDED_TO")

    return summary


# ─── Entity Resolution Endpoints ─────────────────────────────

@router.post("/resolve")
async def resolve_entities():
    """Run entity resolution across all Company nodes."""
    try:
        result = entity_resolution.resolve_companies()
        return result
    except Exception as e:
        logger.error(f"Entity resolution failed: {e}")
        raise HTTPException(500, f"Entity resolution error: {str(e)}")


class AliasAction(BaseModel):
    node_id_1: str
    node_id_2: str

@router.post("/alias/confirm")
async def confirm_alias(body: AliasAction):
    """Investigator confirms two companies are the same entity — merges them."""
    return entity_resolution.confirm_alias(body.node_id_1, body.node_id_2)

@router.post("/alias/reject")
async def reject_alias(body: AliasAction):
    """Investigator rejects alias — marks edge as rejected."""
    return entity_resolution.reject_alias(body.node_id_1, body.node_id_2)