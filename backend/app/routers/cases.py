"""
SONAR — Cases Router
Case management and multi-source data search/ingest endpoints.

Workflow:
  1. POST /api/cases/              → create a case
  2. POST /api/cases/{id}/search   → search all sources, preview results
  3. POST /api/cases/{id}/ingest   → pull USASpending award details, write to Neo4j
  4. POST /api/cases/{id}/enrich   → enrich Company node with SAM.gov data
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
import asyncio
import logging

from app.services import case_service
from app.services import usaspending
from app.services import sam_gov
from app.services import graph_service
from app.services import entity_resolution
from app.services.source_registry import sources_for_search_type

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
    credentials: dict = Field(
        default={},
        description="Source credentials, e.g. {'sam_gov': {'api_key': '...'}}"
    )

class IngestRequest(BaseModel):
    """Cherry-pick which search results to pull into the graph."""
    internal_ids: list[str] = Field(
        ...,
        min_length=1,
        description="USASpending internal_id values from search results"
    )

class EnrichRequest(BaseModel):
    """Enrich a Company node with SAM.gov entity data."""
    uei: str = Field(..., min_length=1, description="UEI of the company to enrich")
    credentials: dict = Field(
        default={},
        description="SAM.gov credentials: {'api_key': '...'}"
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


# ─── Multi-Source Search (preview, no write) ────────────────

@router.post("/{case_id}/search")
async def search_sources(case_id: str, body: SearchRequest):
    """
    Search all applicable data sources in parallel.
    Sources are determined by search_type: keyword → both, piid → USASpending only.
    Sources requiring credentials are skipped if credentials not provided.
    Nothing is written to Neo4j — the investigator reviews results first.
    """
    case = case_service.get_case(case_id)
    if not case:
        raise HTTPException(404, "Case not found")

    applicable_sources = sources_for_search_type(body.search_type)
    results = {}

    # Build coroutines for each source
    tasks = {}
    for source in applicable_sources:
        sid = source["id"]

        if source["auth_required"]:
            creds = body.credentials.get(sid, {})
            if not creds:
                results[sid] = {
                    "status": "skipped",
                    "reason": "No credentials provided",
                    "source_name": source["name"],
                    "results": [],
                }
                continue
        else:
            creds = {}

        tasks[sid] = _search_source(sid, body.query, body.search_type, body.limit, creds, source["name"])

    # Execute all source queries in parallel
    if tasks:
        task_results = await asyncio.gather(
            *tasks.values(),
            return_exceptions=True,
        )
        for sid, result in zip(tasks.keys(), task_results):
            if isinstance(result, Exception):
                source_name = next(s["name"] for s in applicable_sources if s["id"] == sid)
                logger.error(f"Source {sid} search failed: {result}")
                results[sid] = {
                    "status": "error",
                    "error": str(result),
                    "source_name": source_name,
                    "results": [],
                }
            else:
                results[sid] = result

    return {
        "case_id": case_id,
        "query": body.query,
        "search_type": body.search_type,
        "sources": results,
    }


async def _search_source(source_id: str, query: str, search_type: str,
                          limit: int, credentials: dict, source_name: str) -> dict:
    """Dispatch search to the appropriate source service."""

    if source_id == "usaspending":
        if search_type == "piid":
            raw = await usaspending.search_awards_by_piid(query, limit=limit)
        else:
            raw = await usaspending.search_awards_by_keyword(query, limit=limit, page=1)

        results_raw = raw.get("results", [])
        page_meta = raw.get("page_metadata", {})
        summaries = [usaspending.map_search_result_summary(r) for r in results_raw]

        return {
            "status": "success",
            "source_name": source_name,
            "result_count": len(summaries),
            "total_available": page_meta.get("total", 0),
            "has_next": page_meta.get("hasNext", False),
            "results": summaries,
        }

    elif source_id == "sam_gov":
        api_key = credentials.get("api_key", "")
        if not api_key:
            return {
                "status": "skipped",
                "reason": "No API key provided",
                "source_name": source_name,
                "results": [],
            }

        raw = await sam_gov.search_entities(query, api_key, limit=limit)
        entities = raw.get("entityData", [])
        summaries = [sam_gov.map_entity_to_summary(e) for e in entities]
        total = raw.get("totalRecords", len(summaries))

        return {
            "status": "success",
            "source_name": source_name,
            "result_count": len(summaries),
            "total_available": total,
            "has_next": False,  # Simplified; SAM.gov pagination is page-based
            "results": summaries,
        }

    return {
        "status": "error",
        "error": f"Unknown source: {source_id}",
        "source_name": source_name,
        "results": [],
    }


# ─── Enrich (SAM.gov → Company node) ────────────────────────

@router.post("/{case_id}/enrich")
async def enrich_company(case_id: str, body: EnrichRequest):
    """
    Fetch full SAM.gov entity data for a UEI and merge into
    the existing Company node in Neo4j.
    """
    case = case_service.get_case(case_id)
    if not case:
        raise HTTPException(404, "Case not found")

    api_key = body.credentials.get("api_key", "")
    if not api_key:
        raise HTTPException(400, "SAM.gov API key required for enrichment")

    try:
        entity = await sam_gov.get_entity_by_uei(body.uei, api_key)
        if not entity:
            raise HTTPException(404, f"No SAM.gov entity found for UEI: {body.uei}")

        company_data = sam_gov.map_entity_to_company(entity)
        result = graph_service.enrich_company(body.uei, company_data)

        if not result:
            # Company doesn't exist yet — create it
            company_data["uei"] = body.uei
            company_data["source"] = "SAM.gov"
            company_data["first_seen"] = company_data.get("registration_date", "")
            company_data["naics_codes"] = []
            result = graph_service.create_company(company_data)
            if result:
                node = result["c"]
                case_service.link_node_to_case(node.get("node_id"), case_id)

        return {
            "status": "enriched",
            "uei": body.uei,
            "company": company_data,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"SAM.gov enrichment failed for UEI {body.uei}: {e}")
        raise HTTPException(502, f"SAM.gov enrichment error: {str(e)}")


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