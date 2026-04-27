"""
SONAR — Manual Data Entry Router
Supports:
  - Manual entity creation via form (Company, Individual)
  - Manual relationship creation with subcontractor support
  - Excel/CSV bulk upload
  - Node listing for connect-to-existing-node picker
  - Auto-enrichment of manually added entities
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field
from typing import Optional
import csv
import io
import logging
import asyncio

from app.services import graph_service, case_service

router = APIRouter()
logger = logging.getLogger(__name__)


# ─── Pydantic Models ─────────────────────────────────────────

class ConnectionInput(BaseModel):
    """Describes a connection from the new node to an existing node."""
    target_node_id: str = Field(..., min_length=1)
    relationship_type: str = Field(default="ASSOCIATED_WITH")
    notes: str = Field(default="")


class ManualCompanyInput(BaseModel):
    name: str = Field(..., min_length=1)
    uei: str = Field(default="")
    address: str = Field(default="")
    city: str = Field(default="")
    state: str = Field(default="")
    zip_code: str = Field(default="")
    entity_type: str = Field(default="")
    cage_code: str = Field(default="")
    phone: str = Field(default="")
    website: str = Field(default="")
    profit_structure: str = Field(default="")
    ein: str = Field(default="")
    notes: str = Field(default="")
    # Subcontractor fields
    is_subcontractor: bool = Field(default=False)
    prime_contractor_node_id: str = Field(default="", description="Node ID of prime contractor")
    billed_amount: float = Field(default=0.0)
    contract_year: str = Field(default="")
    contract_description: str = Field(default="")
    # Connections to existing nodes
    connections: list[ConnectionInput] = Field(default_factory=list)


class ManualIndividualInput(BaseModel):
    name: str = Field(..., min_length=1)
    title: str = Field(default="")
    email: str = Field(default="")
    phone: str = Field(default="")
    compensation: float = Field(default=0.0)
    notes: str = Field(default="")
    # Connections to existing nodes
    connections: list[ConnectionInput] = Field(default_factory=list)


class ManualRelationshipInput(BaseModel):
    source_node_id: str = Field(..., min_length=1)
    target_node_id: str = Field(..., min_length=1)
    relationship_type: str = Field(
        ..., min_length=1,
        description="e.g. PRINCIPAL_OF, OFFICER_OF, SUBSIDIARY_OF, SUBCONTRACTOR_OF"
    )
    weight: float = Field(default=1.0)
    confidence: float = Field(default=0.90)
    notes: str = Field(default="")
    billed_amount: float = Field(default=0.0)
    contract_year: str = Field(default="")


# ─── Node listing for the connect-to picker ──────────────────

@router.get("/{case_id}/nodes")
async def list_case_nodes(case_id: str, q: str = ""):
    """
    List all nodes in a case, optionally filtered by name.
    Used by the frontend node-picker to connect new entities.
    """
    case = case_service.get_case(case_id)
    if not case:
        raise HTTPException(404, "Case not found")

    from app.database import db
    if q:
        query = """
        MATCH (n)-[:PART_OF_CASE]->(:Case {case_id: $case_id})
        WHERE toLower(n.name) CONTAINS toLower($q)
           OR toLower(n.piid) CONTAINS toLower($q)
           OR toLower(n.node_id) CONTAINS toLower($q)
        RETURN n.node_id AS node_id, n.name AS name, labels(n) AS labels, n.piid AS piid
        ORDER BY n.name
        LIMIT 50
        """
        params = {"case_id": case_id, "q": q}
    else:
        query = """
        MATCH (n)-[:PART_OF_CASE]->(:Case {case_id: $case_id})
        RETURN n.node_id AS node_id, n.name AS name, labels(n) AS labels, n.piid AS piid
        ORDER BY n.name
        LIMIT 50
        """
        params = {"case_id": case_id}

    with db.session() as session:
        result = session.run(query, params)
        nodes = []
        for record in result:
            data = record.data()
            labels = data.get("labels", [])
            # Filter out the Case label
            labels = [l for l in labels if l != "Case"]
            nodes.append({
                "node_id": data.get("node_id", ""),
                "name": data.get("name") or data.get("piid") or data.get("node_id", ""),
                "type": labels[0] if labels else "Unknown",
            })
        return {"nodes": nodes}


# ─── Manual Entity Endpoints ─────────────────────────────────

@router.post("/{case_id}/add-company")
async def add_company(case_id: str, body: ManualCompanyInput):
    """Manually add a Company node to the graph, with optional subcontractor info."""
    case = case_service.get_case(case_id)
    if not case:
        raise HTTPException(404, "Case not found")

    # Build full address from parts
    address_parts = [body.address, body.city, body.state, body.zip_code]
    full_address = ", ".join(p for p in address_parts if p)

    data = {
        "uei": body.uei or f"MANUAL-{body.name[:10].upper().replace(' ', '')}-{case_id[:8]}",
        "name": body.name,
        "cage_code": body.cage_code,
        "address": full_address,
        "entity_type": body.entity_type,
        "exclusion_flag": False,
        "active": True,
        "first_seen": "",
    }

    result = graph_service.create_company(data)
    if result:
        node = result["c"]
        node_id = node.get("node_id")
        case_service.link_node_to_case(node_id, case_id)

        # Set additional manual-entry properties
        extra = {
            "phone": body.phone,
            "website": body.website,
            "profit_structure": body.profit_structure,
            "ein": body.ein,
            "city": body.city,
            "state": body.state,
            "zip_code": body.zip_code,
            "notes": body.notes,
            "data_source": "manual",
        }

        # Subcontractor properties
        if body.is_subcontractor:
            extra["is_subcontractor"] = True
            extra["billed_amount"] = body.billed_amount
            extra["contract_year"] = body.contract_year
            extra["contract_description"] = body.contract_description

        _set_extra_props(node_id, extra)

        # Create SUBCONTRACTOR_OF relationship if prime contractor specified
        if body.is_subcontractor and body.prime_contractor_node_id:
            _create_generic_relationship(
                source_id=node_id,
                target_id=body.prime_contractor_node_id,
                rel_type="SUBCONTRACTOR_OF",
                weight=1.0,
                confidence=0.95,
                notes=body.contract_description,
                billed_amount=body.billed_amount,
                contract_year=body.contract_year,
            )

        # Create connections to existing nodes
        for conn in body.connections:
            try:
                _create_generic_relationship(
                    source_id=node_id,
                    target_id=conn.target_node_id,
                    rel_type=conn.relationship_type,
                    weight=1.0,
                    confidence=0.90,
                    notes=conn.notes,
                )
            except Exception as e:
                logger.warning(f"Connection to {conn.target_node_id} failed: {e}")

        return {
            "status": "created",
            "node_id": node_id,
            "name": body.name,
            "uei": data["uei"],
        }

    raise HTTPException(500, "Failed to create company node")


@router.post("/{case_id}/add-individual")
async def add_individual(case_id: str, body: ManualIndividualInput):
    """Manually add an Individual (person) node to the graph."""
    case = case_service.get_case(case_id)
    if not case:
        raise HTTPException(404, "Case not found")

    data = {
        "name": body.name,
        "roles": [body.title] if body.title else [],
        "first_seen": "",
    }

    result = graph_service.create_individual(data)
    if result:
        node = result["i"]
        node_id = node.get("node_id")
        case_service.link_node_to_case(node_id, case_id)

        # Set additional properties
        _set_extra_props(node_id, {
            "title": body.title,
            "email": body.email,
            "phone": body.phone,
            "compensation": body.compensation,
            "notes": body.notes,
            "data_source": "manual",
        })

        # Create connections to existing nodes
        for conn in body.connections:
            try:
                _create_generic_relationship(
                    source_id=node_id,
                    target_id=conn.target_node_id,
                    rel_type=conn.relationship_type,
                    weight=1.0,
                    confidence=0.90,
                    notes=conn.notes,
                )
            except Exception as e:
                logger.warning(f"Connection to {conn.target_node_id} failed: {e}")

        return {"status": "created", "node_id": node_id, "name": body.name}

    raise HTTPException(500, "Failed to create individual node")


@router.post("/{case_id}/add-relationship")
async def add_relationship(case_id: str, body: ManualRelationshipInput):
    """Manually create a relationship between two existing nodes."""
    case = case_service.get_case(case_id)
    if not case:
        raise HTTPException(404, "Case not found")

    try:
        _create_generic_relationship(
            body.source_node_id,
            body.target_node_id,
            body.relationship_type,
            body.weight,
            body.confidence,
            body.notes,
            body.billed_amount,
            body.contract_year,
        )
        return {
            "status": "created",
            "relationship": body.relationship_type,
            "source": body.source_node_id,
            "target": body.target_node_id,
        }
    except Exception as e:
        logger.error(f"Failed to create relationship: {e}")
        raise HTTPException(500, f"Failed to create relationship: {str(e)}")


# ─── Edit Existing Node ──────────────────────────────────────

class NodeUpdateInput(BaseModel):
    """Arbitrary key-value updates for a node."""
    properties: dict = Field(..., description="Key-value pairs to set on the node")

# Fields that cannot be edited by the user
PROTECTED_FIELDS = {
    "node_id", "prominence_score", "prominence_factors",
    "wfa_flags", "wfa_explanations", "wfa_confidence",
    "auto_enriched", "_labels",
}


@router.get("/{case_id}/node/{node_id}")
async def get_node(case_id: str, node_id: str):
    """Get a single node's properties for editing."""
    case = case_service.get_case(case_id)
    if not case:
        raise HTTPException(404, "Case not found")

    from app.database import db
    query = """
    MATCH (n {node_id: $node_id})-[:PART_OF_CASE]->(:Case {case_id: $case_id})
    RETURN n, labels(n) AS labels
    """
    with db.session() as session:
        result = session.run(query, {"node_id": node_id, "case_id": case_id})
        record = result.single()

    if not record:
        raise HTTPException(404, "Node not found in this case")

    node_data = dict(record["n"])
    node_data["_labels"] = [l for l in record["labels"] if l != "Case"]
    return {"node": node_data}


