// ============================================================
// SONAR - Neo4j Schema
// Suspicious Organization and Network Analysis & Reporting
// ============================================================

// --- CONSTRAINTS (enforce uniqueness) ---

CREATE CONSTRAINT company_id IF NOT EXISTS
FOR (c:Company) REQUIRE c.node_id IS UNIQUE;

CREATE CONSTRAINT individual_id IF NOT EXISTS
FOR (i:Individual) REQUIRE i.node_id IS UNIQUE;

CREATE CONSTRAINT contract_id IF NOT EXISTS
FOR (ct:Contract) REQUIRE ct.node_id IS UNIQUE;

CREATE CONSTRAINT organization_id IF NOT EXISTS
FOR (o:Organization) REQUIRE o.node_id IS UNIQUE;

// --- INDEXES (query performance) ---

CREATE INDEX company_uei IF NOT EXISTS
FOR (c:Company) ON (c.uei);

CREATE INDEX company_cage IF NOT EXISTS
FOR (c:Company) ON (c.cage_code);

CREATE INDEX company_name IF NOT EXISTS
FOR (c:Company) ON (c.name);

CREATE INDEX individual_name IF NOT EXISTS
FOR (i:Individual) ON (i.name);

CREATE INDEX contract_piid IF NOT EXISTS
FOR (ct:Contract) ON (ct.piid);

CREATE INDEX organization_name IF NOT EXISTS
FOR (o:Organization) ON (o.name);

CREATE INDEX node_prominence IF NOT EXISTS
FOR (n:Company) ON (n.prominence_score);