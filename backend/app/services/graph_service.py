from app.database import db
from uuid import uuid4

# ─── Node Creation ───────────────────────────────────────────

def create_company(data: dict):
    query = """
    MERGE (c:Company {uei: $uei})
    ON CREATE SET
        c.node_id = $node_id,
        c.name = $name,
        c.cage_code = $cage_code,
        c.address = $address,
        c.naics_codes = $naics_codes,
        c.entity_type = $entity_type,
        c.set_aside_status = $set_aside_status,
        c.exclusion_flag = $exclusion_flag,
        c.active = $active,
        c.first_seen = $first_seen,
        c.prominence_score = 0.0
    ON MATCH SET
        c.name = $name,
        c.active = $active
    RETURN c
    """
    params = {
        "node_id": str(uuid4()),
        "uei": data.get("uei", ""),
        "name": data.get("name", ""),
        "cage_code": data.get("cage_code", ""),
        "address": data.get("address", ""),
        "naics_codes": data.get("naics_codes", []),
        "entity_type": data.get("entity_type", ""),
        "set_aside_status": data.get("set_aside_status", []),
        "exclusion_flag": data.get("exclusion_flag", False),
        "active": data.get("active", True),
        "first_seen": data.get("first_seen", ""),
    }
    with db.session() as session:
        result = session.run(query, params)
        return result.single()


def create_individual(data: dict):
    query = """
    MERGE (i:Individual {name: $name})
    ON CREATE SET
        i.node_id = $node_id,
        i.roles = $roles,
        i.complaint_appearances = 0,
        i.first_seen = $first_seen,
        i.prominence_score = 0.0
    RETURN i
    """
    params = {
        "node_id": str(uuid4()),
        "name": data.get("name", ""),
        "roles": data.get("roles", []),
        "first_seen": data.get("first_seen", ""),
    }
    with db.session() as session:
        result = session.run(query, params)
        return result.single()


def create_contract(data: dict):
    query = """
    MERGE (ct:Contract {piid: $piid})
    ON CREATE SET
        ct.node_id = $node_id,
        ct.award_amount = $award_amount,
        ct.obligated_amount = $obligated_amount,
        ct.award_date = $award_date,
        ct.contract_type = $contract_type,
        ct.competition_type = $competition_type,
        ct.set_aside_type = $set_aside_type,
        ct.naics_code = $naics_code,
        ct.place_of_performance = $place_of_performance,
        ct.mod_count = $mod_count,
        ct.prominence_score = 0.0
    RETURN ct
    """
    params = {
        "node_id": str(uuid4()),
        "piid": data.get("piid", ""),
        "award_amount": data.get("award_amount", 0.0),
        "obligated_amount": data.get("obligated_amount", 0.0),
        "award_date": data.get("award_date", ""),
        "contract_type": data.get("contract_type", ""),
        "competition_type": data.get("competition_type", ""),
        "set_aside_type": data.get("set_aside_type", ""),
        "naics_code": data.get("naics_code", ""),
        "place_of_performance": data.get("place_of_performance", ""),
        "mod_count": data.get("mod_count", 0),
    }
    with db.session() as session:
        result = session.run(query, params)
        return result.single()


def create_organization(data: dict):
    query = """
    MERGE (o:Organization {name: $name})
    ON CREATE SET
        o.node_id = $node_id,
        o.org_type = $org_type,
        o.uic = $uic,
        o.total_obligated = 0.0,
        o.prominence_score = 0.0
    RETURN o
    """
    params = {
        "node_id": str(uuid4()),
        "name": data.get("name", ""),
        "org_type": data.get("org_type", ""),
        "uic": data.get("uic", ""),
    }
    with db.session() as session:
        result = session.run(query, params)
        return result.single()


def create_filing990(data: dict):
    """Create a Filing990 node for IRS 990 tax filing data."""
    query = """
    MERGE (f:Filing990 {ein: $ein, tax_period: $tax_period})
    ON CREATE SET
        f.node_id = $node_id,
        f.tax_year = $tax_year,
        f.form_type = $form_type,
        f.total_revenue = $total_revenue,
        f.total_expenses = $total_expenses,
        f.total_assets = $total_assets,
        f.total_liabilities = $total_liabilities,
        f.net_assets = $net_assets,
        f.officer_compensation_pct = $officer_compensation_pct,
        f.program_service_revenue = $program_service_revenue,
        f.contributions_grants = $contributions_grants,
        f.investment_income = $investment_income,
        f.government_grants = $government_grants,
        f.comp_curnt_ofcrs_key = $comp_curnt_ofcrs_key,
        f.comp_former_ofcrs = $comp_former_ofcrs,
        f.other_salaries = $other_salaries,
        f.total_compensation = $total_compensation,
        f.pdf_url = $pdf_url,
        f.prominence_score = 0.0
    ON MATCH SET
        f.total_revenue = $total_revenue,
        f.total_expenses = $total_expenses,
        f.total_assets = $total_assets
    RETURN f
    """
    params = {
        "node_id": str(uuid4()),
        "ein": data.get("ein", ""),
        "tax_period": data.get("tax_period", ""),
        "tax_year": data.get("tax_year", 0),
        "form_type": data.get("form_type", ""),
        "total_revenue": data.get("total_revenue", 0.0),
        "total_expenses": data.get("total_expenses", 0.0),
        "total_assets": data.get("total_assets", 0.0),
        "total_liabilities": data.get("total_liabilities", 0.0),
        "net_assets": data.get("net_assets", 0.0),
        "officer_compensation_pct": data.get("officer_compensation_pct", 0.0),
        "program_service_revenue": data.get("program_service_revenue", 0.0),
        "contributions_grants": data.get("contributions_grants", 0.0),
        "investment_income": data.get("investment_income", 0.0),
        "government_grants": data.get("government_grants", 0.0),
        "comp_curnt_ofcrs_key": data.get("comp_curnt_ofcrs_key", 0.0),
        "comp_former_ofcrs": data.get("comp_former_ofcrs", 0.0),
        "other_salaries": data.get("other_salaries", 0.0),
        "total_compensation": data.get("total_compensation", 0.0),
        "pdf_url": data.get("pdf_url", ""),
    }
    with db.session() as session:
        result = session.run(query, params)
        return result.single()