@router.patch("/{case_id}/node/{node_id}")
async def update_node(case_id: str, node_id: str, body: NodeUpdateInput):
    """Update properties on an existing node."""
    case = case_service.get_case(case_id)
    if not case:
        raise HTTPException(404, "Case not found")

    # Filter out protected and empty fields
    updates = {
        k: v for k, v in body.properties.items()
        if k not in PROTECTED_FIELDS and v is not None
    }

    if not updates:
        raise HTTPException(400, "No valid properties to update")

    from app.database import db

    # Build SET clause — allow clearing fields by setting to empty string
    set_clauses = ", ".join(f"n.{k} = ${k}" for k in updates)
    query = f"""
    MATCH (n {{node_id: $node_id}})-[:PART_OF_CASE]->(c:Case {{case_id: $case_id}})
    SET {set_clauses}
    RETURN n, labels(n) AS labels
    """
    params = {"node_id": node_id, "case_id": case_id, **updates}

    with db.session() as session:
        result = session.run(query, params)
        record = result.single()

    if not record:
        raise HTTPException(404, "Node not found in this case")

    node_data = dict(record["n"])
    node_data["_labels"] = [l for l in record["labels"] if l != "Case"]
    return {"status": "updated", "node": node_data}


@router.delete("/{case_id}/node/{node_id}")
async def delete_node(case_id: str, node_id: str):
    """Delete a node and all its relationships from the case."""
    case = case_service.get_case(case_id)
    if not case:
        raise HTTPException(404, "Case not found")

    from app.database import db
    query = """
    MATCH (n {node_id: $node_id})-[:PART_OF_CASE]->(:Case {case_id: $case_id})
    DETACH DELETE n
    RETURN count(n) AS deleted
    """
    with db.session() as session:
        result = session.run(query, {"node_id": node_id, "case_id": case_id})
        record = result.single()

    if not record or record["deleted"] == 0:
        raise HTTPException(404, "Node not found")

    return {"status": "deleted", "node_id": node_id}


