from app.database import db

# ─── Pattern 1: Shell Company Cluster ────────────────────────
# Companies sharing address AND principal

def detect_shell_clusters():
    query = """
    MATCH (c1:Company)-[sa:SHARES_ADDRESS_WITH]-(c2:Company)
    MATCH (i:Individual)-[:PRINCIPAL_OF]->(c1)
    MATCH (i)-[:PRINCIPAL_OF]->(c2)
    RETURN
        c1.node_id as node_id_1,
        c1.name as company_1,
        c2.node_id as node_id_2,
        c2.name as company_2,
        i.name as shared_principal,
        sa.address as shared_address,
        0.92 as confidence
    """
    with db.session() as session:
        result = session.run(query)
        findings = [record.data() for record in result]
        for f in findings:
            explanation = (
                f"SHELL CLUSTER: {f['company_1']} and {f['company_2']} "
                f"share the same address ({f.get('shared_address', 'unknown')}) "
                f"and the same principal ({f['shared_principal']}). "
                f"This pattern is consistent with shell company structures "
                f"used to circumvent competition requirements."
            )
            _tag_node(f["node_id_1"], "SHELL_CLUSTER", f["confidence"], explanation)
            _tag_node(f["node_id_2"], "SHELL_CLUSTER", f["confidence"], explanation)
        return findings


# ─── Pattern 2: Revolving Door ───────────────────────────────
# Individual formerly employed by org that awarded to company
# where individual is now principal

def detect_revolving_door():
    query = """
    MATCH (i:Individual)-[fe:FORMERLY_EMPLOYED_BY]->(o:Organization)
    MATCH (i)-[:PRINCIPAL_OF]->(c:Company)
    MATCH (o)-[aw:AWARDED_TO]->(c)
    RETURN
        i.node_id as individual_id,
        i.name as individual,
        o.name as org,
        c.node_id as company_id,
        c.name as company,
        fe.last_role as last_role,
        fe.departure_date as departure_date,
        aw.date as award_date,
        aw.amount as award_amount,
        0.88 as confidence
    """
    with db.session() as session:
        result = session.run(query)
        findings = [record.data() for record in result]
        for f in findings:
            amt = f.get('award_amount')
            amt_str = f" totaling ${amt:,.0f}" if amt else ""
            dep = f.get('departure_date')
            dep_str = f" (departed {dep})" if dep else ""
            explanation = (
                f"REVOLVING DOOR: {f['individual']} formerly served as "
                f"{f.get('last_role', 'unknown role')} at {f['org']}"
                f"{dep_str}, "
                f"and is now a principal of {f['company']}, which received "
                f"award(s) from that same organization{amt_str}. "
                f"This may indicate improper post-government employment activity."
            )
            _tag_node(f["individual_id"], "REVOLVING_DOOR", f["confidence"], explanation)
            _tag_node(f["company_id"],    "REVOLVING_DOOR", f["confidence"], explanation)
        return findings


# ─── Pattern 3: Split Award ───────────────────────────────────
# Same org awarding multiple sole-source contracts to related
# companies below threshold in short succession

def detect_split_awards():
    query = """
    MATCH (o:Organization)-[r1:AWARDED_TO]->(c1:Company)
    MATCH (o)-[r2:AWARDED_TO]->(c2:Company)
    WHERE c1 <> c2
    AND r1.competition_type = 'SOLE_SOURCE'
    AND r2.competition_type = 'SOLE_SOURCE'
    AND r1.amount < 250000
    AND r2.amount < 250000
    AND (c1)-[:SHARES_ADDRESS_WITH|SHARES_PRINCIPAL_WITH]-(c2)
    RETURN
        o.name as org,
        c1.node_id as company_id_1,
        c1.name as company_1,
        r1.amount as amount_1,
        r1.piid as piid_1,
        c2.node_id as company_id_2,
        c2.name as company_2,
        r2.amount as amount_2,
        r2.piid as piid_2,
        (r1.amount + r2.amount) as combined_value,
        0.85 as confidence
    """
    with db.session() as session:
        result = session.run(query)
        findings = [record.data() for record in result]
        for f in findings:
            explanation = (
                f"SPLIT AWARD: {f['org']} awarded sole-source contracts to "
                f"{f['company_1']} (${f['amount_1']:,.0f}, {f.get('piid_1', '')}) and "
                f"{f['company_2']} (${f['amount_2']:,.0f}, {f.get('piid_2', '')}), "
                f"both below the $250K threshold (combined ${f['combined_value']:,.0f}). "
                f"These companies share an address or principal, suggesting possible "
                f"award splitting to avoid competition requirements."
            )
            _tag_node(f["company_id_1"], "SPLIT_AWARD", f["confidence"], explanation)
            _tag_node(f["company_id_2"], "SPLIT_AWARD", f["confidence"], explanation)
        return findings


