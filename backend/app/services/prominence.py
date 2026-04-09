import math
from app.database import db

# ─── Tunable Weights ─────────────────────────────────────────
ALPHA = 0.4   # degree centrality weight
BETA  = 0.6   # influence weight
GAMMA = 0.3   # complaint/investigation appearance weight
DELTA = 0.5   # derogatory flag multiplier
LAMBDA_DECAY = 0.001  # time decay rate (per day)

# ─── Recency Factor ──────────────────────────────────────────
def recency_factor(days_since_activity: float) -> float:
    return math.exp(-LAMBDA_DECAY * days_since_activity)

# ─── Normalize a value against a max ─────────────────────────
def normalize(value: float, max_value: float) -> float:
    if max_value == 0:
        return 0.0
    return min(value / max_value, 1.0)

# ─── Compute prominence for all nodes ────────────────────────
def compute_all_prominence():
    with db.session() as session:

        # Get max values for normalization
        max_vals = session.run("""
            MATCH (n)
            OPTIONAL MATCH (n)-[r]-()
            WITH n,
                 count(r) as degree,
                 coalesce(n.total_obligated, 0) as dollars,
                 coalesce(n.complaint_appearances, 0) as complaints
            RETURN
                max(degree) as max_degree,
                max(dollars) as max_dollars,
                max(complaints) as max_complaints
        """).single()

        max_degree     = max_vals["max_degree"] or 1
        max_dollars    = max_vals["max_dollars"] or 1
        max_complaints = max_vals["max_complaints"] or 1

        # Get all nodes with their stats
        nodes = session.run("""
            MATCH (n)
            OPTIONAL MATCH (n)-[r]-()
            WITH n,
                 count(r) as degree,
                 coalesce(n.total_obligated, 0) as dollars,
                 coalesce(n.complaint_appearances, 0) as complaints,
                 coalesce(n.exclusion_flag, false) as excluded,
                 n.node_id as node_id,
                 n.name as name
            RETURN node_id, name, degree, dollars, complaints, excluded
        """)

        for record in nodes:
            node_id = record["node_id"]
            if not node_id:
                continue

            degree     = record["degree"]
            dollars    = record["dollars"]
            complaints = record["complaints"]
            excluded   = record["excluded"]

            cd = normalize(degree, max_degree)
            wd = normalize(dollars, max_dollars)
            f  = normalize(complaints, max_complaints)
            x  = DELTA if excluded else 0.0

            W = normalize(wd, 1.0) + GAMMA * f + x
            W = min(W, 1.0)

            P = round(ALPHA * cd + BETA * W, 4)

            # ─── Build explanation trail ─────────────────
            factors = []

            if degree > 0:
                factors.append(
                    f"Degree centrality: {degree} connection(s) "
                    f"(normalized {cd:.2f}, weighted {ALPHA * cd:.3f})"
                )

            if dollars > 0:
                factors.append(
                    f"Financial weight: ${dollars:,.0f} obligated "
                    f"(normalized {wd:.2f})"
                )

            if complaints > 0:
                factors.append(
                    f"Complaint appearances: {complaints} "
                    f"(adds {GAMMA * f:.3f} to influence)"
                )

            if excluded:
                factors.append(
                    f"Exclusion flag active (adds {DELTA} to influence)"
                )

            if not factors:
                factors.append("No significant activity detected")

            # Tier label for the explanation header
            if P >= 0.75:
                tier = "CRITICAL"
            elif P >= 0.50:
                tier = "ELEVATED"
            elif P >= 0.25:
                tier = "WATCH"
            else:
                tier = "BASELINE"

            factors.insert(0, f"{tier} — prominence score {P:.4f}")

            session.run("""
                MATCH (n {node_id: $node_id})
                SET n.prominence_score = $score,
                    n.prominence_factors = $factors
            """, {
                "node_id": node_id,
                "score": P,
                "factors": factors,
            })

    return {"status": "Prominence scores updated"}