# ─── Relationship Management ─────────────────────────────────

@router.get("/{case_id}/node/{node_id}/relationships")
async def list_node_relationships(case_id: str, node_id: str):
    """List all relationships for a node within a case."""
    case = case_service.get_case(case_id)
    if not case:
        raise HTTPException(404, "Case not found")

    from app.database import db
    query = """
    MATCH (n {node_id: $node_id})-[:PART_OF_CASE]->(:Case {case_id: $case_id})
    OPTIONAL MATCH (n)-[r]-(m)
    WHERE type(r) <> 'PART_OF_CASE'
    RETURN
        id(r) AS rel_id,
        type(r) AS rel_type,
        properties(r) AS rel_props,
        startNode(r) = n AS is_outgoing,
        m.node_id AS other_node_id,
        m.name AS other_name,
        labels(m) AS other_labels
    """
    with db.session() as session:
        result = session.run(query, {"node_id": node_id, "case_id": case_id})
        rels = []
        for record in result:
            data = record.data()
            if data.get("rel_id") is None:
                continue
            other_labels = [l for l in (data.get("other_labels") or []) if l != "Case"]
            rels.append({
                "rel_id": data["rel_id"],
                "rel_type": data["rel_type"],
                "rel_props": data.get("rel_props", {}),
                "is_outgoing": data.get("is_outgoing", True),
                "other_node_id": data.get("other_node_id", ""),
                "other_name": data.get("other_name") or data.get("other_node_id", ""),
                "other_type": other_labels[0] if other_labels else "Unknown",
            })
        return {"relationships": rels}


