// ============================================================
// SONAR - Seed Data
// Fictional data for development and testing
// ============================================================

// --- ORGANIZATIONS ---

MERGE (o1:Organization {name: "Naval Supply Systems Command"})
SET o1.node_id = randomUUID(),
    o1.org_type = "SYSCOM",
    o1.uic = "N00189",
    o1.total_obligated = 0.0,
    o1.prominence_score = 0.0;

MERGE (o2:Organization {name: "NAVFAC Southwest"})
SET o2.node_id = randomUUID(),
    o2.org_type = "Command",
    o2.uic = "N62473",
    o2.total_obligated = 0.0,
    o2.prominence_score = 0.0;

MERGE (o3:Organization {name: "Program Executive Office Digital"})
SET o3.node_id = randomUUID(),
    o3.org_type = "PEO",
    o3.uic = "N00039",
    o3.total_obligated = 0.0,
    o3.prominence_score = 0.0;

// --- COMPANIES ---

// Legitimate company
MERGE (c1:Company {uei: "ABC123DEF456"})
SET c1.node_id = randomUUID(),
    c1.name = "Meridian Defense Solutions LLC",
    c1.cage_code = "7X4A1",
    c1.address = "1400 Defense Blvd, Arlington, VA 22201",
    c1.naics_codes = ["541512", "541519"],
    c1.entity_type = "LLC",
    c1.set_aside_status = [],
    c1.exclusion_flag = false,
    c1.active = true,
    c1.first_seen = "2018-03-15",
    c1.prominence_score = 0.0;

// Shell company 1 - shares address with shell company 2
MERGE (c2:Company {uei: "XYZ789GHI012"})
SET c2.node_id = randomUUID(),
    c2.name = "Coastal Technical Services Inc",
    c2.cage_code = "8B3C2",
    c2.address = "7701 Ringwood Ave Suite 100, San Diego, CA 92111",
    c2.naics_codes = ["541330"],
    c2.entity_type = "Corporation",
    c2.set_aside_status = ["SDVOSB"],
    c2.exclusion_flag = false,
    c2.active = true,
    c2.first_seen = "2020-06-01",
    c2.prominence_score = 0.0;

// Shell company 2 - shares address and principal with shell company 1
MERGE (c3:Company {uei: "LMN345OPQ678"})
SET c3.node_id = randomUUID(),
    c3.name = "Pacific Rim Consulting Group",
    c3.cage_code = "9D5E3",
    c3.address = "7701 Ringwood Ave Suite 100, San Diego, CA 92111",
    c3.naics_codes = ["541330", "541512"],
    c3.entity_type = "Corporation",
    c3.set_aside_status = ["8(a)"],
    c3.exclusion_flag = false,
    c3.active = true,
    c3.first_seen = "2020-07-15",
    c3.prominence_score = 0.0;

// Excluded company
MERGE (c4:Company {uei: "RST901UVW234"})
SET c4.node_id = randomUUID(),
    c4.name = "Titan Logistics Group",
    c4.cage_code = "4F6G7",
    c4.address = "200 Commerce Dr, Norfolk, VA 23502",
    c4.naics_codes = ["488510"],
    c4.entity_type = "Corporation",
    c4.set_aside_status = [],
    c4.exclusion_flag = true,
    c4.active = false,
    c4.first_seen = "2015-01-10",
    c4.prominence_score = 0.0;

// New company formed by excluded principal
MERGE (c5:Company {uei: "EFG567HIJ890"})
SET c5.node_id = randomUUID(),
    c5.name = "Apex Maritime Solutions",
    c5.cage_code = "2H8I9",
    c5.address = "200 Commerce Dr, Norfolk, VA 23502",
    c5.naics_codes = ["488510", "541614"],
    c5.entity_type = "LLC",
    c5.set_aside_status = [],
    c5.exclusion_flag = false,
    c5.active = true,
    c5.first_seen = "2022-03-01",
    c5.prominence_score = 0.0;

// --- INDIVIDUALS ---

// Legitimate contracting officer
MERGE (i1:Individual {name: "Commander Sarah Whitfield"})
SET i1.node_id = randomUUID(),
    i1.roles = ["KO", "PCO"],
    i1.complaint_appearances = 0,
    i1.first_seen = "2017-08-01",
    i1.prominence_score = 0.0;

// Revolving door individual - former KO now company principal
MERGE (i2:Individual {name: "James R. Holloway"})
SET i2.node_id = randomUUID(),
    i2.roles = ["KO", "ACO"],
    i2.complaint_appearances = 2,
    i2.first_seen = "2016-04-01",
    i2.prominence_score = 0.0;

// Shell company principal - appears in both shell companies
MERGE (i3:Individual {name: "Marcus T. Delgado"})
SET i3.node_id = randomUUID(),
    i3.roles = ["company principal"],
    i3.complaint_appearances = 1,
    i3.first_seen = "2020-06-01",
    i3.prominence_score = 0.0;

