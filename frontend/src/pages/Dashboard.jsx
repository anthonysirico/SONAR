import { useEffect, useState } from 'react'
import GraphCanvas from '../components/GraphCanvas'
import TopBar from '../components/TopBar'
import { fetchFullGraph, computeProminence } from '../services/api'

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

export default function Dashboard() {
  const [elements, setElements] = useState([])
  const [loading, setLoading] = useState(true)
  const [status, setStatus] = useState('')

  const loadGraph = async () => {
    setLoading(true)
    const raw = await fetchFullGraph()
    setElements(transformGraphData(raw))
    setLoading(false)
  }

  const handleCompute = async () => {
    setStatus('Recomputing...')
    await computeProminence()
    await loadGraph()
    setStatus('Done')
    setTimeout(() => setStatus(''), 2000)
  }

  useEffect(() => { loadGraph() }, [])

  return (
    <div className="flex flex-col h-screen bg-gray-950 text-white">
      <TopBar onCompute={handleCompute} />
      {status && (
        <div className="text-center text-xs text-cyan-400 py-1 bg-gray-900">
          {status}
        </div>
      )}
      <div className="flex-1 relative">
        {loading ? (
          <div className="flex items-center justify-center h-full text-gray-500">
            Initializing SONAR...
          </div>
        ) : (
          <GraphCanvas elements={elements} />
        )}
      </div>
    </div>
  )
}