class AddConnectionInput(BaseModel):
    target_node_id: str = Field(..., min_length=1)
    relationship_type: str = Field(default="ASSOCIATED_WITH")
    direction: str = Field(default="outgoing", description="'outgoing' or 'incoming'")
    notes: str = Field(default="")
    billed_amount: float = Field(default=0.0)
    contract_year: str = Field(default="")


@router.post("/{case_id}/node/{node_id}/relationships")
async def add_node_relationship(case_id: str, node_id: str, body: AddConnectionInput):
    """Add a relationship from this node to another node."""
    case = case_service.get_case(case_id)
    if not case:
        raise HTTPException(404, "Case not found")

    if body.direction == "incoming":
        src, tgt = body.target_node_id, node_id
    else:
        src, tgt = node_id, body.target_node_id

    try:
        _create_generic_relationship(
            source_id=src,
            target_id=tgt,
            rel_type=body.relationship_type,
            weight=1.0,
            confidence=0.90,
            notes=body.notes,
            billed_amount=body.billed_amount,
            contract_year=body.contract_year,
        )
        return {"status": "created", "relationship_type": body.relationship_type}
    except Exception as e:
        logger.error(f"Failed to add relationship: {e}")
        raise HTTPException(500, f"Failed: {str(e)}")


@router.delete("/{case_id}/node/{node_id}/relationships/{rel_id}")
async def delete_node_relationship(case_id: str, node_id: str, rel_id: int):
    """Delete a specific relationship by its internal Neo4j ID."""
    case = case_service.get_case(case_id)
    if not case:
        raise HTTPException(404, "Case not found")

    from app.database import db
    # Verify the relationship touches this node and is in the case
    query = """
    MATCH (n {node_id: $node_id})-[:PART_OF_CASE]->(:Case {case_id: $case_id})
    WITH n
    MATCH (n)-[r]-()
    WHERE id(r) = $rel_id AND type(r) <> 'PART_OF_CASE'
    DELETE r
    RETURN count(r) AS deleted
    """
    with db.session() as session:
        result = session.run(query, {
            "node_id": node_id,
            "case_id": case_id,
            "rel_id": rel_id,
        })
        record = result.single()

    if not record or record["deleted"] == 0:
        raise HTTPException(404, "Relationship not found")

    return {"status": "deleted", "rel_id": rel_id}