// Excluded individual who formed new company
MERGE (i4:Individual {name: "Patricia L. Vance"})
SET i4.node_id = randomUUID(),
    i4.roles = ["company principal"],
    i4.complaint_appearances = 3,
    i4.first_seen = "2015-01-10",
    i4.prominence_score = 0.0;

// --- CONTRACTS ---

MERGE (ct1:Contract {piid: "N00189-21-C-0042"})
SET ct1.node_id = randomUUID(),
    ct1.award_amount = 4800000.00,
    ct1.obligated_amount = 4800000.00,
    ct1.award_date = "2021-03-10",
    ct1.contract_type = "FFP",
    ct1.competition_type = "FULL_AND_OPEN",
    ct1.set_aside_type = "NONE",
    ct1.naics_code = "541512",
    ct1.place_of_performance = "Arlington, VA",
    ct1.mod_count = 2,
    ct1.prominence_score = 0.0;

MERGE (ct2:Contract {piid: "N62473-20-C-0187"})
SET ct2.node_id = randomUUID(),
    ct2.award_amount = 249000.00,
    ct2.obligated_amount = 249000.00,
    ct2.award_date = "2020-09-15",
    ct2.contract_type = "FFP",
    ct2.competition_type = "SOLE_SOURCE",
    ct2.set_aside_type = "SDVOSB",
    ct2.naics_code = "541330",
    ct2.place_of_performance = "San Diego, CA",
    ct2.mod_count = 0,
    ct2.prominence_score = 0.0;

MERGE (ct3:Contract {piid: "N62473-20-C-0201"})
SET ct3.node_id = randomUUID(),
    ct3.award_amount = 247500.00,
    ct3.obligated_amount = 247500.00,
    ct3.award_date = "2020-11-02",
    ct3.contract_type = "FFP",
    ct3.competition_type = "SOLE_SOURCE",
    ct3.set_aside_type = "8A",
    ct3.naics_code = "541330",
    ct3.place_of_performance = "San Diego, CA",
    ct3.mod_count = 0,
    ct3.prominence_score = 0.0;

MERGE (ct4:Contract {piid: "N00039-22-C-0091"})
SET ct4.node_id = randomUUID(),
    ct4.award_amount = 1200000.00,
    ct4.obligated_amount = 1200000.00,
    ct4.award_date = "2022-05-20",
    ct4.contract_type = "T&M",
    ct4.competition_type = "SOLE_SOURCE",
    ct4.set_aside_type = "NONE",
    ct4.naics_code = "488510",
    ct4.place_of_performance = "Norfolk, VA",
    ct4.mod_count = 4,
    ct4.prominence_score = 0.0;

// --- RELATIONSHIPS ---

// Legitimate award
MATCH (o1:Organization {name: "Naval Supply Systems Command"})
MATCH (c1:Company {uei: "ABC123DEF456"})
MERGE (o1)-[r1:AWARDED_TO {piid: "N00189-21-C-0042"}]->(c1)
SET r1.weight = 0.85,
    r1.confidence = 1.0,
    r1.source = ["FPDS"],
    r1.amount = 4800000.00,
    r1.date = "2021-03-10",
    r1.competition_type = "FULL_AND_OPEN";

// Shell company awards - split threshold pattern
MATCH (o2:Organization {name: "NAVFAC Southwest"})
MATCH (c2:Company {uei: "XYZ789GHI012"})
MERGE (o2)-[r2:AWARDED_TO {piid: "N62473-20-C-0187"}]->(c2)
SET r2.weight = 0.4,
    r2.confidence = 1.0,
    r2.source = ["FPDS"],
    r2.amount = 249000.00,
    r2.date = "2020-09-15",
    r2.competition_type = "SOLE_SOURCE";

MATCH (o2:Organization {name: "NAVFAC Southwest"})
MATCH (c3:Company {uei: "LMN345OPQ678"})
MERGE (o2)-[r3:AWARDED_TO {piid: "N62473-20-C-0201"}]->(c3)
SET r3.weight = 0.4,
    r3.confidence = 1.0,
    r3.source = ["FPDS"],
    r3.amount = 247500.00,
    r3.date = "2020-11-02",
    r3.competition_type = "SOLE_SOURCE";

// Exclusion evasion award
MATCH (o3:Organization {name: "Program Executive Office Digital"})
MATCH (c5:Company {uei: "EFG567HIJ890"})
MERGE (o3)-[r4:AWARDED_TO {piid: "N00039-22-C-0091"}]->(c5)
SET r4.weight = 0.6,
    r4.confidence = 1.0,
    r4.source = ["FPDS"],
    r4.amount = 1200000.00,
    r4.date = "2022-05-20",
    r4.competition_type = "SOLE_SOURCE";

