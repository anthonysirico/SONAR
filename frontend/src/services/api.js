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

// ─── Search ─────────────────────────────────────────────────

export async function searchUSASpending(caseId, query, searchType = 'keyword', limit = 25) {
  const res = await fetch(`${API}/api/cases/${caseId}/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, search_type: searchType, limit }),
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