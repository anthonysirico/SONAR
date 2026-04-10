import { useEffect, useRef, useState } from 'react'
import CytoscapeComponent from 'react-cytoscapejs'
import NodeDetail from './NodeDetail'

const NODE_COLORS = {
  Company:      '#0ea5e9',
  Individual:   '#a78bfa',
  Contract:     '#34d399',
  Organization: '#fb923c',
}

function scoreToSize(score) {
  return 20 + score * 80
}

function scoreToColor(score) {
  if (score >= 0.75) return '#ef4444'
  if (score >= 0.50) return '#f97316'
  if (score >= 0.25) return '#eab308'
  return '#6b7280'
}

function transformGraphData(raw) {
  const elements = []

  raw.forEach((record) => {
    const n = record.n
    const m = record.m
    const r = record.r

    if (n) {
      const id = n.node_id || JSON.stringify(n)
      const label = n.name || n.piid || n.node_id || 'Unknown'
      const type = n._labels?.[0] ?? 'Unknown'
      const score = n.prominence_score ?? 0

      elements.push({
        data: {
          id,
          label,
          type,
          color: scoreToColor(score),
          size: scoreToSize(score),
          ...n,
        },
        classes: type,
      })
    }

    if (m) {
      const id = m.node_id || JSON.stringify(m)
      const label = m.name || m.piid || m.node_id || 'Unknown'
      const type = m._labels?.[0] ?? 'Unknown'
      const score = m.prominence_score ?? 0

      elements.push({
        data: {
          id,
          label,
          type,
          color: scoreToColor(score),
          size: scoreToSize(score),
          ...m,
        },
        classes: type,
      })
    }

    if (r && n && m) {
      const sourceId = n.node_id || JSON.stringify(n)
      const targetId = m.node_id || JSON.stringify(m)
      elements.push({
        data: {
          id: `${sourceId}-${targetId}-${r.type ?? ''}`,
          source: sourceId,
          target: targetId,
          label: r.type ?? '',
          weight: r.weight ?? 1,
          confidence: r.confidence ?? 1,
        },
      })
    }
  })

  // Deduplicate nodes by id
  const seen = new Set()
  return elements.filter((el) => {
    if (!el.data.source) {
      if (seen.has(el.data.id)) return false
      seen.add(el.data.id)
    }
    return true
  })
}

const stylesheet = [
  {
    selector: 'node',
    style: {
      'background-color': 'data(color)',
      'width': 'data(size)',
      'height': 'data(size)',
      'label': 'data(label)',
      'color': '#e2e8f0',
      'font-size': '10px',
      'text-valign': 'bottom',
      'text-margin-y': '4px',
      'text-outline-color': '#0f172a',
      'text-outline-width': '2px',
    },
  },
  {
    selector: 'edge',
    style: {
      'width': 1.5,
      'line-color': '#334155',
      'target-arrow-color': '#334155',
      'target-arrow-shape': 'triangle',
      'curve-style': 'bezier',
      'label': 'data(label)',
      'font-size': '8px',
      'color': '#64748b',
      'text-rotation': 'autorotate',
    },
  },
  {
    selector: 'edge[confidence < 0.85]',
    style: {
      'line-style': 'dashed',
    },
  },
  {
    selector: 'edge[confidence < 0.50]',
    style: {
      'line-style': 'dotted',
    },
  },
  {
    selector: 'node:selected',
    style: {
      'border-width': 3,
      'border-color': '#22d3ee',
    },
  },
]

const LAYOUT_OPTIONS = { name: 'cose', animate: true, padding: 40, fit: true }

export default function GraphCanvas({ elements }) {
  const cyRef = useRef(null)
  const [selectedNode, setSelectedNode] = useState(null)

  // Re-run layout whenever elements change
  useEffect(() => {
    const cy = cyRef.current
    if (!cy) return
    if (elements.length === 0) return

    // Small delay to let Cytoscape process the new elements
    const timer = setTimeout(() => {
      try {
        cy.layout(LAYOUT_OPTIONS).run()
      } catch (e) {
        // Guard against renderer-not-ready errors
        console.warn('Layout skipped:', e.message)
      }
    }, 50)

    return () => clearTimeout(timer)
  }, [elements])

  // Tap handlers
  useEffect(() => {
    const cy = cyRef.current
    if (!cy) return

    const onNodeTap = (evt) => setSelectedNode(evt.target)
    const onBgTap = (evt) => { if (evt.target === cy) setSelectedNode(null) }

    cy.on('tap', 'node', onNodeTap)
    cy.on('tap', onBgTap)

    return () => {
      cy.off('tap', 'node', onNodeTap)
      cy.off('tap', onBgTap)
    }
  }, [])

  return (
    <div className="relative w-full h-full">
      <CytoscapeComponent
        elements={elements}
        stylesheet={stylesheet}
        layout={{ name: 'preset' }}
        style={{ width: '100%', height: '100%', background: '#0f172a' }}
        cy={(cy) => { cyRef.current = cy }}
      />
      <NodeDetail
        node={selectedNode}
        onClose={() => setSelectedNode(null)}
      />
    </div>
  )
}