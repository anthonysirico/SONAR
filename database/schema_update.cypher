// ============================================================
// SONAR — Schema Update: Case Support
// Run after initial schema.cypher
// ============================================================

// --- Case node constraint ---
CREATE CONSTRAINT case_id IF NOT EXISTS
FOR (c:Case) REQUIRE c.case_id IS UNIQUE;

// --- Case indexes ---
CREATE INDEX case_status IF NOT EXISTS
FOR (c:Case) ON (c.status);

CREATE INDEX case_created IF NOT EXISTS
FOR (c:Case) ON (c.created_at);