// KO administered legitimate contract
MATCH (ct1:Contract {piid: "N00189-21-C-0042"})
MATCH (i1:Individual {name: "Commander Sarah Whitfield"})
MERGE (ct1)-[r5:ADMINISTERED_BY]->(i1)
SET r5.weight = 1.0,
    r5.confidence = 1.0,
    r5.source = ["FPDS"],
    r5.role = "PCO";

// Revolving door - Holloway administered contract then became principal
MATCH (ct2:Contract {piid: "N62473-20-C-0187"})
MATCH (i2:Individual {name: "James R. Holloway"})
MERGE (ct2)-[r6:ADMINISTERED_BY]->(i2)
SET r6.weight = 0.8,
    r6.confidence = 1.0,
    r6.source = ["FPDS"],
    r6.role = "ACO";

MATCH (i2:Individual {name: "James R. Holloway"})
MATCH (c2:Company {uei: "XYZ789GHI012"})
MERGE (i2)-[r7:PRINCIPAL_OF]->(c2)
SET r7.weight = 0.9,
    r7.confidence = 0.85,
    r7.source = ["SAM", "complaint"],
    r7.title = "Vice President",
    r7.start_date = "2021-06-01";

MATCH (i2:Individual {name: "James R. Holloway"})
MATCH (o2:Organization {name: "NAVFAC Southwest"})
MERGE (i2)-[r8:FORMERLY_EMPLOYED_BY]->(o2)
SET r8.weight = 1.0,
    r8.confidence = 1.0,
    r8.source = ["FPDS"],
    r8.departure_date = "2021-02-28",
    r8.last_role = "ACO";

// Shell company - shared principal
MATCH (i3:Individual {name: "Marcus T. Delgado"})
MATCH (c2:Company {uei: "XYZ789GHI012"})
MERGE (i3)-[r9:PRINCIPAL_OF]->(c2)
SET r9.weight = 1.0,
    r9.confidence = 1.0,
    r9.source = ["SAM"],
    r9.title = "President",
    r9.start_date = "2020-06-01";

MATCH (i3:Individual {name: "Marcus T. Delgado"})
MATCH (c3:Company {uei: "LMN345OPQ678"})
MERGE (i3)-[r10:PRINCIPAL_OF]->(c3)
SET r10.weight = 1.0,
    r10.confidence = 1.0,
    r10.source = ["SAM"],
    r10.title = "Managing Director",
    r10.start_date = "2020-07-15";

// Shell companies share address
MATCH (c2:Company {uei: "XYZ789GHI012"})
MATCH (c3:Company {uei: "LMN345OPQ678"})
MERGE (c2)-[r11:SHARES_ADDRESS_WITH]-(c3)
SET r11.weight = 0.95,
    r11.confidence = 0.99,
    r11.source = ["SAM"],
    r11.address = "7701 Ringwood Ave Suite 100, San Diego, CA 92111",
    r11.shared_attributes = ["address", "principal"];

// Exclusion evasion - Vance principal of excluded company and new company
MATCH (i4:Individual {name: "Patricia L. Vance"})
MATCH (c4:Company {uei: "RST901UVW234"})
MERGE (i4)-[r12:PRINCIPAL_OF]->(c4)
SET r12.weight = 1.0,
    r12.confidence = 1.0,
    r12.source = ["SAM"],
    r12.title = "CEO",
    r12.start_date = "2015-01-10";

MATCH (i4:Individual {name: "Patricia L. Vance"})
MATCH (c5:Company {uei: "EFG567HIJ890"})
MERGE (i4)-[r13:PRINCIPAL_OF]->(c5)
SET r13.weight = 1.0,
    r13.confidence = 0.9,
    r13.source = ["SAM", "complaint"],
    r13.title = "Managing Member",
    r13.start_date = "2022-02-15";

// Complaint co-appearances
MATCH (i4:Individual {name: "Patricia L. Vance"})
MATCH (c5:Company {uei: "EFG567HIJ890"})
MERGE (i4)-[r14:APPEARS_IN_COMPLAINT_WITH]-(c5)
SET r14.weight = 0.7,
    r14.confidence = 0.75,
    r14.source = ["IG complaint"],
    r14.complaint_id = "NAVINSGEN-2023-0042",
    r14.allegation_type = "exclusion_evasion";

MATCH (i2:Individual {name: "James R. Holloway"})
MATCH (c2:Company {uei: "XYZ789GHI012"})
MERGE (i2)-[r15:APPEARS_IN_COMPLAINT_WITH]-(c2)
SET r15.weight = 0.6,
    r15.confidence = 0.7,
    r15.source = ["IG complaint"],
    r15.complaint_id = "NAVINSGEN-2022-0117",
    r15.allegation_type = "revolving_door";