# ─── Edge Creation ───────────────────────────────────────────

def create_awarded_to(org_name: str, company_uei: str, props: dict):
    query = """
    MATCH (o:Organization {name: $org_name})
    MATCH (c:Company {uei: $company_uei})
    MERGE (o)-[r:AWARDED_TO {piid: $piid}]->(c)
    SET r.weight = $weight,
        r.confidence = $confidence,
        r.source = $source,
        r.amount = $amount,
        r.date = $date,
        r.competition_type = $competition_type
    RETURN r
    """
    params = {
        "org_name": org_name,
        "company_uei": company_uei,
        "piid": props.get("piid", ""),
        "weight": props.get("weight", 0.0),
        "confidence": props.get("confidence", 1.0),
        "source": props.get("source", ["FPDS"]),
        "amount": props.get("amount", 0.0),
        "date": props.get("date", ""),
        "competition_type": props.get("competition_type", ""),
    }
    with db.session() as session:
        result = session.run(query, params)
        return result.single()


def create_principal_of(individual_name: str, company_uei: str, props: dict):
    query = """
    MATCH (i:Individual {name: $individual_name})
    MATCH (c:Company {uei: $company_uei})
    MERGE (i)-[r:PRINCIPAL_OF]->(c)
    SET r.weight = $weight,
        r.confidence = $confidence,
        r.source = $source,
        r.title = $title,
        r.start_date = $start_date
    RETURN r
    """
    params = {
        "individual_name": individual_name,
        "company_uei": company_uei,
        "weight": props.get("weight", 1.0),
        "confidence": props.get("confidence", 1.0),
        "source": props.get("source", ["SAM"]),
        "title": props.get("title", ""),
        "start_date": props.get("start_date", ""),
    }
    with db.session() as session:
        result = session.run(query, params)
        return result.single()


def create_shares_address_with(company_uei_1: str, company_uei_2: str, props: dict):
    query = """
    MATCH (c1:Company {uei: $uei_1})
    MATCH (c2:Company {uei: $uei_2})
    MERGE (c1)-[r:SHARES_ADDRESS_WITH]-(c2)
    SET r.weight = $weight,
        r.confidence = $confidence,
        r.source = $source,
        r.address = $address,
        r.shared_attributes = $shared_attributes
    RETURN r
    """
    params = {
        "uei_1": company_uei_1,
        "uei_2": company_uei_2,
        "weight": props.get("weight", 1.0),
        "confidence": props.get("confidence", 0.9),
        "source": props.get("source", ["SAM"]),
        "address": props.get("address", ""),
        "shared_attributes": props.get("shared_attributes", []),
    }
    with db.session() as session:
        result = session.run(query, params)
        return result.single()


def create_filed_by(company_uei: str, filing_ein: str, filing_tax_period: str, props: dict):
    """Create FILED edge from Company → Filing990."""
    query = """
    MATCH (c:Company {uei: $uei})
    MATCH (f:Filing990 {ein: $ein, tax_period: $tax_period})
    MERGE (c)-[r:FILED]->(f)
    SET r.source = $source,
        r.confidence = $confidence
    RETURN r
    """
    params = {
        "uei": company_uei,
        "ein": filing_ein,
        "tax_period": filing_tax_period,
        "source": props.get("source", ["ProPublica"]),
        "confidence": props.get("confidence", 0.85),
    }
    with db.session() as session:
        result = session.run(query, params)
        return result.single()


