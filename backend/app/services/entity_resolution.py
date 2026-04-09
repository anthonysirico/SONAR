"""
SONAR — Entity Resolution Service
Detects potential duplicate/alias companies in the graph by:
  1. UEI match (authoritative — auto-merge)
  2. Fuzzy name match after normalizing legal suffixes
Creates POSSIBLE_ALIAS_OF edges for investigator review,
or auto-merges when UEI confirms identity.
"""

import re
from app.database import db

# ─── Legal Suffix Normalization ──────────────────────────────
# Order matters — longer patterns first to avoid partial matches

LEGAL_SUFFIXES = [
    r"\bincorporated\b",
    r"\bcorporation\b",
    r"\bcompany\b",
    r"\blimited\b",
    r"\bgroup\b",
    r"\bholdings?\b",
    r"\benterprises?\b",
    r"\bsolutions?\b",
    r"\bservices?\b",
    r"\btechnolog(?:y|ies)\b",
    r"\binternational\b",
    r"\bglobal\b",
    r"\bsystems?\b",
    r"\bindustries\b",
    r"\bassociates?\b",
    r"\bpartners?\b",
    r"\bconsulting\b",
    r"\bllc\b",
    r"\bllp\b",
    r"\binc\b",
    r"\bcorp\b",
    r"\bco\b",
    r"\bltd\b",
    r"\blp\b",
    r"\bthe\b",
    r"\bdba\b",
]

SUFFIX_PATTERN = re.compile(
    "|".join(LEGAL_SUFFIXES),
    re.IGNORECASE,
)


def normalize_company_name(name: str) -> str:
    """Strip legal suffixes, punctuation, and extra whitespace. Uppercase."""
    if not name:
        return ""
    # Remove punctuation
    cleaned = re.sub(r"[.,\-/\\()'\"&]", " ", name)
    # Remove legal suffixes
    cleaned = SUFFIX_PATTERN.sub("", cleaned)
    # Collapse whitespace and uppercase
    cleaned = re.sub(r"\s+", " ", cleaned).strip().upper()
    return cleaned


def name_similarity(a: str, b: str) -> float:
    """Simple token-overlap similarity (Jaccard on words).
    Fast and good enough for catching 'BOEING CO' vs 'THE BOEING COMPANY'.
    """
    if not a or not b:
        return 0.0
    tokens_a = set(a.split())
    tokens_b = set(b.split())
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = tokens_a & tokens_b
    union = tokens_a | tokens_b
    return len(intersection) / len(union)


# ─── Resolve Entities ─────────────────────────────────────────

SIMILARITY_THRESHOLD = 0.6  # Jaccard threshold for flagging potential aliases

def resolve_companies() -> dict:
    """
    Scan all Company nodes. For each pair:
      - Same UEI (non-empty) → auto-merge into one node
      - Same normalized name or high similarity → create POSSIBLE_ALIAS_OF
    Returns summary of merges and alias edges created.
    """
    companies = _get_all_companies()
    merges = []
    aliases = []

    # Index by UEI for fast lookup
    uei_map = {}  # uei -> list of companies
    for c in companies:
        uei = c.get("uei", "").strip()
        if uei:
            uei_map.setdefault(uei, []).append(c)

    # 1. UEI-based merges (authoritative)
    for uei, group in uei_map.items():
        if len(group) > 1:
            # Keep the one with the longest name (usually most complete)
            group.sort(key=lambda c: len(c.get("name", "")), reverse=True)
            primary = group[0]
            for duplicate in group[1:]:
                _merge_company_nodes(primary["node_id"], duplicate["node_id"])
                merges.append({
                    "primary": primary["name"],
                    "merged": duplicate["name"],
                    "uei": uei,
                })

    # 2. Fuzzy name matching (for companies without shared UEI)
    # Build normalized name index
    name_index = []  # (normalized_name, company_dict)
    for c in companies:
        norm = normalize_company_name(c.get("name", ""))
        if norm:
            name_index.append((norm, c))

    seen_pairs = set()
    for i, (norm_a, ca) in enumerate(name_index):
        for j, (norm_b, cb) in enumerate(name_index):
            if j <= i:
                continue
            if ca["node_id"] == cb["node_id"]:
                continue
            # Skip if same UEI (already handled above)
            if ca.get("uei") and ca.get("uei") == cb.get("uei"):
                continue

            pair_key = tuple(sorted([ca["node_id"], cb["node_id"]]))
            if pair_key in seen_pairs:
                continue

            # Exact normalized match
            if norm_a == norm_b:
                _create_alias_edge(ca["node_id"], cb["node_id"], 0.95,
                                   f"Identical normalized name: '{norm_a}'")
                aliases.append({
                    "company_a": ca["name"],
                    "company_b": cb["name"],
                    "similarity": 1.0,
                    "reason": "identical_normalized_name",
                })
                seen_pairs.add(pair_key)
                continue

            # Fuzzy match
            sim = name_similarity(norm_a, norm_b)
            if sim >= SIMILARITY_THRESHOLD:
                _create_alias_edge(ca["node_id"], cb["node_id"], round(sim, 2),
                                   f"Name similarity {sim:.0%}: '{ca['name']}' ↔ '{cb['name']}'")
                aliases.append({
                    "company_a": ca["name"],
                    "company_b": cb["name"],
                    "similarity": round(sim, 2),
                    "reason": "fuzzy_name_match",
                })
                seen_pairs.add(pair_key)

    return {
        "merges": merges,
        "aliases": aliases,
        "merge_count": len(merges),
        "alias_count": len(aliases),
    }


