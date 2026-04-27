const API = 'http://localhost:8000'

// ─── Graph ──────────────────────────────────────────────────

export async function fetchFullGraph() {
  const res = await fetch(`${API}/api/graph/`)
  const data = await res.json()
  return data
}

export async function computeProminence() {
  const res = await fetch(`${API}/api/graph/prominence/compute`, { method: 'POST' })
  return res.json()
}

// ─── Cases ──────────────────────────────────────────────────

export async function fetchCases(status = null) {
  const url = status
    ? `${API}/api/cases/?status=${status}`
    : `${API}/api/cases/`
  const res = await fetch(url)
  const data = await res.json()
  return data.cases || []
}

export async function createCase(name, description = '') {
  const res = await fetch(`${API}/api/cases/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, description }),
  })
  const data = await res.json()
  return data.case
}

export async function fetchCaseGraph(caseId) {
  const res = await fetch(`${API}/api/cases/${caseId}/graph`)
  const data = await res.json()
  return data.graph || []
}

// ─── Sources ────────────────────────────────────────────────

export async function fetchSources() {
  const res = await fetch(`${API}/api/sources/`)
  const data = await res.json()
  return data.sources || []
}

// ─── Multi-Source Search ────────────────────────────────────

export async function searchSources(caseId, query, searchType = 'keyword', limit = 25, credentials = {}) {
  const res = await fetch(`${API}/api/cases/${caseId}/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      query,
      search_type: searchType,
      limit,
      credentials,
    }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || `Search failed (${res.status})`)
  }
  return res.json()
}

// ─── Ingest ─────────────────────────────────────────────────

export async function ingestAwards(caseId, internalIds) {
  const res = await fetch(`${API}/api/cases/${caseId}/ingest`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ internal_ids: internalIds }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || `Ingest failed (${res.status})`)
  }
  return res.json()
}

// ─── Enrich (SAM.gov) ───────────────────────────────────────

export async function enrichCompany(caseId, uei, credentials = {}) {
  const res = await fetch(`${API}/api/cases/${caseId}/enrich`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ uei, credentials }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || `Enrichment failed (${res.status})`)
  }
  return res.json()
}

// ─── Enrich (ProPublica 990) ────────────────────────────────

export async function enrichNonprofit(caseId, ein, uei = '') {
  const res = await fetch(`${API}/api/cases/${caseId}/enrich-nonprofit`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ein, uei }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || `Nonprofit enrichment failed (${res.status})`)
  }
  return res.json()
}

// ─── Auto-Enrichment ────────────────────────────────────────

export async function autoEnrich(caseId) {
  const res = await fetch(`${API}/api/cases/${caseId}/auto-enrich`, {
    method: 'POST',
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || `Auto-enrichment failed (${res.status})`)
  }
  return res.json()
}

// ─── Node Listing (for connect-to picker) ───────────────────

export async function fetchCaseNodes(caseId, query = '') {
  const url = query
    ? `${API}/api/cases/${caseId}/nodes?q=${encodeURIComponent(query)}`
    : `${API}/api/cases/${caseId}/nodes`
  const res = await fetch(url)
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || `Node listing failed (${res.status})`)
  }
  const data = await res.json()
  return data.nodes || []
}

// ─── Node Edit ──────────────────────────────────────────────

export async function updateNode(caseId, nodeId, properties) {
  const res = await fetch(`${API}/api/cases/${caseId}/node/${nodeId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ properties }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || `Update failed (${res.status})`)
  }
  return res.json()
}

export async function deleteNode(caseId, nodeId) {
  const res = await fetch(`${API}/api/cases/${caseId}/node/${nodeId}`, {
    method: 'DELETE',
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || `Delete failed (${res.status})`)
  }
  return res.json()
}

// ─── Node Relationships ─────────────────────────────────────

export async function fetchNodeRelationships(caseId, nodeId) {
  const res = await fetch(`${API}/api/cases/${caseId}/node/${nodeId}/relationships`)
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || `Failed (${res.status})`)
  }
  const data = await res.json()
  return data.relationships || []
}

export async function addNodeRelationship(caseId, nodeId, { target_node_id, relationship_type, direction, notes }) {
  const res = await fetch(`${API}/api/cases/${caseId}/node/${nodeId}/relationships`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ target_node_id, relationship_type, direction: direction || 'outgoing', notes: notes || '' }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || `Failed (${res.status})`)
  }
  return res.json()
}

export async function deleteNodeRelationship(caseId, nodeId, relId) {
  const res = await fetch(`${API}/api/cases/${caseId}/node/${nodeId}/relationships/${relId}`, {
    method: 'DELETE',
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || `Failed (${res.status})`)
  }
  return res.json()
}