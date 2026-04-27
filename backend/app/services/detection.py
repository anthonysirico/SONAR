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


# ─── Pattern 6: Nonprofit Revenue Anomaly ────────────────────
# Nonprofit company receiving more in government contracts
# than its total reported 990 revenue

def detect_nonprofit_revenue_anomaly():
    query = """
    MATCH (c:Company)
    WHERE c.nonprofit_status = true
      AND c.total_990_revenue IS NOT NULL
      AND c.total_990_revenue > 0
    OPTIONAL MATCH (o:Organization)-[r:AWARDED_TO]->(c)
    WITH c, sum(r.amount) as total_awarded
    WHERE total_awarded > 0
      AND total_awarded > c.total_990_revenue * 0.8
    RETURN
        c.node_id as company_id,
        c.name as company,
        c.total_990_revenue as reported_revenue,
        total_awarded,
        c.profit_structure as profit_structure,
        c.latest_990_year as latest_990_year,
        CASE
            WHEN total_awarded > c.total_990_revenue * 2 THEN 0.92
            WHEN total_awarded > c.total_990_revenue THEN 0.85
            ELSE 0.78
        END as confidence
    ORDER BY total_awarded DESC
    """
    with db.session() as session:
        result = session.run(query)
        findings = [record.data() for record in result]
        for f in findings:
            ratio = f['total_awarded'] / f['reported_revenue'] if f['reported_revenue'] > 0 else 0
            explanation = (
                f"NONPROFIT REVENUE ANOMALY: {f['company']} claims nonprofit status "
                f"but received ${f['total_awarded']:,.0f} in government contracts, "
                f"which is {ratio:.1f}x its reported 990 revenue of "
                f"${f['reported_revenue']:,.0f} (tax year {f.get('latest_990_year', 'unknown')}). "
                f"This discrepancy between nonprofit filings and federal contract revenue "
                f"warrants investigation for misclassification or undisclosed revenue."
            )
            _tag_node(f["company_id"], "NONPROFIT_REVENUE_ANOMALY", f["confidence"], explanation)
        return findings


# ─── Pattern 7: Executive Compensation Outlier ───────────────
# Nonprofit where officer compensation is disproportionately
# high relative to total revenue

def detect_exec_comp_outlier():
    query = """
    MATCH (c:Company)
    WHERE c.nonprofit_status = true
      AND c.total_officer_compensation IS NOT NULL
      AND c.total_officer_compensation > 0
      AND c.total_990_revenue IS NOT NULL
      AND c.total_990_revenue > 0
    WITH c,
         c.total_officer_compensation as officer_comp,
         c.total_990_revenue as revenue,
         toFloat(c.total_officer_compensation) / toFloat(c.total_990_revenue) as comp_ratio
    WHERE comp_ratio > 0.20 OR officer_comp > 1000000
    RETURN
        c.node_id as company_id,
        c.name as company,
        officer_comp,
        revenue,
        comp_ratio,
        CASE
            WHEN comp_ratio > 0.50 THEN 0.90
            WHEN officer_comp > 2000000 THEN 0.85
            WHEN comp_ratio > 0.30 THEN 0.80
            ELSE 0.72
        END as confidence
    ORDER BY comp_ratio DESC
    """
    with db.session() as session:
        result = session.run(query)
        findings = [record.data() for record in result]
        for f in findings:
            explanation = (
                f"EXEC COMP OUTLIER: {f['company']} (nonprofit) reported "
                f"${f['officer_comp']:,.0f} in officer compensation against "
                f"${f['revenue']:,.0f} total revenue ({f['comp_ratio']:.1%} ratio). "
                f"Nonprofit organizations directing a disproportionate share of "
                f"revenue to executive compensation may indicate private inurement "
                f"or abuse of tax-exempt status."
            )
            _tag_node(f["company_id"], "EXEC_COMP_OUTLIER", f["confidence"], explanation)
        return findings


# ─── Pattern 8: Nonprofit + Sole Source Concentration ────────
# Nonprofit receiving multiple sole-source awards from same org

def detect_nonprofit_sole_source():
    query = """
    MATCH (o:Organization)-[r:AWARDED_TO]->(c:Company)
    WHERE c.nonprofit_status = true
      AND r.competition_type IN ['SOLE_SOURCE', 'Not Competed', 'Not Available for Competition']
    WITH o, c, count(r) as sole_count, sum(r.amount) as total
    WHERE sole_count >= 2
    RETURN
        o.name as org,
        c.node_id as company_id,
        c.name as company,
        sole_count,
        total,
        0.85 as confidence
    ORDER BY sole_count DESC
    """
    with db.session() as session:
        result = session.run(query)
        findings = [record.data() for record in result]
        for f in findings:
            explanation = (
                f"NONPROFIT SOLE SOURCE: {f['company']} (nonprofit) received "
                f"{f['sole_count']} sole-source award(s) from {f['org']} "
                f"totaling ${f['total']:,.0f}. Nonprofits receiving repeated "
                f"non-competitive awards from a single agency may indicate "
                f"improper steering or abuse of nonprofit set-aside preferences."
            )
            _tag_node(f["company_id"], "NONPROFIT_SOLE_SOURCE", f["confidence"], explanation)
        return findings


# ─── Run All Patterns ─────────────────────────────────────────

def run_all_detections():
    # Clear previous flags before re-running
    _clear_wfa_flags()
    return {
        "shell_clusters":              detect_shell_clusters(),
        "revolving_door":              detect_revolving_door(),
        "split_awards":                detect_split_awards(),
        "exclusion_evasion":           detect_exclusion_evasion(),
        "sole_source_concentration":   detect_sole_source_concentration(),
        "nonprofit_revenue_anomaly":   detect_nonprofit_revenue_anomaly(),
        "exec_comp_outlier":           detect_exec_comp_outlier(),
        "nonprofit_sole_source":       detect_nonprofit_sole_source(),
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