# ─── Auto-Enrichment ─────────────────────────────────────────

@router.post("/{case_id}/auto-enrich")
async def auto_enrich(case_id: str):
    """
    Scour external sources for additional data about all nodes in the case.
    Called by the frontend 'Recompute' button to supplement manual entries.

    For each Company node, searches:
      - USASpending for contract history
      - SAM.gov for registration/exclusion data
      - ProPublica for nonprofit 990 data (if EIN present)

    For each Individual, searches:
      - SAM.gov exclusions
    """
    case = case_service.get_case(case_id)
    if not case:
        raise HTTPException(404, "Case not found")

    from app.database import db
    from app.services import usaspending

    # Gather all company and individual nodes in this case
    query = """
    MATCH (n)-[:PART_OF_CASE]->(:Case {case_id: $case_id})
    RETURN n.node_id AS node_id, n.name AS name, n.uei AS uei,
           n.ein AS ein, labels(n) AS labels,
           n.data_source AS data_source, n.auto_enriched AS auto_enriched
    """
    with db.session() as session:
        result = session.run(query, {"case_id": case_id})
        nodes = [record.data() for record in result]

    enriched = []
    errors = []

    for node in nodes:
        labels = node.get("labels", [])
        name = node.get("name", "")
        node_id = node.get("node_id", "")

        if not name:
            continue

        try:
            if "Company" in labels:
                # Search USASpending by company name
                try:
                    usa_results = await usaspending.search_awards_by_keyword(
                        keyword=name, limit=5
                    )
                    results_list = usa_results.get("results", [])
                    if results_list:
                        enriched.append({
                            "node_id": node_id,
                            "name": name,
                            "source": "USASpending",
                            "results_found": len(results_list),
                        })
                except Exception as e:
                    logger.warning(f"USASpending search for {name}: {e}")

                # Try SAM.gov exclusion check
                try:
                    from app.services import sam_exclusions
                    exclusions = await sam_exclusions.search_exclusions(
                        keyword=name, api_key="", limit=5
                    )
                    exclusion_list = exclusions.get("results", [])
                    if exclusion_list:
                        _set_extra_props(node_id, {"exclusion_flag": "true"})
                        enriched.append({
                            "node_id": node_id,
                            "name": name,
                            "source": "SAM.gov Exclusions",
                            "results_found": len(exclusion_list),
                        })
                except Exception as e:
                    logger.warning(f"SAM exclusion check for {name}: {e}")

                # If has EIN, try ProPublica nonprofit lookup
                ein = node.get("ein")
                if ein:
                    try:
                        from app.services import propublica_nonprofit
                        org_data = await propublica_nonprofit.get_organization(str(ein))
                        if org_data:
                            _set_extra_props(node_id, {"nonprofit_status": "true"})
                            enriched.append({
                                "node_id": node_id,
                                "name": name,
                                "source": "ProPublica 990",
                                "results_found": 1,
                            })
                    except Exception as e:
                        logger.warning(f"ProPublica lookup for {name}: {e}")

            elif "Individual" in labels:
                # Check SAM.gov exclusions for individuals
                try:
                    from app.services import sam_exclusions
                    exclusions = await sam_exclusions.search_exclusions(
                        keyword=name, api_key="", limit=5
                    )
                    exclusion_list = exclusions.get("results", [])
                    if exclusion_list:
                        _set_extra_props(node_id, {"exclusion_flag": "true"})
                        enriched.append({
                            "node_id": node_id,
                            "name": name,
                            "source": "SAM.gov Exclusions",
                            "results_found": len(exclusion_list),
                        })
                except Exception as e:
                    logger.warning(f"SAM exclusion check for {name}: {e}")

            # Mark as auto-enriched so we don't re-enrich next time
            _set_extra_props(node_id, {"auto_enriched": "true"})

        except Exception as e:
            errors.append({"node_id": node_id, "name": name, "error": str(e)})
            logger.error(f"Auto-enrich failed for {name}: {e}")

    return {
        "status": "completed",
        "total_nodes": len(nodes),
        "enriched": enriched,
        "errors": errors[:10],
    }


