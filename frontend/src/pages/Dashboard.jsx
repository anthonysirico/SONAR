import { useEffect, useState, useCallback } from 'react'
import GraphCanvas from '../components/GraphCanvas'
import TopBar from '../components/TopBar'
import SearchPanel from '../components/SearchPanel'
import {
  fetchFullGraph,
  fetchCaseGraph,
  computeProminence,
  fetchCases,
  createCase,
  searchUSASpending,
  ingestAwards,
} from '../services/api'

// ─── Graph Transform ────────────────────────────────────────

function transformGraphData(raw) {
  const elements = []
  const seen = new Set()

  raw.forEach((record) => {
    const addNode = (n) => {
      if (!n || !n.node_id) return
      if (seen.has(n.node_id)) return
      seen.add(n.node_id)

      const score = n.prominence_score ?? 0
      const label = n.name || n.piid || n.node_id

      let color = '#6b7280'
      if (score >= 0.75) color = '#ef4444'
      else if (score >= 0.50) color = '#f97316'
      else if (score >= 0.25) color = '#eab308'

      elements.push({
        data: {
          id: n.node_id,
          label,
          color,
          size: 20 + score * 80,
          ...n,
        },
      })
    }

    addNode(record.n)
    addNode(record.m)

    const r = record.r
    const n = record.n
    const m = record.m

    if (r && n?.node_id && m?.node_id) {
      const edgeId = `${n.node_id}-${m.node_id}-${JSON.stringify(r)}`
      elements.push({
        data: {
          id: edgeId,
          source: n.node_id,
          target: m.node_id,
          label: '',
          confidence: r.confidence ?? 1,
          weight: r.weight ?? 1,
        },
      })
    }
  })

  return elements
}

// ─── Dashboard ──────────────────────────────────────────────

export default function Dashboard() {
  const [elements, setElements] = useState([])
  const [loading, setLoading] = useState(true)
  const [status, setStatus] = useState('')

  // Case state
  const [cases, setCases] = useState([])
  const [activeCase, setActiveCase] = useState(null)

  // Search state
  const [searchResults, setSearchResults] = useState(null)
  const [searchOpen, setSearchOpen] = useState(false)
  const [searching, setSearching] = useState(false)
  const [ingesting, setIngesting] = useState(false)

  // ─── Load graph ───────────────────────────────────────────

  const loadGraph = useCallback(async () => {
    setLoading(true)
    try {
      let raw
      if (activeCase) {
        raw = await fetchCaseGraph(activeCase.case_id)
      } else {
        raw = await fetchFullGraph()
      }
      setElements(transformGraphData(raw))
    } catch (e) {
      console.error('Graph load failed:', e)
      setElements([])
    }
    setLoading(false)
  }, [activeCase])

  // ─── Load cases on mount ──────────────────────────────────

  useEffect(() => {
    const init = async () => {
      try {
        const c = await fetchCases()
        setCases(c)
      } catch (e) {
        console.error('Failed to load cases:', e)
      }
    }
    init()
  }, [])

  // ─── Reload graph when active case changes ────────────────

  useEffect(() => {
    loadGraph()
  }, [loadGraph])

  // ─── Handlers ─────────────────────────────────────────────

  const handleCreateCase = async (name, description) => {
    try {
      const newCase = await createCase(name, description)
      setCases((prev) => [newCase, ...prev])
      setActiveCase(newCase)
      flash('Case created')
    } catch (e) {
      flash('Failed to create case')
    }
  }

  const handleSelectCase = (c) => {
    setActiveCase(c)
    setSearchResults(null)
    setSearchOpen(false)
  }

  const handleViewAll = () => {
    setActiveCase(null)
    setSearchResults(null)
    setSearchOpen(false)
  }

  const handleSearch = async (query, searchType) => {
    if (!activeCase) return
    setSearching(true)
    setSearchOpen(true)
    setSearchResults(null)
    try {
      const data = await searchUSASpending(activeCase.case_id, query, searchType)
      setSearchResults(data)
    } catch (e) {
      flash(`Search error: ${e.message}`)
      setSearchResults({ error: e.message, results: [] })
    }
    setSearching(false)
  }

  const handleIngest = async (internalIds) => {
    if (!activeCase || internalIds.length === 0) return
    setIngesting(true)
    try {
      const result = await ingestAwards(activeCase.case_id, internalIds)
      flash(`Ingested ${result.ingested} award(s)`)
      if (result.errors?.length > 0) {
        console.warn('Ingest errors:', result.errors)
      }
      await loadGraph()
    } catch (e) {
      flash(`Ingest error: ${e.message}`)
    }
    setIngesting(false)
  }

  const handleCompute = async () => {
    flash('Recomputing...')
    await computeProminence()
    await loadGraph()
    flash('Done')
  }

  const flash = (msg) => {
    setStatus(msg)
    setTimeout(() => setStatus(''), 3000)
  }

  // ─── Render ───────────────────────────────────────────────

  return (
    <div className="flex flex-col h-screen bg-gray-950 text-white">
      <TopBar
        cases={cases}
        activeCase={activeCase}
        onSelectCase={handleSelectCase}
        onViewAll={handleViewAll}
        onCreateCase={handleCreateCase}
        onSearch={handleSearch}
        onCompute={handleCompute}
      />

      {status && (
        <div className="text-center text-xs text-cyan-400 py-1 bg-gray-900 border-b border-gray-800">
          {status}
        </div>
      )}

      <div className="flex-1 relative overflow-hidden">
        {/* Always mount GraphCanvas to avoid Cytoscape destroy/recreate errors */}
        <GraphCanvas elements={elements} />

        {/* Overlay states on top of canvas */}
        {loading && (
          <div className="absolute inset-0 flex items-center justify-center bg-gray-950 text-gray-500 z-10">
            Initializing SONAR...
          </div>
        )}
        {!loading && elements.length === 0 && activeCase && (
          <div className="absolute inset-0 flex flex-col items-center justify-center bg-gray-950 text-gray-500 gap-3 z-10">
            <div className="text-lg">Case: {activeCase.name}</div>
            <div className="text-sm">No nodes yet — search to populate the graph</div>
          </div>
        )}
        {!loading && elements.length === 0 && !activeCase && (
          <div className="absolute inset-0 flex flex-col items-center justify-center bg-gray-950 text-gray-500 gap-3 z-10">
            <div className="text-lg">SONAR ready</div>
            <div className="text-sm">Create a case to begin</div>
          </div>
        )}

        {/* Search results panel — slides over graph from right */}
        <SearchPanel
          open={searchOpen}
          searching={searching}
          ingesting={ingesting}
          results={searchResults}
          onIngest={handleIngest}
          onClose={() => setSearchOpen(false)}
        />
      </div>
    </div>
  )
}