def create_officer_of(individual_name: str, company_uei: str, props: dict):
    """Create OFFICER_OF edge from Individual → Company (from 990 data)."""
    query = """
    MATCH (i:Individual {name: $individual_name})
    MATCH (c:Company {uei: $company_uei})
    MERGE (i)-[r:OFFICER_OF]->(c)
    SET r.weight = $weight,
        r.confidence = $confidence,
        r.source = $source,
        r.title = $title,
        r.compensation = $compensation
    RETURN r
    """
    params = {
        "individual_name": individual_name,
        "company_uei": company_uei,
        "weight": props.get("weight", 1.0),
        "confidence": props.get("confidence", 0.85),
        "source": props.get("source", ["990"]),
        "title": props.get("title", ""),
        "compensation": props.get("compensation", 0.0),
    }
    with db.session() as session:
        result = session.run(query, params)
        return result.single()


# ─── Nonprofit Enrichment ────────────────────────────────────

def enrich_company_nonprofit(uei: str, data: dict):
    """Enrich a Company node with 990 nonprofit data."""
    query = """
    MATCH (c:Company {uei: $uei})
    SET c.ein = $ein,
        c.nonprofit_status = true,
        c.total_990_revenue = $total_990_revenue,
        c.total_990_expenses = $total_990_expenses,
        c.total_990_assets = $total_990_assets,
        c.officer_comp_pct = $officer_comp_pct,
        c.total_officer_compensation = $total_officer_compensation,
        c.latest_990_year = $latest_990_year,
        c.ntee_code = $ntee_code,
        c.subsection_code = $subsection_code,
        c.nonprofit_enriched = true
    RETURN c
    """
    params = {
        "uei": uei,
        "ein": data.get("ein", ""),
        "total_990_revenue": data.get("latest_revenue", 0),
        "total_990_expenses": data.get("latest_expenses", 0),
        "total_990_assets": data.get("latest_assets", 0),
        "officer_comp_pct": data.get("officer_comp_pct", 0),
        "total_officer_compensation": data.get("total_officer_compensation", 0),
        "latest_990_year": data.get("latest_tax_year", 0),
        "ntee_code": data.get("ntee_code", ""),
        "subsection_code": data.get("subsection_code", ""),
    }
    with db.session() as session:
        result = session.run(query, params)
        return result.single()


# ─── Graph Queries ───────────────────────────────────────────

def get_full_graph():
    query = """
    MATCH (n)-[r]->(m)
    RETURN n, r, m
    LIMIT 500
    """
    with db.session() as session:
        result = session.run(query)
        return [record.data() for record in result]


def get_node_by_id(node_id: str):
    query = """
    MATCH (n {node_id: $node_id})
    OPTIONAL MATCH (n)-[r]-(m)
    RETURN n, collect(r) as relationships, collect(m) as neighbors
    """
    with db.session() as session:
        result = session.run(query, {"node_id": node_id})
        return result.single()


def get_top_prominence(limit: int = 20):
    query = """
    MATCH (n)
    WHERE n.prominence_score IS NOT NULL
    RETURN n.name as name, labels(n) as type, n.prominence_score as score
    ORDER BY n.prominence_score DESC
    LIMIT $limit
    """
    with db.session() as session:
        result = session.run(query, {"limit": limit})
        return [record.data() for record in result]


# ─── Enrichment ──────────────────────────────────────────────

def enrich_company(uei: str, data: dict):
    """
    Enrich an existing Company node with SAM.gov data.
    Only updates fields that are empty or add new SAM-specific data.
    Does not overwrite name or existing non-empty fields from USASpending.
    """
    query = """
    MATCH (c:Company {uei: $uei})
    SET c.cage_code = CASE WHEN c.cage_code IS NULL OR c.cage_code = ''
                           THEN $cage_code ELSE c.cage_code END,
        c.entity_type = CASE WHEN c.entity_type IS NULL OR c.entity_type = ''
                              THEN $entity_type ELSE c.entity_type END,
        c.set_aside_status = CASE WHEN c.set_aside_status IS NULL OR size(c.set_aside_status) = 0
                                   THEN $set_aside_status ELSE c.set_aside_status END,
        c.exclusion_flag = $exclusion_flag,
        c.address = CASE WHEN c.address IS NULL OR c.address = ''
                         THEN $address ELSE c.address END,
        c.dba_name = $dba_name,
        c.registration_date = $registration_date,
        c.registration_expiration = $registration_expiration,
        c.state_of_incorporation = $state_of_incorporation,
        c.country_of_incorporation = $country_of_incorporation,
        c.profit_structure = $profit_structure,
        c.sam_enriched = true
    RETURN c
    """
    params = {
        "uei": uei,
        "cage_code": data.get("cage_code", ""),
        "entity_type": data.get("entity_type", ""),
        "set_aside_status": data.get("set_aside_status", []),
        "exclusion_flag": data.get("exclusion_flag", False),
        "address": data.get("address", ""),
        "dba_name": data.get("dba_name", ""),
        "registration_date": data.get("registration_date", ""),
        "registration_expiration": data.get("registration_expiration", ""),
        "state_of_incorporation": data.get("state_of_incorporation", ""),
        "country_of_incorporation": data.get("country_of_incorporation", ""),
        "profit_structure": data.get("profit_structure", ""),
    }
    with db.session() as session:
        result = session.run(query, params)
        return result.single()