# ─── Excel / CSV Upload ──────────────────────────────────────

@router.post("/{case_id}/upload")
async def upload_file(
    case_id: str,
    file: UploadFile = File(...),
    entity_type: str = Form(default="company"),
):
    """
    Upload a CSV/Excel file with entity data.

    Expected columns for companies:
      name, uei, address, city, state, zip_code, entity_type, cage_code,
      phone, website, profit_structure, ein, is_subcontractor,
      prime_contractor, billed_amount, contract_year

    Expected columns for individuals:
      name, title, email, phone, company_name, relationship_type, compensation
    """
    case = case_service.get_case(case_id)
    if not case:
        raise HTTPException(404, "Case not found")

    if not file.filename:
        raise HTTPException(400, "No file provided")

    content = await file.read()

    filename = file.filename.lower()
    if filename.endswith('.csv'):
        rows = _parse_csv(content)
    elif filename.endswith(('.xlsx', '.xls')):
        rows = _parse_excel(content)
    else:
        raise HTTPException(400, "Unsupported file type. Please upload .csv or .xlsx")

    if not rows:
        raise HTTPException(400, "File is empty or could not be parsed")

    created = 0
    errors = []

    for i, row in enumerate(rows):
        try:
            if entity_type == "individual":
                _create_individual_from_row(row, case_id)
            else:
                _create_company_from_row(row, case_id)
            created += 1
        except Exception as e:
            errors.append({"row": i + 2, "error": str(e)})

    return {
        "status": "uploaded",
        "filename": file.filename,
        "entity_type": entity_type,
        "created": created,
        "total_rows": len(rows),
        "errors": errors[:10],
    }


# ─── Helpers ─────────────────────────────────────────────────

def _set_extra_props(node_id: str, props: dict):
    """Set additional properties on any node by node_id."""
    from app.database import db
    non_empty = {k: v for k, v in props.items() if v is not None and v != ""}
    if not non_empty:
        return

    set_clauses = ", ".join(f"n.{k} = ${k}" for k in non_empty)
    query = f"""
    MATCH (n {{node_id: $node_id}})
    SET {set_clauses}
    RETURN n
    """
    params = {"node_id": node_id, **non_empty}
    with db.session() as session:
        session.run(query, params)


def _create_generic_relationship(
    source_id, target_id, rel_type, weight=1.0, confidence=0.90,
    notes="", billed_amount=0.0, contract_year=""
):
    """Create a relationship between two nodes by node_id."""
    from app.database import db

    # Sanitize rel_type to valid Neo4j relationship name
    safe_type = "".join(c if c.isalnum() or c == "_" else "_" for c in rel_type).upper()
    if not safe_type:
        safe_type = "ASSOCIATED_WITH"

    query = f"""
    MATCH (a {{node_id: $source_id}})
    MATCH (b {{node_id: $target_id}})
    CREATE (a)-[r:{safe_type} {{
        weight: $weight,
        confidence: $confidence,
        notes: $notes,
        source: 'manual',
        billed_amount: $billed_amount,
        contract_year: $contract_year
    }}]->(b)
    RETURN r
    """
    params = {
        "source_id": source_id,
        "target_id": target_id,
        "weight": weight,
        "confidence": confidence,
        "notes": notes,
        "billed_amount": billed_amount,
        "contract_year": contract_year,
    }
    with db.session() as session:
        result = session.run(query, params)
        return result.single()