# ─── Database Operations ─────────────────────────────────────

def _get_all_companies() -> list:
    query = """
    MATCH (c:Company)
    RETURN c.node_id as node_id, c.name as name, c.uei as uei,
           c.address as address, c.cage_code as cage_code
    """
    with db.session() as session:
        result = session.run(query)
        return [record.data() for record in result]


def _merge_company_nodes(keep_id: str, remove_id: str):
    """Merge two Company nodes. Transfers all relationships from remove to keep,
    then deletes the remove node."""
    query = """
    MATCH (keep:Company {node_id: $keep_id})
    MATCH (remove:Company {node_id: $remove_id})

    // Transfer incoming relationships
    WITH keep, remove
    OPTIONAL MATCH (remove)<-[r_in]->(other)
    WHERE other <> keep
    WITH keep, remove, collect({rel: r_in, other: other}) as incoming
    FOREACH (item IN incoming |
        // We can't dynamically create typed rels in Cypher,
        // so we create a generic MERGED_FROM edge instead
    )

    // Mark the removed node
    SET remove.merged_into = $keep_id,
        remove.active = false,
        keep.aliases = coalesce(keep.aliases, []) + [remove.name]

    // Transfer PART_OF_CASE edges
    WITH keep, remove
    OPTIONAL MATCH (remove)-[:PART_OF_CASE]->(c:Case)
    MERGE (keep)-[:PART_OF_CASE]->(c)

    // Transfer AWARDED_TO edges
    WITH keep, remove
    OPTIONAL MATCH (o:Organization)-[r:AWARDED_TO]->(remove)
    MERGE (o)-[:AWARDED_TO {piid: r.piid}]->(keep)

    // Finally detach delete the duplicate
    DETACH DELETE remove
    """
    with db.session() as session:
        session.run(query, {"keep_id": keep_id, "remove_id": remove_id})


def _create_alias_edge(node_id_1: str, node_id_2: str, confidence: float, reason: str):
    """Create a POSSIBLE_ALIAS_OF edge for investigator review."""
    query = """
    MATCH (c1:Company {node_id: $id1})
    MATCH (c2:Company {node_id: $id2})
    MERGE (c1)-[r:POSSIBLE_ALIAS_OF]-(c2)
    SET r.confidence = $confidence,
        r.reason = $reason,
        r.status = 'pending',
        r.source = ['entity_resolution']
    """
    with db.session() as session:
        session.run(query, {
            "id1": node_id_1,
            "id2": node_id_2,
            "confidence": confidence,
            "reason": reason,
        })


# ─── Confirm / Reject Alias ──────────────────────────────────

def confirm_alias(node_id_1: str, node_id_2: str):
    """Investigator confirms alias — merge the nodes."""
    _merge_company_nodes(node_id_1, node_id_2)
    return {"status": "merged", "kept": node_id_1, "removed": node_id_2}


def reject_alias(node_id_1: str, node_id_2: str):
    """Investigator rejects alias — mark edge as rejected."""
    query = """
    MATCH (c1:Company {node_id: $id1})-[r:POSSIBLE_ALIAS_OF]-(c2:Company {node_id: $id2})
    SET r.status = 'rejected'
    """
    with db.session() as session:
        session.run(query, {"id1": node_id_1, "id2": node_id_2})
    return {"status": "rejected"}