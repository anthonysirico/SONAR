"""
SONAR — Case Service
Manages investigation cases in Neo4j. Each case groups related nodes
discovered during searches and analysis.
"""

from app.database import db
from uuid import uuid4
from datetime import datetime, timezone


def create_case(name: str, description: str = "") -> dict:
    """Create a new investigation case."""
    query = """
    CREATE (c:Case {
        case_id: $case_id,
        name: $name,
        description: $description,
        created_at: $created_at,
        updated_at: $created_at,
        status: 'open',
        node_count: 0,
        edge_count: 0
    })
    RETURN c
    """
    case_id = str(uuid4())
    now = datetime.now(timezone.utc).isoformat()
    with db.session() as session:
        result = session.run(query, {
            "case_id": case_id,
            "name": name,
            "description": description,
            "created_at": now,
        })
        record = result.single()
        return dict(record["c"]) if record else {}


def get_case(case_id: str) -> dict:
    """Get a case by ID with node/edge counts."""
    query = """
    MATCH (c:Case {case_id: $case_id})
    OPTIONAL MATCH (n)-[:PART_OF_CASE]->(c)
    WITH c, count(n) as node_count
    RETURN c, node_count
    """
    with db.session() as session:
        result = session.run(query, {"case_id": case_id})
        record = result.single()
        if not record:
            return {}
        case = dict(record["c"])
        case["node_count"] = record["node_count"]
        return case


def list_cases(status: str = None) -> list:
    """List all cases, optionally filtered by status."""
    if status:
        query = """
        MATCH (c:Case {status: $status})
        OPTIONAL MATCH (n)-[:PART_OF_CASE]->(c)
        WITH c, count(n) as node_count
        RETURN c, node_count
        ORDER BY c.created_at DESC
        """
        params = {"status": status}
    else:
        query = """
        MATCH (c:Case)
        OPTIONAL MATCH (n)-[:PART_OF_CASE]->(c)
        WITH c, count(n) as node_count
        RETURN c, node_count
        ORDER BY c.created_at DESC
        """
        params = {}
    with db.session() as session:
        result = session.run(query, params)
        cases = []
        for record in result:
            case = dict(record["c"])
            case["node_count"] = record["node_count"]
            cases.append(case)
        return cases


def close_case(case_id: str) -> dict:
    """Close a case."""
    query = """
    MATCH (c:Case {case_id: $case_id})
    SET c.status = 'closed',
        c.updated_at = $updated_at
    RETURN c
    """
    now = datetime.now(timezone.utc).isoformat()
    with db.session() as session:
        result = session.run(query, {"case_id": case_id, "updated_at": now})
        record = result.single()
        return dict(record["c"]) if record else {}


def link_node_to_case(node_id: str, case_id: str) -> bool:
    """Create PART_OF_CASE edge from any node to a case."""
    query = """
    MATCH (n {node_id: $node_id})
    MATCH (c:Case {case_id: $case_id})
    MERGE (n)-[:PART_OF_CASE]->(c)
    SET c.updated_at = $updated_at
    RETURN n, c
    """
    now = datetime.now(timezone.utc).isoformat()
    with db.session() as session:
        result = session.run(query, {
            "node_id": node_id,
            "case_id": case_id,
            "updated_at": now,
        })
        return result.single() is not None


def get_case_graph(case_id: str) -> list:
    """Get all nodes and their relationships within a case."""
    query = """
    MATCH (n)-[:PART_OF_CASE]->(c:Case {case_id: $case_id})
    OPTIONAL MATCH (n)-[r]-(m)
    WHERE (m)-[:PART_OF_CASE]->(c)
    RETURN n, r, m
    """
    with db.session() as session:
        result = session.run(query, {"case_id": case_id})
        return [record.data() for record in result]


def update_case_timestamp(case_id: str):
    """Touch the updated_at timestamp."""
    query = """
    MATCH (c:Case {case_id: $case_id})
    SET c.updated_at = $updated_at
    """
    now = datetime.now(timezone.utc).isoformat()
    with db.session() as session:
        session.run(query, {"case_id": case_id, "updated_at": now})


def delete_case(case_id: str) -> bool:
    """
    Delete a case and clear all of its data.
    Nodes that belong only to this case are DETACH DELETEd (removing all their edges too).
    Nodes shared with other cases have only their PART_OF_CASE edge to this case removed.
    The Case node itself is deleted last.
    """
    with db.session() as session:
        exists = session.run(
            "MATCH (c:Case {case_id: $case_id}) RETURN c",
            {"case_id": case_id}
        ).single()
        if not exists:
            return False

        # Delete nodes that belong exclusively to this case
        session.run("""
            MATCH (n)-[:PART_OF_CASE]->(c:Case {case_id: $case_id})
            OPTIONAL MATCH (n)-[:PART_OF_CASE]->(other:Case)
            WHERE other.case_id <> $case_id
            WITH n, count(other) AS shared
            WHERE shared = 0
            DETACH DELETE n
        """, {"case_id": case_id})

        # Remove the PART_OF_CASE edges for nodes shared with other cases
        session.run("""
            MATCH (n)-[r:PART_OF_CASE]->(c:Case {case_id: $case_id})
            DELETE r
        """, {"case_id": case_id})

        # Delete the Case node itself
        session.run("""
            MATCH (c:Case {case_id: $case_id})
            DETACH DELETE c
        """, {"case_id": case_id})

        return True