# ─── Pattern 4: Exclusion Evasion ────────────────────────────
# Individual principal of excluded company is also principal
# of an active company receiving awards

def detect_exclusion_evasion():
    query = """
    MATCH (i:Individual)-[:PRINCIPAL_OF]->(c_excl:Company {exclusion_flag: true})
    MATCH (i)-[:PRINCIPAL_OF]->(c_active:Company {exclusion_flag: false, active: true})
    MATCH (o:Organization)-[aw:AWARDED_TO]->(c_active)
    RETURN
        i.node_id as individual_id,
        i.name as individual,
        c_excl.name as excluded_company,
        c_active.node_id as active_company_id,
        c_active.name as active_company,
        o.name as awarding_org,
        aw.amount as award_amount,
        0.95 as confidence
    """
    with db.session() as session:
        result = session.run(query)
        findings = [record.data() for record in result]
        for f in findings:
            amt = f.get('award_amount')
            amt_str = f" totaling ${amt:,.0f}" if amt else ""
            explanation = (
                f"EXCLUSION EVASION: {f['individual']} is a principal of "
                f"{f['excluded_company']} (EXCLUDED) and also a principal of "
                f"{f['active_company']} (ACTIVE), which received award(s) from "
                f"{f['awarding_org']}{amt_str}. "
                f"This is a high-confidence indicator of excluded party evasion."
            )
            _tag_node(f["individual_id"],     "EXCLUSION_EVASION", f["confidence"], explanation)
            _tag_node(f["active_company_id"], "EXCLUSION_EVASION", f["confidence"], explanation)
        return findings


# ─── Pattern 5: Sole Source Concentration ────────────────────
# Single vendor receiving disproportionate sole source awards
# from one org

def detect_sole_source_concentration():
    query = """
    MATCH (o:Organization)-[r:AWARDED_TO]->(c:Company)
    WHERE r.competition_type = 'SOLE_SOURCE'
    WITH o, c, count(r) as sole_source_count, sum(r.amount) as total
    WHERE sole_source_count >= 2
    RETURN
        o.name as org,
        c.node_id as company_id,
        c.name as company,
        sole_source_count,
        total,
        0.78 as confidence
    ORDER BY sole_source_count DESC
    """
    with db.session() as session:
        result = session.run(query)
        findings = [record.data() for record in result]
        for f in findings:
            explanation = (
                f"SOLE SOURCE CONCENTRATION: {f['company']} received "
                f"{f['sole_source_count']} sole-source award(s) from {f['org']} "
                f"totaling ${f['total']:,.0f}. Disproportionate sole-source "
                f"activity from a single agency may indicate favoritism or "
                f"improper steering."
            )
            _tag_node(f["company_id"], "SOLE_SOURCE_CONCENTRATION", f["confidence"], explanation)
        return findings


# ─── Run All Patterns ─────────────────────────────────────────

def run_all_detections():
    # Clear previous flags before re-running
    _clear_wfa_flags()
    return {
        "shell_clusters":           detect_shell_clusters(),
        "revolving_door":           detect_revolving_door(),
        "split_awards":             detect_split_awards(),
        "exclusion_evasion":        detect_exclusion_evasion(),
        "sole_source_concentration": detect_sole_source_concentration(),
    }


# ─── Clear WFA Flags ──────────────────────────────────────────

def _clear_wfa_flags():
    """Remove all WFA flags/explanations before re-detection."""
    query = """
    MATCH (n)
    WHERE n.wfa_flags IS NOT NULL
    SET n.wfa_flags = [],
        n.wfa_explanations = [],
        n.wfa_confidence = null
    """
    with db.session() as session:
        session.run(query)


# ─── Tag Node with WFA Flag ───────────────────────────────────

def _tag_node(node_id: str, flag: str, confidence: float, explanation: str = ""):
    query = """
    MATCH (n {node_id: $node_id})
    SET n.wfa_flags = [x IN coalesce(n.wfa_flags, []) WHERE x <> $flag] + [$flag],
        n.wfa_explanations = coalesce(n.wfa_explanations, []) + [$explanation],
        n.wfa_confidence = CASE
            WHEN coalesce(n.wfa_confidence, 0) < $confidence
            THEN $confidence
            ELSE n.wfa_confidence
        END
    """
    with db.session() as session:
        session.run(query, {
            "node_id": node_id,
            "flag": flag,
            "confidence": confidence,
            "explanation": explanation,
        })