def _parse_csv(content: bytes) -> list[dict]:
    """Parse CSV content into list of dicts."""
    text = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    return [dict(row) for row in reader]


def _parse_excel(content: bytes) -> list[dict]:
    """Parse Excel content using openpyxl."""
    try:
        import openpyxl
        wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True)
        ws = wb.active
        if ws is None:
            return []
        rows = list(ws.iter_rows(values_only=True))
        if len(rows) < 2:
            return []
        headers = [
            str(h).strip().lower().replace(" ", "_") if h else f"col_{i}"
            for i, h in enumerate(rows[0])
        ]
        return [dict(zip(headers, row)) for row in rows[1:] if any(v for v in row)]
    except ImportError:
        raise HTTPException(400, "Excel support requires openpyxl: pip install openpyxl")


def _create_company_from_row(row: dict, case_id: str):
    """Create a Company node from an uploaded row."""
    name = str(row.get("name", "") or "").strip()
    if not name:
        raise ValueError("Name is required")

    address_parts = [
        str(row.get("address", "") or ""),
        str(row.get("city", "") or ""),
        str(row.get("state", "") or ""),
        str(row.get("zip_code", "") or row.get("zip", "") or ""),
    ]
    full_address = ", ".join(p.strip() for p in address_parts if p.strip())

    uei = str(row.get("uei", "") or "").strip()
    if not uei:
        uei = f"UPLOAD-{name[:10].upper().replace(' ', '')}-{case_id[:8]}"

    data = {
        "uei": uei,
        "name": name,
        "cage_code": str(row.get("cage_code", "") or ""),
        "address": full_address,
        "entity_type": str(row.get("entity_type", "") or ""),
        "exclusion_flag": False,
        "active": True,
        "first_seen": "",
    }

    result = graph_service.create_company(data)
    if result:
        node = result["c"]
        node_id = node.get("node_id")
        case_service.link_node_to_case(node_id, case_id)

        _set_extra_props(node_id, {
            "phone": str(row.get("phone", "") or ""),
            "website": str(row.get("website", "") or ""),
            "profit_structure": str(row.get("profit_structure", "") or ""),
            "ein": str(row.get("ein", "") or ""),
            "city": str(row.get("city", "") or ""),
            "state": str(row.get("state", "") or ""),
            "zip_code": str(row.get("zip_code", "") or row.get("zip", "") or ""),
            "billed_amount": str(row.get("billed_amount", "") or ""),
            "contract_year": str(row.get("contract_year", "") or ""),
            "data_source": "upload",
        })


def _create_individual_from_row(row: dict, case_id: str):
    """Create an Individual node from an uploaded row."""
    name = str(row.get("name", "") or "").strip()
    if not name:
        raise ValueError("Name is required")

    data = {
        "name": name,
        "roles": [str(row.get("title", "") or "")] if row.get("title") else [],
        "first_seen": "",
    }

    result = graph_service.create_individual(data)
    if result:
        node = result["i"]
        node_id = node.get("node_id")
        case_service.link_node_to_case(node_id, case_id)

        _set_extra_props(node_id, {
            "title": str(row.get("title", "") or ""),
            "email": str(row.get("email", "") or ""),
            "phone": str(row.get("phone", "") or ""),
            "data_source": "upload",
        })

        # Try to link to company if company_name provided
        company_name = str(row.get("company_name", "") or "").strip()
        if company_name:
            from app.database import db
            rel_type = str(row.get("relationship_type", "PRINCIPAL_OF") or "PRINCIPAL_OF")
            comp = float(row.get("compensation", 0) or 0)
            query = f"""
            MATCH (i:Individual {{name: $name}})
            MATCH (c:Company)
            WHERE toLower(c.name) = toLower($company_name)
            MERGE (i)-[r:{rel_type}]->(c)
            SET r.source = 'upload',
                r.confidence = 0.90,
                r.compensation = $compensation
            RETURN r
            """
            with db.session() as session:
                session.run(query, {"name": name, "company_name": company_name, "compensation": comp})
